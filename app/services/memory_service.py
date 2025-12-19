"""
Memory Service for AI Museum Guide

Extracts important user information from conversations and stores it
for personalized future interactions.
"""

import json
import os
from datetime import datetime
from typing import Optional

from app.models.memory_models import MemoryExtraction, UserMemory
from app.services.llm import call_llm


# Storage directory for memory files
MEMORY_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "storage", "memory"
)


def _ensure_memory_dir():
    """Ensure the memory storage directory exists."""
    os.makedirs(MEMORY_DIR, exist_ok=True)


def _get_memory_path(user_id: str) -> str:
    """Get the file path for a user's memory."""
    return os.path.join(MEMORY_DIR, f"{user_id}.json")


def get_memory(user_id: str) -> Optional[UserMemory]:
    """
    Load user memory from disk.
    
    Returns None if no memory exists for this user.
    """
    _ensure_memory_dir()
    path = _get_memory_path(user_id)
    
    if not os.path.exists(path):
        return None
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return UserMemory(**data)
    except (json.JSONDecodeError, Exception):
        return None


def save_memory(memory: UserMemory) -> None:
    """Save user memory to disk."""
    _ensure_memory_dir()
    path = _get_memory_path(memory.user_id)
    
    memory.updated_at = datetime.now()
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(memory.model_dump(mode="json"), f, ensure_ascii=False, indent=2, default=str)


def update_memory(user_id: str, extraction: MemoryExtraction) -> UserMemory:
    """
    Update user memory with new extracted information.
    
    Creates new memory if none exists.
    """
    memory = get_memory(user_id)
    
    if memory is None:
        memory = UserMemory(user_id=user_id)
    
    # Update name if provided
    if extraction.name:
        memory.name = extraction.name
    
    # Merge interests (avoid duplicates)
    for interest in extraction.interests:
        if interest.lower() not in [i.lower() for i in memory.interests]:
            memory.interests.append(interest)
    
    # Merge preferences
    memory.preferences.update(extraction.preferences)
    
    save_memory(memory)
    return memory


def add_visited_exhibit(user_id: str, exhibit_id: str) -> None:
    """Record that a user has visited an exhibit."""
    memory = get_memory(user_id)
    
    if memory is None:
        memory = UserMemory(user_id=user_id)
    
    if exhibit_id not in memory.visited_exhibits:
        memory.visited_exhibits.append(exhibit_id)
        save_memory(memory)


EXTRACTION_PROMPT = """Analyze this conversation and extract ONLY important user information.

User message: {user_message}
Assistant response: {assistant_response}

Extract:
- name: User's name if they mentioned it (null if not mentioned)
- interests: Art styles, artists, periods, or topics they expressed interest in (empty list if none)
- preferences: Any stated preferences like language or detail level (empty dict if none)
- is_important: true ONLY if there's genuinely new, memorable info; false for normal questions

Return ONLY valid JSON, no explanation:
{{"name": null, "interests": [], "preferences": {{}}, "is_important": false}}"""


def extract_important_data(user_message: str, assistant_response: str) -> MemoryExtraction:
    """
    Use LLM to extract important user information from a conversation.
    
    Returns MemoryExtraction with is_important=False if nothing notable found.
    """
    prompt = EXTRACTION_PROMPT.format(
        user_message=user_message,
        assistant_response=assistant_response
    )
    
    try:
        result = call_llm(
            system_prompt="You are a JSON extractor. Return only valid JSON, no markdown or explanation.",
            user_prompt=prompt
        )
        
        # Clean up response (remove markdown code blocks if present)
        result = result.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1] if "\n" in result else result[3:]
        if result.endswith("```"):
            result = result.rsplit("```", 1)[0]
        result = result.strip()
        
        data = json.loads(result)
        return MemoryExtraction(**data)
    except (json.JSONDecodeError, Exception):
        # If extraction fails, return empty extraction
        return MemoryExtraction(is_important=False)


def get_memory_context(user_id: str) -> str:
    """
    Generate a context string from user memory for inclusion in prompts.
    
    Returns empty string if no memory exists.
    """
    memory = get_memory(user_id)
    
    if memory is None:
        return ""
    
    parts = []
    
    if memory.name:
        parts.append(f"- Visitor name: {memory.name}")
    
    if memory.interests:
        parts.append(f"- Interests: {', '.join(memory.interests)}")
    
    if memory.visited_exhibits:
        parts.append(f"- Previously viewed: {', '.join(memory.visited_exhibits)}")
    
    if memory.preferences:
        prefs = [f"{k}: {v}" for k, v in memory.preferences.items()]
        parts.append(f"- Preferences: {', '.join(prefs)}")
    
    if not parts:
        return ""
    
    return "About this visitor:\n" + "\n".join(parts)
