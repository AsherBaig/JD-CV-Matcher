import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

# Application statuses shown in the dashboard dropdown.
STATUSES = ("tailored", "applied", "interview", "rejected", "offer")


# Path is read on every call so tests can point DB_PATH at a temp file.
def get_db_path() -> str:
    return os.getenv("DB_PATH", "applications.db")


# Opens a connection that returns rows as dict-like objects, commits on success,
# rolls back on error, and always closes. Like a short-lived DbContext in EF Core.
@contextmanager
def get_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            yield conn
    finally:
        conn.close()


# Creates the applications table if it does not exist yet. Called once on startup.
def init_db() -> None:
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name    TEXT    NOT NULL,
                created_at      TEXT    NOT NULL,
                jd_language     TEXT,
                match_score     INTEGER,
                verdict         TEXT,
                status          TEXT    NOT NULL DEFAULT 'tailored',
                job_description TEXT    NOT NULL,
                pdf_filename    TEXT,
                result_json     TEXT    NOT NULL
            )
        """)


# Stores one analysis run. The full LLM result is kept as JSON so an old
# application can be re-opened in the UI exactly as it was generated.
def save_application(company_name: str, job_description: str, result: dict) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO applications
                (company_name, created_at, jd_language, match_score, verdict,
                 job_description, pdf_filename, result_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                company_name,
                datetime.now().isoformat(timespec="seconds"),
                result.get("jd_language"),
                result.get("match_score"),
                (result.get("validation") or {}).get("verdict"),
                job_description,
                result.get("pdf_filename"),
                json.dumps(result, ensure_ascii=False),
            ),
        )
        return cursor.lastrowid


# Returns summary rows for the dashboard table, newest first (no large text fields).
def list_applications() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, company_name, created_at, jd_language, match_score,
                   verdict, status, pdf_filename
            FROM applications
            ORDER BY created_at DESC, id DESC
        """).fetchall()
    return [dict(row) for row in rows]


# Aggregated numbers for the dashboard stat cards.
def get_stats() -> dict:
    with get_connection() as conn:
        row = conn.execute("""
            SELECT COUNT(*)                                        AS total,
                   CAST(ROUND(AVG(match_score)) AS INTEGER)       AS avg_score,
                   SUM(status = 'applied')                         AS applied,
                   SUM(status = 'interview')                       AS interviews,
                   SUM(status = 'offer')                           AS offers
            FROM applications
        """).fetchone()
    stats = dict(row)
    # SUM over zero rows returns NULL — normalise to 0 for the frontend.
    return {key: (value or 0) for key, value in stats.items()}


# Returns one application with its full stored result, or None if not found.
def get_application(app_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()
    if row is None:
        return None
    application = dict(row)
    application["result"] = json.loads(application.pop("result_json"))
    return application


# Updates the pipeline status. Returns False if the id does not exist.
def update_status(app_id: int, status: str) -> bool:
    if status not in STATUSES:
        raise ValueError(f"Invalid status: {status}")
    with get_connection() as conn:
        cursor = conn.execute("UPDATE applications SET status = ? WHERE id = ?", (status, app_id))
        return cursor.rowcount > 0


# Deletes one application record. Returns False if the id does not exist.
def delete_application(app_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM applications WHERE id = ?", (app_id,))
        return cursor.rowcount > 0
