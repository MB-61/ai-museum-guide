"""
Status Router - System status and health endpoints
"""

from fastapi import APIRouter
from app.services.key_rotation import get_key_manager

router = APIRouter()


@router.get("/status/key")
async def get_key_status():
    """Get current API key status."""
    manager = get_key_manager()
    return manager.get_key_info()


@router.post("/status/reload-keys")
async def reload_api_keys():
    """Reload API keys from environment."""
    manager = get_key_manager()
    manager.reload_keys()
    return manager.get_key_info()
