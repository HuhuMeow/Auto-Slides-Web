"""
Simplified Repair Agent: Lightweight Content Supplementation
Focus on adding missing critical content to improve presentation coverage
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv

from backend.progress import emit_progress

# Load environment variables
if os.path.exists(".env"):
    load_dotenv(".env")
elif os.path.exists("env.local"):
    load_dotenv("env.local")

# Try to import LangChain packages
try:
    from langchain_openai import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate
    from langchain.schema import HumanMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


class RepairAgent:
    """
    Simplified Repair Agent focused on content supplementation

    This agent performs lightweight repairs to improve content coverage:
    1. Add missing key contributions
    2. Supplement methodology explanations
    3. Include important results
    4. Enhance conclusions

    NO complex error correction to avoid introducing new issues.
    """

    def __init__(
        self,
        model_name: str = "gpt-4o",
        temperature: float = 0.4,  # Moderate temperature for creative content generation
        api_key: Optional[str] = None,
        language: str = "zh"
    ):
        """Initialize the Simplified Repair Agent"""
        self.model_name = model_name
        self.temperature = temperature

        # Load API key
        if not api_key:
            api_key = os.environ.get("OPENAI_API_KEY")

        self.api_key = api_key
        self.language = language
        self.logger = logging.getLogger(__name__)

        # Initialize language model
        self._init_model()

    def _init_model(self):
        """Initialize the language model"""
        if not LANGCHAIN_AVAILABLE:
            self.logger.warning("LangChain not available, repair functionality disabled")
            self.llm = None
            emit_progress("Repair Agent", "Repair dependencies are unavailable", stage="repairing", level="warning")
            return

        if not self.api_key:
            self.logger.warning("No OpenAI API key provided, repair functionality disabled")
            self.llm = None
            emit_progress("Repair Agent", "No model credential is available for repair", stage="repairing", level="warning")
            return

        try:
            emit_progress("Repair Agent", f"Initializing repair model {self.model_name}", stage="repairing", progress=70)
            self.llm = ChatOpenAI(
                model_name=self.model_name,
                temperature=self.temperature,
                openai_api_key=self.api_key,
                openai_api_base=os.environ.get("OPENAI_API_BASE")
            )
            self.logger.info(f"Simplified Repair Agent initialized with model: {self.model_name}")
            emit_progress("Repair Agent", "Repair model is ready", stage="repairing", progress=71)
        except Exception as e:
            self.logger.error(f"Failed to initialize language model: {str(e)}")
            self.llm = None
            emit_progress("Repair Agent", "Repair model initialization failed", stage="repairing", level="error")

    def repair_content_coverage(
        self,
        presentation_plan_path: str,
        verification_report_path: str,
        original_content_path: str,
        output_dir: str = "output"
    ) -> Tuple[bool, Dict[str, Any], str]:
        """
        Repair presentation plan by adding missing critical content

        Args:
            presentation_plan_path: Path to original presentation plan JSON
            verification_report_path: Path to verification report JSON
            original_content_path: Path to original content for reference
            output_dir: Directory to save repaired plan

        Returns:
            Tuple of (repair_applied, repair_report, repaired_plan_path)
        """
        if not self.llm:
            self.logger.warning("Language model not available, skipping repair")
            emit_progress("Repair Agent", "Repair skipped because no model is available", stage="repairing", progress=79, level="warning")
            return False, {"status": "skipped", "reason": "No LLM available"}, presentation_plan_path

        self.logger.info("Starting content coverage repair...")
        emit_progress("Repair Agent", "Loading the plan, verification report, and source evidence", stage="repairing", progress=72)

        try:
            # Load content files
            presentation_plan = self._load_json_file(presentation_plan_path)
            verification_report = self._load_json_file(verification_report_path)
            original_content = self._load_json_file(original_content_path)

            if not presentation_plan:
                self.logger.error("Failed to load presentation plan")
                return False, {"error": "Failed to load presentation plan"}, ""

            # Check if repair is needed
            if not verification_report or verification_report.get("overall_adequate", True):
                self.logger.info("Content coverage is adequate, no repair needed")
                emit_progress("Repair Agent", "Verification already passed; no plan repair is needed", stage="repairing", progress=79, level="success")
                return False, {"status": "no_repair_needed", "reason": "Coverage adequate"}, presentation_plan_path

            # Extract missing content information
            missing_content = verification_report.get("missing_content", [])
            if not missing_content:
                self.logger.info("No specific missing content identified, no repair needed")
                emit_progress("Repair Agent", "No actionable missing-content items were reported", stage="repairing", progress=79)
                return False, {"status": "no_missing_content"}, presentation_plan_path

            high_priority = [item for item in missing_content if item.get("importance") == "high"]
            emit_progress("Repair Agent", f"Preparing repairs for {len(high_priority)} high-priority gap(s)", stage="repairing", progress=73)

            # Make a copy of the presentation plan for modification
            repaired_plan = self._deep_copy_plan(presentation_plan)

            # Initialize repair report
            repair_report = {
                "repair_timestamp": self._get_timestamp(),
                "original_plan_path": presentation_plan_path,
                "verification_report_path": verification_report_path,
                "repairs_applied": [],
                "repair_summary": {}
            }

            # Apply repairs for missing content
            repairs_made = 0
            for item_index, missing_item in enumerate(missing_content):
                if missing_item.get("importance") == "high":
                    try:
                        repair_applied = self._add_missing_content(
                            repaired_plan,
                            missing_item,
                            original_content
                        )

                        if repair_applied:
                            repair_report["repairs_applied"].append(repair_applied)
                            repairs_made += 1
                            self.logger.info(f"Added missing content for: {missing_item.get('area', 'unknown')}")
                            emit_progress(
                                "Repair Agent",
                                f"Added evidence-backed content for {missing_item.get('area', 'an uncovered area')}",
                                stage="repairing",
                                progress=min(78, 74 + item_index),
                            )

                    except Exception as e:
                        self.logger.warning(f"Failed to repair missing content: {e}")

            # Generate repair summary
            repair_report["repair_summary"] = {
                "total_repairs": repairs_made,
                "repair_success": repairs_made > 0,
                "status": "completed" if repairs_made > 0 else "no_changes"
            }

            # Save repaired plan if changes were made
            if repairs_made > 0:
                os.makedirs(output_dir, exist_ok=True)
                repaired_plan_path = os.path.join(output_dir, "content_repaired_presentation_plan.json")
                with open(repaired_plan_path, 'w', encoding='utf-8') as f:
                    json.dump(repaired_plan, f, ensure_ascii=False, indent=2)

                # Save repair report
                repair_report_path = os.path.join(output_dir, "content_repair_report.json")
                with open(repair_report_path, 'w', encoding='utf-8') as f:
                    json.dump(repair_report, f, ensure_ascii=False, indent=2)

                self.logger.info(f"Content repair completed. Repaired plan saved to: {repaired_plan_path}")
                emit_progress("Repair Agent", f"Repair completed with {repairs_made} plan change(s)", stage="repairing", progress=79, level="success")
                return True, repair_report, repaired_plan_path
            else:
                self.logger.info("No repairs were applied")
                emit_progress("Repair Agent", "No safe evidence-backed repairs could be applied", stage="repairing", progress=79, level="warning")
                return False, repair_report, presentation_plan_path

        except Exception as e:
            self.logger.error(f"Repair process failed: {str(e)}")
            emit_progress("Repair Agent", "Repair failed; the original plan remains unchanged", stage="repairing", progress=79, level="error")
            return False, {"error": str(e)}, presentation_plan_path

    def _add_missing_content(self, presentation_plan: Dict, missing_item: Dict, original_content: Dict) -> Optional[Dict]:
        """Add missing content to appropriate slide"""

        area = missing_item.get("area", "")
        missing_content_desc = missing_item.get("missing_content", "")

        # Generate supplementary content
        supplementary_content = self._generate_supplementary_content(
            area, missing_content_desc, original_content
        )

        if not supplementary_content:
            return None

        # Find appropriate slide to add content
        target_slide_index = self._find_target_slide(presentation_plan, area)

        if target_slide_index is not None:
            # Add content to existing slide
            slides = presentation_plan.get("slides_plan", [])
            if target_slide_index < len(slides):
                slides[target_slide_index]["content"].extend(supplementary_content)

                return {
                    "type": "content_addition",
                    "area": area,
                    "content_added": supplementary_content,
                    "target_slide": target_slide_index,
                    "slide_title": slides[target_slide_index].get("title", "")
                }
        else:
            # Create new slide for missing content
            new_slide = self._create_supplementary_slide(area, supplementary_content)
            if new_slide:
                presentation_plan.setdefault("slides_plan", []).append(new_slide)

                return {
                    "type": "new_slide_creation",
                    "area": area,
                    "new_slide": new_slide,
                    "slide_position": len(presentation_plan["slides_plan"]) - 1
                }

        return None

    def _generate_supplementary_content(self, area: str, missing_content_desc: str, original_content: Dict) -> List[str]:
        """Generate supplementary content for missing area"""

        # Extract relevant original content
        enhanced_content = original_content.get("enhanced_content", {})
        presentation_sections = enhanced_content.get("presentation_sections", {})

        # Map area to original content section
        area_mapping = {
            "problem_motivation": presentation_sections.get("problem_motivation", ""),
            "main_contributions": presentation_sections.get("solution_overview", ""),
            "methodology": presentation_sections.get("technical_approach", ""),
            "key_results": presentation_sections.get("evidence_proof", ""),
            "conclusions": presentation_sections.get("impact_significance", "")
        }

        original_section_content = area_mapping.get(area, "")

        # Create generation prompt
        generation_prompt = self._create_content_generation_prompt(
            area, missing_content_desc, original_section_content
        )

        try:
            response = self.llm.invoke([HumanMessage(content=generation_prompt)])
            content_list = self._parse_content_response(response.content)
            return content_list

        except Exception as e:
            self.logger.error(f"Failed to generate supplementary content: {e}")
            return []

    def _create_content_generation_prompt(self, area: str, missing_desc: str, original_content: str) -> str:
        """Create prompt for generating supplementary content"""

        return f"""
You are an academic presentation content generation expert. Please generate missing slide points based on the original paper content.

**Missing Content Area:** {area}
**Missing Content Description:** {missing_desc}

**Original Paper Related Content:**
{original_content[:2000] if original_content else "No relevant original content"}

**Task Requirements:**
1. Generate 2-4 concise slide points
2. Each point should be a complete sentence or phrase
3. Content should be based on the original paper, don't add non-existent information
4. Use professional academic presentation language
5. If original content is insufficient, generate general but reasonable points

**Output Format:**
Please return the points list directly, one point per line, no numbering required:

Point 1
Point 2
Point 3
Point 4 (if needed)

**Example Output:**
Proposed a new deep learning framework to address limitations of existing methods
The method achieved significant performance improvements on multiple benchmark datasets
Experiments validated the effectiveness and generalization ability of the proposed method
"""

    def _parse_content_response(self, response_content: str) -> List[str]:
        """Parse content generation response into list of bullet points"""
        try:
            lines = response_content.strip().split('\n')
            content_list = []

            for line in lines:
                line = line.strip()
                # Remove common prefixes
                line = line.lstrip('- •*').strip()
                # Remove numbering
                import re
                line = re.sub(r'^\d+[\.\)]\s*', '', line)

                if line and len(line) > 5:  # Valid content
                    content_list.append(line)

            return content_list[:4]  # Limit to 4 points max

        except Exception as e:
            self.logger.error(f"Failed to parse content response: {e}")
            return []

    def _find_target_slide(self, presentation_plan: Dict, area: str) -> Optional[int]:
        """Find appropriate slide to add content based on area"""

        slides = presentation_plan.get("slides_plan", [])

        # Define area keywords to match slide titles
        area_keywords = {
            "problem_motivation": ["问题", "挑战", "动机", "背景", "problem", "challenge", "motivation"],
            "main_contributions": ["贡献", "创新", "方法", "contribution", "innovation", "approach"],
            "methodology": ["方法", "算法", "技术", "methodology", "algorithm", "technique", "method"],
            "key_results": ["结果", "实验", "评估", "result", "experiment", "evaluation", "performance"],
            "conclusions": ["结论", "总结", "conclusion", "summary", "future"]
        }

        keywords = area_keywords.get(area, [])

        # Look for matching slide titles
        for i, slide in enumerate(slides):
            title = slide.get("title", "").lower()
            if any(keyword in title for keyword in keywords):
                return i

        return None

    def _create_supplementary_slide(self, area: str, content_list: List[str]) -> Optional[Dict]:
        """Create a new slide for supplementary content"""

        if not content_list:
            return None

        # Define slide titles based on area
        area_titles = {
            "problem_motivation": "研究动机与挑战",
            "main_contributions": "主要贡献",
            "methodology": "技术方法",
            "key_results": "关键结果",
            "conclusions": "结论与展望"
        }

        title = area_titles.get(area, f"{area.title()} 补充")

        # Get next slide number
        slide_number = 999  # Will be adjusted when inserted

        return {
            "slide_number": slide_number,
            "title": title,
            "content": content_list,
            "includes_figure": False,
            "figure_reference": None,
            "includes_table": False,
            "table_reference": None,
            "presenter_notes": f"补充内容：{area}相关的重要信息",
            "supplementary": True  # Mark as supplementary slide
        }

    def _deep_copy_plan(self, plan: Dict) -> Dict:
        """Create a deep copy of the presentation plan"""
        import copy
        return copy.deepcopy(plan)

    def _load_json_file(self, file_path: str) -> Optional[Dict]:
        """Load and parse JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load JSON file {file_path}: {str(e)}")
            return None

    def _get_timestamp(self) -> str:
        """Get current timestamp for reporting"""
        from datetime import datetime
        return datetime.now().isoformat()


def repair_content_coverage(
    presentation_plan_path: str,
    verification_report_path: str,
    original_content_path: str,
    output_dir: str = "output",
    model_name: str = "gpt-4o",
    api_key: Optional[str] = None,
    language: str = "zh"
) -> Tuple[bool, Dict[str, Any], str]:
    """
    Convenient function for content coverage repair

    Args:
        presentation_plan_path: Path to original presentation plan JSON
        verification_report_path: Path to verification report JSON
        original_content_path: Path to original content for reference
        output_dir: Directory to save repaired plan
        model_name: Language model to use
        api_key: OpenAI API key
        language: Output language

    Returns:
        Tuple of (repair_applied, repair_report, repaired_plan_path)
    """
    agent = RepairAgent(
        model_name=model_name,
        api_key=api_key,
        language=language
    )

    return agent.repair_content_coverage(
        presentation_plan_path=presentation_plan_path,
        verification_report_path=verification_report_path,
        original_content_path=original_content_path,
        output_dir=output_dir
    )
