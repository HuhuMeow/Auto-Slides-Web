from __future__ import annotations

from fastapi import APIRouter

from backend.schemas import ThemeOption
from backend.themes import list_themes

router = APIRouter(prefix="/api/themes", tags=["themes"])


@router.get("", response_model=list[ThemeOption])
def themes():
    return list_themes()
