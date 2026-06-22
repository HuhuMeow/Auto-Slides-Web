"""Presentation-planning service used by the web conversion pipeline."""

from __future__ import annotations

from backend.agents.planning import PlanningAgent


def generate_presentation_plan(
    raw_content_path: str,
    output_dir: str,
    model_name: str,
    language: str,
    api_key: str | None = None,
) -> tuple[dict | None, str | None, PlanningAgent]:
    planner = PlanningAgent(
        lightweight_content_path=raw_content_path,
        output_dir=output_dir,
        model_name=model_name,
        api_key=api_key,
        language=language,
    )
    plan = planner.generate_presentation_plan()
    if not plan:
        return None, None, planner
    path = planner.save_presentation_plan(plan)
    return plan, path, planner
