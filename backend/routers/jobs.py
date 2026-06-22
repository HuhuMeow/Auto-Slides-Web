from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from backend.agents.editor import apply_agent_edit, create_agent_edit
from backend.downloads import build_tex_bundle
from backend.jobs import create_job, create_uploaded_job, delete_job, list_jobs, require_job, to_job_out, update_job
from backend.mappers import normalize_plan, normalize_speech, normalize_verification
from backend.pipeline import compile_tex, repair_job, save_tex, submit_job
from backend.progress import emit_progress, job_progress_context
from backend.schemas import (
    AgentRequest,
    AgentResponse,
    ConversionConfig,
    CreateJobRequest,
    JobOut,
    PresentationPlan,
    SaveTexRequest,
    UpdateJobRequest,
    UserOut,
    VerificationReport,
)
from backend.security import get_current_user

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=list[JobOut])
def get_jobs(user: UserOut = Depends(get_current_user)):
    return list_jobs(user)


@router.post("", response_model=JobOut)
def post_job(payload: CreateJobRequest, user: UserOut = Depends(get_current_user)):
    return create_job(payload, user)


@router.post("/upload", response_model=JobOut)
async def upload_job(
    pdf: UploadFile = File(...),
    config: str = Form("{}"),
    title: str | None = Form(default=None),
    user: UserOut = Depends(get_current_user),
):
    raw = await pdf.read()
    parsed_config = ConversionConfig(**json.loads(config or "{}"))
    return create_uploaded_job(pdf.filename or "paper.pdf", len(raw), title, parsed_config, user, raw)


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, user: UserOut = Depends(get_current_user)):
    return to_job_out(require_job(job_id, user), include_tex=True, include_events=True)


@router.patch("/{job_id}", response_model=JobOut)
def patch_job(job_id: str, payload: UpdateJobRequest, user: UserOut = Depends(get_current_user)):
    require_job(job_id, user)
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=422, detail="Title cannot be empty")
    updated = update_job(job_id, title=title)
    return to_job_out(updated, include_tex=True, include_events=True)


@router.delete("/{job_id}", status_code=204)
def remove_job(job_id: str, user: UserOut = Depends(get_current_user)):
    delete_job(job_id, user)
    return None


@router.post("/{job_id}/start", response_model=JobOut)
def start_job(job_id: str, user: UserOut = Depends(get_current_user)):
    submit_job(job_id, user)
    return to_job_out(require_job(job_id, user), include_tex=True, include_events=True)


@router.post("/{job_id}/cancel", response_model=JobOut)
def cancel_job(job_id: str, user: UserOut = Depends(get_current_user)):
    require_job(job_id, user)
    with job_progress_context(job_id):
        emit_progress("Pipeline", "User requested cancellation; finishing the current atomic operation", level="warning", update_job_state=False)
    return to_job_out(
        update_job(job_id, status="cancelled", message="Conversion cancelled"),
        include_tex=True,
        include_events=True,
    )


@router.post("/{job_id}/retry", response_model=JobOut)
def retry_job(job_id: str, user: UserOut = Depends(get_current_user)):
    require_job(job_id, user)
    submit_job(job_id, user)
    return to_job_out(require_job(job_id, user), include_tex=True, include_events=True)


@router.get("/{job_id}/plan", response_model=PresentationPlan)
def get_plan(job_id: str, user: UserOut = Depends(get_current_user)):
    job = require_job(job_id, user)
    artifacts = json.loads(job.get("artifacts_json") or "{}")
    plan = artifacts.get("plan")
    if not plan:
        return normalize_plan(None)
    with open(plan["path"], "r", encoding="utf-8") as handle:
        return normalize_plan(json.load(handle))


@router.put("/{job_id}/tex", response_model=JobOut)
def put_tex(job_id: str, payload: SaveTexRequest, user: UserOut = Depends(get_current_user)):
    with job_progress_context(job_id):
        emit_progress("TEX Editor", "Saving the user-edited TEX source", stage="done", progress=100)
        return save_tex(job_id, payload.tex, user)


@router.post("/{job_id}/compile", response_model=JobOut)
def post_compile(job_id: str, user: UserOut = Depends(get_current_user)):
    with job_progress_context(job_id):
        return compile_tex(job_id, user)


@router.get("/{job_id}/download-all")
def download_all(job_id: str, user: UserOut = Depends(get_current_user)):
    job = require_job(job_id, user)
    archive = build_tex_bundle(job)
    return Response(
        content=archive,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{job_id}-download-all.zip"'},
    )


@router.post("/{job_id}/repair", response_model=JobOut)
def post_repair(job_id: str, user: UserOut = Depends(get_current_user)):
    with job_progress_context(job_id):
        return repair_job(job_id, user)


@router.post("/{job_id}/agent", response_model=AgentResponse)
def post_agent(job_id: str, payload: AgentRequest, user: UserOut = Depends(get_current_user)):
    with job_progress_context(job_id):
        return create_agent_edit(job_id, payload.message, user)


@router.post("/{job_id}/agent/edits/{edit_id}/apply", response_model=JobOut)
def post_apply_edit(job_id: str, edit_id: str, user: UserOut = Depends(get_current_user)):
    with job_progress_context(job_id):
        return apply_agent_edit(job_id, edit_id, user)


@router.get("/{job_id}/speech")
def get_speech(job_id: str, user: UserOut = Depends(get_current_user)):
    job = require_job(job_id, user)
    return normalize_speech(json.loads(job.get("speech_script_json") or "null"))


@router.get("/{job_id}/verification", response_model=VerificationReport)
def get_verification(job_id: str, user: UserOut = Depends(get_current_user)):
    job = require_job(job_id, user)
    return normalize_verification(json.loads(job.get("verification_report_json") or "null"))
