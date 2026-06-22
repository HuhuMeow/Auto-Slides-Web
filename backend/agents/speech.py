"""
Speech Generator Agent: Generate presentation speech scripts for slides

This module creates natural, engaging speech scripts that accompany the generated slides,
with proper timing, transitions, and presentation techniques.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv

# Import our unified LLM interface and parameter system
from backend.llm.client import LLMInterface
from backend.llm.settings import TaskType
from backend.progress import emit_progress

# Load environment variables
if os.path.exists(".env"):
    load_dotenv(".env")
elif os.path.exists("env.local"):
    load_dotenv("env.local")

logger = logging.getLogger(__name__)

class SpeechAgent:
    """
    Speech Generator Agent for creating presentation speech scripts

    This agent generates natural, engaging speech content that accompanies slides,
    with proper timing, transitions, and presentation techniques.
    """

    def __init__(
        self,
        model_name: str = "gpt-4o",
        api_key: Optional[str] = None,
        language: str = "en"
    ):
        """
        Initialize the Speech Generator Agent

        Args:
            model_name: Language model to use for speech generation
            api_key: OpenAI API key
            language: Output language for speech script
        """
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.language = language

        # Setup logging
        self.logger = logging.getLogger(__name__)

        # Initialize unified LLM interface for task-optimized speech generation
        try:
            self.llm_interface = LLMInterface(model_name, api_key)
            self.logger.info("Speech Generator initialized with unified LLM interface")
            emit_progress("Speech Agent", f"Speech model {model_name} is ready", stage="generating_speech", progress=96)
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM interface: {e}")
            self.llm_interface = None
            emit_progress("Speech Agent", "Speech model initialization failed", stage="generating_speech", level="error")

    def generate_speech_script(
        self,
        presentation_plan_path: str,
        output_dir: str,
        original_content_path: Optional[str] = None,
        target_duration_minutes: int = 15,
        presentation_style: str = "academic_conference",
        audience_level: str = "expert"
    ) -> Tuple[bool, Dict[str, Any], str]:
        """
        Generate a complete speech script for the presentation

        Args:
            presentation_plan_path: Path to the presentation plan JSON file
            original_content_path: Optional path to original paper content for context
            output_dir: Directory to save the speech script
            target_duration_minutes: Target duration for the presentation
            presentation_style: Style of presentation (academic_conference, seminar, pitch, etc.)
            audience_level: Target audience level (expert, general, student)

        Returns:
            Tuple of (success, speech_data, output_path)
        """
        try:
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)

            # Load presentation plan
            presentation_plan = self._load_presentation_plan(presentation_plan_path)
            if not presentation_plan:
                return False, {"error": "Failed to load presentation plan"}, ""
            emit_progress(
                "Speech Agent",
                f"Preparing narration for {len(presentation_plan.get('slides_plan', []))} slides",
                stage="generating_speech",
                progress=97,
            )

            # Load original content if provided
            original_content = None
            if original_content_path:
                original_content = self._load_original_content(original_content_path)

            # Generate speech script
            self.logger.info("Generating speech script...")
            emit_progress("Speech Agent", f"Writing a {target_duration_minutes}-minute {presentation_style} script", stage="generating_speech", progress=97)
            speech_script = self._generate_speech_content(
                presentation_plan,
                original_content,
                target_duration_minutes,
                presentation_style,
                audience_level
            )

            # Calculate timing and add presentation notes
            timed_script = self._add_timing_and_notes(speech_script, target_duration_minutes)
            emit_progress("Speech Agent", "Adding slide timing, transitions, and presenter guidance", stage="generating_speech", progress=98)

            # Generate speech metadata
            speech_metadata = self._generate_speech_metadata(
                timed_script, presentation_plan, target_duration_minutes
            )

            # Combine all speech data
            complete_speech_data = {
                "metadata": speech_metadata,
                "full_script": timed_script,
                "presentation_plan_source": presentation_plan_path,
                "generation_timestamp": datetime.now().isoformat(),
                "target_duration_minutes": target_duration_minutes,
                "presentation_style": presentation_style,
                "audience_level": audience_level
            }

            # Save speech script
            output_path = os.path.join(output_dir, "speech_script.json")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(complete_speech_data, f, ensure_ascii=False, indent=2)

            # Also save as readable text format
            text_output_path = os.path.join(output_dir, "speech_script.txt")
            self._save_readable_script(complete_speech_data, text_output_path)

            self.logger.info(f"Speech script generated successfully: {output_path}")
            emit_progress("Speech Agent", "Speech script and readable notes are ready", stage="generating_speech", progress=99, level="success")
            return True, complete_speech_data, output_path

        except Exception as e:
            self.logger.error(f"Failed to generate speech script: {e}")
            emit_progress("Speech Agent", "Speech generation failed", stage="generating_speech", progress=99, level="error")
            return False, {"error": str(e)}, ""

    def _load_presentation_plan(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load presentation plan from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load presentation plan: {e}")
            return None

    def _load_original_content(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load original paper content from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load original content: {e}")
            return None

    def _generate_speech_content(
        self,
        presentation_plan: Dict[str, Any],
        original_content: Optional[Dict[str, Any]],
        target_duration: int,
        style: str,
        audience: str
    ) -> Dict[str, Any]:
        """Generate the main speech content using LLM"""

        if not self.llm_interface:
            raise Exception("LLM interface not available")

        # Prepare complete context for high-quality speech generation
        slides_content = self._extract_slides_for_speech(presentation_plan)
        original_context = self._extract_original_context(original_content) if original_content else ""

        # Create speech generation prompt
        system_prompt = self._create_speech_generation_system_prompt(style, audience, target_duration)
        user_prompt = self._create_speech_generation_user_prompt(
            slides_content, original_context, presentation_plan
        )

        # Generate speech using task-optimized parameters
        speech_result = self.llm_interface.call_llm(
            TaskType.SPEECH_GENERATION,
            system_prompt,
            user_prompt,
            json_mode=True
        )

        if not speech_result:
            raise Exception("Failed to generate speech content")

        # Validate the structure of the response
        if "speech_script" not in speech_result:
            self.logger.error(f"Invalid speech result structure: {list(speech_result.keys())}")
            raise Exception("LLM response missing 'speech_script' key")

        self.logger.info("Speech content generated successfully")
        return speech_result

    def _extract_slides_for_speech(self, presentation_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract complete slide content for high-quality speech generation"""
        slides_for_speech = []

        slides_plan = presentation_plan.get("slides_plan", [])
        for slide in slides_plan:
            slide_info = {
                "slide_number": slide.get("slide_number", 0),
                "title": slide.get("title", ""),
                "content": slide.get("content", []),
                "slide_type": slide.get("slide_type", "content"),
                "estimated_time": slide.get("estimated_time", "2-3 minutes")
            }
            slides_for_speech.append(slide_info)

        return slides_for_speech

    def _extract_original_context(self, original_content: Dict[str, Any]) -> str:
        """Extract relevant context from original paper"""
        context_parts = []

        # Get enhanced content sections
        enhanced_content = original_content.get("enhanced_content", {})

        # Add key narrative elements
        key_narratives = enhanced_content.get("key_narratives", {})
        for narrative_type, content in key_narratives.items():
            if content:
                context_parts.append(f"[{narrative_type.upper()}] {content}")

        # Add presentation sections
        presentation_sections = enhanced_content.get("presentation_sections", {})
        for section_type, content in presentation_sections.items():
            if content:
                context_parts.append(f"[{section_type.upper()}] {content}")

        return " ".join(context_parts)  # Use complete context for quality

    def _create_speech_generation_system_prompt(
        self, style: str, audience: str, duration: int
    ) -> str:
        """Create system prompt for speech generation"""

        style_guidelines = {
            "academic_conference": "Professional, authoritative, research-focused with clear technical explanations",
            "seminar": "Educational, interactive, encouraging questions and discussion",
            "pitch": "Persuasive, engaging, emphasizing practical value and impact",
            "workshop": "Practical, hands-on focused, with actionable insights",
            "keynote": "Inspirational, big-picture thinking, memorable key messages"
        }

        audience_guidelines = {
            "expert": "Use technical terminology, assume deep domain knowledge, focus on novel contributions",
            "general": "Explain technical concepts clearly, use analogies, emphasize practical implications",
            "student": "Educational approach, build concepts step-by-step, encourage learning",
            "industry": "Focus on practical applications, business value, implementation considerations"
        }

        style_guide = style_guidelines.get(style, style_guidelines["academic_conference"])
        audience_guide = audience_guidelines.get(audience, audience_guidelines["expert"])
        output_language = (
            "Simplified Chinese. All spoken script, transitions, speaker notes, timing notes, and guidance must be written in Chinese. "
            "Keep paper titles, author names, formulas, code identifiers, and established technical terms unchanged when appropriate."
            if self.language == "zh"
            else "English."
        )

        return f"""
You are an expert presentation coach and speech writer specializing in academic and technical presentations. Your task is to create a natural, engaging speech script that accompanies presentation slides.

**PRESENTATION CONTEXT:**
- Style: {style} - {style_guide}
- Audience: {audience} - {audience_guide}
- Target Duration: {duration} minutes
- Output Language: {output_language}

**SPEECH GENERATION PRINCIPLES:**

1. **Natural Flow**: Create smooth transitions between slides that feel conversational and engaging
2. **Timing Awareness**: Distribute content appropriately for the target duration
3. **Audience Engagement**: Include rhetorical questions, pauses, and emphasis points
4. **Technical Clarity**: Explain complex concepts in accessible ways while maintaining accuracy
5. **Presentation Techniques**: Use storytelling, examples, and structured delivery

**SPEECH STRUCTURE REQUIREMENTS:**

1. **Opening Hook**: Compelling introduction that captures attention
2. **Clear Navigation**: Help audience follow the presentation structure
3. **Slide Transitions**: Smooth bridges between topics
4. **Key Emphasis**: Highlight important points with verbal cues
5. **Interactive Elements**: Include pauses for questions or reflection
6. **Strong Conclusion**: Memorable closing that reinforces key messages

**OUTPUT FORMAT:**
Generate a complete speech script in JSON format with proper timing, speaker notes, and presentation guidance.
"""

    def _create_speech_generation_user_prompt(
        self,
        slides_content: List[Dict[str, Any]],
        original_context: str,
        presentation_plan: Dict[str, Any]
    ) -> str:
        """Create user prompt with slides and context"""

        # Get paper information
        paper_info = presentation_plan.get("paper_info", {})
        title = paper_info.get("title", "Research Presentation")
        authors = paper_info.get("authors", "Research Team")

        # Format slides content
        slides_text = ""
        for slide in slides_content:
            slides_text += f"\n**Slide {slide['slide_number']}: {slide['title']}**\n"
            slides_text += f"Type: {slide['slide_type']}\n"
            if slide['content']:
                slides_text += "Content:\n"
                for item in slide['content']:
                    slides_text += f"- {item}\n"
            slides_text += f"Estimated Time: {slide['estimated_time']}\n\n"

        return f"""
Please generate a complete speech script for the following presentation:

**PRESENTATION DETAILS:**
Title: {title}
Authors: {authors}

**SLIDES TO COVER:**
{slides_text}

**ORIGINAL PAPER CONTEXT:**
{original_context[:4000] if original_context else "No additional context provided."}

**REQUIREMENTS:**
1. Create natural, engaging speech content for each slide
2. Include smooth transitions between slides
3. Add speaker notes for timing, emphasis, and delivery
4. Include suggestions for audience interaction
5. Ensure content flows logically and maintains audience interest
6. Provide specific guidance for technical explanations
7. Include opening hook and strong conclusion

**OUTPUT JSON FORMAT:**
{{
  "speech_script": {{
    "opening": {{
      "content": "Opening speech content...",
      "duration_minutes": 2,
      "speaker_notes": ["Emphasis points", "Delivery guidance"]
    }},
    "slides": [
      {{
        "slide_number": 1,
        "slide_title": "...",
        "speech_content": "Natural speech for this slide...",
        "duration_minutes": 3,
        "speaker_notes": ["Technical emphasis", "Pause for questions"],
        "transition_to_next": "Smooth transition to next slide..."
      }}
    ],
    "conclusion": {{
      "content": "Concluding remarks...",
      "duration_minutes": 2,
      "speaker_notes": ["Final emphasis", "Thank audience"]
    }}
  }},
  "presentation_guidance": {{
    "key_messages": ["Main takeaway 1", "Main takeaway 2"],
    "technical_explanations": {{"concept": "How to explain this concept"}},
    "audience_interaction_points": ["When to pause for questions"],
    "timing_notes": ["Where to speed up or slow down"]
  }}
}}

Generate a complete, natural speech script that will create an engaging presentation experience.
"""

    def _add_timing_and_notes(
        self, speech_script: Dict[str, Any], target_duration: int
    ) -> Dict[str, Any]:
        """Add detailed timing and presentation notes to the speech script"""

        if not speech_script or "speech_script" not in speech_script:
            self.logger.error(f"Invalid speech_script structure: {list(speech_script.keys()) if speech_script else 'None'}")
            return speech_script

        script = speech_script["speech_script"]

        # Calculate and adjust timing with error handling
        total_estimated = 0

        # Count opening and conclusion with safe access
        opening = script.get("opening", {})
        conclusion = script.get("conclusion", {})

        try:
            opening_duration = opening.get("duration_minutes", 2)
            conclusion_duration = conclusion.get("duration_minutes", 2)

            total_estimated += opening_duration
            total_estimated += conclusion_duration

            # Count slides with safe access
            slides = script.get("slides", [])
            for i, slide in enumerate(slides):
                slide_duration = slide.get("duration_minutes", 2)
                if not isinstance(slide_duration, (int, float)):
                    self.logger.warning(f"Slide {i} has invalid duration_minutes: {slide_duration}, using default 2")
                    slide_duration = 2
                total_estimated += slide_duration

        except Exception as e:
            self.logger.error(f"Error calculating timing: {e}")
            self.logger.error(f"Opening structure: {opening}")
            self.logger.error(f"Conclusion structure: {conclusion}")
            self.logger.error(f"Slides structure: {slides[:1] if slides else 'Empty'}")
            raise

        # Adjust timing if needed
        if total_estimated != target_duration and total_estimated > 0:
            adjustment_factor = target_duration / total_estimated

            # Adjust each section with safe access
            if "opening" in script and "duration_minutes" in script["opening"]:
                script["opening"]["duration_minutes"] = round(
                    script["opening"]["duration_minutes"] * adjustment_factor, 1
                )

            if "conclusion" in script and "duration_minutes" in script["conclusion"]:
                script["conclusion"]["duration_minutes"] = round(
                    script["conclusion"]["duration_minutes"] * adjustment_factor, 1
                )

            for slide in slides:
                if "duration_minutes" in slide:
                    slide["duration_minutes"] = round(
                        slide["duration_minutes"] * adjustment_factor, 1
                    )

        # Add cumulative timing with safe access
        cumulative_time = 0

        if "opening" in script:
            opening_duration = script["opening"].get("duration_minutes", 2)
            cumulative_time += opening_duration
            script["opening"]["cumulative_time"] = cumulative_time

        for slide in slides:
            slide_duration = slide.get("duration_minutes", 2)
            cumulative_time += slide_duration
            slide["cumulative_time"] = cumulative_time

        if "conclusion" in script:
            conclusion_duration = script["conclusion"].get("duration_minutes", 2)
            cumulative_time += conclusion_duration
            script["conclusion"]["cumulative_time"] = cumulative_time

        return speech_script

    def _generate_speech_metadata(
        self, speech_script: Dict[str, Any], presentation_plan: Dict[str, Any], target_duration: int
    ) -> Dict[str, Any]:
        """Generate metadata about the speech script"""

        paper_info = presentation_plan.get("paper_info", {})
        script = speech_script.get("speech_script", {})

        # Count words for speaking rate estimation
        total_words = 0
        slides = script.get("slides", [])

        # Count opening words
        opening_content = script.get("opening", {}).get("content", "")
        total_words += len(opening_content.split())

        # Count slide words
        for slide in slides:
            speech_content = slide.get("speech_content", "")
            total_words += len(speech_content.split())

        # Count conclusion words
        conclusion_content = script.get("conclusion", {}).get("content", "")
        total_words += len(conclusion_content.split())

        # Calculate speaking rate (words per minute)
        speaking_rate = round(total_words / target_duration) if target_duration > 0 else 0

        return {
            "title": paper_info.get("title", "Unknown Title"),
            "authors": paper_info.get("authors", "Unknown Authors"),
            "total_slides": len(slides),
            "estimated_duration_minutes": target_duration,
            "total_words": total_words,
            "speaking_rate_wpm": speaking_rate,
            "sections": {
                "opening_duration": script.get("opening", {}).get("duration_minutes", 0),
                "slides_duration": sum(slide.get("duration_minutes", 0) for slide in slides),
                "conclusion_duration": script.get("conclusion", {}).get("duration_minutes", 0)
            }
        }

    def _save_readable_script(self, speech_data: Dict[str, Any], output_path: str):
        """Save speech script in human-readable text format"""

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                metadata = speech_data.get("metadata", {})
                script = speech_data.get("full_script", {}).get("speech_script", {})

                # Write header
                f.write("="*80 + "\n")
                f.write(f"PRESENTATION SPEECH SCRIPT\n")
                f.write("="*80 + "\n\n")

                f.write(f"Title: {metadata.get('title', 'Unknown')}\n")
                f.write(f"Authors: {metadata.get('authors', 'Unknown')}\n")
                f.write(f"Duration: {metadata.get('estimated_duration_minutes', 0)} minutes\n")
                f.write(f"Total Words: {metadata.get('total_words', 0)}\n")
                f.write(f"Speaking Rate: {metadata.get('speaking_rate_wpm', 0)} WPM\n\n")

                # Write opening
                if "opening" in script:
                    opening = script["opening"]
                    f.write("-"*60 + "\n")
                    f.write(f"OPENING ({opening.get('duration_minutes', 0)} minutes)\n")
                    f.write("-"*60 + "\n")
                    f.write(f"{opening.get('content', '')}\n\n")

                    if opening.get('speaker_notes'):
                        f.write("Speaker Notes:\n")
                        for note in opening['speaker_notes']:
                            f.write(f"• {note}\n")
                        f.write("\n")

                # Write slides
                slides = script.get("slides", [])
                for slide in slides:
                    f.write("-"*60 + "\n")
                    f.write(f"SLIDE {slide.get('slide_number', 0)}: {slide.get('slide_title', '')} ")
                    f.write(f"({slide.get('duration_minutes', 0)} min)\n")
                    f.write("-"*60 + "\n")
                    f.write(f"{slide.get('speech_content', '')}\n\n")

                    if slide.get('speaker_notes'):
                        f.write("Speaker Notes:\n")
                        for note in slide['speaker_notes']:
                            f.write(f"• {note}\n")
                        f.write("\n")

                    if slide.get('transition_to_next'):
                        f.write(f"Transition: {slide['transition_to_next']}\n\n")

                # Write conclusion
                if "conclusion" in script:
                    conclusion = script["conclusion"]
                    f.write("-"*60 + "\n")
                    f.write(f"CONCLUSION ({conclusion.get('duration_minutes', 0)} minutes)\n")
                    f.write("-"*60 + "\n")
                    f.write(f"{conclusion.get('content', '')}\n\n")

                    if conclusion.get('speaker_notes'):
                        f.write("Speaker Notes:\n")
                        for note in conclusion['speaker_notes']:
                            f.write(f"• {note}\n")
                        f.write("\n")

                # Write presentation guidance
                guidance = speech_data.get("full_script", {}).get("presentation_guidance", {})
                if guidance:
                    f.write("="*80 + "\n")
                    f.write("PRESENTATION GUIDANCE\n")
                    f.write("="*80 + "\n\n")

                    if guidance.get('key_messages'):
                        f.write("Key Messages:\n")
                        for msg in guidance['key_messages']:
                            f.write(f"• {msg}\n")
                        f.write("\n")

                    if guidance.get('audience_interaction_points'):
                        f.write("Audience Interaction Points:\n")
                        for point in guidance['audience_interaction_points']:
                            f.write(f"• {point}\n")
                        f.write("\n")

                    if guidance.get('timing_notes'):
                        f.write("Timing Notes:\n")
                        for note in guidance['timing_notes']:
                            f.write(f"• {note}\n")
                        f.write("\n")

        except Exception as e:
            self.logger.error(f"Failed to save readable script: {e}")

# Convenience function for direct use
def generate_speech_for_presentation(
    presentation_plan_path: str,
    output_dir: str,
    original_content_path: Optional[str] = None,
    target_duration_minutes: int = 15,
    presentation_style: str = "academic_conference",
    audience_level: str = "expert",
    model_name: str = "gpt-4o",
    language: str = "en",
) -> Tuple[bool, Dict[str, Any], str]:
    """
    Generate speech script for a presentation

    Args:
        presentation_plan_path: Path to presentation plan JSON
        output_dir: Output directory for speech script
        original_content_path: Optional path to original paper content
        target_duration_minutes: Target presentation duration
        presentation_style: Style of presentation
        audience_level: Target audience level
        model_name: LLM model to use

    Returns:
        Tuple of (success, speech_data, output_path)
    """
    generator = SpeechAgent(model_name=model_name, language=language)
    return generator.generate_speech_script(
        presentation_plan_path=presentation_plan_path,
        original_content_path=original_content_path,
        output_dir=output_dir,
        target_duration_minutes=target_duration_minutes,
        presentation_style=presentation_style,
        audience_level=audience_level
    )
