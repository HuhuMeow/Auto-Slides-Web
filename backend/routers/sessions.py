from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from backend.artifacts import safe_artifact_path
from backend.jobs import job_artifact_list, require_job_by_session
from backend.schemas import ArtifactRef, UserOut
from backend.security import get_current_user

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("/{session_id}/artifacts", response_model=list[ArtifactRef])
def get_artifacts(session_id: str, user: UserOut = Depends(get_current_user)):
    return job_artifact_list(session_id, user)


@router.get("/{session_id}/files/{artifact_type}/{filename}")
def get_file(session_id: str, artifact_type: str, filename: str, user: UserOut = Depends(get_current_user)):
    job = require_job_by_session(session_id, user)
    path = safe_artifact_path(job["artifacts_json"], artifact_type, filename)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="Artifact not found")
    return FileResponse(path)
