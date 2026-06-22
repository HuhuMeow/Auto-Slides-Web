from __future__ import annotations

from backend.config import STATIC_DIR
from backend.schemas import ThemeOption


def list_themes() -> list[ThemeOption]:
    theme_dir = STATIC_DIR / "themes"
    if not theme_dir.exists():
        return []
    return [
        ThemeOption(name=path.stem, previewUrl=f"/static/themes/{path.name}")
        for path in sorted(theme_dir.glob("*.png"))
        if path.stem not in {"placeholder", "homepage"}
    ]
