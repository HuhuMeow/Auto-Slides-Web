from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.types import Scope

from backend.config import FRONTEND_DIST_DIR, STATIC_DIR
from backend.database import init_db
from backend.routers import auth, jobs, models, sessions, themes


class SpaStaticFiles(StaticFiles):
    """Serve Vite assets and fall back to index.html for client-side routes."""

    async def get_response(self, path: str, scope: Scope):
        response = await super().get_response(path, scope)
        if response.status_code == 404 and not path.startswith("api/"):
            return await super().get_response("index.html", scope)
        return response


def create_app() -> FastAPI:
    init_db()
    app = FastAPI(title="Auto-Slides API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.include_router(auth.router)
    app.include_router(jobs.router)
    app.include_router(models.router)
    app.include_router(sessions.router)
    app.include_router(themes.router)
    if FRONTEND_DIST_DIR.is_dir():
        app.mount("/", SpaStaticFiles(directory=FRONTEND_DIST_DIR, html=True), name="frontend")
    return app


app = create_app()
