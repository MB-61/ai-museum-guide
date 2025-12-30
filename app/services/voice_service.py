import base64
import os
from google import genai
from google.genai import types as genai_types

from app.models.voice_models import TTSResponse, STTResponse


def get_genai_client():
    """Get Gemini API client."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not set")
    return genai.Client(api_key=api_key)


async def stt_transcribe(audio_data: bytes, content_type: str = "audio/webm") -> STTResponse:
    """Transcribe audio using Gemini API."""
    try:
        client = get_genai_client()
        
        # Encode audio to base64
        audio_base64 = base64.b64encode(audio_data).decode("utf-8")
        
        # Determine MIME type
        mime_type = content_type
        if "webm" in content_type:
            mime_type = "audio/webm"
        elif "wav" in content_type:
            mime_type = "audio/wav"
        elif "mp3" in content_type:
            mime_type = "audio/mp3"
        elif "ogg" in content_type:
            mime_type = "audio/ogg"
        
        # Create content with audio
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                genai_types.Content(
                    parts=[
                        genai_types.Part(
                            inline_data=genai_types.Blob(
                                mime_type=mime_type,
                                data=audio_base64
                            )
                        ),
                        genai_types.Part(
                            text="Bu ses kaydını Türkçe olarak yazıya dök. Sadece konuşmayı yazıya dök, başka açıklama ekleme. Eğer ses anlaşılmıyorsa veya boşsa, 'Ses algılanamadı' yaz."
                        )
                    ]
                )
            ]
        )
        
        transcript = response.text.strip()
        return STTResponse(text=transcript)
        
    except Exception as e:
        print(f"STT Error: {e}")
        return STTResponse(text=f"Ses tanıma hatası: {str(e)}")


def stt_transcribe_dummy() -> STTResponse:
    """Fake STT – later connect to real STT (Whisper, etc.)."""
    return STTResponse(text="(placeholder) Tell me about this artwork")


def tts_synthesize_dummy(text: str, voice: str | None = None) -> TTSResponse:
    """Fake TTS – later connect to a real TTS engine."""
    fake_url = "https://cdn.example.com/audio/placeholder.wav"
    return TTSResponse(audio_url=fake_url)

