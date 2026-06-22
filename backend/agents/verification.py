"""
Simplified Verification Agent: Lightweight Content Coverage Verification
Focus on ensuring core paper content is adequately covered in the presentation
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


class VerificationAgent:
    """
    Simplified Verification Agent focused on content coverage validation

    This agent performs lightweight verification to ensure:
    1. Core contributions are covered
    2. Key methodology is explained
    3. Important results are presented
    4. Main conclusions are conveyed

    NO complex fact-checking or hallucination detection to avoid false positives.
    """

    def __init__(
        self,
        model_name: str = "gpt-4o",
        temperature: float = 0.3,  # Moderate temperature for balanced assessment
        api_key: Optional[str] = None,
        language: str = "zh"
    ):
        """Initialize the Simplified Verification Agent"""
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
            self.logger.warning("LangChain not available, verification functionality disabled")
            self.llm = None
            emit_progress("Verification Agent", "Verification dependencies are unavailable", stage="verifying", level="warning")
            return

        if not self.api_key:
            self.logger.warning("No OpenAI API key provided, verification functionality disabled")
            self.llm = None
            emit_progress("Verification Agent", "No model credential is available for verification", stage="verifying", level="warning")
            return

        try:
            emit_progress("Verification Agent", f"Initializing verification model {self.model_name}", stage="verifying", progress=55)
            self.llm = ChatOpenAI(
                model_name=self.model_name,
                temperature=self.temperature,
                openai_api_key=self.api_key,
                openai_api_base=os.environ.get("OPENAI_API_BASE")
            )
            self.logger.info(f"Simplified Verification Agent initialized with model: {self.model_name}")
            emit_progress("Verification Agent", "Verification model is ready", stage="verifying", progress=56)
        except Exception as e:
            self.logger.error(f"Failed to initialize language model: {str(e)}")
            self.llm = None
            emit_progress("Verification Agent", "Verification model initialization failed", stage="verifying", level="error")

    def verify_content_coverage(
        self,
        original_content_path: str,
        presentation_plan_path: str,
        output_dir: str = "output"
    ) -> Tuple[bool, Dict[str, Any], str]:
        """
        Verify content coverage between original paper and presentation

        Args:
            original_content_path: Path to original extracted content JSON
            presentation_plan_path: Path to generated presentation plan JSON
            output_dir: Directory to save verification report

        Returns:
            Tuple of (coverage_adequate, verification_report, report_path)
        """
        if not self.llm:
            self.logger.error("Language model not available for verification")
            emit_progress("Verification Agent", "Verification skipped because no model is available", stage="verifying", progress=64, level="warning")
            return True, {"status": "skipped", "reason": "No LLM available"}, ""

        self.logger.info("Starting content coverage verification...")
        emit_progress("Verification Agent", "Comparing the slide plan against the extracted paper", stage="verifying", progress=57)

        try:
            # Load content files
            original_content = self._load_json_file(original_content_path)
            presentation_plan = self._load_json_file(presentation_plan_path)

            if not original_content or not presentation_plan:
                self.logger.warning("Failed to load content files, skipping verification")
                return True, {"status": "skipped", "reason": "Failed to load files"}, ""

            # Extract key content areas from original paper
            key_content_areas = self._extract_key_content_areas(original_content)
            emit_progress("Verification Agent", "Built the paper-side checklist for motivation, method, results, and conclusions", stage="verifying", progress=59)

            # Extract presentation coverage
            presentation_coverage = self._extract_presentation_coverage(presentation_plan)
            emit_progress("Verification Agent", f"Reviewed coverage across {len(presentation_plan.get('slides_plan', []))} planned slides", stage="verifying", progress=60)

            # Perform coverage assessment
            coverage_report = self._assess_content_coverage(key_content_areas, presentation_coverage)
            missing_count = len(coverage_report.get("missing_critical_content", []))
            adequate = coverage_report.get("overall_coverage_adequate", True)
            emit_progress(
                "Verification Agent",
                f"Coverage assessment {'passed' if adequate else 'found gaps'}; {missing_count} critical item(s) reported",
                stage="verifying",
                progress=63,
                level="success" if adequate else "warning",
            )

            # Generate verification report
            verification_report = {
                "verification_timestamp": self._get_timestamp(),
                "original_content_path": original_content_path,
                "presentation_plan_path": presentation_plan_path,
                "coverage_assessment": coverage_report,
                "overall_adequate": coverage_report.get("overall_coverage_adequate", True),
                "missing_content": coverage_report.get("missing_critical_content", []),
                "recommendations": coverage_report.get("improvement_recommendations", [])
            }

            # Save verification report
            os.makedirs(output_dir, exist_ok=True)
            report_path = os.path.join(output_dir, "coverage_verification_report.json")
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(verification_report, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Coverage verification completed. Report saved to: {report_path}")
            emit_progress("Verification Agent", "Verification report saved", stage="verifying", progress=64)

            coverage_adequate = verification_report["overall_adequate"]
            return coverage_adequate, verification_report, report_path

        except Exception as e:
            self.logger.error(f"Verification process failed: {str(e)}")
            # Don't fail the entire pipeline - return True to continue
            emit_progress("Verification Agent", "Verification encountered an error; the pipeline will continue conservatively", stage="verifying", progress=64, level="warning")
            return True, {"status": "error", "error": str(e)}, ""

    def _extract_key_content_areas(self, original_content: Dict) -> Dict[str, str]:
        """Extract key content areas from original paper"""
        enhanced_content = original_content.get("enhanced_content", {})
        presentation_sections = enhanced_content.get("presentation_sections", {})

        # Extract core content areas
        key_areas = {
            "problem_motivation": presentation_sections.get("problem_motivation", ""),
            "main_contributions": presentation_sections.get("solution_overview", ""),
            "methodology": presentation_sections.get("technical_approach", ""),
            "key_results": presentation_sections.get("evidence_proof", ""),
            "conclusions": presentation_sections.get("impact_significance", "")
        }

        # Also include paper title and abstract for context
        key_areas["title"] = original_content.get("title", "")
        key_areas["abstract"] = enhanced_content.get("abstract", "")

        return key_areas

    def _extract_presentation_coverage(self, presentation_plan: Dict) -> str:
        """Extract coverage from presentation plan"""
        slides_content = []

        for slide in presentation_plan.get("slides_plan", []):
            slide_info = f"Slide: {slide.get('title', '')}\n"
            slide_info += "Content: " + " | ".join(slide.get("content", []))
            slides_content.append(slide_info)

        return "\n\n".join(slides_content)

    def _assess_content_coverage(self, key_areas: Dict[str, str], presentation_coverage: str) -> Dict[str, Any]:
        """Assess how well the presentation covers key content areas"""

        # Create assessment prompt
        assessment_prompt = self._create_coverage_assessment_prompt(key_areas, presentation_coverage)

        try:
            response = self.llm.invoke([HumanMessage(content=assessment_prompt)])
            result = self._parse_assessment_response(response.content)

            return result

        except Exception as e:
            self.logger.error(f"Coverage assessment failed: {str(e)}")
            return {
                "overall_coverage_adequate": True,  # Default to adequate to avoid blocking
                "missing_critical_content": [],
                "improvement_recommendations": [],
                "error": str(e)
            }

    def _create_coverage_assessment_prompt(self, key_areas: Dict[str, str], presentation_coverage: str) -> str:
        """Create prompt for coverage assessment"""

        # Prepare key areas text
        key_areas_text = ""
        for area, content in key_areas.items():
            if content.strip():
                key_areas_text += f"**{area.upper()}:**\n{content[:500]}...\n\n"

        return f"""
You are an academic presentation evaluation expert. Please evaluate whether the generated slides adequately cover the core content of the paper.

**Important Notes:**
- This is a content coverage evaluation, not detailed fact-checking
- Focus on whether main content is included, not precision
- Use lenient standards: as long as key concepts are mentioned, consider them covered
- Don't be overly critical of wording or expression differences

**Paper Core Content:**
{key_areas_text}

**Generated Presentation Content:**
{presentation_coverage}

Please evaluate content coverage and return in JSON format:

```json
{{
  "overall_coverage_adequate": true/false,
  "coverage_scores": {{
    "problem_motivation": <0-100>,
    "main_contributions": <0-100>,
    "methodology": <0-100>,
    "key_results": <0-100>,
    "conclusions": <0-100>
  }},
  "missing_critical_content": [
    {{
      "area": "领域名称",
      "missing_content": "缺失的关键内容描述",
      "importance": "high|medium"
    }}
  ],
  "improvement_recommendations": [
    "具体的改进建议"
  ],
  "overall_assessment": "总体评估说明"
}}
```

**评估标准：**
- **充分覆盖(80-100分)**: 关键概念和要点都被提及
- **基本覆盖(60-79分)**: 主要内容被涵盖，但可能缺少一些细节
- **覆盖不足(40-59分)**: 遗漏了一些重要内容
- **严重不足(0-39分)**: 大量关键内容缺失

只有当总体覆盖度低于60分或有多个high重要性缺失时，才设置overall_coverage_adequate为false。
"""

    def _parse_assessment_response(self, response_content: str) -> Dict[str, Any]:
        """Parse JSON response from assessment prompt"""
        try:
            # Extract JSON from response if wrapped in markdown
            import re
            json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                json_str = response_content.strip()

            result = json.loads(json_str)

            # Ensure required fields exist with safe defaults
            if "overall_coverage_adequate" not in result:
                # Calculate based on scores
                scores = result.get("coverage_scores", {})
                avg_score = sum(scores.values()) / len(scores) if scores else 70
                result["overall_coverage_adequate"] = avg_score >= 60

            return result

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse assessment response: {str(e)}")
            return {
                "overall_coverage_adequate": True,  # Default to adequate
                "missing_critical_content": [],
                "improvement_recommendations": [],
                "error": "Failed to parse response"
            }

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


def verify_content_coverage(
    original_content_path: str,
    presentation_plan_path: str,
    output_dir: str = "output",
    model_name: str = "gpt-4o",
    api_key: Optional[str] = None,
    language: str = "zh"
) -> Tuple[bool, Dict[str, Any], str]:
    """
    Convenient function for content coverage verification

    Args:
        original_content_path: Path to original extracted content JSON
        presentation_plan_path: Path to generated presentation plan JSON
        output_dir: Directory to save verification report
        model_name: Language model to use
        api_key: OpenAI API key
        language: Output language

    Returns:
        Tuple of (coverage_adequate, verification_report, report_path)
    """
    agent = VerificationAgent(
        model_name=model_name,
        api_key=api_key,
        language=language
    )

    return agent.verify_content_coverage(
        original_content_path=original_content_path,
        presentation_plan_path=presentation_plan_path,
        output_dir=output_dir
    )
