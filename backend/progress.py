"""Structured job events shared by agents, services, and the Web API."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator, Literal

from backend.database import connect, now_iso

EventLevel = Literal["info", "warning", "error", "success"]
_CURRENT_JOB_ID: ContextVar[str | None] = ContextVar("autoslides_job_id", default=None)
_LOGGER = logging.getLogger("autoslides.progress")


@contextmanager
def job_progress_context(job_id: str) -> Iterator[None]:
    """Bind structured events emitted in this context to one job."""
    token = _CURRENT_JOB_ID.set(job_id)
    try:
        yield
    finally:
        _CURRENT_JOB_ID.reset(token)


def emit_progress(
    agent: str,
    message: str,
    *,
    stage: str | None = None,
    progress: int | None = None,
    level: EventLevel = "info",
    update_job_state: bool = True,
) -> None:
    """Write a user-safe event to logs and, when bound, the job event stream."""
    log_level = logging.ERROR if level == "error" else logging.WARNING if level == "warning" else logging.INFO
    _LOGGER.log(log_level, "[%s] %s", agent, message)

    job_id = _CURRENT_JOB_ID.get()
    if not job_id:
        return

    created_at = now_iso()
    normalized_progress = None if progress is None else max(0, min(100, int(progress)))
    with connect() as conn:
        if stage is None:
            row = conn.execute("SELECT stage FROM jobs WHERE id = ?", (job_id,)).fetchone()
            stage = row["stage"] if row else None
        conn.execute(
            """
            INSERT INTO job_events (job_id, agent, stage, level, message, progress, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (job_id, agent, stage, level, message[:1000], normalized_progress, created_at),
        )
        if update_job_state:
            fields = ["message = ?", "updated_at = ?"]
            values: list[object] = [message[:1000], created_at]
            if stage is not None:
                fields.append("stage = ?")
                values.append(stage)
            if normalized_progress is not None:
                fields.append("progress = MAX(progress, ?)")
                values.append(normalized_progress)
            values.append(job_id)
            conn.execute(f"UPDATE jobs SET {', '.join(fields)} WHERE id = ?", values)
        conn.execute(
            """
            DELETE FROM job_events
            WHERE job_id = ? AND id NOT IN (
                SELECT id FROM job_events WHERE job_id = ? ORDER BY id DESC LIMIT 200
            )
            """,
            (job_id, job_id),
        )


def list_job_events(job_id: str, limit: int = 40) -> list[dict]:
    safe_limit = max(1, min(200, limit))
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, agent, stage, level, message, progress, created_at
            FROM job_events WHERE job_id = ? ORDER BY id DESC LIMIT ?
            """,
            (job_id, safe_limit),
        ).fetchall()
    return [
        {
            "id": row["id"],
            "agent": row["agent"],
            "stage": row["stage"],
            "level": row["level"],
            "message": row["message"],
            "progress": row["progress"],
            "createdAt": row["created_at"],
        }
        for row in reversed(rows)
    ]
