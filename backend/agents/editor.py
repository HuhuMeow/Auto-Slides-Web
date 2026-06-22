from __future__ import annotations

import difflib
import json
import os
import re
import time
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status

from backend.config import OUTPUT_DIR
from backend.database import connect, json_loads, now_iso
from backend.jobs import require_job, to_job_out, update_job
from backend.llm.router import llm_provider_context
from backend.progress import emit_progress
from backend.schemas import AgentResponse, ProposedEdit, UserOut


EDITOR_SYSTEM_PROMPT = """
You are Auto-Slides Editor Agent, a careful LaTeX Beamer editor.

You will receive the current complete TEX source and a user's edit request.
Return a JSON object only:
{
  "summary": "one short sentence describing the edit",
  "analysis": "brief technical explanation of what changed and where",
  "proposed_tex": "the complete updated TEX document"
}

Rules:
- proposed_tex must be the full compilable TEX document, not a patch and not a snippet.
- Preserve all unrelated content, package imports, Beamer theme, image paths, labels, and comments.
- Make the smallest sufficient change that satisfies the user request.
- Do not invent paper facts. If adding content, reuse information already present in the TEX or source paper context.
- Keep Beamer syntax valid and avoid overfull slides when possible.
- Do not wrap proposed_tex in Markdown fences.
- If the request is unsafe, impossible, or ambiguous, keep proposed_tex unchanged and explain why in analysis.
"""


def create_agent_edit(job_id: str, message: str, user: UserOut) -> AgentResponse:
    job = require_job(job_id, user)
    current_tex = job.get("tex_content")
    if not current_tex:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="TEX is not ready")

    emit_progress("Editor Agent", "Reading the current TEX and the requested revision", stage="done", progress=100)

    edit_id = f"edit_{int(time.time() * 1000)}"
    config = json_loads(job.get("config_json"), {})
    try:
        with llm_provider_context(config):
            emit_progress("Editor Agent", "Preparing a minimal, reviewable full-document edit", stage="done", progress=100)
            agent_result = build_proposed_tex(current_tex=current_tex, message=message, job=job)
    except RuntimeError as exc:
        emit_progress("Editor Agent", "The model did not produce a valid reviewable TEX edit", stage="done", progress=100, level="error")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    proposed_tex = agent_result["proposed_tex"]
    emit_progress("Editor Agent", "Valid TEX proposal received; computing a unified diff", stage="done", progress=100)
    diff = "\n".join(
        difflib.unified_diff(
            current_tex.splitlines(),
            proposed_tex.splitlines(),
            fromfile="output.tex",
            tofile="proposed_output.tex",
            lineterm="",
        )
    )
    edit_dir = OUTPUT_DIR / "agent_edits" / job["session_id"]
    edit_dir.mkdir(parents=True, exist_ok=True)
    edit_path = edit_dir / f"{edit_id}.tex"
    edit_path.write_text(proposed_tex, encoding="utf-8")

    analysis = agent_result["analysis"]
    summary = agent_result["summary"]
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO agent_edits (
                id, job_id, user_id, message, analysis, summary, diff_preview,
                proposed_tex_path, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (edit_id, job_id, user.id, message, analysis, summary, diff, str(edit_path), "pending", now_iso()),
        )

    emit_progress("Editor Agent", "Pending edit saved and ready for user review", stage="done", progress=100, level="success")

    return AgentResponse(
        id=f"agent_{int(time.time() * 1000)}",
        message="I prepared a pending TEX edit from the real backend agent. Review it before applying.",
        analysis=analysis,
        proposedEdit=ProposedEdit(
            editId=edit_id,
            summary=summary,
            diffPreview=diff,
            proposedTex=proposed_tex,
            requiresConfirmation=True,
        ),
    )


def build_proposed_tex(current_tex: str, message: str, job: dict[str, Any]) -> dict[str, str]:
    source_context = _load_source_context(job)
    emit_progress(
        "Editor Agent",
        "Source-paper context loaded" if source_context else "No source context available; editing only from current TEX",
        stage="done",
        progress=100,
        level="info" if source_context else "warning",
    )
    prompt = _build_editor_prompt(current_tex=current_tex, message=message, source_context=source_context)
    result = _call_editor_llm(prompt)

    proposed_tex = _extract_tex(result.get("proposed_tex", ""))
    if not _looks_like_complete_tex(proposed_tex):
        raise RuntimeError("Editor Agent returned invalid TEX. No edit was created.")

    summary = str(result.get("summary") or "Apply Agent-requested TEX modification.").strip()
    analysis = str(result.get("analysis") or "Generated a reviewable TEX edit with the configured LLM provider.").strip()
    return {"summary": summary[:500], "analysis": analysis[:2000], "proposed_tex": proposed_tex}


def _build_editor_prompt(current_tex: str, message: str, source_context: str | None) -> str:
    parts = [
        f"User edit request:\n{message.strip()}",
        f"Current complete TEX document:\n```latex\n{current_tex}\n```",
    ]
    if source_context:
        parts.append(f"Source paper context, extracted from the original PDF:\n```text\n{source_context}\n```")
    return "\n\n".join(parts)


def _call_editor_llm(prompt: str) -> dict[str, Any]:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("The openai package is not installed in the backend environment.") from exc

    api_key = os.environ.get("OPENAI_API_KEY")
    api_base = os.environ.get("OPENAI_API_BASE")
    model = os.environ.get("MODEL_NAME")
    if not api_key or not model:
        raise RuntimeError("LLM provider is not configured for Editor Agent.")

    client = OpenAI(api_key=api_key, base_url=api_base or None)
    messages = [
        {"role": "system", "content": EDITOR_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
    except Exception:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.1,
        )

    content = response.choices[0].message.content or ""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            raise RuntimeError("Editor Agent returned a non-JSON response.")
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise RuntimeError("Editor Agent returned malformed JSON.") from exc


def _extract_tex(value: str) -> str:
    text = str(value or "").strip()
    fence = re.search(r"```(?:latex|tex)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    return fence.group(1).strip() if fence else text


def _looks_like_complete_tex(value: str) -> bool:
    if not value or len(value) < 100:
        return False
    return "\\documentclass" in value and "\\begin{document}" in value and "\\end{document}" in value


def _load_source_context(job: dict[str, Any]) -> str | None:
    artifacts = json_loads(job.get("artifacts_json"), {})
    raw_artifact = artifacts.get("rawContent") if isinstance(artifacts, dict) else None
    raw_path = Path(raw_artifact.get("path", "")) if isinstance(raw_artifact, dict) else None
    if not raw_path or not raw_path.exists():
        return None
    try:
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
    except Exception:
        return None

    chunks: list[str] = []
    full_text = raw.get("full_text")
    if isinstance(full_text, str) and full_text:
        chunks.append(full_text[:12000])
    enhanced = raw.get("enhanced_content")
    if isinstance(enhanced, dict):
        chunks.append(json.dumps(enhanced, ensure_ascii=False)[:8000])
    return "\n\n".join(chunks)[:18000] or None


def apply_agent_edit(job_id: str, edit_id: str, user: UserOut):
    job = require_job(job_id, user)
    with connect() as conn:
        row = conn.execute("SELECT * FROM agent_edits WHERE id = ? AND job_id = ?", (edit_id, job_id)).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Edit not found")
        edit = dict(row)
        if edit["status"] != "pending":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Edit is not pending")
        proposed_path = Path(edit["proposed_tex_path"])
        if not proposed_path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposed TEX file not found")
        proposed_tex = proposed_path.read_text(encoding="utf-8")
        conn.execute("UPDATE agent_edits SET status = ?, applied_at = ? WHERE id = ?", ("applied", now_iso(), edit_id))
    tex_dir = OUTPUT_DIR / "tex" / job["session_id"]
    tex_dir.mkdir(parents=True, exist_ok=True)
    (tex_dir / "output.tex").write_text(proposed_tex, encoding="utf-8")
    updated = update_job(job_id, tex_content=proposed_tex, message="Agent edit applied. Recompile to refresh PDF.")
    emit_progress("Editor Agent", "Approved edit applied to TEX; PDF recompilation is now available", stage="done", progress=100, level="success")
    return to_job_out(updated, include_tex=True, include_events=True)
