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
    import os
    import json
    
    # Load metadata
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
    metadata_file = os.path.join(data_dir, "exhibit_metadata.json")
    
    try:
        with open(metadata_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        exhibits = data.get("exhibits", {})
        
        if qr_id not in exhibits:
            return {"qr_id": qr_id, "image": "", "title": ""}
        
        exhibit = exhibits[qr_id]
        return {"qr_id": qr_id, "image": exhibit.get("image", ""), "title": exhibit.get("title", "")}
    except Exception as e:
        logger.error(f"Error loading exhibit metadata: {e}")
        return {"qr_id": qr_id, "image": "", "title": ""}
