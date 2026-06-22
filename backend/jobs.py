from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status

from backend.artifacts import artifact_list, make_artifact, public_artifacts
from backend.config import OUTPUT_DIR, UPLOAD_DIR
from backend.database import connect, get_average_conversion_duration, json_dumps, json_loads, now_iso
from backend.progress import list_job_events
from backend.schemas import ConversionConfig, CreateJobRequest, JobOut, UserOut


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


_AVERAGE_DURATION_UNSET = object()


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _estimated_remaining_seconds(row: dict[str, Any], average_duration: float | None | object = _AVERAGE_DURATION_UNSET) -> int | None:
    if row.get("status") not in {"queued", "running"}:
        return None
    if average_duration is _AVERAGE_DURATION_UNSET:
        average_duration = get_average_conversion_duration()
    if not average_duration:
        return None
    if row.get("status") == "queued":
        return max(1, round(average_duration))

    progress = max(0, min(100, int(row.get("progress") or 0)))
    if progress > 0:
        return max(1, round(average_duration * (1 - progress / 100)))

    started_at = _parse_iso(row.get("started_at"))
    if not started_at:
        return max(1, round(average_duration))
    elapsed = max(0.0, (datetime.now() - started_at).total_seconds())
    return max(1, round(average_duration - elapsed))


def to_job_out(
    row: dict[str, Any] | None,
    include_tex: bool = False,
    include_events: bool = False,
    average_duration_seconds: float | None | object = _AVERAGE_DURATION_UNSET,
) -> JobOut:
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    artifacts = json_loads(row.get("artifacts_json"), {})
    config = json_loads(row.get("config_json"), {})
    return JobOut(
        id=row["id"],
        sessionId=row["session_id"],
        userId=row["user_id"],
        title=row["title"],
        status=row["status"],
        stage=row.get("stage"),
        progress=row["progress"],
        message=row.get("message"),
        error=row.get("error"),
        createdAt=row["created_at"],
        updatedAt=row["updated_at"],
        estimatedRemainingSeconds=_estimated_remaining_seconds(row, average_duration_seconds),
        paperFileName=row.get("paper_file_name"),
        paperFileSize=row.get("paper_file_size"),
        config=ConversionConfig(**config),
        artifacts=public_artifacts(artifacts),
        texContent=row.get("tex_content") if include_tex else None,
        verificationReport=json_loads(row.get("verification_report_json"), None),
        speechScript=json_loads(row.get("speech_script_json"), None),
        events=list_job_events(row["id"]) if include_events else [],
    )


def require_job(job_id: str, user: UserOut) -> dict[str, Any]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ? AND deleted_at IS NULL", (job_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    data = dict(row)
    if data["user_id"] != user.id and user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return data


def require_job_by_session(session_id: str, user: UserOut) -> dict[str, Any]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE session_id = ? AND deleted_at IS NULL", (session_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    data = dict(row)
    if data["user_id"] != user.id and user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return data


def list_jobs(user: UserOut) -> list[JobOut]:
    with connect() as conn:
        if user.role == "admin":
            rows = conn.execute("SELECT * FROM jobs WHERE deleted_at IS NULL ORDER BY updated_at DESC").fetchall()
        else:
            rows = conn.execute("SELECT * FROM jobs WHERE user_id = ? AND deleted_at IS NULL ORDER BY updated_at DESC", (user.id,)).fetchall()
    average_duration = get_average_conversion_duration()
    return [to_job_out(dict(row), include_tex=False, average_duration_seconds=average_duration) for row in rows]


def delete_job(job_id: str, user: UserOut) -> None:
    require_job(job_id, user)
    with connect() as conn:
        conn.execute("UPDATE jobs SET deleted_at = ?, updated_at = ? WHERE id = ?", (now_iso(), now_iso(), job_id))


def create_job(payload: CreateJobRequest, user: UserOut, paper_path: str | None = None) -> JobOut:
    created = now_iso()
    job_id = _new_id("job")
    session_id = _new_id("session")
    title = payload.title or Path(payload.fileName).stem or "Untitled paper"
    upload_path = paper_path
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO jobs (
                id, session_id, user_id, title, status, stage, progress, message, error,
                created_at, updated_at, paper_file_name, paper_file_size, paper_path,
                config_json, artifacts_json, tex_content
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                session_id,
                user.id,
                title,
                "queued" if upload_path else "waiting_user_input",
                "uploading" if not upload_path else None,
                0,
                "Queued for conversion" if upload_path else "PDF upload required before starting",
                None,
                created,
                created,
                payload.fileName,
                payload.fileSize,
                upload_path,
                payload.config.model_dump_json(),
                "{}",
                None,
            ),
        )
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return to_job_out(dict(row), include_tex=True)


def create_uploaded_job(file_name: str, file_size: int, title: str | None, config: ConversionConfig, user: UserOut, content: bytes) -> JobOut:
    session_id = _new_id("upload")
    upload_dir = UPLOAD_DIR / session_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file_name).name or "paper.pdf"
    upload_path = upload_dir / safe_name
    upload_path.write_bytes(content)
    return create_job(
        CreateJobRequest(fileName=safe_name, fileSize=file_size, title=title, config=config),
        user=user,
        paper_path=str(upload_path),
    )


def update_job(job_id: str, **fields: Any) -> dict[str, Any]:
    fields["updated_at"] = now_iso()
    assignments = ", ".join(f"{key} = ?" for key in fields)
    values = list(fields.values()) + [job_id]
    with connect() as conn:
        conn.execute(f"UPDATE jobs SET {assignments} WHERE id = ?", values)
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return dict(row)


def queue_job_for_execution(job_id: str, user: UserOut) -> tuple[dict[str, Any], bool]:
    job = require_job(job_id, user)
    if not job.get("paper_path"):
        row = update_job(
            job_id,
            status="waiting_user_input",
            stage="uploading",
            progress=0,
            message="PDF upload required before starting",
        )
        return row, False
    if job["status"] == "running":
        return job, False
    row = update_job(
        job_id,
        status="queued",
        stage="extracting",
        progress=0,
        message="Queued for conversion",
        error=None,
    )
    return row, True


def claim_queued_job_for_execution(job_id: str) -> dict[str, Any] | None:
    started = now_iso()
    with connect() as conn:
        cursor = conn.execute(
            """
            UPDATE jobs
            SET status = ?, stage = ?, progress = ?, message = ?, error = ?, started_at = ?, updated_at = ?
            WHERE id = ? AND status = ? AND deleted_at IS NULL
            """,
            ("running", "extracting", 10, "Extracting Markdown, figures, and metadata", None, started, started, job_id, "queued"),
        )
        if cursor.rowcount != 1:
            return None
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return dict(row) if row else None


def merge_artifact(job_id: str, key: str, artifact: dict[str, Any]) -> dict[str, Any]:
    with connect() as conn:
        row = conn.execute("SELECT artifacts_json FROM jobs WHERE id = ?", (job_id,)).fetchone()
        artifacts = json_loads(row["artifacts_json"] if row else None, {})
        artifacts[key] = artifact
        conn.execute("UPDATE jobs SET artifacts_json = ?, updated_at = ? WHERE id = ?", (json_dumps(artifacts), now_iso(), job_id))
        next_row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return dict(next_row)


def make_output_artifact(job: dict[str, Any], key: str, artifact_type: str, path: str, group: str, artifact_id: str | None = None) -> dict[str, Any]:
    created = now_iso()
    return make_artifact(
        session_id=job["session_id"],
        artifact_id=artifact_id or key,
        artifact_type=artifact_type,
        name=Path(path).name,
        group=group,
        created_at=created,
        path=str(Path(path).resolve()),
    )


def job_artifact_list(session_id: str, user: UserOut):
    job = require_job_by_session(session_id, user)
    return artifact_list(json_loads(job.get("artifacts_json"), {}))
