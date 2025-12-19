"""
API Key Rotation Manager for Gemini API

This module manages multiple API keys and automatically rotates to the next key
when a rate limit error is encountered. After using the last key, it cycles back
to the first one.
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv
from google.api_core.exceptions import ResourceExhausted
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIKeyRotationManager:
    """
    Manages multiple API keys and rotates them when rate limits are hit.
    
    Usage:
        manager = APIKeyRotationManager()
        response = manager.call_llm_with_retry(system_prompt, user_prompt)
    """
    
    def __init__(self):
        """Initialize the key manager with API keys from environment."""
        self._load_api_keys()
        self.current_key_index = 0
        self.model_name = os.getenv("LLM_MODEL", "gemini-2.0-flash")
        self.max_retries = len(self.api_keys)  # Try each key once
        
    def _load_api_keys(self):
        """Load API keys from environment variables."""
        # Look for GOOGLE_API_KEY_1, GOOGLE_API_KEY_2, etc.
        # Also include the main GOOGLE_API_KEY if it exists
        self.api_keys = []
        
        # Add main key first if exists
        main_key = os.getenv("GOOGLE_API_KEY")
        if main_key:
            self.api_keys.append(main_key)
        
        # Add numbered keys (GOOGLE_API_KEY_1, GOOGLE_API_KEY_2, ...)
        i = 1
        while True:
            key = os.getenv(f"GOOGLE_API_KEY_{i}")
            if key:
                # Avoid duplicates
                if key not in self.api_keys:
                    self.api_keys.append(key)
                i += 1
            else:
                break
        
        if not self.api_keys:
            raise ValueError("No API keys found. Set GOOGLE_API_KEY or GOOGLE_API_KEY_1, GOOGLE_API_KEY_2, etc.")
        
        logger.info(f"Loaded {len(self.api_keys)} API key(s)")
    
    def get_current_key(self) -> str:
        """Get the current API key."""
        return self.api_keys[self.current_key_index]
    
    def rotate_to_next_key(self) -> str:
        """Rotate to the next API key, cycling back to the first if necessary."""
        old_index = self.current_key_index
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        new_key = self.api_keys[self.current_key_index]
        logger.info(f"Rotated from key {old_index + 1} to key {self.current_key_index + 1}/{len(self.api_keys)}")
        return new_key
    
    def get_key_info(self) -> dict:
        """Get information about current key state."""
        return {
            "current_key": self.current_key_index + 1,
            "total_keys": len(self.api_keys),
            "model": self.model_name
        }
    
    def reload_keys(self):
        """Reload API keys from environment (useful if keys are added at runtime)."""
        old_count = len(self.api_keys)
        self._load_api_keys()
        new_count = len(self.api_keys)
        if new_count != old_count:
            logger.info(f"Reloaded keys: {old_count} -> {new_count}")
        self.max_retries = len(self.api_keys)
    
    def _create_llm(self, api_key: str) -> ChatGoogleGenerativeAI:
        """Create a new LLM instance with the given API key."""
        # Set the API key in environment for langchain
        os.environ["GOOGLE_API_KEY"] = api_key
        return ChatGoogleGenerativeAI(
            model=self.model_name,
            temperature=0.2,
            google_api_key=api_key
        )
    
    def call_llm_with_retry(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> str:
        """
        Call the LLM with automatic key rotation on rate limit errors.
        
        Args:
            system_prompt: The system prompt for the LLM
            user_prompt: The user's question/prompt
            
        Returns:
            The LLM's response text
            
        Raises:
            Exception: If all API keys are rate limited
        """
        last_error = None
        attempts = 0
        
        while attempts < self.max_retries:
            current_key = self.get_current_key()
            
            try:
                logger.info(f"Attempting with API key {self.current_key_index + 1}/{len(self.api_keys)}")
                
                llm = self._create_llm(current_key)
                response = llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ])
                
                return response.content
                
            except ResourceExhausted as e:
                # Rate limit error - rotate to next key
                logger.warning(f"Rate limit hit on key {self.current_key_index + 1}: {str(e)[:100]}")
                last_error = e
                self.rotate_to_next_key()
                attempts += 1
                
            except Exception as e:
                # Check if it's a rate limit error in the message
                error_str = str(e).lower()
                if "rate" in error_str and "limit" in error_str:
                    logger.warning(f"Rate limit error on key {self.current_key_index + 1}: {str(e)[:100]}")
                    last_error = e
                    self.rotate_to_next_key()
                    attempts += 1
                elif "quota" in error_str:
                    logger.warning(f"Quota exceeded on key {self.current_key_index + 1}: {str(e)[:100]}")
                    last_error = e
                    self.rotate_to_next_key()
                    attempts += 1
                else:
                    # Other error - re-raise
                    raise
        
        # All keys exhausted
        logger.error(f"All {len(self.api_keys)} API keys are rate limited")
        raise Exception(f"All API keys are rate limited. Last error: {last_error}")


# Global instance for easy access
_manager: Optional[APIKeyRotationManager] = None


def get_key_manager() -> APIKeyRotationManager:
    """Get or create the global API key rotation manager."""
    global _manager
    if _manager is None:
        _manager = APIKeyRotationManager()
    return _manager


def call_llm_with_rotation(system_prompt: str, user_prompt: str) -> str:
    """
    Convenience function to call LLM with automatic key rotation.
    
    This is a drop-in replacement for the original call_llm function,
    but with rate limit handling and key rotation.
    
    Args:
        system_prompt: The system prompt for the LLM
        user_prompt: The user's question/prompt
        
    Returns:
        The LLM's response text
    """
    manager = get_key_manager()
    return manager.call_llm_with_retry(system_prompt, user_prompt)
