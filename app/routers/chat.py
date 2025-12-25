from fastapi import APIRouter
from app.models.chat_models import ChatRequest, ChatResponse
from app.services.chat_service import ask_museum_guide

router = APIRouter(prefix="/chat", tags=["Chat Agent"])


@router.post("", response_model=ChatResponse)
async def chat_with_guide(payload: ChatRequest) -> ChatResponse:
    return ask_museum_guide(
        question=payload.question, 
        qr_id=payload.qr_id,
        history=payload.history
    )
