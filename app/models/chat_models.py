from pydantic import BaseModel
from typing import List, Optional


class Message(BaseModel):
    """Single message in conversation history"""
    role: str  # 'user' or 'assistant'
    content: str


class ChatRequest(BaseModel):
    qr_id: Optional[str] = None
    question: str
    history: List[Message] = []  # Last N messages for context


class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []
