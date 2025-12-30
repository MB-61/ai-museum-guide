from typing import Optional, Dict, Any

from app.models.qr_models import QRLookupResponse
from app.utils.ids import resolve_qr
from app.services.retriever import retrieve


def build_basic_metadata(meta: Dict[str, Any]) -> Dict[str, str]:
    """
    Chroma metadata'ından UI için anlamlı alanlar seç.
    Kendi metadata şemanı göre key'leri değiştirmen gerekebilir.
    Örn: title, period, location, artist, year...
    """
    fields = ["title", "artist", "year", "period", "location"]
    return {k: str(v) for k, v in meta.items() if k in fields and v is not None}


def lookup_exhibit(qr_id: str) -> QRLookupResponse:
    """
    QR kodundan sergi bilgisini döndürür.

    Adımlar:
    1. qr_id -> exhibit_id (resolve_qr)
    2. retriever ile o esere ait 1–2 chunk çek
    3. İlk chunk'tan kısa bir özet üret (şimdilik sadece kırpıyoruz)
    4. metadata'dan title / artist / period vb. alanları al
    """
    exhibit_id = resolve_qr(qr_id)

    # Sadece o sergiye ait dokümanları çek
    chunks = retrieve(query="short description", exhibit_id=exhibit_id, k=2)

    if chunks:
        first_doc, first_meta = chunks[0]
        # Çok uzun olmasın diye basit kırpma
        summary = (first_doc[:280] + "…") if len(first_doc) > 280 else first_doc
        metadata = build_basic_metadata(first_meta or {})
        image = first_meta.get("image_url") if first_meta else None
        title = first_meta.get("title") or exhibit_id
    else:
        summary = "No detailed description found yet for this exhibit."
        metadata = {}
        image = None
        title = exhibit_id

    return QRLookupResponse(
        exhibit_id=exhibit_id,
        title=title,
        summary=summary,
        image=image,
        metadata=metadata,
    )