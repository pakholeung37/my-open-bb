from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.db import fetchall_dicts, get_connection


class IngestionRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def record_run(self, job_type: str, status: str, started_at: str, finished_at: str, message: str | None = None) -> None:
        with get_connection(self.database_path) as conn:
            conn.execute(
                """
                INSERT INTO ingestion_runs(job_type, status, message, started_at, finished_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                [job_type, status, message, started_at, finished_at],
            )

    def latest_by_job_type(self) -> dict[str, dict]:
        query = """
        SELECT r1.job_type, r1.status, r1.message, r1.started_at, r1.finished_at
        FROM ingestion_runs r1
        INNER JOIN (
            SELECT job_type, MAX(finished_at) AS max_finished
            FROM ingestion_runs
            GROUP BY job_type
        ) r2
          ON r1.job_type = r2.job_type AND r1.finished_at = r2.max_finished
        """
        with get_connection(self.database_path) as conn:
            rows = fetchall_dicts(conn, query)
        return {
            row["job_type"]: {
                "status": row["status"],
                "message": row["message"],
                "started_at": _to_iso(row["started_at"]),
                "finished_at": _to_iso(row["finished_at"]),
            }
            for row in rows
        }


def _to_iso(value: object) -> str:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc).isoformat()
        return value.astimezone(timezone.utc).isoformat()
    return str(value)
