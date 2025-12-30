from pydantic import BaseModel


class QRLookupRequest(BaseModel):
    qr_id: str


class QRLookupResponse(BaseModel):
    title: str
    summary: str
    image: str | None = None
    metadata: dict | None = None
