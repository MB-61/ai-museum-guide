from pydantic import BaseModel


class TTSRequest(BaseModel):
    text: str
    voice: str | None = "default"


class TTSResponse(BaseModel):
    audio_url: str


class STTResponse(BaseModel):
    text: str
