from typing import Optional, List

from app.models.chat_models import ChatResponse, Message
from app.services.rag import run_rag


def ask_museum_guide(
    question: str, 
    qr_id: Optional[str] = None,
    history: List[Message] = None
) -> ChatResponse:
    """Main entry point for museum guide chat with optional conversation history"""
    if history is None:
        history = []
    answer, sources = run_rag(question=question, qr_id=qr_id, history=history)
    return ChatResponse(answer=answer, sources=sources)
