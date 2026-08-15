import sqlite3
from pathlib import Path

from app.core.config import settings


def get_connection():
    db_path = Path(settings.database_path)

    if db_path.parent:
        db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        settings.database_path,
        check_same_thread=False
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT NOT NULL,
            retry_count INTEGER DEFAULT 0,
            failure_reason TEXT,
            retry_history TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS failed_jobs (
            job_id TEXT PRIMARY KEY,
            original_request TEXT NOT NULL,
            failure_reason TEXT NOT NULL,
            retry_history TEXT,
            failed_at TEXT NOT NULL,
            replayed INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS actions (
            idempotency_key TEXT PRIMARY KEY,
            action_type TEXT NOT NULL,
            request_payload TEXT NOT NULL,
            status TEXT NOT NULL,
            result TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()