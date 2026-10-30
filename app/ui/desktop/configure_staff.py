"""Local administrator tool for preconfigured staff accounts; never a public endpoint.

Example (run from the repository root):
  .venv/Scripts/python.exe app/ui/desktop/configure_staff.py --username therese --first-name Therese --last-name Reyes --role ADMIN
Passwords are requested securely at the terminal and are never command arguments.
"""
from __future__ import annotations

import argparse
from getpass import getpass
from pathlib import Path
import re
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import get_connection
from app.ui.desktop.staff_auth import PASSWORD_HASHER, ROLES


def validate_password(password: str):
    if not isinstance(password, str) or not 12 <= len(password) <= 1024 or not all((any(c.islower() for c in password), any(c.isupper() for c in password), any(c.isdigit() for c in password), any(not c.isalnum() and not c.isspace() for c in password))):
        raise ValueError("Use 12+ characters with uppercase, lowercase, a number, and a symbol.")


def configure_account(username, first_name, last_name, role, password, *, reset_password=False):
    username = str(username).strip()
    first_name = str(first_name).strip()
    last_name = str(last_name).strip()
    if not re.fullmatch(r"[A-Za-z0-9._@+\-]{3,50}", username):
        raise ValueError("Username must contain 3 to 50 letters, numbers, dots, underscores, @, +, or hyphens.")
    if not first_name or not last_name or len(first_name) > 100 or len(last_name) > 100:
        raise ValueError("First and last names are required and must each be 100 characters or fewer.")
    if role not in ROLES:
        raise ValueError("Role must be ADMIN or LYDO_OFFICIAL.")
    validate_password(password)
    password_hash = PASSWORD_HASHER.hash(password)
    connection = get_connection()
    try:
        with connection.cursor(dictionary=True) as cursor:
            # Additive schema setup only: existing scholarship tables are untouched.
            schema = (PROJECT_ROOT / "database" / "staff_access.sql").read_text(encoding="utf-8-sig")
            cursor.execute(schema)
            cursor.execute("SELECT user_id, first_name, last_name, role FROM users WHERE username = %s", (username,))
            current = cursor.fetchone()
            if current:
                if not reset_password:
                    raise ValueError("That account already exists. Use --reset-password explicitly to replace its password.")
                if (first_name, last_name, role) != (current["first_name"], current["last_name"], current["role"]):
                    raise ValueError("Password reset must preserve the existing name and role. Supply the account's current identity.")
                cursor.execute("UPDATE users SET password_hash = %s WHERE user_id = %s", (password_hash, current["user_id"]))
                user_id = int(current["user_id"])
            else:
                if reset_password:
                    raise ValueError("Account not found. Omit --reset-password to configure a new account.")
                cursor.execute(
                    "INSERT INTO users (username, password_hash, first_name, last_name, role, is_active) VALUES (%s, %s, %s, %s, %s, 1)",
                    (username, password_hash, first_name, last_name, role),
                )
                user_id = int(cursor.lastrowid)
        connection.commit()
        return user_id
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser(description="Preconfigure an individual staff login. No public account creation is enabled.")
    parser.add_argument("--username", required=True)
    parser.add_argument("--first-name", required=True)
    parser.add_argument("--last-name", required=True)
    parser.add_argument("--role", required=True, choices=sorted(ROLES))
    parser.add_argument("--reset-password", action="store_true")
    args = parser.parse_args()
    try:
        password = getpass("Staff password (12+ characters, uppercase/lowercase/number/symbol): ")
        confirmation = getpass("Confirm password: ")
        if password != confirmation:
            raise ValueError("Passwords do not match. No account was saved.")
        configure_account(args.username, args.first_name, args.last_name, args.role, password, reset_password=args.reset_password)
        print("Staff login configured. Both supported roles have the same workspace access. Restarting the bridge revokes all sessions.")
    except (ValueError, KeyboardInterrupt, EOFError) as error:
        print(str(error) or "Cancelled. No account was saved.", file=sys.stderr)
        return 1
    except Exception:
        print("Staff login could not be saved. Check the local database connection and permissions.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
