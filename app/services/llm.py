"""
LLM Service - Gemini API Integration with Key Rotation

This module provides the LLM interface for the AI Museum Guide,
with automatic API key rotation when rate limits are hit.
"""

from app.services.key_rotation import call_llm_with_rotation


def call_llm(system_prompt: str, user_prompt: str) -> str:
    """
    Call the LLM with the given prompts.
    
    This function automatically handles rate limits by rotating
    through available API keys.
    
    Args:
        system_prompt: The system prompt for the LLM
        user_prompt: The user's question/prompt
        
    Returns:
        The LLM's response text
    """
    return call_llm_with_rotation(system_prompt, user_prompt)
