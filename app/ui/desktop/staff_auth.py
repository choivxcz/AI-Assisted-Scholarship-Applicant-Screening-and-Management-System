"""Verified local staff sessions for the desktop bridge; no public registration."""
from __future__ import annotations

from collections import deque
import hashlib
import secrets
from threading import BoundedSemaphore, RLock
import time

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from database.connection import get_connection

ROLES = frozenset({"ADMIN", "LYDO_OFFICIAL"})
SESSION_SECONDS = 8 * 60 * 60
RATE_WINDOW_SECONDS = 60
MAX_ATTEMPTS_PER_USER = 5
MAX_ATTEMPTS_GLOBAL = 60
MAX_TRACKED_USERNAMES = 1024
MAX_SESSIONS = 1024
PASSWORD_HASHER = PasswordHasher()
_DUMMY_HASH = PASSWORD_HASHER.hash(secrets.token_urlsafe(32))
_lock = RLock()
_password_checks = BoundedSemaphore(2)
_sessions: dict[str, dict] = {}
_attempts: dict[str, deque] = {}
_global_attempts: deque = deque()


class AccessError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


def _read_user(column: str, value):
    # Column values are internal constants; user values remain SQL parameters.
    if column not in {"username", "user_id"}:
        raise ValueError("Unsupported account lookup.")
    connection = None
    try:
        connection = get_connection()
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT user_id, username, password_hash, first_name, last_name, role, is_active "
                f"FROM users WHERE {column} = %s LIMIT 1",
                (value,),
            )
            return cursor.fetchone()
    except Exception as error:
        raise AccessError(503, "Staff account storage is unavailable. Configure the local staff accounts and check the database connection.") from error
    finally:
        if connection is not None:
            connection.close()


def _actor(row: dict) -> dict:
    return {
        "user_id": int(row["user_id"]),
        "username": str(row["username"]),
        "first_name": str(row.get("first_name") or ""),
        "last_name": str(row.get("last_name") or ""),
        "display_name": " ".join(str(row.get(key) or "").strip() for key in ("first_name", "last_name")).strip() or str(row["username"]),
        "role": str(row["role"]),
        "is_active": True,
    }


def _usable(row) -> bool:
    return bool(row and row.get("is_active") in (1, True) and row.get("role") in ROLES)


def _credential_fingerprint(row: dict) -> str:
    return hashlib.sha256(str(row.get("password_hash") or "").encode("utf-8")).hexdigest()


def _reserve_attempt(username: str, now: float):
    with _lock:
        while _global_attempts and _global_attempts[0] <= now - RATE_WINDOW_SECONDS:
            _global_attempts.popleft()
        for key in list(_attempts):
            while _attempts[key] and _attempts[key][0] <= now - RATE_WINDOW_SECONDS:
                _attempts[key].popleft()
            if not _attempts[key]:
                del _attempts[key]
        per_user = _attempts.get(username)
        if len(_global_attempts) >= MAX_ATTEMPTS_GLOBAL or (per_user is not None and len(per_user) >= MAX_ATTEMPTS_PER_USER):
            raise AccessError(429, "Too many sign-in attempts. Wait a minute and try again.")
        if per_user is None:
            if len(_attempts) >= MAX_TRACKED_USERNAMES:
                raise AccessError(429, "Too many sign-in attempts. Wait a minute and try again.")
            per_user = _attempts[username] = deque()
        per_user.append(now)
        _global_attempts.append(now)


def authenticate(username, password) -> dict:
    if not isinstance(username, str) or not isinstance(password, str) or not username.strip() or not password or len(username.strip()) > 50 or len(password) > 1024:
        raise AccessError(400, "Enter a valid username and password.")
    username = username.strip()
    _reserve_attempt(username.casefold(), time.monotonic())
    row = _read_user("username", username)
    password_hash = row.get("password_hash") if row else _DUMMY_HASH
    if not _password_checks.acquire(blocking=False):
        raise AccessError(503, "Sign-in is busy. Try again shortly.")
    try:
        try:
            valid_password = PASSWORD_HASHER.verify(password_hash or _DUMMY_HASH, password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            valid_password = False
    finally:
        _password_checks.release()
    if not valid_password or not _usable(row):
        raise AccessError(401, "Invalid username or password.")

    now = time.monotonic()
    token = secrets.token_urlsafe(32)
    token_digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    with _lock:
        for key in list(_sessions):
            if _sessions[key]["expires_at"] <= now:
                del _sessions[key]
        if len(_sessions) >= MAX_SESSIONS:
            raise AccessError(503, "Too many active sessions. Try again later.")
        _sessions[token_digest] = {
            "user_id": int(row["user_id"]),
            "credential_fingerprint": _credential_fingerprint(row),
            "expires_at": now + SESSION_SECONDS,
        }
        _attempts.pop(username.casefold(), None)
    return {"token": token, "user": _actor(row)}


def _token_digest(headers) -> str | None:
    authorization = str((headers or {}).get("Authorization", ""))
    scheme, separator, token = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not token or len(token) > 256 or any(char.isspace() for char in token):
        return None
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def require_user(headers) -> dict:
    digest = _token_digest(headers)
    with _lock:
        session = _sessions.get(digest)
        if session is None or session["expires_at"] <= time.monotonic():
            _sessions.pop(digest, None)
            raise AccessError(401, "Sign in with your staff account to continue.")
        session = dict(session)
    row = _read_user("user_id", session["user_id"])
    if not _usable(row) or int(row["user_id"]) != session["user_id"] or not secrets.compare_digest(_credential_fingerprint(row), session["credential_fingerprint"]):
        with _lock:
            _sessions.pop(digest, None)
        raise AccessError(401, "Your session is no longer valid. Sign in again.")
    return _actor(row)


def logout(headers):
    with _lock:
        _sessions.pop(_token_digest(headers), None)
