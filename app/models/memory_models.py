"""
Memory Models for AI Museum Guide

Pydantic models for storing and extracting user memory data.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class MemoryExtraction(BaseModel):
    """Data extracted from a conversation by LLM."""
    name: str | None = None
    interests: list[str] = Field(default_factory=list)
    preferences: dict = Field(default_factory=dict)
    is_important: bool = False  # LLM decides if worth saving


class UserMemory(BaseModel):
    """Persistent user memory stored on disk."""
    user_id: str
    name: str | None = None
    interests: list[str] = Field(default_factory=list)
    visited_exhibits: list[str] = Field(default_factory=list)
    preferences: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
