"""
Unified LLM Interface Module

This module provides a unified interface for all LLM calls in the paper-to-beamer system,
with task-specific parameter optimization and consistent error handling.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage, BaseMessage
from dotenv import load_dotenv

# Import our parameter configuration system
from backend.llm.settings import LLMParameterConfig, TaskType

# Load environment variables
if os.path.exists(".env"):
    load_dotenv(".env")
elif os.path.exists("env.local"):
    load_dotenv("env.local")

logger = logging.getLogger(__name__)

class LLMInterface:
    """
    Unified LLM Interface with task-specific optimization

    This class provides a consistent interface for all LLM interactions
    while applying optimal parameters for different task types.
    """

    def __init__(self, model_name: str = "gpt-4o", api_key: Optional[str] = None):
        """
        Initialize the LLM interface

        Args:
            model_name: The model to use (default: gpt-4o)
            api_key: OpenAI API key (optional, will use env var if not provided)
        """
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.base_url = os.environ.get("OPENAI_API_BASE")

        if not self.api_key:
            logger.warning("OpenAI API key not provided. LLM functionality will be limited.")
            self.llm = None
        else:
            # Initialize with conservative default parameters
            self.llm = ChatOpenAI(
                model_name=self.model_name,
                temperature=0.1,
                openai_api_key=self.api_key,
                openai_api_base=self.base_url
            )

        logger.info(f"LLM Interface initialized with model: {self.model_name}")

    def call_llm(
        self,
        task_type: TaskType,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = False,
        custom_params: Optional[Dict[str, Any]] = None,
        messages: Optional[List[BaseMessage]] = None
    ) -> Optional[Union[Dict[str, Any], str]]:
        """
        Make an LLM call with task-specific optimized parameters

        Args:
            task_type: The type of task (determines parameter optimization)
            system_prompt: System message content
            user_prompt: User message content (ignored if messages provided)
            json_mode: Whether to use JSON mode for structured output
            custom_params: Optional custom parameter overrides
            messages: Optional pre-built message list (overrides prompts)

        Returns:
            LLM response as dict (if json_mode) or string, None if failed
        """
        if not self.llm:
            logger.error("LLM not initialized. Cannot make API call.")
            return None

        try:
            # Get optimized parameters for this task type
            params = LLMParameterConfig.get_params(task_type, custom_params)

            # Log parameter selection for debugging
            logger.debug(f"Using {task_type.value} parameters: temperature={params['temperature']}")

            # Prepare messages
            if messages is None:
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ]

            # Configure response format
            response_format = {"type": "json_object"} if json_mode else {"type": "text"}

            # Create a new LLM instance with task-specific parameters
            task_llm = ChatOpenAI(
                model_name=self.model_name,
                temperature=params["temperature"],
                top_p=params.get("top_p", 1.0),
                frequency_penalty=params.get("frequency_penalty", 0.0),
                presence_penalty=params.get("presence_penalty", 0.0),
                max_tokens=params.get("max_tokens", 4000),
                openai_api_key=self.api_key,
                openai_api_base=self.base_url
            )

            # Make the API call
            response = task_llm.invoke(messages, response_format=response_format)
            content = response.content

            # Parse JSON if requested
            if json_mode:
                try:
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response for {task_type.value}: {e}")
                    logger.debug(f"Raw response: {content[:500]}...")
                    return None

            return content

        except Exception as e:
            logger.error(f"LLM call failed for {task_type.value}: {e}")
            return None

    def call_for_extraction(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = True
    ) -> Optional[Union[Dict[str, Any], str]]:
        """Convenience method for content extraction tasks"""
        return self.call_llm(
            TaskType.CONTENT_EXTRACTION,
            system_prompt,
            user_prompt,
            json_mode
        )

    def call_for_planning(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = True
    ) -> Optional[Union[Dict[str, Any], str]]:
        """Convenience method for presentation planning tasks"""
        return self.call_llm(
            TaskType.PRESENTATION_PLANNING,
            system_prompt,
            user_prompt,
            json_mode
        )

    def call_for_verification(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = True
    ) -> Optional[Union[Dict[str, Any], str]]:
        """Convenience method for verification tasks"""
        return self.call_llm(
            TaskType.VERIFICATION,
            system_prompt,
            user_prompt,
            json_mode
        )

    def call_for_generation(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = False
    ) -> Optional[Union[Dict[str, Any], str]]:
        """Convenience method for TEX generation tasks"""
        return self.call_llm(
            TaskType.TEX_GENERATION,
            system_prompt,
            user_prompt,
            json_mode
        )

    def call_for_repair(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = True
    ) -> Optional[Union[Dict[str, Any], str]]:
        """Convenience method for content repair tasks"""
        return self.call_llm(
            TaskType.CONTENT_REPAIR,
            system_prompt,
            user_prompt,
            json_mode
        )

    def call_for_fact_checking(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = True
    ) -> Optional[Union[Dict[str, Any], str]]:
        """Convenience method for fact checking with ultra-precise parameters"""
        return self.call_llm(
            TaskType.FACT_CHECKING,
            system_prompt,
            user_prompt,
            json_mode
        )

    def call_for_hallucination_detection(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = True
    ) -> Optional[Union[Dict[str, Any], str]]:
        """Convenience method for hallucination detection with minimum temperature"""
        return self.call_llm(
            TaskType.HALLUCINATION_DETECTION,
            system_prompt,
            user_prompt,
            json_mode
        )

    def get_task_info(self, task_type: TaskType) -> Dict[str, Any]:
        """Get information about parameters used for a specific task type"""
        return {
            "task_type": task_type.value,
            "parameters": LLMParameterConfig.get_params(task_type),
            "description": LLMParameterConfig.get_description(task_type)
        }

    def compare_task_params(self, task1: TaskType, task2: TaskType) -> Dict[str, Any]:
        """Compare parameters between two task types"""
        return LLMParameterConfig.compare_configs(task1, task2)

# Global LLM interface instance for convenience
_global_llm_interface = None

def get_llm_interface(model_name: str = "gpt-4o", api_key: Optional[str] = None) -> LLMInterface:
    """Get or create a global LLM interface instance"""
    global _global_llm_interface

    if _global_llm_interface is None:
        _global_llm_interface = LLMInterface(model_name, api_key)

    return _global_llm_interface

# Convenience functions for direct use
def call_llm_for_task(
    task_type: TaskType,
    system_prompt: str,
    user_prompt: str,
    json_mode: bool = False,
    model_name: str = "gpt-4o"
) -> Optional[Union[Dict[str, Any], str]]:
    """
    Direct function for making task-optimized LLM calls

    This is a convenience function that creates an interface if needed
    and makes the call with appropriate parameters.
    """
    interface = get_llm_interface(model_name)
    return interface.call_llm(task_type, system_prompt, user_prompt, json_mode)

# Example usage and testing
if __name__ == "__main__":
    print("🤖 LLM Interface Testing")
    print("=" * 50)

    # Test parameter retrieval
    interface = LLMInterface()

    print("\\n📊 Task Parameter Comparison:")
    for task in [TaskType.VERIFICATION, TaskType.TEX_GENERATION, TaskType.CONTENT_EXTRACTION]:
        info = interface.get_task_info(task)
        print(f"\\n{task.value.upper()}:")
        print(f"  Temperature: {info['parameters']['temperature']}")
        print(f"  Purpose: {info['description']}")

    print("\\n🔍 Verification vs Generation Comparison:")
    comparison = interface.compare_task_params(TaskType.VERIFICATION, TaskType.TEX_GENERATION)
    for param, values in comparison["differences"].items():
        print(f"  {param}: {values['task1_value']} vs {values['task2_value']}")
