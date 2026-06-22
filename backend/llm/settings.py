"""
LLM Parameter Configuration System

This module defines optimal LLM parameters for different tasks in the paper-to-beamer system.
Different tasks require different parameter settings to achieve optimal performance.
"""

from typing import Dict, Any, Optional
from enum import Enum

class TaskType(Enum):
    """Define different task types that require specific LLM parameters"""

    # Content extraction and analysis (require high accuracy)
    CONTENT_EXTRACTION = "content_extraction"
    TABLE_EXTRACTION = "table_extraction"
    EQUATION_EXTRACTION = "equation_extraction"

    # Planning and structuring (require logical consistency)
    PRESENTATION_PLANNING = "presentation_planning"
    SLIDE_ORGANIZATION = "slide_organization"

    # Generation tasks (require creativity but controlled)
    TEX_GENERATION = "tex_generation"
    SPEECH_GENERATION = "speech_generation"

    # Verification and checking (require high precision)
    VERIFICATION = "verification"
    FACT_CHECKING = "fact_checking"
    HALLUCINATION_DETECTION = "hallucination_detection"

    # Repair and fixing (require surgical precision)
    CONTENT_REPAIR = "content_repair"
    TEX_ERROR_FIXING = "tex_error_fixing"

    # Interactive tasks (require balanced responsiveness)
    INTERACTIVE_EDITING = "interactive_editing"
    USER_ASSISTANCE = "user_assistance"

class LLMParameterConfig:
    """
    LLM Parameter Configuration System

    This class provides optimized parameter settings for different task types.
    Each task type has carefully tuned parameters based on the specific requirements.
    """

    # Base parameter configurations for different task categories
    _TASK_CONFIGS = {
        # High-precision extraction tasks
        TaskType.CONTENT_EXTRACTION: {
            "temperature": 0.05,  # Very low for maximum accuracy
            "top_p": 0.85,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.0,
            "max_tokens": 4000,
            "description": "Optimized for accurate content extraction with minimal hallucination"
        },

        TaskType.TABLE_EXTRACTION: {
            "temperature": 0.02,  # Extremely low for data accuracy
            "top_p": 0.8,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "max_tokens": 3000,
            "description": "Maximum precision for numerical data and table structure"
        },

        TaskType.EQUATION_EXTRACTION: {
            "temperature": 0.02,  # Extremely low for LaTeX accuracy
            "top_p": 0.8,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "max_tokens": 2500,
            "description": "Optimized for LaTeX formula extraction accuracy"
        },

        # Planning and structuring tasks
        TaskType.PRESENTATION_PLANNING: {
            "temperature": 0.15,  # Low-medium for logical structure
            "top_p": 0.9,
            "frequency_penalty": 0.2,
            "presence_penalty": 0.1,
            "max_tokens": 12000,  # Increased to support rich presentations (15-25+ slides)
            "description": "Balanced creativity and structure for presentation planning with flexible page count"
        },

        TaskType.SLIDE_ORGANIZATION: {
            "temperature": 0.1,  # Low for consistent organization
            "top_p": 0.85,
            "frequency_penalty": 0.15,
            "presence_penalty": 0.05,
            "max_tokens": 8000,  # Increased for comprehensive slide organization
            "description": "Structured approach to slide organization with flexible content length"
        },

        # Generation tasks
        TaskType.TEX_GENERATION: {
            "temperature": 0.2,  # Medium-low for controlled creativity
            "top_p": 0.9,
            "frequency_penalty": 0.3,
            "presence_penalty": 0.1,
            "max_tokens": 15000,  # Significantly increased for rich presentations
            "description": "Balanced for LaTeX generation with proper formatting and support for extensive content"
        },

        TaskType.SPEECH_GENERATION: {
            "temperature": 0.25,  # Medium for natural speech
            "top_p": 0.92,
            "frequency_penalty": 0.4,
            "presence_penalty": 0.2,
            "max_tokens": 16000,  # Large token limit for comprehensive speech scripts
            "description": "Natural and engaging speech generation with comprehensive content"
        },

        # Verification tasks
        TaskType.VERIFICATION: {
            "temperature": 0.05,  # Very low for consistent evaluation
            "top_p": 0.8,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "max_tokens": 3000,
            "description": "Maximum accuracy for verification tasks"
        },

        TaskType.FACT_CHECKING: {
            "temperature": 0.03,  # Extremely low for fact accuracy
            "top_p": 0.75,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "max_tokens": 2500,
            "description": "Highest precision for fact verification"
        },

        TaskType.HALLUCINATION_DETECTION: {
            "temperature": 0.02,  # Minimum temperature for detection
            "top_p": 0.7,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "max_tokens": 2000,
            "description": "Ultra-conservative parameters for hallucination detection"
        },

        # Repair tasks
        TaskType.CONTENT_REPAIR: {
            "temperature": 0.08,  # Very low for surgical precision
            "top_p": 0.85,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.0,
            "max_tokens": 3500,
            "description": "Surgical precision for content repair"
        },

        TaskType.TEX_ERROR_FIXING: {
            "temperature": 0.05,  # Very low for syntax accuracy
            "top_p": 0.8,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "max_tokens": 3000,
            "description": "Maximum accuracy for LaTeX error fixing"
        },

        # Interactive tasks
        TaskType.INTERACTIVE_EDITING: {
            "temperature": 0.12,  # Low-medium for responsive editing
            "top_p": 0.88,
            "frequency_penalty": 0.2,
            "presence_penalty": 0.1,
            "max_tokens": 4000,
            "description": "Balanced responsiveness for interactive editing"
        },

        TaskType.USER_ASSISTANCE: {
            "temperature": 0.18,  # Medium-low for helpful responses
            "top_p": 0.9,
            "frequency_penalty": 0.25,
            "presence_penalty": 0.15,
            "max_tokens": 3500,
            "description": "Helpful and clear user assistance"
        }
    }

    @classmethod
    def get_params(cls, task_type: TaskType, custom_overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get optimized parameters for a specific task type

        Args:
            task_type: The type of task requiring LLM parameters
            custom_overrides: Optional custom parameter overrides

        Returns:
            Dictionary of LLM parameters optimized for the task
        """
        if task_type not in cls._TASK_CONFIGS:
            raise ValueError(f"Unknown task type: {task_type}")

        # Get base configuration
        config = cls._TASK_CONFIGS[task_type].copy()

        # Apply custom overrides if provided
        if custom_overrides:
            config.update(custom_overrides)

        return config

    @classmethod
    def get_temperature(cls, task_type: TaskType) -> float:
        """Get just the temperature parameter for a task type"""
        return cls._TASK_CONFIGS[task_type]["temperature"]

    @classmethod
    def get_description(cls, task_type: TaskType) -> str:
        """Get the description of why these parameters are used for this task"""
        return cls._TASK_CONFIGS[task_type]["description"]

    @classmethod
    def list_all_configs(cls) -> Dict[str, Dict[str, Any]]:
        """Get all configurations for inspection"""
        return {task.value: config for task, config in cls._TASK_CONFIGS.items()}

    @classmethod
    def compare_configs(cls, task1: TaskType, task2: TaskType) -> Dict[str, Any]:
        """Compare configurations between two task types"""
        config1 = cls._TASK_CONFIGS[task1]
        config2 = cls._TASK_CONFIGS[task2]

        comparison = {
            "task1": task1.value,
            "task2": task2.value,
            "differences": {}
        }

        for key in config1:
            if key in config2 and config1[key] != config2[key]:
                comparison["differences"][key] = {
                    "task1_value": config1[key],
                    "task2_value": config2[key]
                }

        return comparison

# Convenience functions for common use cases
def get_extraction_params() -> Dict[str, Any]:
    """Get parameters optimized for content extraction tasks"""
    return LLMParameterConfig.get_params(TaskType.CONTENT_EXTRACTION)

def get_planning_params() -> Dict[str, Any]:
    """Get parameters optimized for presentation planning"""
    return LLMParameterConfig.get_params(TaskType.PRESENTATION_PLANNING)

def get_verification_params() -> Dict[str, Any]:
    """Get parameters optimized for verification tasks"""
    return LLMParameterConfig.get_params(TaskType.VERIFICATION)

def get_generation_params() -> Dict[str, Any]:
    """Get parameters optimized for TEX generation"""
    return LLMParameterConfig.get_params(TaskType.TEX_GENERATION)

def get_repair_params() -> Dict[str, Any]:
    """Get parameters optimized for content repair"""
    return LLMParameterConfig.get_params(TaskType.CONTENT_REPAIR)

# Example usage and testing
if __name__ == "__main__":
    print("🔧 LLM Parameter Configuration System")
    print("=" * 50)

    # Show all configurations
    for task_type in TaskType:
        config = LLMParameterConfig.get_params(task_type)
        print(f"\n📋 {task_type.value.upper()}:")
        print(f"   Temperature: {config['temperature']}")
        print(f"   Description: {config['description']}")

    # Compare verification vs generation
    print("\n🔍 COMPARISON: Verification vs Generation")
    comparison = LLMParameterConfig.compare_configs(
        TaskType.VERIFICATION,
        TaskType.TEX_GENERATION
    )
    for key, values in comparison["differences"].items():
        print(f"   {key}: {values['task1_value']} vs {values['task2_value']}")
