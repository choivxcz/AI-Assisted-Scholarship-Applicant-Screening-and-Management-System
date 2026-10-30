
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
from app.ui.desktop import staff_auth, activity_store
from functools import wraps


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
        item["barangay"] = applicant.get("barangay")
        item["municipality"] = applicant.get("municipality")

        enriched.append(item)

    return enriched


def dashboard_data():
    applicants = ApplicantRepository.get_all()
    applications = enrich_applications(ApplicationRepository.get_all())
    interviews = InterviewRepository.get_all()
    decisions = ScholarshipDecisionRepository.get_all()
    application_lookup = {int(item["application_id"]): item for item in applications}
    activity = []
    for application in applications:
        stamp = application.get("submitted_at") or application.get("created_at")
        if stamp:
            activity.append({
                "type": "application", "id": application["application_id"], "at": stamp,
                "title": "New application submitted" if application.get("submitted_at") else "Application created",
                "detail": " · ".join(str(value) for value in (application.get("applicant_name"), application.get("scholarship_program")) if value),
            })
    for interview in interviews:
        completed = interview.get("status") == "COMPLETED"
        stamp = interview.get("updated_at") if completed else interview.get("created_at")
        if stamp:
            activity.append({
                "type": "interview", "id": interview["interview_id"], "at": stamp,
                "title": "Interview result recorded" if completed else "Interview scheduled",
                "detail": " · ".join(str(value) for value in (interview.get("applicant_name"), interview.get("result") if completed else interview.get("location")) if value),
            })
    for decision in decisions:
        if decision.get("decided_at"):
            application = application_lookup.get(int(decision.get("application_id") or 0), {})
            activity.append({
                "type": "decision", "id": decision["decision_id"], "at": decision["decided_at"],
                "title": "Official decision recorded",
                "detail": " · ".join(str(value) for value in (application.get("applicant_name"), decision.get("decision")) if value),
            })

    counts = {}

    for application in applications:
        status = str(application.get("status") or "UNKNOWN").upper()
        counts[status] = counts.get(status, 0) + 1

    latest = sorted(
        applications,
        key=lambda application: str(application.get("created_at") or ""),
        reverse=True,
    )[:6]

    trend = {}
    for application in applications:
        created = application.get("created_at")
        if created:
            month = str(created)[:7]
            trend[month] = trend.get(month, 0) + 1

    return {
        "recentActivity": sorted(activity, key=lambda event: str(event["at"]), reverse=True)[:6],
        "applicationTrend": dict(sorted(trend.items())[-12:]),
        "stats": {
            "applicants": len(applicants),
            "applications": len(applications),
            "awaitingDecision": sum(
                1 for interview in interviews
                if interview.get("status") == "COMPLETED"
                and interview.get("application_status") in {"FOR_INTERVIEW", "INTERVIEWED"}
            ),
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


def staff_access(method):
    """Verify individual identity and reserve audit entries before workspace writes."""
    @wraps(method)
    def protected(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        self._activity_id = None
        if method.__name__ == "do_GET" and path == "/api/health":
            return method(self)
        if path == "/api/auth/requests":
            return self._send(410, {"error": "Staff sign-up is disabled. Use a preconfigured individual account."})
        if method.__name__ == "do_POST" and path == "/api/auth/login":
            return method(self)
        try:
            self.user = staff_auth.require_user(getattr(self, "headers", {}))
            if method.__name__ in {"do_POST", "do_PUT", "do_DELETE"}:
                data = self._body() if method.__name__ != "do_DELETE" else {}
                self._parsed_body = data
                parts = path.removeprefix("/api/").split("/")
                entity_type = {"register": "application", "applicants": "applicant", "applications": "application", "screening": "screening", "interviews": "interview", "decisions": "decision", "auth": "session"}.get(parts[0], "workspace")
                entity_id = None
                if len(parts) > 1 and parts[1].isdigit():
                    entity_id = int(parts[1])
                action = {
                    ("do_POST", "register"): "REGISTER_APPLICANT_AND_APPLICATION",
                    ("do_POST", "screening"): "SCREEN_APPLICATION",
                    ("do_POST", "decisions"): "RECORD_OFFICIAL_DECISION",
                    ("do_POST", "interviews"): "SCHEDULE_INTERVIEW" if len(parts) == 1 else "RECORD_INTERVIEW_RESULT",
                    ("do_POST", "auth"): "SIGN_OUT",
                    ("do_PUT", "applicants"): "EDIT_APPLICANT",
                    ("do_PUT", "applications"): "CHANGE_APPLICATION_STATUS" if "status" in data else "EDIT_APPLICATION",
                    ("do_DELETE", "applicants"): "ARCHIVE_APPLICANT",
                }.get((method.__name__, parts[0]), "WORKSPACE_REQUEST")
                details = {"fields": sorted(key for key in data if key not in {"password", "token", "actor", "user_id", "role"}), "http_method": method.__name__.removeprefix("do_")}
                for key in ("status", "decision", "result"):
                    if key in data:
                        details["new_status" if key == "status" else key] = str(data[key])[:100]
                if str(data.get("application_id", "")).isdigit():
                    details["application_id"] = int(data["application_id"])
                if entity_type == "application" and entity_id and method.__name__ == "do_PUT":
                    current = ApplicationRepository.get_by_id(entity_id)
                    if current:
                        details["previous_status"] = current.get("status")
                self._activity_id = activity_store.begin_activity(self.user, action, entity_type, entity_id, details)
            return method(self)
        except staff_auth.AccessError as exc:
            return self._send(exc.status, {"error": str(exc)})
        except Exception as exc:
            return self._error(exc)
    return protected


class Handler(BaseHTTPRequestHandler):
    server_version = "IskolarLocalBridge/2.1"

    def log_message(self, fmt, *args):
        # Keep personal applicant details out of the console log.
        print(f"[bridge] {self.address_string()} - {fmt % args}")

    def _send(self, status, payload):
        activity_id = getattr(self, "_activity_id", None)
        if activity_id is not None:
            self._activity_id = None
            entity_id = None
            if isinstance(payload, dict):
                for key in ("decision_id", "interview_id", "application_id", "applicant_id"):
                    if isinstance(payload.get(key), int):
                        entity_id = payload[key]
                        break
                result = payload.get("result")
                if isinstance(result, dict) and isinstance(result.get("screening_id"), int):
                    entity_id = result["screening_id"]
            try:
                activity_store.finish_activity(activity_id, status < 400, entity_id=entity_id, http_status=status)
            except Exception:
                print(f"[bridge] Could not finalize activity {activity_id}", flush=True)
                status, payload = 503, {"error": "The operation may already be saved, but its activity entry could not be finalized. Check Activity Log before retrying."}
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

        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))

            origin = self.headers.get("Origin", "")

            if origin and origin not in ALLOWED_ORIGINS:
                print(f"[bridge] Browser origin is not allowed: {origin!r}", flush=True)
            if origin in ALLOWED_ORIGINS:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")

            self.send_header(
                "Access-Control-Allow-Methods",
                "GET, POST, PUT, DELETE, OPTIONS",
            )
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
            self.end_headers()

            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            # Navigation, refresh, or AbortController can close the frontend
            # connection during either the headers or the response body.
            # Do not attempt a second response on that disconnected socket.
            self.close_connection = True

    def _body(self):
        if hasattr(self, "_parsed_body"):
            return self._parsed_body
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

    @staff_access
    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/") or "/"

        try:
            if path == "/api/health":
                return self._send(
                    200,
                    {"ok": True, "service": "Iskolar local bridge"},
                )

            if path == "/api/auth/me":
                return self._send(200, {"user": self.user})
            if path == "/api/activity":
                return self._send(200, {"items": activity_store.list_activity()})

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
                            ORDER BY sr.screened_at DESC, sr.screening_id DESC
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

    @staff_access
    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/") or "/"

        try:
            data = self._body()

            if path == "/api/auth/login":
                try:
                    session = staff_auth.authenticate(data.get("username", ""), data.get("password", ""))
                    try:
                        entry = activity_store.begin_activity(session["user"], "SIGN_IN", "session")
                        activity_store.finish_activity(entry, True, http_status=200)
                    except Exception:
                        staff_auth.logout({"Authorization": "Bearer " + session["token"]})
                        raise
                    return self._send(200, session)
                except staff_auth.AccessError as exc:
                    return self._send(exc.status, {"error": str(exc)})
            if path == "/api/auth/logout":
                staff_auth.logout(self.headers)
                return self._send(200, {"ok": True})

            if path == "/api/register":
                applicant = data.get("applicant") or {}
                application = dict(data.get("application") or {})
                # Public/local registration cannot create an official award.
                if str(application.get("status") or "DRAFT").upper() != "DRAFT":
                    return self._send(403, {"error": "New applications must begin as draft. Official decisions require verified authorization."})
                application["status"] = "DRAFT"

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
                    screened_by=self.user["user_id"],
                )

                return self._send(201, {"ok": True, "result": result})

            if path == "/api/decisions":
                decision_id = ScholarshipDecisionRepository.save(
                    int(data.get("application_id", 0)),
                    data.get("decision", ""),
                    data.get("reason", ""),
                    datetime.now(),
                )
                return self._send(201, {"ok": True, "decision_id": decision_id})

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

    @staff_access
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
                    if requested_status in {"APPROVED", "REJECTED", "WAITLISTED"}:
                        return self._send(403, {"error": "Use Record decision to save an official decision with required remarks and accountable history."})
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

    @staff_access
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
