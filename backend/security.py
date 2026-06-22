from __future__ import annotations

import hashlib
import hmac
import secrets

from fastapi import Depends, Header, HTTPException, status

from backend.config import NO_LOGIN_MODE
from backend.database import SINGLE_USER_ID, connect, new_token, now_iso, row_to_dict
from backend.schemas import UserOut

PASSWORD_PREFIX = "pbkdf2_sha256"
PBKDF2_ITERATIONS = 260_000


def hash_password(password: str) -> str:
    salt = secrets.token_urlsafe(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS)
    return f"{PASSWORD_PREFIX}${PBKDF2_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    if stored.startswith(f"{PASSWORD_PREFIX}$"):
        try:
            _prefix, iterations, salt, expected = stored.split("$", 3)
            digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iterations)).hex()
            return hmac.compare_digest(digest, expected)
        except Exception:
            return False
    return hmac.compare_digest(password, stored)


def issue_token(user_row) -> tuple[UserOut, str]:
    token = new_token()
    with connect() as conn:
        conn.execute(
            "INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)",
            (token, user_row["id"], now_iso()),
        )
    user = UserOut(id=user_row["id"], username=user_row["username"], role=user_row["role"])
    return user, token


def authenticate_user(username: str, password: str) -> tuple[UserOut, str]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if not row or not verify_password(password, row["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": {"code": "UNAUTHORIZED", "message": "Invalid username or password", "details": {}}},
            )
        if not row["password"].startswith(f"{PASSWORD_PREFIX}$"):
            conn.execute("UPDATE users SET password = ? WHERE id = ?", (hash_password(password), row["id"]))
    return issue_token(row)


def auto_login_single_user() -> tuple[UserOut, str] | None:
    """Return a real account session only when the server uses --nologin mode."""
    if not NO_LOGIN_MODE:
        return None
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (SINGLE_USER_ID,)).fetchone()
        session = conn.execute(
            "SELECT token FROM sessions WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
            (SINGLE_USER_ID,),
        ).fetchone()
    if not row:
        raise RuntimeError("Single-user account was not initialized")
    user = UserOut(id=row["id"], username=row["username"], role=row["role"])
    if session:
        return user, session["token"]
    return issue_token(row)


def register_user(username: str, password: str) -> tuple[UserOut, str]:
    username = username.strip()
    if len(username) < 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username must be at least 3 characters")
    if len(password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 6 characters")
    user_id = f"u_{secrets.token_urlsafe(12)}"
    with connect() as conn:
        exists = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username is already taken")
        conn.execute(
            "INSERT INTO users (id, username, password, role, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, username, hash_password(password), "user", now_iso()),
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return issue_token(row)


def get_current_user(authorization: str | None = Header(default=None)) -> UserOut:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    with connect() as conn:
        row = conn.execute(
            """
            SELECT users.* FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token = ?
            """,
            (token,),
        ).fetchone()
    data = row_to_dict(row)
    if not data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token")
    return UserOut(id=data["id"], username=data["username"], role=data["role"])


def get_current_user_or_none(authorization: str | None = Header(default=None)) -> UserOut | None:
    try:
        return get_current_user(authorization)
    except HTTPException:
        return None


def logout_token(authorization: str | None) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        return
    token = authorization.removeprefix("Bearer ").strip()
    with connect() as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))


CurrentUser = Depends(get_current_user)
