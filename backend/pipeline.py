from __future__ import annotations

import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from backend.config import MAX_WORKERS, OUTPUT_DIR
from backend.database import connect, json_dumps, json_loads, now_iso, record_conversion_duration
from backend.jobs import claim_queued_job_for_execution, make_output_artifact, merge_artifact, queue_job_for_execution, require_job, to_job_out, update_job
from backend.llm.router import llm_provider_context
from backend.mappers import normalize_speech, normalize_verification
from backend.progress import emit_progress, job_progress_context
from backend.schemas import UserOut

logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
_SUBMITTED_LOCK = threading.Lock()
_SUBMITTED_JOBS: set[str] = set()


class JobCancelled(Exception):
    pass


def ensure_job_active(job_id: str) -> None:
    with connect() as conn:
        row = conn.execute("SELECT status FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if row and row["status"] == "cancelled":
        raise JobCancelled


def submit_job(job_id: str, user: UserOut) -> None:
    _job, should_queue = queue_job_for_execution(job_id, user)
    if not should_queue:
        return
    with _SUBMITTED_LOCK:
        if job_id in _SUBMITTED_JOBS:
            return
        _SUBMITTED_JOBS.add(job_id)
    with job_progress_context(job_id):
        emit_progress("Pipeline", "Job accepted and waiting for an available worker", stage="extracting", progress=0)
    executor.submit(_run_submitted_job, job_id)


def _run_submitted_job(job_id: str) -> None:
    try:
        run_pipeline(job_id)
    finally:
        with _SUBMITTED_LOCK:
            _SUBMITTED_JOBS.discard(job_id)


def update_stage(job_id: str, stage: str, progress: int, message: str) -> dict[str, Any]:
    ensure_job_active(job_id)
    row = update_job(job_id, stage=stage, progress=progress, message=message)
    emit_progress("Pipeline", message, stage=stage, progress=progress, update_job_state=False)
    return row


def run_pipeline(job_id: str) -> None:
    with job_progress_context(job_id):
        _run_pipeline_in_context(job_id)


def _run_pipeline_in_context(job_id: str) -> None:
    started = time.monotonic()
    try:
        job = claim_queued_job_for_execution(job_id)
        if not job:
            logger.info("Job %s was not queued when a worker became available; skipping", job_id)
            return
        emit_progress("Pipeline", "Worker started; preparing the configured LLM provider", stage="extracting", progress=8)
        config = json.loads(job["config_json"])
        with llm_provider_context(config):
            _run_pipeline_with_provider(job_id, job, config)
        record_conversion_duration(time.monotonic() - started)
    except JobCancelled:
        emit_progress("Pipeline", "Cancellation acknowledged; no further stages will run", level="warning", update_job_state=False)
        update_job(job_id, status="cancelled", message="Conversion cancelled", error=None)
    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        emit_progress("Pipeline", f"Job stopped because {type(exc).__name__} occurred", level="error", update_job_state=False)
        update_job(job_id, status="failed", error=str(exc), message="Pipeline failed")


def _run_pipeline_with_provider(job_id: str, job: dict[str, Any], config: dict[str, Any]) -> None:
    session_id = job["session_id"]
    output_base = OUTPUT_DIR

    raw_dir = output_base / "raw" / session_id
    plan_dir = output_base / "plan" / session_id
    tex_dir = output_base / "tex" / session_id
    images_dir = output_base / "images" / session_id
    verification_dir = output_base / "verification" / session_id
    repair_dir = output_base / "repair" / session_id
    speech_dir = output_base / "speech" / session_id
    for directory in [raw_dir, plan_dir, tex_dir, images_dir, verification_dir, repair_dir, speech_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    from backend.services.paper_extractor import extract_pdf_content
    from backend.services.presentation import generate_presentation_plan
    from backend.services.tex_workflow import run_tex_workflow

    pdf_content, raw_content_path, _img_dir = extract_pdf_content(
        pdf_path=job["paper_path"],
        output_dir=str(raw_dir),
        enable_llm_enhancement=config.get("enableLlmEnhancement", True),
        model_name=config.get("model", "deepseek-chat"),
        session_id=session_id,
        images_dir=str(images_dir),
    )
    if not pdf_content or not raw_content_path:
        raise RuntimeError("PDF content extraction failed")
    job = merge_artifact(job_id, "rawContent", make_output_artifact(job, "rawContent", "json", raw_content_path, "raw", "raw_content"))
    emit_progress("Extraction Service", "Extracted paper content was saved as a job artifact", stage="extracting", progress=35)

    update_stage(job_id, "planning", 40, "Generating PMRC presentation plan")
    presentation_plan, plan_path, _planner = generate_presentation_plan(
        raw_content_path=raw_content_path,
        output_dir=str(plan_dir),
        model_name=config.get("model", "deepseek-chat"),
        language=config.get("language", "en"),
    )
    if not presentation_plan or not plan_path:
        raise RuntimeError("Presentation plan generation failed")
    job = merge_artifact(job_id, "plan", make_output_artifact(job, "plan", "json", plan_path, "plan", "presentation_plan"))
    emit_progress("Planning Agent", f"Presentation plan saved with {len(presentation_plan.get('slides_plan', []))} slides", stage="planning", progress=54)

    verification_report_path = None
    verification_passed = True
    if config.get("enableVerification", True):
        update_stage(job_id, "verifying", 55, "Checking content coverage")
        from backend.agents.verification import verify_content_coverage

        verification_passed, verification_report, verification_report_path = verify_content_coverage(
            original_content_path=raw_content_path,
            presentation_plan_path=plan_path,
            output_dir=str(verification_dir),
            model_name=config.get("model", "deepseek-chat"),
            language=config.get("language", "en"),
        )
        normalized = normalize_verification(verification_report, passed=verification_passed).model_dump()
        update_job(job_id, verification_report_json=json_dumps(normalized))
        if verification_report_path:
            job = merge_artifact(
                job_id,
                "verificationReport",
                make_output_artifact(job, "verificationReport", "json", verification_report_path, "verification", "verification_report"),
            )
    else:
        emit_progress("Verification Agent", "Verification is disabled for this job", stage="verifying", progress=64)

    if config.get("enableAutoRepair", True) and config.get("enableVerification", True) and verification_report_path and not verification_passed:
        update_stage(job_id, "repairing", 70, "Repairing high-importance omissions")
        from backend.agents.repair import repair_content_coverage

        repair_success, _repair_report, repaired_plan_path = repair_content_coverage(
            presentation_plan_path=plan_path,
            verification_report_path=verification_report_path,
            original_content_path=raw_content_path,
            output_dir=str(repair_dir),
            model_name=config.get("model", "deepseek-chat"),
            language=config.get("language", "en"),
        )
        if repair_success and repaired_plan_path:
            plan_path = repaired_plan_path
            job = merge_artifact(job_id, "plan", make_output_artifact(job, "plan", "json", plan_path, "repair", "presentation_plan"))
        elif not repair_success:
            emit_progress("Repair Agent", "No automatic plan changes were required", stage="repairing", progress=79)

    update_stage(job_id, "generating_tex", 82, "Generating Beamer LaTeX")
    success, message, pdf_or_tex_path = run_tex_workflow(
        presentation_plan_path=plan_path,
        output_dir=str(tex_dir),
        images_dir=str(images_dir),
        model_name=config.get("model", "deepseek-chat"),
        language=config.get("language", "en"),
        theme=config.get("theme", "Madrid"),
        max_retries=5,
        skip_compilation=config.get("skipCompilation", False),
    )
    if not success or not pdf_or_tex_path:
        raise RuntimeError(message)
    tex_path = tex_dir / "output.tex"
    if tex_path.exists():
        tex_content = tex_path.read_text(encoding="utf-8")
        job = update_job(job_id, tex_content=tex_content)
        job = merge_artifact(job_id, "tex", make_output_artifact(job, "tex", "tex", str(tex_path), "tex"))
    if str(pdf_or_tex_path).endswith(".pdf"):
        job = merge_artifact(job_id, "pdf", make_output_artifact(job, "pdf", "pdf", pdf_or_tex_path, "pdf"))
        emit_progress("TEX Workflow", "Compiled PDF artifact is ready for preview", stage="compiling", progress=95, level="success")

    if config.get("enableSpeech", False):
        update_stage(job_id, "generating_speech", 96, "Generating speech script")
        try:
            from backend.agents.speech import generate_speech_for_presentation

            speech_success, speech_result, speech_path = generate_speech_for_presentation(
                presentation_plan_path=plan_path,
                output_dir=str(speech_dir),
                original_content_path=raw_content_path,
                target_duration_minutes=config.get("speechDuration", 15),
                presentation_style=config.get("speechStyle", "academic_conference"),
                model_name=config.get("model", "deepseek-chat"),
                language=config.get("language", "en"),
            )
            if speech_success and speech_path:
                normalized_speech = normalize_speech(speech_result)
                update_job(job_id, speech_script_json=json_dumps(normalized_speech))
                job = merge_artifact(job_id, "speech", make_output_artifact(job, "speech", "json", speech_path, "speech"))
        except Exception:
            logger.exception("Optional Speech Agent failed for job %s", job_id)
            emit_progress("Speech Agent", "Speech generation failed, but slide delivery can continue", stage="generating_speech", progress=99, level="warning")

    ensure_job_active(job_id)
    emit_progress("Pipeline", "All requested outputs are ready", stage="done", progress=100, level="success")
    update_job(job_id, status="succeeded", stage="done", progress=100, message="Slides generated successfully", error=None)


def save_tex(job_id: str, tex: str, user: UserOut):
    job = require_job(job_id, user)
    tex_dir = OUTPUT_DIR / "tex" / job["session_id"]
    tex_dir.mkdir(parents=True, exist_ok=True)
    tex_path = tex_dir / "output.tex"
    tex_path.write_text(tex, encoding="utf-8")
    job = update_job(job_id, tex_content=tex, message="TEX saved")
    job = merge_artifact(job_id, "tex", make_output_artifact(job, "tex", "tex", str(tex_path), "tex"))
    return to_job_out(job, include_tex=True, include_events=True)


def compile_tex(job_id: str, user: UserOut):
    job = require_job(job_id, user)
    tex_content = job.get("tex_content")
    if not tex_content:
        raise RuntimeError("No TEX content to compile")
    tex_dir = OUTPUT_DIR / "tex" / job["session_id"]
    tex_dir.mkdir(parents=True, exist_ok=True)
    tex_path = tex_dir / "output.tex"
    tex_path.write_text(tex_content, encoding="utf-8")
    from backend.services.tex_compiler import TexValidator

    update_job(job_id, status="running", stage="compiling", progress=95, message="Compiling current TEX")
    validator = TexValidator(
        output_dir=str(tex_dir),
        language=json.loads(job["config_json"]).get("language", "en"),
        images_dir=str(OUTPUT_DIR / "images" / job["session_id"]),
    )
    success, message, pdf_path = validator.validate(str(tex_path))
    if not success or not pdf_path:
        row = update_job(job_id, status="failed", message=message, error=message)
        return to_job_out(row, include_tex=True, include_events=True)
    row = merge_artifact(job_id, "pdf", make_output_artifact(job, "pdf", "pdf", pdf_path, "pdf"))
    row = update_job(job_id, status="succeeded", stage="done", progress=100, message="TEX compiled successfully", error=None)
    return to_job_out(row, include_tex=True, include_events=True)


def repair_job(job_id: str, user: UserOut):
    """Repair a verified plan and regenerate the Web job's TEX/PDF artifacts."""
    job = require_job(job_id, user)
    artifacts = json_loads(job.get("artifacts_json"), {})

    def artifact_path(key: str) -> str:
        artifact = artifacts.get(key)
        path = artifact.get("path") if isinstance(artifact, dict) else None
        if not path or not Path(path).is_file():
            raise RuntimeError(f"Required {key} artifact is not available")
        return path

    raw_path = artifact_path("rawContent")
    plan_path = artifact_path("plan")
    report_path = artifact_path("verificationReport")
    config = json_loads(job.get("config_json"), {})
    session_id = job["session_id"]
    repair_dir = OUTPUT_DIR / "repair" / session_id
    verification_dir = OUTPUT_DIR / "verification" / session_id
    tex_dir = OUTPUT_DIR / "tex" / session_id
    images_dir = OUTPUT_DIR / "images" / session_id
    for directory in (repair_dir, verification_dir, tex_dir, images_dir):
        directory.mkdir(parents=True, exist_ok=True)

    update_job(job_id, status="running", stage="repairing", progress=70, message="Repairing verified content gaps", error=None)
    try:
        with llm_provider_context(config):
            from backend.agents.repair import repair_content_coverage
            from backend.agents.verification import verify_content_coverage
            from backend.services.tex_workflow import run_tex_workflow

            repaired, _repair_report, repaired_plan_path = repair_content_coverage(
                presentation_plan_path=plan_path,
                verification_report_path=report_path,
                original_content_path=raw_path,
                output_dir=str(repair_dir),
                model_name=config.get("model", "deepseek-chat"),
                language=config.get("language", "en"),
            )
            if not repaired or not repaired_plan_path:
                raise RuntimeError("Repair Agent did not produce an updated plan")

            passed, report, next_report_path = verify_content_coverage(
                original_content_path=raw_path,
                presentation_plan_path=repaired_plan_path,
                output_dir=str(verification_dir),
                model_name=config.get("model", "deepseek-chat"),
                language=config.get("language", "en"),
            )
            normalized = normalize_verification(report, passed=passed).model_dump()
            update_job(job_id, verification_report_json=json_dumps(normalized))

            success, message, output_path = run_tex_workflow(
                presentation_plan_path=repaired_plan_path,
                output_dir=str(tex_dir),
                images_dir=str(images_dir),
                model_name=config.get("model", "deepseek-chat"),
                language=config.get("language", "en"),
                theme=config.get("theme", "Madrid"),
                max_retries=5,
                skip_compilation=config.get("skipCompilation", False),
            )
            if not success or not output_path:
                raise RuntimeError(message)

        job = require_job(job_id, user)
        job = merge_artifact(job_id, "plan", make_output_artifact(job, "plan", "json", repaired_plan_path, "repair", "presentation_plan"))
        if next_report_path:
            job = merge_artifact(job_id, "verificationReport", make_output_artifact(job, "verificationReport", "json", next_report_path, "verification", "verification_report"))
        tex_path = tex_dir / "output.tex"
        if tex_path.is_file():
            job = update_job(job_id, tex_content=tex_path.read_text(encoding="utf-8"))
            job = merge_artifact(job_id, "tex", make_output_artifact(job, "tex", "tex", str(tex_path), "tex"))
        if output_path.endswith(".pdf"):
            job = merge_artifact(job_id, "pdf", make_output_artifact(job, "pdf", "pdf", output_path, "pdf"))
        job = update_job(job_id, status="succeeded", stage="done", progress=100, message="Plan repaired and slides regenerated", error=None)
        return to_job_out(job, include_tex=True, include_events=True)
    except Exception as exc:
        update_job(job_id, status="failed", message="Plan repair failed", error=str(exc))
        raise
