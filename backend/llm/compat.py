#!/usr/bin/env python3
"""
Fix OpenAI client initialization proxies parameter issue
"""
import os
import sys
import logging
import importlib.util
import inspect
from types import FunctionType, MethodType

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def patch_openai_client():
    """
    Patch OpenAI client to remove proxies parameter
    """
    try:
        # Try to import OpenAI client
        import openai
        from openai import OpenAI

        # Get original __init__ method
        original_init = OpenAI.__init__

        # Define new __init__ method
        def patched_init(self, *args, **kwargs):
            # Remove proxies parameter if it exists
            if 'proxies' in kwargs:
                logging.info("Removed 'proxies' parameter")
                del kwargs['proxies']

            # Call original __init__ method
            return original_init(self, *args, **kwargs)

        # Replace __init__ method
        OpenAI.__init__ = patched_init
        logging.info("Successfully patched OpenAI client")

        return True
    except Exception as e:
        logging.error(f"Failed to patch OpenAI client: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def patch_langchain_openai():
    """
    Patch LangChain OpenAI integration
    """
    try:
        # Try to import LangChain OpenAI
        import langchain_openai
        from langchain_openai.chat_models import ChatOpenAI

        # Get original __init__ method
        original_init = ChatOpenAI.__init__

        # Define new __init__ method
        def patched_init(self, *args, **kwargs):
            # Remove proxies parameter if it exists
            if 'proxies' in kwargs:
                logging.info("Removed 'proxies' parameter from ChatOpenAI")
                del kwargs['proxies']

            # Call original __init__ method
            return original_init(self, *args, **kwargs)

        # Replace __init__ method
        ChatOpenAI.__init__ = patched_init
        logging.info("Successfully patched LangChain ChatOpenAI")

        return True
    except Exception as e:
        logging.error(f"Failed to patch LangChain ChatOpenAI: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# Apply patches when run as script
if __name__ == "__main__":
    success1 = patch_openai_client()
    success2 = patch_langchain_openai()

    if success1 and success2:
        logging.info("All patches applied successfully")
    else:
        logging.warning("Some patches failed to apply")

    sys.exit(0 if (success1 or success2) else 1)