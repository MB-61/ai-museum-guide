from dotenv import load_dotenv
load_dotenv()  # Load .env variables

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.routers import qr, chat, voice, character, admin


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
    app.include_router(admin.router, prefix="/api/v1", tags=["Admin"])

    # Serve frontend static files
    web_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")
    static_dir = os.path.join(web_dir, "static")
    css_dir = os.path.join(web_dir, "css")
    js_dir = os.path.join(web_dir, "js")
    
    if os.path.exists(web_dir):
        # Mount static directory (for exhibits images, avatar, etc)
        if os.path.exists(static_dir):
            app.mount("/static", StaticFiles(directory=static_dir), name="static")
        # Mount CSS directory
        if os.path.exists(css_dir):
            app.mount("/css", StaticFiles(directory=css_dir), name="css")
        # Mount JS directory
        if os.path.exists(js_dir):
            app.mount("/js", StaticFiles(directory=js_dir), name="js")
        
        @app.get("/")
        async def serve_frontend():
            return FileResponse(os.path.join(web_dir, "index.html"))
        
        @app.get("/index.html")
        async def serve_index():
            return FileResponse(os.path.join(web_dir, "index.html"))
        
        @app.get("/qr-scan.html")
        async def serve_qr_scan():
            return FileResponse(os.path.join(web_dir, "qr-scan.html"))
        
        @app.get("/chat.html")
        async def serve_chat():
            return FileResponse(os.path.join(web_dir, "chat.html"))
        
        @app.get("/admin")
        async def serve_admin():
            return FileResponse(os.path.join(web_dir, "admin.html"))

    return app


app = create_app()