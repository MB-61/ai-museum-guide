from typing import Optional

from app.models.chat_models import ChatResponse
from app.services.rag import run_rag


def ask_museum_guide(
    question: str,
    qr_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> ChatResponse:
    answer, sources = run_rag(question=question, qr_id=qr_id, user_id=user_id)
    return ChatResponse(answer=answer, sources=sources)
