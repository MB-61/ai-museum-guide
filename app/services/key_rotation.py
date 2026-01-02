"""
API Key Rotation Manager for Gemini API

This module manages multiple API keys and automatically rotates to the next key
when a rate limit error, leaked key, or timeout is encountered.

Features:
- Automatic key rotation on errors
- File-based error logging with timestamps
- Timeout-based key switching
- Detailed error categorization
"""

import os
import logging
import threading
import concurrent.futures
from datetime import datetime
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from google.api_core.exceptions import ResourceExhausted
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

# Load environment variables
load_dotenv()

# Configure console logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Error categories for logging
ERROR_CATEGORIES = {
    "RATE_LIMIT": "Rate limit exceeded",
    "LEAKED": "API key marked as leaked",
    "INVALID": "Invalid or missing API key",
    "TIMEOUT": "Request timeout",
    "QUOTA": "Quota exceeded",
    "PERMISSION": "Permission denied",
    "UNKNOWN": "Unknown error"
}


class APIErrorLogger:
    """Logs API errors to a file with timestamps."""
    
    def __init__(self, log_dir: str = "logs"):
        """Initialize the error logger."""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / "api_errors.log"
        self._lock = threading.Lock()
    
    def log_error(
        self,
        error_category: str,
        key_index: int,
        total_keys: int,
        error_message: str,
        action_taken: str = "rotated_key"
    ):
        """Log an API error with timestamp and details."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = (
            f"[{timestamp}] "
            f"CATEGORY: {error_category} | "
            f"KEY: {key_index + 1}/{total_keys} | "
            f"ACTION: {action_taken} | "
            f"ERROR: {error_message[:200]}\n"
        )
        
        with self._lock:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        
        logger.warning(f"[{error_category}] Key {key_index + 1}: {error_message[:100]}")
    
    def get_recent_errors(self, count: int = 50) -> list:
        """Get recent error entries for admin panel."""
        if not self.log_file.exists():
            return []
        
        with open(self.log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        return lines[-count:]


class APIKeyRotationManager:
    """
    Manages multiple API keys and rotates them when rate limits are hit.
    
    Features:
    - Automatic rotation on rate limit/quota/leaked key errors
    - Timeout handling with automatic key switch
    - Detailed file-based error logging
    
    Usage:
        manager = APIKeyRotationManager()
        response = manager.call_llm_with_retry(system_prompt, user_prompt)
    """
    
    # Default timeout in seconds
    DEFAULT_TIMEOUT = 15
    
    def __init__(self):
        """Initialize the key manager with API keys from environment."""
        self.timeout = int(os.getenv("LLM_TIMEOUT", self.DEFAULT_TIMEOUT))
        self._load_api_keys()
        self.current_key_index = 0
        self.model_name = os.getenv("LLM_MODEL", "gemini-2.0-flash")
        self.max_retries = len(self.api_keys)  # Try each key once
        self.error_logger = APIErrorLogger()
        logger.info(f"Key manager ready: {len(self.api_keys)} key(s), timeout={self.timeout}s")
        
    def _load_api_keys(self):
        """Load API keys from environment variables."""
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
                if key not in self.api_keys:
                    self.api_keys.append(key)
                i += 1
            else:
                break
        
        if not self.api_keys:
            raise ValueError("No API keys found. Set GOOGLE_API_KEY or GOOGLE_API_KEY_1, GOOGLE_API_KEY_2, etc.")
    
    def get_current_key(self) -> str:
        """Get the current API key."""
        return self.api_keys[self.current_key_index]
    
    def rotate_to_next_key(self) -> str:
        """Rotate to the next API key, cycling back to the first if necessary."""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        new_key = self.api_keys[self.current_key_index]
        logger.info(f"Rotated to API key {self.current_key_index + 1}/{len(self.api_keys)}")
        return new_key
    
    def _create_llm(self, api_key: str) -> ChatGoogleGenerativeAI:
        """Create a new LLM instance with the given API key."""
        os.environ["GOOGLE_API_KEY"] = api_key
        return ChatGoogleGenerativeAI(
            model=self.model_name,
            temperature=0.2,
            google_api_key=api_key,
            max_retries=0
        )
    
    def _categorize_error(self, error: Exception) -> str:
        """Categorize an error for logging."""
        error_str = str(error).lower()
        
        if "leaked" in error_str:
            return "LEAKED"
        elif "rate" in error_str and "limit" in error_str:
            return "RATE_LIMIT"
        elif "quota" in error_str:
            return "QUOTA"
        elif "invalid" in error_str or "not found" in error_str:
            return "INVALID"
        elif "permission" in error_str or "denied" in error_str:
            return "PERMISSION"
        elif isinstance(error, concurrent.futures.TimeoutError):
            return "TIMEOUT"
        else:
            return "UNKNOWN"
    
    def _should_rotate_on_error(self, error_category: str) -> bool:
        """Determine if we should rotate keys based on error category."""
        rotatable_errors = {"RATE_LIMIT", "LEAKED", "INVALID", "TIMEOUT", "QUOTA", "PERMISSION"}
        return error_category in rotatable_errors
    
    def _invoke_with_timeout(self, llm, messages):
        """Invoke LLM with timeout using ThreadPoolExecutor."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(llm.invoke, messages)
            try:
                return future.result(timeout=self.timeout)
            except concurrent.futures.TimeoutError:
                raise concurrent.futures.TimeoutError(f"LLM request timed out after {self.timeout} seconds")
    
    def call_llm_with_retry(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> str:
        """
        Call the LLM with automatic key rotation on errors.
        
        Features:
        - Rotates key on rate limit, leaked, invalid, or timeout errors
        - Logs all errors to file with timestamp
        - Has configurable timeout (LLM_TIMEOUT env var, default 15s)
        
        Args:
            system_prompt: The system prompt for the LLM
            user_prompt: The user's question/prompt
            
        Returns:
            The LLM's response text
            
        Raises:
            Exception: If all API keys fail
        """
        last_error = None
        attempts = 0
        
        while attempts < self.max_retries:
            current_key = self.get_current_key()
            
            try:
                logger.info(f"Attempting with API key {self.current_key_index + 1}/{len(self.api_keys)} (timeout={self.timeout}s)")
                
                llm = self._create_llm(current_key)
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ]
                
                # Use timeout wrapper
                response = self._invoke_with_timeout(llm, messages)
                
                # Track token usage
                try:
                    from app.services import token_tracker
                    input_tokens = (len(system_prompt) + len(user_prompt)) // 4
                    output_tokens = len(response.content) // 4
                    token_tracker.track_tokens(input_tokens, output_tokens)
                except Exception as track_err:
                    logger.debug(f"Token tracking skipped: {track_err}")
                
                return response.content
                
            except Exception as e:
                error_category = self._categorize_error(e)
                error_msg = str(e)
                
                # Log to file
                self.error_logger.log_error(
                    error_category=error_category,
                    key_index=self.current_key_index,
                    total_keys=len(self.api_keys),
                    error_message=error_msg,
                    action_taken="rotating_key" if self._should_rotate_on_error(error_category) else "re-raising"
                )
                
                last_error = e
                
                if self._should_rotate_on_error(error_category):
                    self.rotate_to_next_key()
                    attempts += 1
                else:
                    # Non-rotatable error - re-raise immediately
                    raise
        
        # All keys exhausted
        self.error_logger.log_error(
            error_category="ALL_KEYS_EXHAUSTED",
            key_index=self.current_key_index,
            total_keys=len(self.api_keys),
            error_message=f"All {len(self.api_keys)} keys failed. Last: {str(last_error)[:100]}",
            action_taken="giving_up"
        )
        raise Exception(f"All API keys failed. Last error: {last_error}")


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
    but with rate limit handling, key rotation, and timeout support.
    """
    manager = get_key_manager()
    return manager.call_llm_with_retry(system_prompt, user_prompt)


# Export API keys for admin panel
def get_gemini_keys():
    """Get list of API keys (for admin)."""
    manager = get_key_manager()
    return manager.api_keys


def get_key_status():
    """Get API key status for admin panel."""
    manager = get_key_manager()
    keys_info = []
    for i, key in enumerate(manager.api_keys):
        # Mask key for security - show only last 5 chars
        masked = "..." + key[-5:] if len(key) > 5 else "***"
        keys_info.append({
            "key": masked,
            "status": "active" if i == manager.current_key_index else "standby",
            "index": i + 1
        })
    return {
        "current_index": manager.current_key_index,
        "total_keys": len(manager.api_keys),
        "timeout": manager.timeout,
        "keys": keys_info
    }


def get_recent_errors(count: int = 50) -> list:
    """Get recent API errors for admin panel."""
    try:
        manager = get_key_manager()
        return manager.error_logger.get_recent_errors(count)
    except:
        return []


# For admin panel import
GEMINI_API_KEYS = None
try:
    GEMINI_API_KEYS = get_gemini_keys()
except:
    GEMINI_API_KEYS = []

