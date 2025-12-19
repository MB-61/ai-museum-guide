from pydantic import BaseModel


class ChatRequest(BaseModel):
    qr_id: str | None = None
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []
