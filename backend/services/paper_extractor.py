"""
PDF Parser Module: Responsible for parsing PDF files and extracting basic information
This module now calls lightweight extractor functionality for efficient content extraction
and uses LLM for presentation-oriented content enhancement
"""
import os
import json
import logging
import re
from typing import Dict, Any, Optional
from backend.services.layout_extractor import extract_lightweight_content

# Import LLM-related packages
try:
    from langchain_openai import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Import enhancement prompts
from backend.prompts import EXTRACT_TABLES_AND_EQUATIONS_PROMPT, SUMMARIZE_TEXT_FOR_PRESENTATION_PROMPT
from backend.progress import emit_progress

def enhance_content_with_llm(lightweight_content: Dict[str, Any], model_name: str = "gpt-4o", api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Enhance content using LLM, reorganize and structure content from presentation perspective
    Now divided into two steps: 1) Extract tables and formulas 2) Summarize text content

    Args:
        lightweight_content: Basic content from lightweight extraction
        model_name: Language model name to use
        api_key: OpenAI API key

    Returns:
        Dict: Enhanced content
    """
    logger = logging.getLogger(__name__)
    emit_progress("Content Enhancement Agent", "Initializing semantic enhancement for extracted paper content", stage="enhancing", progress=24)

    if not OPENAI_AVAILABLE:
        logger.warning("Cannot import OpenAI packages, skipping LLM enhancement")
        emit_progress("Content Enhancement Agent", "Enhancement dependencies are unavailable; using raw extraction", stage="enhancing", progress=35, level="warning")
        return lightweight_content

    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OpenAI API key not provided, skipping LLM enhancement")
            emit_progress("Content Enhancement Agent", "No model credential is available; using raw extraction", stage="enhancing", progress=35, level="warning")
            return lightweight_content

    try:
        # Initialize LLM
        llm = ChatOpenAI(
            model_name=model_name,
            temperature=0.2,
            openai_api_key=api_key,
            openai_api_base=os.environ.get("OPENAI_API_BASE")
        )

        # Get full text
        full_text = lightweight_content.get("full_text", "")
        if not full_text:
            logger.warning("No full_text found, skipping LLM enhancement")
            return lightweight_content

        logger.info("Starting LLM content enhancement...")

        # Step 1: Extract tables and formulas
        logger.info("Step 1: Extracting tables and formulas...")
        tables_equations_result = _extract_tables_and_equations(llm, full_text)

        # Step 2: Summarize text content
        logger.info("Step 2: Summarizing presentation content...")
        presentation_summary = _summarize_for_presentation(llm, full_text)

        # Merge results
        enhanced_content = lightweight_content.copy()
        enhanced_content["enhanced_content"] = presentation_summary

        # If tables and formulas were successfully extracted, add to results
        if tables_equations_result:
            if "tables" in tables_equations_result:
                enhanced_content["enhanced_content"]["tables"] = tables_equations_result["tables"]
            if "equations" in tables_equations_result:
                enhanced_content["enhanced_content"]["equations"] = tables_equations_result["equations"]

        logger.info("LLM content enhancement completed")
        return enhanced_content

    except Exception as e:
        logger.error(f"Error during LLM enhancement: {str(e)}")
        emit_progress("Content Enhancement Agent", "Semantic enhancement failed; using raw extraction", stage="enhancing", progress=35, level="warning")
        return lightweight_content


def _extract_tables_and_equations(llm, full_text: str) -> Optional[Dict]:
    """
    Step 1: Specifically extract tables and formulas
    """
    logger = logging.getLogger(__name__)
    emit_progress("Content Enhancement Agent", "Identifying important tables, equations, and quantitative evidence", stage="enhancing", progress=26)

    try:
        # Import special character handling module
        from backend.services.latex import postprocess_content_from_llm, preprocess_content_for_llm, validate_special_chars_in_output

        # Preprocess text to protect special characters
        protected_text = preprocess_content_for_llm(full_text)
        logger.debug("Special characters have been preprocessed and protected")

        prompt = ChatPromptTemplate.from_template(EXTRACT_TABLES_AND_EQUATIONS_PROMPT)
        chain = prompt | llm
        response = chain.invoke({"full_text": protected_text})

        response_text = response.content if hasattr(response, 'content') else str(response)

        # Restore special characters
        response_text = postprocess_content_from_llm(response_text)

        # Extract JSON part
        json_match = re.search(r'```(?:json)?(.*?)```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            json_str = response_text.strip()

        # Parse JSON
        result = json.loads(json_str)

        # Validate if special characters are lost
        if result.get('tables'):
            for table in result['tables']:
                markdown_content = table.get('markdown_content', '')
                lost_chars = validate_special_chars_in_output(full_text, markdown_content)
                if lost_chars:
                    logger.warning(f"Table {table.get('id', 'unknown')} lost special characters: {lost_chars}")

        logger.info(f"Successfully extracted {len(result.get('tables', []))} tables and {len(result.get('equations', []))} equations")
        emit_progress(
            "Content Enhancement Agent",
            f"Identified {len(result.get('tables', []))} tables and {len(result.get('equations', []))} equations",
            stage="enhancing",
            progress=29,
        )
        return result

    except Exception as e:
        logger.warning(f"Error extracting tables and formulas: {str(e)}")
        emit_progress("Content Enhancement Agent", "Table and equation enhancement was skipped after a recoverable error", stage="enhancing", progress=29, level="warning")
        return None


def _summarize_for_presentation(llm, full_text: str) -> Dict:
    """
    Step 2: Summarize presentation content
    """
    logger = logging.getLogger(__name__)
    emit_progress("Content Enhancement Agent", "Building a presentation-oriented summary of the paper", stage="enhancing", progress=31)

    try:
        prompt = ChatPromptTemplate.from_template(SUMMARIZE_TEXT_FOR_PRESENTATION_PROMPT)
        chain = prompt | llm
        response = chain.invoke({"full_text": full_text})

        response_text = response.content if hasattr(response, 'content') else str(response)

        # Extract JSON part
        json_match = re.search(r'```(?:json)?(.*?)```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            json_str = response_text.strip()

        # Parse JSON
        result = json.loads(json_str)
        logger.info("Presentation content summarization completed")
        emit_progress("Content Enhancement Agent", "Presentation narrative and evidence summary completed", stage="enhancing", progress=34)
        return result

    except Exception as e:
        logger.error(f"Error summarizing presentation content: {str(e)}")
        emit_progress("Content Enhancement Agent", "Presentation summary failed; continuing with extracted source text", stage="enhancing", progress=34, level="warning")
        # Return basic structure to avoid complete failure
        return {
            "presentation_sections": {
                "background_context": "Content summarization failed",
                "problem_motivation": "Content summarization failed",
                "solution_overview": "Content summarization failed",
                "technical_approach": "Content summarization failed",
                "evidence_proof": "Content summarization failed",
                "impact_significance": "Content summarization failed"
            },
            "key_narratives": {
                "field_importance": [],
                "problem_scenarios": [],
                "solution_benefits": [],
                "breakthrough_results": []
            }
        }

def extract_pdf_content(
    pdf_path,
    output_dir="output",
    cleanup_temp=False,
    enable_llm_enhancement=True,
    model_name="gpt-4o",
    api_key=None,
    session_id=None,
    images_dir=None,
):
    """
    Extract PDF content (including text, images, metadata etc.) with optional LLM enhancement

    Args:
        pdf_path: PDF file path
        output_dir: Output directory
        cleanup_temp: Whether to clean up temporary files
        enable_llm_enhancement: Whether to enable LLM enhancement processing
        model_name: Language model name to use
        api_key: OpenAI API key

    Returns:
        tuple: (extracted content, content save file path, images directory path)
    """
    logging.info(f"Starting PDF content extraction: {pdf_path}")
    emit_progress("Extraction Service", "Opening the uploaded PDF", stage="extracting", progress=10)

    # Call lightweight extractor module functionality
    lightweight_content, lightweight_content_path, img_dir = extract_lightweight_content(
        pdf_path,
        output_dir,
        cleanup_temp,
        session_id=session_id,
        images_dir=images_dir,
    )

    if not lightweight_content:
        logging.error("PDF content extraction failed")
        return None, None, None

    # If LLM enhancement is enabled, perform enhancement processing
    if enable_llm_enhancement:
        logging.info("Starting LLM enhancement processing...")
        emit_progress("Content Enhancement Agent", "Raw extraction complete; starting semantic enhancement", stage="enhancing", progress=24)
        enhanced_content = enhance_content_with_llm(lightweight_content, model_name, api_key)

        # Save enhanced content
        enhanced_content_path = lightweight_content_path.replace('.json', '_enhanced.json')
        try:
            with open(enhanced_content_path, 'w', encoding='utf-8') as f:
                json.dump(enhanced_content, f, ensure_ascii=False, indent=2)
            logging.info(f"Enhanced content saved to: {enhanced_content_path}")
            emit_progress("Content Enhancement Agent", "Enhanced paper content saved for planning", stage="enhancing", progress=35, level="success")
            return enhanced_content, enhanced_content_path, img_dir
        except Exception as e:
            logging.error(f"Error saving enhanced content: {str(e)}")
            # If save fails, return original content
            return lightweight_content, lightweight_content_path, img_dir
    else:
        logging.info(f"PDF content extracted and saved to: {lightweight_content_path}")
        emit_progress("Extraction Service", "LLM enhancement is disabled; using the raw extraction", stage="extracting", progress=35)
        return lightweight_content, lightweight_content_path, img_dir
