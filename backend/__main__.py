"""Command-line launcher for the Auto-Slides Web backend."""

from __future__ import annotations

import argparse
import os
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Auto-Slides Web application")
    parser.add_argument(
        "--nologin",
        action="store_true",
        help="enable single-user mode and automatically sign in the configured local account",
    )
    parser.add_argument(
        "--initdb",
        "--init-db",
        action="store_true",
        help="delete all users, jobs, uploads, and outputs, rebuild the database, then exit",
    )
    parser.add_argument("--host", default="127.0.0.1", help="listen address (default: 127.0.0.1)")
    parser.add_argument("--port", default=8000, type=int, help="listen port (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="reload when Python source files change")
    parser.add_argument(
        "--settings",
        type=Path,
        help="TOML settings file (default: backend/settings.toml)",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")

    if args.settings:
        settings_path = args.settings.expanduser().resolve()
        if not settings_path.is_file():
            parser.error(f"settings file does not exist: {settings_path}")
        os.environ["AUTOSLIDES_SETTINGS_FILE"] = str(settings_path)
    if args.nologin:
        os.environ["AUTOSLIDES_NOLOGIN"] = "1"
        if not args.initdb and args.host not in {"127.0.0.1", "localhost", "::1"}:
            print("WARNING: --nologin grants anyone who can reach this server access to the local account.")

    if args.initdb:
        from backend.config import DB_PATH
        from backend.database import reset_database

        reset_database()
        print(f"Database reset completed: {DB_PATH}")
        print("All previous users, jobs, sessions, events, uploads, and outputs were deleted.")
        return

    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=1,
    )


if __name__ == "__main__":
    main()
