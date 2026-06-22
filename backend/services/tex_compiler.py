"""Compile generated Beamer source in an isolated directory."""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

from backend.prompts import TEX_ERROR_FIX_PROMPT
from backend.progress import emit_progress

logger = logging.getLogger(__name__)


class TexValidator:
    def __init__(self, output_dir: str, language: str = "en", images_dir: str | None = None) -> None:
        self.output_dir = Path(output_dir)
        self.language = language
        self.images_dir = Path(images_dir) if images_dir else None
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def validate(self, tex_file: str, timeout: int = 60) -> tuple[bool, str, str | None]:
        source = Path(tex_file)
        if not source.is_file():
            emit_progress("TEX Compiler", "The TEX source file is missing", stage="compiling", level="error")
            return False, f"TEX file does not exist: {source}", None

        compiler = "xelatex" if self.language == "zh" else "pdflatex"
        if not shutil.which(compiler):
            emit_progress("TEX Compiler", f"Required compiler {compiler} is not installed", stage="compiling", level="error")
            return False, f"Required LaTeX compiler is not installed: {compiler}", None

        emit_progress("TEX Compiler", f"Staging an isolated {compiler} build environment", stage="compiling", progress=90)

        with tempfile.TemporaryDirectory(prefix="autoslides-") as temp_name:
            temp_dir = Path(temp_name)
            temp_tex = temp_dir / source.name
            shutil.copy2(source, temp_tex)
            self._stage_images(temp_dir / "images")
            self._normalize_image_references(temp_tex, temp_dir / "images")
            emit_progress("TEX Compiler", "TEX source and referenced images staged", stage="compiling", progress=91)

            command = [compiler, "-shell-escape", "-interaction=nonstopmode", source.name]
            last_output = ""
            try:
                for _ in range(3):
                    process = subprocess.run(
                        command,
                        cwd=temp_dir,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                    )
                    last_output = f"{process.stdout}\n{process.stderr}"
                    if process.returncode != 0:
                        emit_progress("TEX Compiler", "Compiler returned an actionable LaTeX error", stage="compiling", progress=93, level="warning")
                        return False, self._extract_error(last_output), None
            except subprocess.TimeoutExpired:
                emit_progress("TEX Compiler", f"Compilation exceeded the {timeout}-second timeout", stage="compiling", level="error")
                return False, f"LaTeX compilation exceeded {timeout} seconds", None

            pdf = temp_dir / f"{source.stem}.pdf"
            if not pdf.exists():
                emit_progress("TEX Compiler", "The compiler exited without producing a PDF", stage="compiling", level="error")
                return False, "LaTeX exited successfully but produced no PDF", None
            destination = self.output_dir / pdf.name
            shutil.copy2(pdf, destination)
            log = temp_dir / f"{source.stem}.log"
            if log.exists():
                shutil.copy2(log, self.output_dir / log.name)
            emit_progress("TEX Compiler", "PDF compiled successfully and copied to job artifacts", stage="compiling", progress=95, level="success")
            return True, "Compilation successful", str(destination)

    def _stage_images(self, target: Path) -> None:
        target.mkdir(parents=True, exist_ok=True)
        if not self.images_dir or not self.images_dir.is_dir():
            return
        for source in self.images_dir.iterdir():
            if source.is_file():
                shutil.copy2(source, target / source.name)

    def _normalize_image_references(self, tex_file: Path, staged_images: Path) -> None:
        content = tex_file.read_text(encoding="utf-8")
        pattern = re.compile(r"\\includegraphics(?:\[[^]]*])?\{([^}]+)}")

        def replace(match: re.Match[str]) -> str:
            filename = Path(match.group(1)).name
            target = staged_images / filename
            if not target.exists():
                filename = f"placeholder_{Path(filename).stem}.png"
                target = staged_images / filename
                self._create_placeholder(target)
            return rf"\includegraphics[width=0.7\textwidth,height=0.4\textheight,keepaspectratio]{{images/{filename}}}"

        tex_file.write_text(pattern.sub(replace, content), encoding="utf-8")

    @staticmethod
    def _create_placeholder(path: Path) -> None:
        image = Image.new("RGB", (640, 360), color=(235, 240, 242))
        draw = ImageDraw.Draw(image)
        draw.text((245, 170), "Image unavailable", fill=(70, 80, 85))
        image.save(path)

    @staticmethod
    def _extract_error(output: str) -> str:
        errors = re.findall(r"^!\s+(.+)$", output, re.MULTILINE)
        if errors:
            return "; ".join(errors[:3])
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        return "\n".join(lines[-12:]) or "Unknown LaTeX compilation error"

    def fix_tex_code(self, tex_code: str, error_message: str, model) -> str:
        if model is None:
            return tex_code
        try:
            from langchain.prompts import ChatPromptTemplate

            prompt = ChatPromptTemplate.from_template(TEX_ERROR_FIX_PROMPT)
            response = (prompt | model).invoke(
                {"error_message": error_message, "tex_code": tex_code, "font_info": ""}
            )
            emit_progress("TEX Fix Agent", "Model returned a repair candidate for the compiler error", stage="compiling", progress=93)
            fixed = response.content if hasattr(response, "content") else str(response)
            fenced = re.search(r"```(?:latex|tex)?\s*(.*?)```", fixed, re.DOTALL)
            return (fenced.group(1) if fenced else fixed).strip()
        except Exception:
            logger.exception("LLM-based TEX repair failed")
            emit_progress("TEX Fix Agent", "Automated TEX repair failed; preserving the current source", stage="compiling", level="error")
            return tex_code
