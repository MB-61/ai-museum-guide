from dotenv import load_dotenv
load_dotenv()  # Load .env variables

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.routers import qr, chat, voice, character


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Museum Guide API",
        version="1.0.0",
        description=(
            "Minimal, clean, multi-agent backend for the AI Museum Guide "
            "(QR, chat, voice, character)."
        ),
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers (each agent = separate namespace)
    app.include_router(qr.router, prefix="/api/v1", tags=["QR Agent"])
    app.include_router(chat.router, prefix="/api/v1", tags=["Chat Agent"])
    app.include_router(voice.router, prefix="/api/v1", tags=["Voice Agent"])
    app.include_router(
        character.router, prefix="/api/v1", tags=["Character Agent"]
    )

    # Serve frontend static files
    web_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")
    if os.path.exists(web_dir):
        app.mount("/static", StaticFiles(directory=web_dir), name="static")
        
        @app.get("/")
        async def serve_frontend():
            return FileResponse(os.path.join(web_dir, "avatar-guide-v2.html"))

    return app


app = create_app()