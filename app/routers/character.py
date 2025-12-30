from fastapi import APIRouter

from app.models.character_models import (
    CharacterAnimateRequest,
    CharacterAnimateResponse,
)
from app.services.character_service import create_animation

router = APIRouter(prefix="/character")


@router.post("/animate", response_model=CharacterAnimateResponse)
async def animate_character(
    payload: CharacterAnimateRequest,
) -> CharacterAnimateResponse:
    """Returns which animation the 2D character should play.

    Frontend decides how to render this key.
    """

    return create_animation(payload)
