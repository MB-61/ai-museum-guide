from fastapi import APIRouter, Request
import logging

from app.models.qr_models import QRLookupRequest, QRLookupResponse
from app.services.qr_service import lookup_exhibit
from app.services import stats_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/qr",
    tags=["QR Agent"],
)


@router.post("/lookup", response_model=QRLookupResponse)
async def qr_lookup(payload: QRLookupRequest, request: Request) -> QRLookupResponse:
    result = lookup_exhibit(payload.qr_id)
    
    # Get client IP
    client_ip = request.client.host if request.client else None
    
    # Track QR scan stats
    try:
        stats_service.track_qr_scan(payload.qr_id, result.title or "")
        stats_service.track_session(client_ip)
        logger.info(f"QR scan tracked: {payload.qr_id}, IP: {client_ip}")
    except Exception as e:
        logger.error(f"Stats tracking error: {e}")
    
    return result


@router.get("/exhibit-image/{qr_id}")
async def get_exhibit_image(qr_id: str):
    """Get exhibit image URL (public, no auth required)."""
    try:
        from app.utils.ids import get_exhibit_by_qr
        
        result = get_exhibit_by_qr(qr_id)
        if not result:
             return {"qr_id": qr_id, "image": "", "title": ""}
             
        exhibit_id, metadata = result
        return {
            "qr_id": qr_id,
            "exhibit_id": exhibit_id,
            "image": metadata.get("image", ""),
            "title": metadata.get("title", "")
        }
    except Exception as e:
        logger.error(f"Error resolving exhibit: {e}")
        return {"qr_id": qr_id, "image": "", "title": ""}
