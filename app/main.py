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
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    
    if os.path.exists(web_dir):
        app.mount("/static", StaticFiles(directory=web_dir), name="static")
        
        # Serve QR code images
        qr_dir = os.path.join(data_dir, "qr")
        if os.path.exists(qr_dir):
            app.mount("/static/qr", StaticFiles(directory=qr_dir), name="qr_codes")
        
        @app.get("/")
        async def serve_frontend():
            return FileResponse(os.path.join(web_dir, "index.html"))
        
        @app.get("/gallery")
        async def serve_gallery():
            return FileResponse(os.path.join(web_dir, "gallery.html"))

    return app


app = create_app()