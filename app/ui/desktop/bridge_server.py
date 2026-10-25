
"""Loopback-only API bridge for the Iskolar ng Bayan desktop UI.

This file lives inside app/ui/desktop and deliberately reuses the existing
repositories and services. It does not create tables or modify backend files.
"""
from __future__ import annotations

import json
import os
import sys
from decimal import Decimal
from datetime import date, datetime, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.chdir(PROJECT_ROOT)

from app.repositories.applicant_repository import ApplicantRepository
from app.repositories.application_repository import ApplicationRepository
from app.repositories.interview_repository import InterviewRepository
from app.repositories.scholarship_decision_repository import (
    ScholarshipDecisionRepository,
)
from app.repositories.screening_result_repository import ScreeningResultRepository
from app.services.application_service import ApplicationService
from app.services.screening_persistence_service import ScreeningPersistenceService
from database.connection import get_connection


HOST, PORT = "127.0.0.1", 8765

ALLOWED_ORIGINS = {
    "http://127.0.0.1:1420",
    "http://localhost:1420",
    "http://tauri.localhost",
    "https://tauri.localhost",
    "tauri://localhost",
    "http://localhost",
    "http://127.0.0.1",
}

_screening_service = None


def clean(value):
    """Recursively convert database values into JSON-compatible values."""
    if isinstance(value, dict):
        return {str(key): clean(item) for key, item in value.items()}

    if isinstance(value, (list, tuple)):
        return [clean(item) for item in value]

    if isinstance(value, Decimal):
        # MySQL DECIMAL values are returned by Python as Decimal.
        # Convert them to numbers so the frontend can use them.
        return float(value)

    if isinstance(value, (datetime, date, time)):
        return value.isoformat()

    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    # Avoid crashing the entire API response if a repository returns an
    # uncommon database-specific value.
    if hasattr(value, "item"):
        try:
            return clean(value.item())
        except (ValueError, TypeError):
            pass

    raise TypeError(
        f"Object of type {type(value).__name__} is not JSON serializable"
    )


def read_screening_service():
    global _screening_service

    if _screening_service is None:
        _screening_service = ScreeningPersistenceService()

    return _screening_service


def enrich_applications(applications):
    applicants = {
        int(applicant["applicant_id"]): applicant
        for applicant in ApplicantRepository.get_all()
    }

    enriched = []

    for application in applications:
        item = dict(application)
        applicant = applicants.get(int(item.get("applicant_id") or 0), {})

        item["applicant_name"] = " ".join(
            str(applicant.get(key) or "").strip()
            for key in ("first_name", "middle_name", "last_name", "suffix")
            if str(applicant.get(key) or "").strip()
        ) or "Unknown applicant"

        enriched.append(item)

    return enriched


def dashboard_data():
    applicants = ApplicantRepository.get_all()
    applications = enrich_applications(ApplicationRepository.get_all())
    interviews = InterviewRepository.get_all()
    decisions = ScholarshipDecisionRepository.get_all()

    counts = {}

    for application in applications:
        status = str(application.get("status") or "UNKNOWN").upper()
        counts[status] = counts.get(status, 0) + 1

    latest = sorted(
        applications,
        key=lambda application: str(application.get("created_at") or ""),
        reverse=True,
    )[:6]

    return {
        "stats": {
            "applicants": len(applicants),
            "applications": len(applications),
            "pending": sum(
                1
                for application in applications
                if str(application.get("status") or "").upper()
                in {
                    "PENDING",
                    "SUBMITTED",
                    "DRAFT",
                    "FOR_REVIEW",
                    "UNDER_REVIEW",
                }
            ),
            "interviews": sum(
                1
                for interview in interviews
                if str(interview.get("status") or "").upper()
                in {"SCHEDULED", "RESCHEDULED"}
            ),
            "approved": sum(
                1
                for decision in decisions
                if str(decision.get("decision") or "").upper() == "APPROVED"
            ),
        },
        "statusCounts": counts,
        "recentApplications": latest,
        "upcomingInterviews": InterviewRepository.get_upcoming(limit=5),
    }


def application_screening_inputs(app):
    """
    Convert a saved applications-table row into the input expected by
    ml_screening_service.py.

    The database stores exam_score as a percentage from 0 to 100.
    It does not store the original raw score or total number of items.
    The database stores dependent as a boolean, not a dependent count.
    """
    percentage = float(app.get("exam_score") or 0)
    percentage = max(0.0, min(100.0, percentage))

    household = int(app.get("household") or 1)

    return {
        "average": float(app.get("academic_average") or 0),
        "income": float(app.get("monthly_income") or 0),
        "household": household,
        "children": int(app.get("children_count") or 0),
        "seniors": int(app.get("senior_count") or 0),
        "pwds": int(app.get("pwd_count") or 0),

        # Only the dependent flag is saved in the current schema.
        "dependents": int(bool(app.get("dependent", 0))),
        "solo": int(bool(app.get("solo_parent", 0))),

        # Reconstruct a percentage-based representation for the model.
        # The original raw score and item total cannot be recovered.
        "exam_score": round(percentage),
        "exam_total": 100,
        "exam_passed": int(percentage >= 80),

        "fourps": int(bool(app.get("four_ps_beneficiary", 0))),
        "spes": int(bool(app.get("spes_beneficiary", 0))),
        "scholars": int(app.get("scholars_in_family") or 0),
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "IskolarLocalBridge/2.1"

    def log_message(self, fmt, *args):
        # Keep personal applicant details out of the console log.
        print(f"[bridge] {self.address_string()} - {fmt % args}")

    def _send(self, status, payload):
        """Send a JSON response after normalizing database values."""
        try:
            body = json.dumps(
                clean(payload),
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")
        except (TypeError, ValueError) as exc:
            # Log serialization failures so they can be diagnosed.
            print(f"[bridge] JSON serialization failed: {exc}")
            status = 500
            body = json.dumps(
                {"error": "The server could not serialize its response."}
            ).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))

        origin = self.headers.get("Origin", "")

        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")

        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, PUT, DELETE, OPTIONS",
        )
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            # The frontend may have closed the request before receiving it.
            pass

    def _body(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise ValueError("Invalid Content-Length header.")

        if length < 0:
            raise ValueError("Invalid Content-Length header.")

        if length > 100_000:
            raise OverflowError("Request too large.")

        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        value = json.loads(raw or "{}")

        if not isinstance(value, dict):
            raise ValueError("Request body must be a JSON object.")

        return value

    def _error(self, exc):
        if isinstance(exc, OverflowError):
            return self._send(413, {"error": str(exc)})

        if isinstance(exc, (ValueError, TypeError, json.JSONDecodeError)):
            return self._send(400, {"error": str(exc)})

        print(f"[bridge] request failed: {type(exc).__name__}: {exc}")
        return self._send(500, {"error": str(exc)})

    def do_OPTIONS(self):
        return self._send(200, {"ok": True})

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/") or "/"

        try:
            if path == "/api/health":
                return self._send(
                    200,
                    {"ok": True, "service": "Iskolar local bridge"},
                )

            if path == "/api/dashboard":
                return self._send(200, dashboard_data())

            if path == "/api/applicants":
                return self._send(
                    200,
                    {"items": ApplicantRepository.get_all()},
                )

            if path == "/api/applications":
                return self._send(
                    200,
                    {
                        "items": enrich_applications(
                            ApplicationRepository.get_all()
                        )
                    },
                )

            if path == "/api/interviews":
                return self._send(
                    200,
                    {
                        "items": InterviewRepository.get_all(),
                        "awaitingSchedule": (
                            InterviewRepository.get_awaiting_schedule()
                        ),
                    },
                )

            if path == "/api/decisions":
                return self._send(
                    200,
                    {"items": ScholarshipDecisionRepository.get_all()},
                )

            if path == "/api/screening-results":
                connection = get_connection()

                try:
                    with connection.cursor(dictionary=True) as cursor:
                        cursor.execute(
                            """
                            SELECT sr.screening_id,
                                   sr.application_id,
                                   sr.predicted_class,
                                   sr.confidence_score,
                                   sr.explanation,
                                   sr.screened_at,
                                   a.scholarship_program,
                                   a.scholarship_year,
                                   CONCAT_WS(
                                       ' ',
                                       p.first_name,
                                       p.middle_name,
                                       p.last_name,
                                       p.suffix
                                   ) AS applicant_name
                            FROM screening_results sr
                            JOIN applications a
                                ON a.application_id = sr.application_id
                            JOIN applicants p
                                ON p.applicant_id = a.applicant_id
                            WHERE a.is_archived = FALSE
                              AND p.is_archived = FALSE
                            ORDER BY sr.screened_at DESC
                            LIMIT 250
                            """
                        )

                        return self._send(
                            200,
                            {"items": cursor.fetchall()},
                        )
                finally:
                    connection.close()

            if path.startswith("/api/applicants/"):
                applicant_id = int(path.rsplit("/", 1)[1])
                item = ApplicantRepository.get_by_id(applicant_id)

                if item:
                    return self._send(200, {"item": item})

                return self._send(404, {"error": "Applicant not found."})

            if path.startswith("/api/applications/"):
                application_id = int(path.rsplit("/", 1)[1])
                item = ApplicationRepository.get_by_id(application_id)

                if item:
                    return self._send(200, {"item": item})

                return self._send(404, {"error": "Application not found."})

            return self._send(404, {"error": "Endpoint not found"})

        except Exception as exc:
            return self._error(exc)

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/") or "/"

        try:
            data = self._body()

            if path == "/api/register":
                applicant = data.get("applicant") or {}
                application = data.get("application") or {}

                applicant_id, application_id = (
                    ApplicationService.register_applicant_with_application(
                        applicant,
                        application,
                    )
                )

                return self._send(
                    201,
                    {
                        "ok": True,
                        "applicant_id": applicant_id,
                        "application_id": application_id,
                    },
                )

            if path == "/api/screening":
                application_id = int(data.get("application_id", 0))
                application = ApplicationRepository.get_by_id(application_id)

                if not application:
                    return self._send(
                        404,
                        {"error": "Application not found."},
                    )

                result = read_screening_service().screen_application(
                    application_id,
                    application_screening_inputs(application),
                )

                return self._send(201, {"ok": True, "result": result})

            if path == "/api/decisions":
                application_id = int(data.get("application_id", 0))
                decision = str(data.get("decision", "")).upper()
                reason = str(data.get("reason", "")).strip()
                decided_at = data.get("decided_at") or (
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )

                new_id = ScholarshipDecisionRepository.save(
                    application_id,
                    decision,
                    reason,
                    decided_at,
                )

                return self._send(
                    201,
                    {"ok": True, "decision_id": new_id},
                )

            if path == "/api/interviews":
                application_id = int(data.get("application_id", 0))
                application = ApplicationRepository.get_by_id(application_id)

                if not application:
                    return self._send(
                        404,
                        {"error": "Application not found."},
                    )

                if application.get("status") != "FOR_INTERVIEW":
                    return self._send(
                        400,
                        {
                            "error": (
                                "Only applications marked FOR_INTERVIEW "
                                "can be scheduled."
                            )
                        },
                    )

                scheduled_at = str(data.get("scheduled_at", "")).strip()

                if not scheduled_at:
                    return self._send(
                        400,
                        {"error": "Interview date and time are required."},
                    )

                new_id = InterviewRepository.create(
                    application_id,
                    scheduled_at,
                    data.get("location"),
                    data.get("remarks"),
                )

                return self._send(
                    201,
                    {"ok": True, "interview_id": new_id},
                )

            if path.startswith("/api/interviews/") and path.endswith("/result"):
                interview_id = int(path.split("/")[-2])
                result = str(data.get("result", "")).upper()
                remarks = str(data.get("remarks", "")).strip()

                updated = InterviewRepository.update_result(
                    interview_id,
                    result,
                    remarks,
                )

                if updated:
                    return self._send(200, {"ok": True})

                return self._send(
                    404,
                    {"error": "Interview not found."},
                )

            return self._send(404, {"error": "Endpoint not found"})

        except Exception as exc:
            return self._error(exc)

    def do_PUT(self):
        path = urlparse(self.path).path.rstrip("/")

        try:
            data = self._body()

            if path.startswith("/api/applicants/"):
                applicant_id = int(path.rsplit("/", 1)[1])
                allowed = ApplicantRepository.ALLOWED_UPDATE_FIELDS

                fields = {
                    key: value
                    for key, value in data.items()
                    if key in allowed
                }

                updated = ApplicantRepository.update(
                    applicant_id,
                    **fields,
                )

                if updated:
                    return self._send(200, {"ok": True})

                return self._send(
                    404,
                    {"error": "Applicant not found or no fields changed."},
                )

            if path.startswith("/api/applications/"):
                application_id = int(path.rsplit("/", 1)[1])
                allowed = (
                    ApplicationRepository.ALLOWED_UPDATE_FIELDS - {"status"}
                )

                fields = {
                    key: value
                    for key, value in data.items()
                    if key in allowed
                }

                # Validate the requested transition before applying edits.
                if "status" in data:
                    current_app = ApplicationRepository.get_by_id(
                        application_id
                    )

                    if current_app is None:
                        return self._send(
                            404,
                            {"error": "Application not found."},
                        )

                    requested_status = str(data["status"]).strip().upper()
                    current_status = str(
                        current_app.get("status") or ""
                    ).upper()

                    allowed_transitions = (
                        ApplicationService.ALLOWED_TRANSITIONS.get(
                            current_status,
                            set(),
                        )
                    )

                    if (
                        requested_status != current_status
                        and requested_status not in allowed_transitions
                    ):
                        raise ValueError(
                            f"Cannot change application status from "
                            f"{current_status} to {requested_status}."
                        )

                # Recalculate poverty eligibility if related fields change.
                if any(
                    key in fields
                    for key in (
                        "monthly_income",
                        "household",
                        "children_count",
                        "senior_count",
                        "pwd_count",
                    )
                ):
                    current = ApplicationRepository.get_by_id(application_id)

                    if current is None:
                        return self._send(
                            404,
                            {"error": "Application not found."},
                        )

                    combined = {
                        key: current.get(key)
                        for key in (
                            "household",
                            "children_count",
                            "senior_count",
                            "pwd_count",
                            "monthly_income",
                        )
                    }

                    combined.update(
                        {
                            key: value
                            for key, value in fields.items()
                            if key in combined
                        }
                    )

                    threshold = ApplicationService.mswdo_threshold(
                        int(combined["household"]),
                        int(combined["children_count"] or 0),
                        int(combined["senior_count"] or 0),
                        int(combined["pwd_count"] or 0),
                    )

                    fields["mswdo_poverty_eligible"] = (
                        float(combined["monthly_income"]) <= threshold
                    )

                # Support this field if an existing repository allows it,
                # while persisting only the schema's dependent boolean.
                if "dependents_count" in fields:
                    fields["dependent"] = (
                        int(fields["dependents_count"]) > 0
                    )
                    fields.pop("dependents_count", None)

                updated = (
                    ApplicationRepository.update(
                        application_id,
                        **fields,
                    )
                    if fields
                    else False
                )

                if "status" in data:
                    status_updated = ApplicationService.change_status(
                        application_id,
                        data["status"],
                    )
                    updated = bool(updated or status_updated)

                if updated:
                    return self._send(200, {"ok": True})

                return self._send(
                    404,
                    {
                        "error": (
                            "Application not found or no fields changed."
                        )
                    },
                )

            return self._send(404, {"error": "Endpoint not found"})

        except Exception as exc:
            return self._error(exc)

    def do_DELETE(self):
        path = urlparse(self.path).path.rstrip("/")

        try:
            if path.startswith("/api/applicants/"):
                applicant_id = int(path.rsplit("/", 1)[1])
                archived = ApplicantRepository.archive(applicant_id)

                if archived:
                    return self._send(200, {"ok": True})

                return self._send(
                    404,
                    {
                        "error": (
                            "Applicant not found or already archived."
                        )
                    },
                )

            return self._send(404, {"error": "Endpoint not found"})

        except Exception as exc:
            return self._error(exc)


def main():
    try:
        server = ThreadingHTTPServer((HOST, PORT), Handler)
    except OSError as exc:
        print(f"Could not start local bridge on {HOST}:{PORT}: {exc}")
        raise SystemExit(1)

    print(f"Iskolar local bridge running at http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop it.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping local bridge...")
    finally:
        server.server_close()



if __name__ == "__main__":
    main()
