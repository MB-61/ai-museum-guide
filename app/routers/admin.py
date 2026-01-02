"""Admin panel API endpoints."""
import os
import json
import hashlib
import secrets
import base64
import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Header, UploadFile, File
from pydantic import BaseModel

from app.services import token_tracker, stats_service
from app.services.key_rotation import get_key_status, get_recent_errors, GEMINI_API_KEYS

router = APIRouter(prefix="/admin", tags=["Admin"])

# Simple auth config
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = hashlib.sha256("1234".encode()).hexdigest()
_sessions = {}  # token -> expiry

# Data paths
WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "web")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")


# ========== MODELS ==========
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    expires_in: int


class GreetingUpdate(BaseModel):
    content: str


# ========== AUTH ==========
def verify_token(authorization: Optional[str] = Header(None)):
    """Verify admin token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    if token not in _sessions or _sessions[token] < datetime.now():
        raise HTTPException(status_code=401, detail="Token expired")
    
    return True


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    """Admin login."""
    password_hash = hashlib.sha256(req.password.encode()).hexdigest()
    if req.username != ADMIN_USERNAME or password_hash != ADMIN_PASSWORD_HASH:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = secrets.token_urlsafe(32)
    _sessions[token] = datetime.now() + timedelta(hours=24)
    
    return LoginResponse(token=token, expires_in=86400)


@router.post("/logout")
async def logout(authorized: bool = Depends(verify_token), authorization: str = Header(None)):
    """Admin logout."""
    token = authorization.replace("Bearer ", "")
    if token in _sessions:
        del _sessions[token]
    return {"status": "ok"}


# ========== DASHBOARD ==========
@router.get("/dashboard")
async def get_dashboard(period: str = "today", authorized: bool = Depends(verify_token)):
    """Get dashboard overview for specified period (today, week, month, year, all)."""
    stats = stats_service.get_stats()
    tokens = token_tracker.get_token_stats()
    daily_activity = stats.get("daily_history", {})
    daily_tokens = tokens.get("daily_history", {})
    
    from datetime import date, timedelta
    today = date.today()
    
    # Calculate date ranges
    if period == "today":
        start_date = today
    elif period == "week":
        start_date = today - timedelta(days=7)
    elif period == "month":
        start_date = today - timedelta(days=30)
    elif period == "year":
        start_date = today - timedelta(days=365)
    else:  # all
        start_date = date(2000, 1, 1)
    
    # Sum stats for the period
    period_scans = 0
    period_chats = 0
    period_input = 0
    period_output = 0
    
    for date_str, activity in daily_activity.items():
        try:
            d = date.fromisoformat(date_str)
            if d >= start_date:
                period_scans += activity.get("scans", 0)
                period_chats += activity.get("chats", 0)
        except:
            pass
    
    for date_str, tok in daily_tokens.items():
        try:
            d = date.fromisoformat(date_str)
            if d >= start_date:
                period_input += tok.get("input", 0)
                period_output += tok.get("output", 0)
        except:
            pass
    
    period_tokens = period_input + period_output
    period_cost = round((period_input * 0.00000015 + period_output * 0.0000006), 4)
    
    return {
        "today_scans": period_scans,
        "today_chats": period_chats,
        "total_sessions": stats["total_sessions"],
        "unique_visitors": stats.get("unique_visitors", 0),
        "total_tokens": tokens["total"]["input"] + tokens["total"]["output"],
        "today_tokens": period_tokens,
        "today_cost": period_cost,
        "total_cost": tokens["estimated_cost_usd"],
        "api_keys_count": len(GEMINI_API_KEYS) if GEMINI_API_KEYS else 0
    }


# ========== GREETINGS ==========
@router.get("/greetings/qr")
async def get_qr_greetings(authorized: bool = Depends(verify_token)):
    """Get QR mode greetings."""
    path = os.path.join(WEB_DIR, "static", "data", "qrli_greeting.txt")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return {"content": f.read(), "path": path}
    except:
        return {"content": "", "path": path}


@router.put("/greetings/qr")
async def update_qr_greetings(data: GreetingUpdate, authorized: bool = Depends(verify_token)):
    """Update QR mode greetings."""
    path = os.path.join(WEB_DIR, "static", "data", "qrli_greeting.txt")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(data.content)
    return {"status": "ok"}


@router.get("/greetings/general")
async def get_general_greetings(authorized: bool = Depends(verify_token)):
    """Get general mode greetings."""
    path = os.path.join(WEB_DIR, "static", "data", "qrsiz_greeting.txt")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return {"content": f.read(), "path": path}
    except:
        return {"content": "", "path": path}


@router.put("/greetings/general")
async def update_general_greetings(data: GreetingUpdate, authorized: bool = Depends(verify_token)):
    """Update general mode greetings."""
    path = os.path.join(WEB_DIR, "static", "data", "qrsiz_greeting.txt")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(data.content)
    return {"status": "ok"}


# ========== STATISTICS ==========
@router.get("/stats")
async def get_stats(authorized: bool = Depends(verify_token)):
    """Get usage statistics."""
    return stats_service.get_stats()


@router.get("/tokens")
async def get_tokens(authorized: bool = Depends(verify_token)):
    """Get token usage statistics."""
    return token_tracker.get_token_stats()


@router.post("/stats/reset")
async def reset_all_stats(authorized: bool = Depends(verify_token)):
    """Reset all statistics."""
    stats_service.reset_stats()
    token_tracker.reset_stats()
    return {"status": "ok"}


# ========== API KEYS ==========
@router.get("/api-keys")
async def get_api_keys(authorized: bool = Depends(verify_token)):
    """Get API key status."""
    status = get_key_status()
    return {
        "current_index": status.get("current_index", 0),
        "total_keys": status.get("total_keys", 0),
        "timeout": status.get("timeout", 15),
        "keys": status.get("keys", [])
    }


@router.get("/api-errors")
async def get_api_errors(authorized: bool = Depends(verify_token)):
    """Get recent API error logs."""
    errors = get_recent_errors(50)
    return {
        "total": len(errors),
        "errors": [e.strip() for e in errors]
    }


# ========== EXHIBITS ==========
EXHIBITS_FILE = os.path.join(DATA_DIR, "exhibits.json")


class ExhibitCreate(BaseModel):
    qr_id: str
    title: str
    description: str = ""


class ExhibitUpdate(BaseModel):
    title: str
    description: str = ""


def _load_exhibits():
    """Load exhibits from file."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(EXHIBITS_FILE):
        # Initialize with default exhibits
        default_exhibits = {
            "qr_01": {"title": "Türk Maarif Cemiyeti Tüzüğü", "description": ""},
            "qr_02": {"title": "Atatürk Fotoğrafı", "description": ""},
            "qr_03": {"title": "Kuruluş Diploması", "description": ""},
            "qr_04": {"title": "Bando Kıyafeti", "description": ""},
            "qr_05": {"title": "Spor Kupası", "description": ""},
            "qr_06": {"title": "İlk Zil", "description": ""},
            "qr_07": {"title": "Mimari Maket", "description": ""},
            "qr_08": {"title": "Eğitim Sırası", "description": ""},
            "qr_09": {"title": "Nota Defteri", "description": ""},
            "qr_10": {"title": "Daktilo Makinesi", "description": ""}
        }
        with open(EXHIBITS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_exhibits, f, indent=2, ensure_ascii=False)
        return default_exhibits
    
    with open(EXHIBITS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_exhibits(exhibits):
    """Save exhibits to file."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(EXHIBITS_FILE, "w", encoding="utf-8") as f:
        json.dump(exhibits, f, indent=2, ensure_ascii=False)


@router.get("/exhibits")
async def get_exhibits(authorized: bool = Depends(verify_token)):
    """Get all exhibits."""
    exhibits = _load_exhibits()
    return {"exhibits": [{"qr_id": k, **v} for k, v in exhibits.items()]}


@router.post("/exhibits")
async def create_exhibit(data: ExhibitCreate, authorized: bool = Depends(verify_token)):
    """Create a new exhibit."""
    exhibits = _load_exhibits()
    if data.qr_id in exhibits:
        raise HTTPException(status_code=400, detail="QR ID already exists")
    
    exhibits[data.qr_id] = {"title": data.title, "description": data.description}
    _save_exhibits(exhibits)
    return {"status": "ok", "qr_id": data.qr_id}


@router.put("/exhibits/{qr_id}")
async def update_exhibit(qr_id: str, data: ExhibitUpdate, authorized: bool = Depends(verify_token)):
    """Update an exhibit."""
    exhibits = _load_exhibits()
    if qr_id not in exhibits:
        raise HTTPException(status_code=404, detail="Exhibit not found")
    
    exhibits[qr_id] = {"title": data.title, "description": data.description}
    _save_exhibits(exhibits)
    return {"status": "ok"}


@router.delete("/exhibits/{qr_id}")
async def delete_exhibit(qr_id: str, authorized: bool = Depends(verify_token)):
    """Delete an exhibit."""
    exhibits = _load_exhibits()
    if qr_id not in exhibits:
        raise HTTPException(status_code=404, detail="Exhibit not found")
    
    del exhibits[qr_id]
    _save_exhibits(exhibits)
    return {"status": "ok"}


# ========== RAG EXHIBITS (ted_museum folder) ==========
TED_MUSEUM_DIR = os.path.join(DATA_DIR, "ted_museum")
METADATA_FILE = os.path.join(DATA_DIR, "exhibit_metadata.json")
EXHIBITS_IMG_DIR = os.path.join(WEB_DIR, "static", "exhibits")


def _load_exhibit_metadata():
    """Load exhibit metadata."""
    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"categories": [], "exhibits": {}}


def _save_exhibit_metadata(data):
    """Save exhibit metadata."""
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _get_next_id() -> str:
    """Get next available exhibit ID, filling gaps first."""
    metadata = _load_exhibit_metadata()
    exhibits = metadata.get("exhibits", {})
    
    # Extract existing numbers
    existing_nums = set()
    for exhibit_id in exhibits.keys():
        if exhibit_id.startswith("ID_"):
            try:
                num = int(exhibit_id.replace("ID_", ""))
                existing_nums.add(num)
            except:
                pass
    
    if not existing_nums:
        return "ID_01"
    
    # Find first gap
    max_num = max(existing_nums)
    for i in range(1, max_num + 2):
        if i not in existing_nums:
            return f"ID_{str(i).zfill(2)}"
    
    return f"ID_{str(max_num + 1).zfill(2)}"


def _id_to_num(exhibit_id: str) -> str:
    """Extract number from ID_XX -> XX."""
    return exhibit_id.replace("ID_", "") if exhibit_id.startswith("ID_") else exhibit_id


@router.get("/rag-exhibits")
async def get_rag_exhibits(authorized: bool = Depends(verify_token)):
    """Get all RAG exhibits."""
    metadata = _load_exhibit_metadata()
    exhibits_data = metadata.get("exhibits", {})
    
    exhibits = []
    for exhibit_id, data in sorted(exhibits_data.items()):
        num = _id_to_num(exhibit_id)
        filename = f"ESER_DATA_{num}.txt"
        filepath = os.path.join(TED_MUSEUM_DIR, filename)
        
        # Get content size
        try:
            content = open(filepath, 'r', encoding='utf-8').read()
            size = len(content)
        except:
            content = ""
            size = 0
        
        exhibits.append({
            "exhibit_id": exhibit_id,
            "title": data.get("title", ""),
            "qr": data.get("qr", ""),
            "category": data.get("category", ""),
            "image": data.get("image", ""),
            "content_file": data.get("content_file", filename),
            "size": size
        })
    
    return {
        "exhibits": exhibits, 
        "total": len(exhibits),
        "next_id": _get_next_id()
    }


@router.get("/rag-exhibits/{exhibit_id}")
async def get_rag_exhibit_content(exhibit_id: str, authorized: bool = Depends(verify_token)):
    """Get content of a specific RAG exhibit."""
    num = _id_to_num(exhibit_id)
    filename = f"ESER_DATA_{num}.txt"
    filepath = os.path.join(TED_MUSEUM_DIR, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Exhibit not found")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Get metadata
    metadata = _load_exhibit_metadata()
    meta = metadata.get("exhibits", {}).get(exhibit_id, {})
    
    return {
        "exhibit_id": exhibit_id,
        "content": content,
        "qr": meta.get("qr", ""),
        "title": meta.get("title", ""),
        "category": meta.get("category", ""),
        "image": meta.get("image", "")
    }


class RAGExhibitUpdate(BaseModel):
    content: str
    qr: str = ""
    title: str = ""
    category: str = ""
    image: str = ""


@router.put("/rag-exhibits/{exhibit_id}")
async def update_rag_exhibit(exhibit_id: str, data: RAGExhibitUpdate, authorized: bool = Depends(verify_token)):
    """Update RAG exhibit content and metadata."""
    num = _id_to_num(exhibit_id)
    filename = f"ESER_DATA_{num}.txt"
    filepath = os.path.join(TED_MUSEUM_DIR, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Exhibit not found")
    
    # Update content file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(data.content)
    
    # Update metadata
    metadata = _load_exhibit_metadata()
    if exhibit_id not in metadata["exhibits"]:
        metadata["exhibits"][exhibit_id] = {}
    
    if data.title:
        metadata["exhibits"][exhibit_id]["title"] = data.title
    if data.qr:
        metadata["exhibits"][exhibit_id]["qr"] = data.qr
    if data.category:
        metadata["exhibits"][exhibit_id]["category"] = data.category
    if data.image:
        metadata["exhibits"][exhibit_id]["image"] = data.image
    metadata["exhibits"][exhibit_id]["content_file"] = filename
    _save_exhibit_metadata(metadata)
    
    return {"status": "ok", "message": "Content updated. Run RAG ingestion to update embeddings."}


class RAGExhibitCreate(BaseModel):
    qr: str = ""
    content: str
    title: str = ""
    category: str = ""


@router.post("/rag-exhibits")
async def create_rag_exhibit(data: RAGExhibitCreate, authorized: bool = Depends(verify_token)):
    """Create a new RAG exhibit with auto-assigned ID."""
    # Get next available ID
    exhibit_id = _get_next_id()
    num = _id_to_num(exhibit_id)
    
    filename = f"ESER_DATA_{num}.txt"
    filepath = os.path.join(TED_MUSEUM_DIR, filename)
    
    if os.path.exists(filepath):
        raise HTTPException(status_code=400, detail="Exhibit already exists")
    
    os.makedirs(TED_MUSEUM_DIR, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(data.content)
    
    # Update metadata
    metadata = _load_exhibit_metadata()
    metadata["exhibits"][exhibit_id] = {
        "title": data.title or data.content.split('\n')[0].strip()[:100],
        "qr": data.qr or f"qr_{num}",  # Default QR if not provided
        "category": data.category,
        "image": "",
        "content_file": filename
    }
    _save_exhibit_metadata(metadata)
    
    return {
        "status": "ok", 
        "message": "Exhibit created. Run RAG ingestion to add to vector DB.",
        "exhibit_id": exhibit_id
    }


@router.delete("/rag-exhibits/{exhibit_id}")
async def delete_rag_exhibit(exhibit_id: str, authorized: bool = Depends(verify_token)):
    """Delete a RAG exhibit and its associated image."""
    num = _id_to_num(exhibit_id)
    filename = f"ESER_DATA_{num}.txt"
    filepath = os.path.join(TED_MUSEUM_DIR, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Exhibit not found")
    
    # Delete the text file
    os.remove(filepath)
    
    # Delete associated image (FOTO_XX.*)
    image_deleted = False
    for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
        img_path = os.path.join(EXHIBITS_IMG_DIR, f"FOTO_{num}{ext}")
        if os.path.exists(img_path):
            os.remove(img_path)
            image_deleted = True
            break
    
    # Remove from metadata
    metadata = _load_exhibit_metadata()
    if exhibit_id in metadata.get("exhibits", {}):
        del metadata["exhibits"][exhibit_id]
        _save_exhibit_metadata(metadata)
    
    msg = "Exhibit deleted."
    if image_deleted:
        msg += " Image also deleted."
    msg += " Run RAG ingestion to update vector DB."
    
    return {"status": "ok", "message": msg}


@router.delete("/delete-image/{exhibit_id}")
async def delete_exhibit_image(exhibit_id: str, authorized: bool = Depends(verify_token)):
    """Delete only the image for an exhibit."""
    num = _id_to_num(exhibit_id)
    
    # Find and delete the image file
    exhibits_img_dir = os.path.join(WEB_DIR, "static", "exhibits")
    image_deleted = False
    
    for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
        img_path = os.path.join(exhibits_img_dir, f"FOTO_{num}{ext}")
        if os.path.exists(img_path):
            os.remove(img_path)
            image_deleted = True
            break
    
    # Update metadata to clear image field
    metadata = _load_exhibit_metadata()
    if exhibit_id in metadata.get("exhibits", {}):
        metadata["exhibits"][exhibit_id]["image"] = ""
        _save_exhibit_metadata(metadata)
    
    if image_deleted:
        return {"status": "ok", "message": "Image deleted."}
    else:
        return {"status": "ok", "message": "No image found to delete."}



# ========== RAG INGESTION ==========
class IngestionRequest(BaseModel):
    clear: bool = True


@router.post("/rag-ingest")
async def run_rag_ingestion(data: IngestionRequest, authorized: bool = Depends(verify_token)):
    """Run RAG ingestion to update vector database."""
    try:
        # Import here to avoid circular imports
        import sys
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        from ingestion.ingest_ted import ingest_all
        
        # Run ingestion
        ingest_all(clear=data.clear)
        
        return {
            "status": "ok",
            "message": f"RAG ingestion completed successfully. Clear={data.clear}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


# ========== EXHIBIT METADATA ==========
METADATA_FILE = os.path.join(DATA_DIR, "exhibit_metadata.json")


def load_metadata():
    """Load exhibit metadata from file."""
    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"categories": [], "exhibits": {}}


def save_metadata(data):
    """Save exhibit metadata to file."""
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@router.get("/exhibit-categories")
async def get_categories(authorized: bool = Depends(verify_token)):
    """Get available exhibit categories."""
    data = load_metadata()
    return {"categories": data.get("categories", [])}


@router.get("/exhibit-metadata")
async def get_all_metadata(authorized: bool = Depends(verify_token)):
    """Get all exhibit metadata."""
    data = load_metadata()
    return data


@router.get("/exhibit-metadata/{qr_id}")
async def get_exhibit_metadata(qr_id: str, authorized: bool = Depends(verify_token)):
    """Get metadata for a specific exhibit (requires auth)."""
    data = load_metadata()
    exhibits = data.get("exhibits", {})
    
    if qr_id not in exhibits:
        return {"qr_id": qr_id, "title": "", "category": "", "image": ""}
    
    return {"qr_id": qr_id, **exhibits[qr_id]}


@router.get("/exhibit-image/{qr_id}")
async def get_exhibit_image(qr_id: str):
    """Get exhibit image URL (public, no auth required)."""
    data = load_metadata()
    exhibits = data.get("exhibits", {})
    
    if qr_id not in exhibits:
        return {"qr_id": qr_id, "image": "", "title": ""}
    
    exhibit = exhibits[qr_id]
    return {"qr_id": qr_id, "image": exhibit.get("image", ""), "title": exhibit.get("title", "")}


class ExhibitMetadataUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    image: Optional[str] = None


@router.put("/exhibit-metadata/{qr_id}")
async def update_exhibit_metadata(
    qr_id: str, 
    update: ExhibitMetadataUpdate,
    authorized: bool = Depends(verify_token)
):
    """Update metadata for a specific exhibit."""
    data = load_metadata()
    
    if "exhibits" not in data:
        data["exhibits"] = {}
    
    if qr_id not in data["exhibits"]:
        data["exhibits"][qr_id] = {"title": "", "category": "", "image": ""}
    
    # Update fields if provided
    if update.title is not None:
        data["exhibits"][qr_id]["title"] = update.title
    if update.category is not None:
        data["exhibits"][qr_id]["category"] = update.category
    if update.image is not None:
        data["exhibits"][qr_id]["image"] = update.image
    
    save_metadata(data)
    
    return {"status": "ok", "message": "Metadata updated", "data": data["exhibits"][qr_id]}


# ========== IMAGE UPLOAD ==========
STATIC_DIR = os.path.join(WEB_DIR, "static", "exhibits")


class ImageUpload(BaseModel):
    image_data: str  # Base64 encoded image
    filename: Optional[str] = None


@router.post("/upload-image")
async def upload_image(data: ImageUpload, authorized: bool = Depends(verify_token)):
    """Upload an image (Base64) and return the URL."""
    try:
        # Ensure directory exists
        os.makedirs(STATIC_DIR, exist_ok=True)
        
        # Parse base64 data
        image_data = data.image_data
        if "," in image_data:
            # Handle "data:image/png;base64,..." format
            header, image_data = image_data.split(",", 1)
            # Extract extension from header
            if "png" in header:
                ext = "png"
            elif "jpeg" in header or "jpg" in header:
                ext = "jpg"
            elif "gif" in header:
                ext = "gif"
            elif "webp" in header:
                ext = "webp"
            else:
                ext = "png"
        else:
            ext = "png"
        
        # Generate filename
        if data.filename:
            # Sanitize filename
            safe_name = "".join(c for c in data.filename if c.isalnum() or c in "._-")
            filename = f"{safe_name}.{ext}"
        else:
            filename = f"{uuid.uuid4().hex[:12]}.{ext}"
        
        # Decode and save
        image_bytes = base64.b64decode(image_data)
        filepath = os.path.join(STATIC_DIR, filename)
        
        with open(filepath, "wb") as f:
            f.write(image_bytes)
        
        # Return URL path
        url = f"/static/exhibits/{filename}"
        
        return {"status": "ok", "url": url, "filename": filename}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}")
