from __future__ import annotations

import io
import json
import re
import zipfile
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from backend.config import DATA_DIR, OUTPUT_DIR
from backend.database import json_loads


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".eps", ".svg", ".webp"}
INCLUDEGRAPHICS_PATTERN = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")


def build_tex_bundle(job: dict[str, Any]) -> bytes:
    artifacts = json_loads(job.get("artifacts_json"), {})
    tex_path = _artifact_path(artifacts, "tex")
    tex_content = _read_tex_content(tex_path, job)
    if not tex_content:
        raise HTTPException(status_code=404, detail="TEX document is not ready")

    files: dict[str, Path] = {}
    tex_base = tex_path.parent if tex_path else OUTPUT_DIR / "tex" / job["session_id"]
    _collect_referenced_images(files, tex_content, tex_base, job["session_id"])
    _collect_raw_content_images(files, artifacts)
    _collect_session_image_dir(files, job["session_id"])

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("output.tex", tex_content)
        for arcname, path in sorted(files.items()):
            if path.exists() and path.is_file():
                archive.write(path, arcname)
    return buffer.getvalue()


def _read_tex_content(tex_path: Path | None, job: dict[str, Any]) -> str | None:
    if tex_path and tex_path.exists() and tex_path.is_file():
        return tex_path.read_text(encoding="utf-8")
    return job.get("tex_content")


def _artifact_path(artifacts: dict[str, Any], key: str) -> Path | None:
    artifact = artifacts.get(key)
    if not isinstance(artifact, dict) or not artifact.get("path"):
        return None
    path = Path(artifact["path"]).resolve()
    return path if _is_allowed_path(path) else None


def _collect_referenced_images(files: dict[str, Path], tex_content: str, tex_base: Path, session_id: str) -> None:
    for raw_ref in INCLUDEGRAPHICS_PATTERN.findall(tex_content):
        ref = raw_ref.strip()
        if not ref:
            continue
        path = _resolve_image_reference(ref, tex_base, session_id)
        if not path:
            continue
        arcname = _archive_name_for_reference(ref, path)
        if arcname:
            files.setdefault(arcname, path)


def _resolve_image_reference(ref: str, tex_base: Path, session_id: str) -> Path | None:
    candidates: list[Path] = []
    ref_path = Path(ref)
    if ref_path.is_absolute():
        candidates.append(ref_path)
    else:
        candidates.extend(
            [
                tex_base / ref_path,
                DATA_DIR / ref_path,
                OUTPUT_DIR / ref_path,
                OUTPUT_DIR / "images" / session_id / ref_path.name,
            ]
        )

    for candidate in candidates:
        resolved = candidate.resolve()
        if _is_allowed_image_path(resolved) and resolved.exists() and resolved.is_file():
            return resolved

    if ref_path.suffix:
        return None
    for extension in IMAGE_EXTENSIONS:
        found = _resolve_image_reference(f"{ref}{extension}", tex_base, session_id)
        if found:
            return found
    return None


def _collect_raw_content_images(files: dict[str, Path], artifacts: dict[str, Any]) -> None:
    raw_path = _artifact_path(artifacts, "rawContent")
    if not raw_path or not raw_path.exists():
        return
    try:
        raw_content = json.loads(raw_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    for image in raw_content.get("images", []):
        if not isinstance(image, dict) or not image.get("path"):
            continue
        path = Path(image["path"]).resolve()
        if _is_allowed_image_path(path) and path.exists() and path.is_file():
            files.setdefault(_default_image_archive_name(path), path)


def _collect_session_image_dir(files: dict[str, Path], session_id: str) -> None:
    directory = (OUTPUT_DIR / "images" / session_id).resolve()
    if not directory.exists():
        return
    for path in directory.rglob("*"):
        if path.is_file() and _is_allowed_image_path(path.resolve()):
            files.setdefault(_default_image_archive_name(path.resolve()), path.resolve())


def _archive_name_for_reference(ref: str, path: Path) -> str | None:
    ref_path = Path(ref)
    if not ref_path.is_absolute() and ".." not in ref_path.parts:
        cleaned = ref_path.as_posix().lstrip("./")
        return cleaned if cleaned else None
    return _default_image_archive_name(path)


def _default_image_archive_name(path: Path) -> str:
    return (Path("images") / path.name).as_posix()


def _is_allowed_image_path(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTENSIONS and _is_allowed_path(path)


def _is_allowed_path(path: Path) -> bool:
    allowed_roots = [
        DATA_DIR.resolve(),
        OUTPUT_DIR.resolve(),
    ]
    for root in allowed_roots:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            continue
    return False
