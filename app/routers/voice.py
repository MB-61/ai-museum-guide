from fastapi import APIRouter, UploadFile, File
import os

from app.models.voice_models import STTResponse, TTSRequest, TTSResponse
from app.services.voice_service import stt_transcribe, tts_synthesize_dummy


router = APIRouter(prefix="/voice")


@router.get("/azure-config")
async def get_azure_config():
    """Get Azure Speech API configuration from environment variables."""
    return {
        "key": os.getenv("AZURE_SPEECH_KEY", ""),
        "region": os.getenv("AZURE_SPEECH_REGION", "westeurope")
    }


@router.post("/stt", response_model=STTResponse)
async def speech_to_text(file: UploadFile = File(...)) -> STTResponse:
    """Transcribe audio to text using Gemini API.
    
    Accepts audio files (webm, wav, mp3, ogg) and returns transcribed text.
    """
    # Read audio data
    audio_data = await file.read()
    content_type = file.content_type or "audio/webm"
    
    # Transcribe using Gemini
    result = await stt_transcribe(audio_data, content_type)
    return result


@router.post("/tts", response_model=TTSResponse)
async def text_to_speech(payload: TTSRequest) -> TTSResponse:
    """Placeholder TTS endpoint.

    Returns a fake URL for now. Later, plug into real TTS.
    """
    return tts_synthesize_dummy(payload.text, payload.voice)

