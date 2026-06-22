"""Web pipeline service for generating and compiling Beamer documents."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from PIL import Image, ImageDraw

from backend.agents.tex_generation import TexGenerationAgent
from backend.services.tex_compiler import TexValidator
from backend.progress import emit_progress

logger = logging.getLogger(__name__)


class TexWorkflow:
    """Turn one presentation plan into reviewable TEX and, optionally, PDF."""

    def __init__(
        self,
        presentation_plan_path: str,
        output_dir: str,
        images_dir: str,
        model_name: str,
        language: str,
        theme: str,
        max_retries: int = 3,
    ) -> None:
        self.plan_path = Path(presentation_plan_path)
        self.output_dir = Path(output_dir)
        self.images_dir = Path(images_dir)
        self.max_retries = max(1, max_retries)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)

        self.generator = TexGenerationAgent(
            presentation_plan_path=str(self.plan_path),
            output_dir=str(self.output_dir),
            images_dir=str(self.images_dir),
            model_name=model_name,
            language=language,
            theme=theme,
        )
        self.validator = TexValidator(
            output_dir=str(self.output_dir),
            language=language,
            images_dir=str(self.images_dir),
        )

    def process(self, skip_compilation: bool = False) -> tuple[bool, str, str | None]:
        try:
            plan = json.loads(self.plan_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            emit_progress("TEX Workflow", "Presentation plan could not be loaded for TEX generation", stage="generating_tex", level="error")
            return False, f"Unable to load presentation plan: {exc}", None

        self._normalize_image_references(plan)
        emit_progress("TEX Workflow", "Image references and placeholders are ready", stage="generating_tex", progress=86)
        self.generator.presentation_plan = plan
        tex_code = self.generator.generate_tex()
        if not tex_code:
            emit_progress("TEX Workflow", "TEX generation returned no usable document", stage="generating_tex", level="error")
            return False, "TEX code generation failed", None

        tex_path = self.output_dir / "output.tex"
        tex_path.write_text(tex_code, encoding="utf-8")
        emit_progress("TEX Workflow", "Generated TEX source saved", stage="generating_tex", progress=89)
        if skip_compilation:
            emit_progress("TEX Workflow", "PDF compilation was disabled; TEX delivery is complete", stage="generating_tex", progress=95, level="success")
            return True, "TEX generation successful", str(tex_path)

        last_error = "LaTeX compilation failed"
        for attempt in range(1, self.max_retries + 1):
            emit_progress("TEX Workflow", f"Starting LaTeX compilation attempt {attempt} of {self.max_retries}", stage="compiling", progress=min(94, 90 + attempt))
            success, message, pdf_path = self.validator.validate(str(tex_path))
            if success:
                emit_progress("TEX Workflow", "LaTeX compilation succeeded", stage="compiling", progress=95, level="success")
                return True, "TEX generation and compilation successful", pdf_path

            last_error = message
            if attempt == self.max_retries:
                break
            emit_progress("TEX Fix Agent", "Compilation reported an error; preparing a minimal TEX repair", stage="compiling", progress=min(94, 90 + attempt), level="warning")
            current_tex = tex_path.read_text(encoding="utf-8")
            repaired_tex = self.validator.fix_tex_code(current_tex, message, self.generator.llm)
            if repaired_tex == current_tex:
                break
            tex_path.write_text(repaired_tex, encoding="utf-8")
            emit_progress("TEX Fix Agent", "Repaired TEX saved for another compilation attempt", stage="compiling", progress=min(94, 91 + attempt))
            time.sleep(1)

        emit_progress("TEX Workflow", "LaTeX compilation exhausted all repair attempts", stage="compiling", level="error")
        return False, f"TEX compilation failed: {last_error}", None

    def _normalize_image_references(self, plan: dict) -> None:
        changed = False
        for slide in plan.get("slides_plan", []):
            figure = slide.get("figure_reference") if slide.get("includes_figure") else None
            if not isinstance(figure, dict):
                continue

            source = figure.get("filename") or figure.get("path")
            if not source:
                slide["includes_figure"] = False
                slide["figure_reference"] = None
                changed = True
                continue

            filename = Path(str(source)).name
            target = self.images_dir / filename
            if not target.exists():
                filename = f"placeholder_{Path(filename).stem}.png"
                target = self.images_dir / filename
                self._create_placeholder(target)

            figure["filename"] = filename
            figure["path"] = f"images/{filename}"
            changed = True

        if changed:
            self.plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _create_placeholder(path: Path) -> None:
        image = Image.new("RGB", (640, 360), color=(235, 240, 242))
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 639, 359), outline=(140, 150, 155), width=2)
        draw.text((245, 170), "Image unavailable", fill=(70, 80, 85))
        image.save(path)


def run_tex_workflow(
    presentation_plan_path: str,
    output_dir: str,
    images_dir: str,
    model_name: str,
    language: str,
    theme: str,
    max_retries: int = 3,
    skip_compilation: bool = False,
) -> tuple[bool, str, str | None]:
    workflow = TexWorkflow(
        presentation_plan_path=presentation_plan_path,
        output_dir=output_dir,
        images_dir=images_dir,
        model_name=model_name,
        language=language,
        theme=theme,
        max_retries=max_retries,
    )
    return workflow.process(skip_compilation=skip_compilation)
