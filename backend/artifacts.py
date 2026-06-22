from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.config import DATA_DIR
from backend.database import json_loads
from backend.schemas import ArtifactRef, Artifacts


ARTIFACT_GROUPS = {
    "raw": "rawContent",
    "plan": "plan",
    "tex": "tex",
    "pdf": "pdf",
    "verification": "verificationReport",
    "speech": "speech",
    "images": "image",
    "repair": "plan",
}


def make_artifact(session_id: str, artifact_id: str, artifact_type: str, name: str, group: str, created_at: str, path: str) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "type": artifact_type,
        "name": name,
        "url": f"/api/sessions/{session_id}/files/{group}/{name}",
        "createdAt": created_at,
        "path": path,
        "group": group,
    }


def public_artifact(raw: dict[str, Any] | None) -> ArtifactRef | None:
    if not raw:
        return None
    return ArtifactRef(
        id=raw["id"],
        type=raw["type"],
        name=raw["name"],
        url=raw["url"],
        createdAt=raw.get("createdAt"),
    )


def public_artifacts(raw: dict[str, Any] | None) -> Artifacts:
    raw = raw or {}
    return Artifacts(
        rawContent=public_artifact(raw.get("rawContent")),
        plan=public_artifact(raw.get("plan")),
        tex=public_artifact(raw.get("tex")),
        pdf=public_artifact(raw.get("pdf")),
        verificationReport=public_artifact(raw.get("verificationReport")),
        speech=public_artifact(raw.get("speech")),
    )


def artifact_list(raw: dict[str, Any] | None) -> list[ArtifactRef]:
    artifacts = public_artifacts(raw)
    return [item for item in artifacts.model_dump().values() if item]


def safe_artifact_path(artifacts_json: str, group: str, filename: str) -> Path | None:
    if "/" in filename or "\\" in filename or filename in {"", ".", ".."}:
        return None
    artifacts = json_loads(artifacts_json, {})
    candidates = list(artifacts.values())
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        if candidate.get("group") == group and candidate.get("name") == filename:
            path = Path(candidate.get("path", "")).resolve()
            try:
                path.relative_to(DATA_DIR.resolve())
            except ValueError:
                return None
            return path
    return None
