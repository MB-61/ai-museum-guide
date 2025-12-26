from fastapi import APIRouter
from app.models.chat_models import ChatRequest, ChatResponse
from app.services.chat_service import ask_museum_guide
from app.services import stats_service

router = APIRouter(prefix="/chat", tags=["Chat Agent"])


@router.post("", response_model=ChatResponse)
async def chat_with_guide(payload: ChatRequest) -> ChatResponse:
    # Track stats
    try:
        stats_service.track_question(payload.question)
    except Exception:
        pass
    
    return ask_museum_guide(
        question=payload.question, 
        qr_id=payload.qr_id,
        history=payload.history
    )

