from __future__ import annotations

import json
import secrets
import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from backend.config import (
    DATA_DIR,
    DB_PATH,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_USERNAME,
    DEFAULT_USER_PASSWORD,
    DEFAULT_USER_USERNAME,
    NO_LOGIN_MODE,
    OUTPUT_DIR,
    PROJECT_ROOT,
    SINGLE_USER_PASSWORD,
    SINGLE_USER_USERNAME,
    UPLOAD_DIR,
)

SINGLE_USER_ID = "u_single_user"


def now_iso() -> str:
    return datetime.now().isoformat()


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 30000")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                session_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL,
                stage TEXT,
                progress INTEGER NOT NULL,
                message TEXT,
                error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                paper_file_name TEXT,
                paper_file_size INTEGER,
                paper_path TEXT,
                config_json TEXT NOT NULL,
                artifacts_json TEXT NOT NULL DEFAULT '{}',
                tex_content TEXT,
                verification_report_json TEXT,
                speech_script_json TEXT,
                started_at TEXT,
                deleted_at TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS conversion_stats (
                id TEXT PRIMARY KEY,
                completed_jobs INTEGER NOT NULL,
                average_duration_seconds REAL NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS agent_edits (
                id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                message TEXT NOT NULL,
                analysis TEXT,
                summary TEXT NOT NULL,
                diff_preview TEXT,
                proposed_tex_path TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                applied_at TEXT,
                FOREIGN KEY(job_id) REFERENCES jobs(id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS job_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                agent TEXT NOT NULL,
                stage TEXT,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                progress INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY(job_id) REFERENCES jobs(id)
            );
            CREATE INDEX IF NOT EXISTS idx_job_events_job_id_id
            ON job_events(job_id, id DESC);
            """
        )
        ensure_column(conn, "jobs", "started_at", "TEXT")
        ensure_column(conn, "jobs", "deleted_at", "TEXT")
        migrate_runtime_paths(conn)
        seed_conversion_stats(conn)
        seed_user(conn, "u_admin", DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD, "admin")
        seed_user(conn, "u_user1", DEFAULT_USER_USERNAME, DEFAULT_USER_PASSWORD, "user")
        if NO_LOGIN_MODE:
            seed_single_user(conn, SINGLE_USER_USERNAME, SINGLE_USER_PASSWORD)


def reset_database() -> None:
    """Delete all persisted users, jobs, sessions, events, uploads, and outputs."""
    for path in (DB_PATH, Path(f"{DB_PATH}-wal"), Path(f"{DB_PATH}-shm")):
        path.unlink(missing_ok=True)
    for directory in (UPLOAD_DIR, OUTPUT_DIR):
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True, exist_ok=True)
    init_db()


def ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = [row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def migrate_runtime_paths(conn: sqlite3.Connection) -> None:
    """Relocate absolute paths created before runtime data moved under .runtime/."""

    def relocate(value: str | None) -> str | None:
        if not value:
            return value
        path = Path(value)
        parts = path.parts
        if "backend_data" in parts:
            index = parts.index("backend_data")
            return str(DATA_DIR.joinpath(*parts[index + 1 :]).resolve())
        legacy_output = PROJECT_ROOT / "output"
        if path.is_absolute():
            try:
                relative = path.relative_to(legacy_output)
                return str((OUTPUT_DIR / relative).resolve())
            except ValueError:
                pass
        elif parts and parts[0] == "output":
            return str(OUTPUT_DIR.joinpath(*parts[1:]).resolve())
        legacy_sample = (PROJECT_ROOT / "autoslides.pdf").resolve()
        if path == legacy_sample:
            return str((PROJECT_ROOT / "examples" / "autoslides.pdf").resolve())
        return value

    for row in conn.execute("SELECT id, paper_path, artifacts_json FROM jobs").fetchall():
        paper_path = relocate(row["paper_path"])
        artifacts = json_loads(row["artifacts_json"], {})
        changed = paper_path != row["paper_path"]
        for artifact in artifacts.values():
            if not isinstance(artifact, dict):
                continue
            current = artifact.get("path")
            relocated = relocate(current)
            if relocated != current:
                artifact["path"] = relocated
                changed = True
        if changed:
            conn.execute(
                "UPDATE jobs SET paper_path = ?, artifacts_json = ? WHERE id = ?",
                (paper_path, json_dumps(artifacts), row["id"]),
            )
        for artifact in artifacts.values():
            if not isinstance(artifact, dict):
                continue
            artifact_path = Path(artifact.get("path", ""))
            if artifact_path.suffix.lower() != ".json" or not artifact_path.is_file():
                continue
            try:
                payload = json.loads(artifact_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            relocated_payload, payload_changed = _relocate_payload_paths(payload, relocate)
            if payload_changed:
                artifact_path.write_text(
                    json.dumps(relocated_payload, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )

    for row in conn.execute("SELECT id, proposed_tex_path FROM agent_edits").fetchall():
        relocated = relocate(row["proposed_tex_path"])
        if relocated != row["proposed_tex_path"]:
            conn.execute(
                "UPDATE agent_edits SET proposed_tex_path = ? WHERE id = ?",
                (relocated, row["id"]),
            )


def _relocate_payload_paths(value: Any, relocate, key: str | None = None) -> tuple[Any, bool]:
    if isinstance(value, dict):
        changed = False
        result = {}
        for child_key, child_value in value.items():
            relocated, child_changed = _relocate_payload_paths(child_value, relocate, child_key)
            result[child_key] = relocated
            changed = changed or child_changed
        return result, changed
    if isinstance(value, list):
        changed = False
        result = []
        for item in value:
            relocated, child_changed = _relocate_payload_paths(item, relocate, key)
            result.append(relocated)
            changed = changed or child_changed
        return result, changed
    if isinstance(value, str) and (key == "path" or (key and key.endswith("_path"))):
        relocated = relocate(value)
        return relocated, relocated != value
    return value, False


def seed_user(conn: sqlite3.Connection, user_id: str, username: str, password: str, role: str) -> None:
    exists = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
    if exists:
        return
    from backend.security import hash_password

    conn.execute(
        "INSERT INTO users (id, username, password, role, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, username, hash_password(password), role, now_iso()),
    )


def seed_single_user(conn: sqlite3.Connection, username: str, password: str) -> None:
    """Create or synchronize the persistent account used by --nologin mode."""
    if len(username) < 3:
        raise RuntimeError("single_user.username in backend/settings.toml must contain at least 3 characters")
    if len(password) < 6:
        raise RuntimeError("single_user.password in backend/settings.toml must contain at least 6 characters")

    conflict = conn.execute(
        "SELECT id FROM users WHERE username = ? AND id != ?",
        (username, SINGLE_USER_ID),
    ).fetchone()
    if conflict:
        raise RuntimeError(
            f"Single-user username '{username}' already belongs to another account; "
            "choose a different value in backend/settings.toml"
        )

    from backend.security import hash_password, verify_password

    existing = conn.execute("SELECT * FROM users WHERE id = ?", (SINGLE_USER_ID,)).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO users (id, username, password, role, created_at) VALUES (?, ?, ?, ?, ?)",
            (SINGLE_USER_ID, username, hash_password(password), "user", now_iso()),
        )
        return

    password_hash = existing["password"]
    if not verify_password(password, password_hash):
        password_hash = hash_password(password)
    conn.execute(
        "UPDATE users SET username = ?, password = ?, role = ? WHERE id = ?",
        (username, password_hash, "user", SINGLE_USER_ID),
    )


def seed_conversion_stats(conn: sqlite3.Connection) -> None:
    exists = conn.execute("SELECT id FROM conversion_stats WHERE id = 'global'").fetchone()
    if exists:
        return
    conn.execute(
        "INSERT INTO conversion_stats (id, completed_jobs, average_duration_seconds, updated_at) VALUES (?, ?, ?, ?)",
        ("global", 0, 0.0, now_iso()),
    )


def record_conversion_duration(duration_seconds: float) -> None:
    if duration_seconds <= 0:
        return
    with connect() as conn:
        seed_conversion_stats(conn)
        row = conn.execute("SELECT completed_jobs, average_duration_seconds FROM conversion_stats WHERE id = 'global'").fetchone()
        completed_jobs = int(row["completed_jobs"]) if row else 0
        current_average = float(row["average_duration_seconds"]) if row else 0.0
        next_count = completed_jobs + 1
        next_average = ((current_average * completed_jobs) + duration_seconds) / next_count
        conn.execute(
            """
            UPDATE conversion_stats
            SET completed_jobs = ?, average_duration_seconds = ?, updated_at = ?
            WHERE id = 'global'
            """,
            (next_count, next_average, now_iso()),
        )


def get_average_conversion_duration() -> float | None:
    with connect() as conn:
        row = conn.execute("SELECT completed_jobs, average_duration_seconds FROM conversion_stats WHERE id = 'global'").fetchone()
    if not row or int(row["completed_jobs"]) <= 0:
        return None
    return float(row["average_duration_seconds"])


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


def json_loads(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def new_token() -> str:
    return secrets.token_urlsafe(32)


def ensure_parent(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
