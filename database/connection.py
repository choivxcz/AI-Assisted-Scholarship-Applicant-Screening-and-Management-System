
import os
from pathlib import Path

import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def get_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            database="iskolar_ng_bayan",
            connection_timeout=10,
        )

        if connection.is_connected():
            return connection

        connection.close()
        raise RuntimeError("MySQL connection could not be established.")

    except (Error, KeyError, ValueError) as exc:
        raise RuntimeError(
            f"Database connection failed: {exc}"
        ) from exc
