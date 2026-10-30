"""Durable staff activity using the existing audit_logs table.

An entry is committed before a business operation starts. If recording its
outcome fails, the STARTED entry remains visible instead of inventing success.
Identity is supplied by the authenticated bridge, never by the request body.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from database.connection import get_connection


_STATUS_FIELDS = {
    "previous_status", "new_status", "status", "result", "decision", "http_method",
}
_ALLOWED_STATUSES = {
    "DRAFT", "SUBMITTED", "UNDER_REVIEW", "FOR_INTERVIEW", "INTERVIEWED",
    "RECOMMENDED", "APPROVED", "REJECTED", "WAITLISTED", "WITHDRAWN",
    "SCHEDULED", "RESCHEDULED", "COMPLETED", "CANCELLED", "NO_SHOW", "ONGOING",
}
_ENUM_VALUES = {
    "previous_status": _ALLOWED_STATUSES,
    "new_status": _ALLOWED_STATUSES,
    "status": _ALLOWED_STATUSES,
    "result": {"PASSED", "FAILED", "FOR_FURTHER_REVIEW"},
    "decision": {"APPROVED", "REJECTED", "WAITLISTED"},
    "http_method": {"GET", "POST", "PUT", "DELETE", "OPTIONS"},
}
_ID_FIELDS = {
    "application_id", "applicant_id", "interview_id", "screening_id", "decision_id",
}
_SENSITIVE_FIELD_PARTS = {"password", "token", "secret", "credential", "authorization"}


def _positive_id(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{label} must be a positive integer.")
    return value


def _label(value: Any, label: str, maximum: int = 100) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f"{label} is required and must be at most {maximum} characters.")
    return value.strip()


def _actor_snapshot(actor: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(actor, dict):
        raise ValueError("Verified actor identity is required.")
    role = actor.get("role")
    if role not in {"ADMIN", "LYDO_OFFICIAL"}:
        raise ValueError("Unsupported staff role.")
    username = _label(actor.get("username"), "Actor username", 255)
    return {
        "user_id": _positive_id(actor.get("user_id"), "Actor user ID"),
        "username": username,
        "display_name": _label(actor.get("display_name") or username, "Actor display name", 255),
        "role": role,
    }


def _safe_details(details: dict[str, Any] | None) -> dict[str, Any]:
    """Keep operation metadata, not credentials, raw form data or contact data."""
    if details is None:
        return {}
    if not isinstance(details, dict):
        raise ValueError("Activity details must be an object.")
    safe: dict[str, Any] = {}
    for key in _STATUS_FIELDS:
        value = details.get(key)
        if isinstance(value, str) and value.strip() and len(value) <= 100:
            normalized = value.strip().upper()
            if normalized in _ENUM_VALUES[key]:
                safe[key] = normalized
    for key in _ID_FIELDS:
        value = details.get(key)
        if isinstance(value, int) and not isinstance(value, bool) and value > 0:
            safe[key] = value
    fields = details.get("fields")
    if isinstance(fields, (list, tuple)):
        safe["fields"] = sorted({
            field for field in fields
            if isinstance(field, str) and 0 < len(field) <= 100
            and field.replace("_", "").isalnum()
            and not any(part in field.lower() for part in _SENSITIVE_FIELD_PARTS)
        })[:100]
    return safe


def begin_activity(
    actor: dict[str, Any], action: str, entity_type: str,
    entity_id: int | None = None, details: dict[str, Any] | None = None,
) -> int:
    """Commit a STARTED entry before the caller performs a business mutation."""
    snapshot = _actor_snapshot(actor)
    action = _label(action, "Activity action")
    entity_type = _label(entity_type, "Activity entity type")
    if entity_id is not None:
        entity_id = _positive_id(entity_id, "Activity entity ID")
    payload = _safe_details(details)
    payload.update({"actor": snapshot, "outcome": "STARTED"})
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO audit_logs (action, entity_type, entity_id, details) "
            "VALUES (%s, %s, %s, %s)",
            (action, entity_type, entity_id, encoded),
        )
        audit_id = int(cursor.lastrowid)
        if audit_id < 1:
            raise RuntimeError("The activity entry could not be identified.")
        connection.commit()
        return audit_id
    except Exception:
        connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def finish_activity(
    audit_id: int, success: bool, entity_id: int | None = None, http_status: int = 200,
) -> None:
    """Finalize a STARTED entry without replacing its verified actor snapshot."""
    audit_id = _positive_id(audit_id, "Audit ID")
    if not isinstance(success, bool):
        raise ValueError("Activity success must be true or false.")
    if isinstance(http_status, bool) or not isinstance(http_status, int) or not 100 <= http_status <= 599:
        raise ValueError("Activity HTTP status is invalid.")
    if entity_id is not None:
        entity_id = _positive_id(entity_id, "Activity entity ID")
    outcome = "SUCCEEDED" if success else "FAILED"
    finished_at = datetime.now(timezone.utc).isoformat()
    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE audit_logs "
            "SET details = JSON_SET(details, '$.outcome', %s, '$.http_status', %s, '$.finished_at', %s), "
            "entity_id = COALESCE(%s, entity_id) "
            "WHERE audit_id = %s AND JSON_UNQUOTE(JSON_EXTRACT(details, '$.outcome')) = 'STARTED'",
            (outcome, http_status, finished_at, entity_id, audit_id),
        )
        if cursor.rowcount != 1:
            raise RuntimeError("The started activity entry was not found or is already finalized.")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def list_activity(limit: int = 250) -> list[dict[str, Any]]:
    """Return latest real audit records; legacy missing identities stay missing."""
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 1000:
        raise ValueError("Activity limit must be an integer between 1 and 1000.")
    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT audit_id, action, entity_type, entity_id, details, created_at "
            "FROM audit_logs ORDER BY created_at DESC, audit_id DESC LIMIT %s",
            (limit,),
        )
        items = []
        for row in cursor.fetchall():
            item = dict(row)
            details = item.get("details")
            if isinstance(details, (str, bytes, bytearray)):
                try:
                    details = json.loads(details)
                except (ValueError, UnicodeDecodeError):
                    details = {}
            item["details"] = details if isinstance(details, dict) else {}
            items.append(item)
        return items
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()
