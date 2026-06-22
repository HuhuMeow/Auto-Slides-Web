from __future__ import annotations

from fastapi import APIRouter, Depends, Header

from backend.schemas import LoginRequest, LoginResponse, RegisterRequest, UserOut
from backend.security import auto_login_single_user, authenticate_user, get_current_user_or_none, logout_token, register_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    user, token = authenticate_user(payload.username, payload.password)
    return LoginResponse(user=user, token=token)


@router.post("/register", response_model=LoginResponse)
def register(payload: RegisterRequest):
    user, token = register_user(payload.username, payload.password)
    return LoginResponse(user=user, token=token)


@router.post("/auto-login", response_model=LoginResponse | None)
def auto_login():
    session = auto_login_single_user()
    if not session:
        return None
    user, token = session
    return LoginResponse(user=user, token=token)


@router.post("/logout")
def logout(authorization: str | None = Header(default=None)):
    logout_token(authorization)
    return None


@router.get("/me", response_model=UserOut | None)
def me(user: UserOut | None = Depends(get_current_user_or_none)):
    return user
