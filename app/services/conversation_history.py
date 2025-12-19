"""
Conversation History Service

Stores and retrieves conversation history per user session.
"""

import json
import os
from datetime import datetime
from typing import Optional
from collections import deque

# In-memory storage for conversation history (per session)
# Using deque with maxlen to limit history size
_conversations: dict[str, deque] = {}

# Maximum messages to keep per conversation
MAX_HISTORY_SIZE = 20


def get_conversation_history(user_id: str) -> list[dict]:
    """
    Get conversation history for a user session.
    
    Returns list of messages: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    """
    if user_id not in _conversations:
        return []
    return list(_conversations[user_id])


def add_message(user_id: str, role: str, content: str) -> None:
    """
    Add a message to the conversation history.
    
    Args:
        user_id: Session/user identifier
        role: "user" or "assistant"
        content: Message content
    """
    if user_id not in _conversations:
        _conversations[user_id] = deque(maxlen=MAX_HISTORY_SIZE)
    
    _conversations[user_id].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })


def clear_conversation(user_id: str) -> None:
    """Clear conversation history for a user."""
    if user_id in _conversations:
        del _conversations[user_id]


def format_history_for_prompt(user_id: str, max_messages: int = 6) -> str:
    """
    Format recent conversation history for inclusion in LLM prompt.
    
    Returns a formatted string of recent exchanges.
    """
    history = get_conversation_history(user_id)
    
    if not history:
        return ""
    
    # Take only the last N messages
    recent = history[-max_messages:]
    
    lines = ["Previous conversation:"]
    for msg in recent:
        role = "Visitor" if msg["role"] == "user" else "Guide"
        lines.append(f"{role}: {msg['content']}")
    
    return "\n".join(lines)
