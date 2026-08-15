import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings


def now():
    return datetime.now(timezone.utc).isoformat()


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
            request_id TEXT NOT NULL,
            status TEXT NOT NULL,
            retry_count INTEGER DEFAULT 0,
            failure_reason TEXT,
            retry_history TEXT,
            response TEXT,
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


def create_job(job: dict):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO jobs (
            job_id,
            conversation_id,
            message,
            request_id,
            status,
            retry_count,
            retry_history,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job["job_id"],
        job["conversation_id"],
        job["message"],
        job["request_id"],
        "queued",
        0,
        json.dumps([]),
        job["created_at"],
        now()
    ))

    connection.commit()
    connection.close()


def update_job_status(
    job_id: str,
    status: str,
    retry_count: int = None,
    failure_reason: str = None,
    retry_history: list = None,
    response: str = None
):
    connection = get_connection()
    cursor = connection.cursor()

    updates = [
        "status = ?",
        "updated_at = ?"
    ]

    values = [
        status,
        now()
    ]

    if retry_count is not None:
        updates.append("retry_count = ?")
        values.append(retry_count)

    if failure_reason is not None:
        updates.append("failure_reason = ?")
        values.append(failure_reason)

    if retry_history is not None:
        updates.append("retry_history = ?")
        values.append(
            json.dumps(retry_history)
        )

    if response is not None:
        updates.append("response = ?")
        values.append(response)

    values.append(job_id)

    cursor.execute(
        f"""
        UPDATE jobs
        SET {", ".join(updates)}
        WHERE job_id = ?
        """,
        values
    )

    connection.commit()
    connection.close()


def get_job(job_id: str):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM jobs WHERE job_id = ?",
        (job_id,)
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    job = dict(row)

    if job.get("retry_history"):
        job["retry_history"] = json.loads(
            job["retry_history"]
        )

    return job


def move_to_dead_letter(
    job: dict,
    failure_reason: str,
    retry_history: list
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO failed_jobs (
            job_id,
            original_request,
            failure_reason,
            retry_history,
            failed_at,
            replayed
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        job["job_id"],
        json.dumps(job),
        failure_reason,
        json.dumps(retry_history),
        now(),
        0
    ))

    connection.commit()
    connection.close()


def get_failed_job(job_id: str):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM failed_jobs WHERE job_id = ?",
        (job_id,)
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    result = dict(row)

    result["original_request"] = json.loads(
        result["original_request"]
    )

    result["retry_history"] = json.loads(
        result["retry_history"]
    )

    return result