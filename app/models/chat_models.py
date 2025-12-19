from pydantic import BaseModel


class ChatRequest(BaseModel):
    qr_id: str | None = None
    question: str
    user_id: str | None = None  # Session ID for memory tracking


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []
