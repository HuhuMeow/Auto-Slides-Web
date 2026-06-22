import os
import tomllib
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ModuleNotFoundError:
    pass

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SETTINGS_PATH = Path(
    os.environ.get("AUTOSLIDES_SETTINGS_FILE", PROJECT_ROOT / "backend" / "settings.toml")
)


def _load_settings() -> dict:
    if not SETTINGS_PATH.is_file():
        return {}
    with SETTINGS_PATH.open("rb") as handle:
        return tomllib.load(handle)


_SETTINGS = _load_settings()
_SINGLE_USER_SETTINGS = _SETTINGS.get("single_user", {})
NO_LOGIN_MODE = os.environ.get("AUTOSLIDES_NOLOGIN", "").lower() in {"1", "true", "yes", "on"}
SINGLE_USER_USERNAME = str(_SINGLE_USER_SETTINGS.get("username", "localuser")).strip()
SINGLE_USER_PASSWORD = str(_SINGLE_USER_SETTINGS.get("password", "localpass"))

RUNTIME_DIR = Path(os.environ.get("AUTOSLIDES_RUNTIME_DIR", PROJECT_ROOT / ".runtime"))
DATA_DIR = Path(os.environ.get("AUTOSLIDES_DATA_DIR", RUNTIME_DIR / "data"))
MODEL_DIR = Path(os.environ.get("AUTOSLIDES_MARKER_MODEL_DIR", RUNTIME_DIR / "models"))
UPLOAD_DIR = DATA_DIR / "uploads"
OUTPUT_DIR = DATA_DIR / "output"
DB_PATH = DATA_DIR / "autoslides.sqlite3"
STATIC_DIR = PROJECT_ROOT / "static"
FRONTEND_DIST_DIR = PROJECT_ROOT / "frontend" / "dist"

DEFAULT_ADMIN_USERNAME = os.environ.get("AUTOSLIDES_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASSWORD = os.environ.get("AUTOSLIDES_ADMIN_PASSWORD", "admin123")
DEFAULT_USER_USERNAME = os.environ.get("AUTOSLIDES_USER_USERNAME", "user1")
DEFAULT_USER_PASSWORD = os.environ.get("AUTOSLIDES_USER_PASSWORD", "user123")

_CONFIGURED_MAX_WORKERS = int(os.environ.get("AUTOSLIDES_MAX_WORKERS", "10"))
MAX_WORKERS = max(1, min(10, _CONFIGURED_MAX_WORKERS))

for path in [RUNTIME_DIR, DATA_DIR, UPLOAD_DIR, OUTPUT_DIR]:
    path.mkdir(parents=True, exist_ok=True)
