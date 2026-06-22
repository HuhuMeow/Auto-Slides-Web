from __future__ import annotations

from typing import Any

from backend.schemas import PresentationPlan, VerificationReport


def camel_slide(slide: dict[str, Any]) -> dict[str, Any]:
    return {
        "slideNumber": slide.get("slideNumber") or slide.get("slide_number") or 0,
        "title": slide.get("title", ""),
        "slideType": slide.get("slideType") or slide.get("slide_type") or "content",
        "content": slide.get("content") if isinstance(slide.get("content"), list) else [],
        "includesFigure": slide.get("includesFigure", slide.get("includes_figure")),
        "figureReference": slide.get("figureReference") or slide.get("figure_reference"),
        "estimatedTime": slide.get("estimatedTime") or slide.get("estimated_time"),
    }


def normalize_plan(raw: dict[str, Any] | None) -> PresentationPlan:
    raw = raw or {}
    return PresentationPlan(
        paperInfo=raw.get("paperInfo") or raw.get("paper_info") or {},
        keyContent=raw.get("keyContent") or raw.get("key_content") or {},
        slidesPlan=[camel_slide(slide) for slide in raw.get("slidesPlan", raw.get("slides_plan", []))],
        language=raw.get("language", "en"),
        pdfPath=raw.get("pdfPath") or raw.get("pdf_path"),
    )


def normalize_verification(raw: dict[str, Any] | None, passed: bool | None = None) -> VerificationReport:
    raw = raw or {}
    missing = raw.get("missingContent") or raw.get("missing_content") or []
    risks = raw.get("risks") or raw.get("issues") or []
    normalized_missing = []
    for item in missing:
        normalized_missing.append(
            {
                "area": item.get("area") or item.get("section") or "Unknown",
                "importance": item.get("importance", "medium") if item.get("importance") in {"low", "medium", "high"} else "medium",
                "missingContent": item.get("missingContent") or item.get("missing_content") or item.get("content") or "",
                "suggestedAction": item.get("suggestedAction") or item.get("suggested_action") or item.get("recommendation") or "",
            }
        )
    normalized_risks = []
    for item in risks:
        risk_type = item.get("type", "omission")
        severity = item.get("severity", "medium")
        normalized_risks.append(
            {
                "type": risk_type if risk_type in {"omission", "hallucination", "weak_evidence", "format"} else "omission",
                "severity": severity if severity in {"low", "medium", "high"} else "medium",
                "message": item.get("message") or item.get("description") or str(item),
            }
        )
    report_passed = bool(raw.get("passed", raw.get("coverage_adequate", passed if passed is not None else not normalized_missing)))
    score = raw.get("coverageScore") or raw.get("coverage_score")
    if score is None:
        score = 96 if report_passed else 75
    return VerificationReport(
        passed=report_passed,
        coverageScore=int(score),
        summary=raw.get("summary") or raw.get("message") or ("Verification passed" if report_passed else "Verification found possible gaps"),
        missingContent=normalized_missing,
        risks=normalized_risks,
    )


def normalize_speech(raw: dict[str, Any] | None) -> dict[str, Any] | None:
    if not raw:
        return None
    if "sections" in raw and isinstance(raw.get("sections"), list):
        return {
            **raw,
            "sections": [_normalize_speech_section(item, index) for index, item in enumerate(raw["sections"], start=1)],
        }
    metadata = raw.get("metadata", {})
    script = raw.get("full_script", {})
    speech_script = script.get("speech_script", script.get("slides", []))
    sections = []

    if isinstance(speech_script, dict):
        opening = speech_script.get("opening")
        if opening:
            sections.append(_normalize_speech_section(opening, 0, title="Opening", number=0))

        slides = speech_script.get("slides", [])
        if isinstance(slides, dict):
            slides = list(slides.values())
        for index, item in enumerate(slides if isinstance(slides, list) else [], start=1):
            sections.append(_normalize_speech_section(item, index))

        conclusion = speech_script.get("conclusion")
        if conclusion:
            next_number = max([section["slideNumber"] for section in sections], default=0) + 1
            sections.append(_normalize_speech_section(conclusion, next_number, title="Conclusion", number=next_number))
    elif isinstance(speech_script, list):
        for index, item in enumerate(speech_script, start=1):
            sections.append(_normalize_speech_section(item, index))
    elif isinstance(speech_script, str):
        sections.append(_normalize_speech_section(speech_script, 1))

    return {
        "title": metadata.get("title", "Speech Script"),
        "targetDurationMinutes": raw.get("target_duration_minutes", metadata.get("target_duration_minutes", 15)),
        "style": raw.get("presentation_style", "academic_conference"),
        "sections": sections,
    }


def _normalize_speech_section(item: Any, index: int, title: str | None = None, number: int | None = None) -> dict[str, Any]:
    if isinstance(item, str):
        return {
            "slideNumber": number if number is not None else index,
            "slideTitle": title or f"Slide {index}",
            "duration": "",
            "script": item,
            "speakerNotes": [],
        }
    if not isinstance(item, dict):
        return {
            "slideNumber": number if number is not None else index,
            "slideTitle": title or f"Slide {index}",
            "duration": "",
            "script": str(item),
            "speakerNotes": [],
        }

    duration = item.get("duration", item.get("estimated_time", item.get("duration_minutes", "")))
    if isinstance(duration, (int, float)):
        duration = f"{duration:g} min"
    notes = item.get("speakerNotes", item.get("speaker_notes", item.get("notes", [])))
    if isinstance(notes, str):
        notes = [notes]
    if not isinstance(notes, list):
        notes = []
    return {
        "slideNumber": number if number is not None else item.get("slide_number", item.get("slideNumber", index)),
        "slideTitle": title or item.get("slide_title", item.get("slideTitle", item.get("title", f"Slide {index}"))),
        "duration": str(duration),
        "script": item.get("script", item.get("speech_text", item.get("speech_content", item.get("content", "")))),
        "speakerNotes": notes,
    }
