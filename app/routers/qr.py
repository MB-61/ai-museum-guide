from fastapi import APIRouter

from app.models.qr_models import QRLookupRequest, QRLookupResponse
from app.services.qr_service import lookup_exhibit

router = APIRouter(
    prefix="/qr",
    tags=["QR Agent"],
)


@router.post("/lookup", response_model=QRLookupResponse)
async def qr_lookup(payload: QRLookupRequest) -> QRLookupResponse:
    return lookup_exhibit(payload.qr_id)
