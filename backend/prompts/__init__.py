"""Prompt templates used by the active Web agents."""

from .key_content_extraction import KEY_CONTENT_EXTRACTION_PROMPT
from .slides_planning import SLIDES_PLANNING_PROMPT
from .tex_generation import TEX_GENERATION_PROMPT
from .tex_error_fix import TEX_ERROR_FIX_PROMPT

from .extract_tables_and_equations import EXTRACT_TABLES_AND_EQUATIONS_PROMPT
from .summarize_text_for_presentation import SUMMARIZE_TEXT_FOR_PRESENTATION_PROMPT

__all__ = [
    "EXTRACT_TABLES_AND_EQUATIONS_PROMPT",
    "KEY_CONTENT_EXTRACTION_PROMPT",
    "SLIDES_PLANNING_PROMPT",
    "SUMMARIZE_TEXT_FOR_PRESENTATION_PROMPT",
    "TEX_ERROR_FIX_PROMPT",
    "TEX_GENERATION_PROMPT",
]
