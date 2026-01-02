"""QR Service - Handles QR code lookups."""
import os
from typing import Optional, Dict, Any

from app.models.qr_models import QRLookupResponse
from app.utils.ids import get_exhibit_by_qr, get_content_file_path
from app.services.retriever import retrieve


def build_basic_metadata(meta: Dict[str, Any]) -> Dict[str, str]:
    """Extract meaningful fields from Chroma metadata for UI."""
    fields = ["title", "artist", "year", "period", "location"]
    return {k: str(v) for k, v in meta.items() if k in fields and v is not None}


def lookup_exhibit(qr_code: str) -> QRLookupResponse:
    """
    Look up exhibit information from QR code.
    
    Steps:
    1. Find exhibit by QR code in exhibit_metadata.json
    2. Get content file path (ESER_DATA_XX.txt)
    3. Use retriever to get relevant chunks for context
    4. Build response with all info
    """
    # Get exhibit by QR code
    result = get_exhibit_by_qr(qr_code)
    
    if result:
        exhibit_id, metadata = result
        title = metadata.get("title", exhibit_id)
        category = metadata.get("category", "")
        image = metadata.get("image", "")
        content_file = metadata.get("content_file", "")
    else:
        # QR code not found in metadata
        return QRLookupResponse(
            exhibit_id="UNKNOWN",
            title="Bilinmeyen Eser",
            summary="Bu QR kod sistemde tanımlı değil.",
            image=None,
            metadata={}
        )
    
    # Get content file path
    content_path = get_content_file_path(exhibit_id)
    
    # Determine exhibit_id for retriever (uses file name format)
    num = exhibit_id.replace("ID_", "") if exhibit_id.startswith("ID_") else exhibit_id
    retriever_id = f"ESER_DATA_{num}"
    
    # Get relevant chunks from retriever
    chunks = retrieve(query="short description", exhibit_id=retriever_id, k=2)
    
    if chunks:
        first_doc, first_meta = chunks[0]
        # Truncate for summary
        summary = (first_doc[:280] + "…") if len(first_doc) > 280 else first_doc
        response_metadata = build_basic_metadata(first_meta or {})
    else:
        # Fallback: try reading content file directly
        summary = "No detailed description found yet for this exhibit."
        response_metadata = {}
        
        if os.path.exists(content_path):
            try:
                with open(content_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    summary = (content[:280] + "…") if len(content) > 280 else content
            except:
                pass
    
    return QRLookupResponse(
        exhibit_id=exhibit_id,
        title=title,
        summary=summary,
        image=image if image else None,
        metadata=response_metadata,
    )