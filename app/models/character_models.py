from pydantic import BaseModel


class CharacterAnimateRequest(BaseModel):
    expression: str  # e.g. "neutral", "happy", "curious"
    gesture: str | None = None  # e.g. "point_right", "wave"


class CharacterAnimateResponse(BaseModel):
    animation: str
    duration: float
