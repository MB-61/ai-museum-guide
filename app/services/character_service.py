from app.models.character_models import (
    CharacterAnimateRequest,
    CharacterAnimateResponse,
)


def create_animation(req: CharacterAnimateRequest) -> CharacterAnimateResponse:
    """Very simple mapping from expression+gesture to animation key.

    Frontend can map `animation` to a sprite / animation clip.
    """

    key_parts: list[str] = []
    if req.gesture:
        key_parts.append(req.gesture)
    key_parts.append(req.expression)

    animation_key = "_".join(key_parts)

    return CharacterAnimateResponse(
        animation=animation_key,
        duration=2.0,
    )
