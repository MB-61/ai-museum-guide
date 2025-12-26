"""Admin panel API endpoints."""
import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel

from app.services import token_tracker, stats_service
from app.services.key_rotation import get_key_status, GEMINI_API_KEYS

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
async def get_dashboard(authorized: bool = Depends(verify_token)):
    """Get dashboard overview."""
    stats = stats_service.get_stats()
    tokens = token_tracker.get_token_stats()
    
    # Calculate today's cost
    today_input = tokens["today"]["input"]
    today_output = tokens["today"]["output"]
    today_cost = round((today_input * 0.00000015 + today_output * 0.0000006), 4)
    
    return {
        "today_scans": stats["today"]["scans"],
        "today_chats": stats["today"]["chats"],
        "total_sessions": stats["total_sessions"],
        "unique_visitors": stats.get("unique_visitors", 0),
        "total_tokens": tokens["total"]["input"] + tokens["total"]["output"],
        "today_tokens": tokens["today"]["input"] + tokens["today"]["output"],
        "today_cost": today_cost,
        "total_cost": tokens["estimated_cost_usd"],
        "api_keys_count": len(GEMINI_API_KEYS) if GEMINI_API_KEYS else 0
    }


# ========== GREETINGS ==========
@router.get("/greetings/qr")
async def get_qr_greetings(authorized: bool = Depends(verify_token)):
    """Get QR mode greetings."""
    path = os.path.join(WEB_DIR, "data", "qrli_greeting.txt")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return {"content": f.read(), "path": path}
    except:
        return {"content": "", "path": path}


@router.put("/greetings/qr")
async def update_qr_greetings(data: GreetingUpdate, authorized: bool = Depends(verify_token)):
    """Update QR mode greetings."""
    path = os.path.join(WEB_DIR, "data", "qrli_greeting.txt")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(data.content)
    return {"status": "ok"}


@router.get("/greetings/general")
async def get_general_greetings(authorized: bool = Depends(verify_token)):
    """Get general mode greetings."""
    path = os.path.join(WEB_DIR, "data", "qrsiz_greeting.txt")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return {"content": f.read(), "path": path}
    except:
        return {"content": "", "path": path}


@router.put("/greetings/general")
async def update_general_greetings(data: GreetingUpdate, authorized: bool = Depends(verify_token)):
    """Update general mode greetings."""
    path = os.path.join(WEB_DIR, "data", "qrsiz_greeting.txt")
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
    # Mask keys for security
    masked_keys = []
    for i, key_info in enumerate(status.get("keys", [])):
        masked_keys.append({
            "index": i,
            "key_preview": key_info.get("key", "")[:8] + "..." if key_info.get("key") else "N/A",
            "status": key_info.get("status", "unknown"),
            "last_used": key_info.get("last_used")
        })
    
    return {
        "current_index": status.get("current_index", 0),
        "total_keys": len(GEMINI_API_KEYS) if GEMINI_API_KEYS else 0,
        "keys": masked_keys
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
QR_MAPPING_FILE = os.path.join(DATA_DIR, "mappings", "qr_to_exhibit.json")


def _load_qr_mapping():
    """Load QR to exhibit mapping."""
    try:
        with open(QR_MAPPING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def _save_qr_mapping(mapping):
    """Save QR to exhibit mapping."""
    os.makedirs(os.path.dirname(QR_MAPPING_FILE), exist_ok=True)
    with open(QR_MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)


@router.get("/rag-exhibits")
async def get_rag_exhibits(authorized: bool = Depends(verify_token)):
    """Get all RAG exhibits from ted_museum folder."""
    mapping = _load_qr_mapping()
    reverse_mapping = {v: k for k, v in mapping.items()}
    
    exhibits = []
    if os.path.exists(TED_MUSEUM_DIR):
        for filename in sorted(os.listdir(TED_MUSEUM_DIR)):
            if filename.endswith('.txt'):
                exhibit_id = filename.replace('.txt', '')
                filepath = os.path.join(TED_MUSEUM_DIR, filename)
                
                # Read first line as title
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        title = content.split('\n')[0].strip() if content else exhibit_id
                except:
                    title = exhibit_id
                    content = ""
                
                qr_id = reverse_mapping.get(exhibit_id, "")
                exhibits.append({
                    "exhibit_id": exhibit_id,
                    "title": title,
                    "qr_id": qr_id,
                    "filename": filename,
                    "size": len(content)
                })
    
    return {"exhibits": exhibits, "total": len(exhibits)}


@router.get("/rag-exhibits/{exhibit_id}")
async def get_rag_exhibit_content(exhibit_id: str, authorized: bool = Depends(verify_token)):
    """Get content of a specific RAG exhibit."""
    filepath = os.path.join(TED_MUSEUM_DIR, f"{exhibit_id}.txt")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Exhibit not found")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    mapping = _load_qr_mapping()
    reverse_mapping = {v: k for k, v in mapping.items()}
    qr_id = reverse_mapping.get(exhibit_id, "")
    
    return {
        "exhibit_id": exhibit_id,
        "content": content,
        "qr_id": qr_id
    }


class RAGExhibitUpdate(BaseModel):
    content: str
    qr_id: str = ""


@router.put("/rag-exhibits/{exhibit_id}")
async def update_rag_exhibit(exhibit_id: str, data: RAGExhibitUpdate, authorized: bool = Depends(verify_token)):
    """Update RAG exhibit content and QR mapping."""
    filepath = os.path.join(TED_MUSEUM_DIR, f"{exhibit_id}.txt")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Exhibit not found")
    
    # Update content
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(data.content)
    
    # Update QR mapping if provided
    if data.qr_id:
        mapping = _load_qr_mapping()
        # Remove old mapping for this exhibit
        old_qr = None
        for qr, ex in mapping.items():
            if ex == exhibit_id:
                old_qr = qr
                break
        if old_qr:
            del mapping[old_qr]
        # Add new mapping
        mapping[data.qr_id] = exhibit_id
        _save_qr_mapping(mapping)
    
    return {"status": "ok", "message": "Content updated. Run RAG ingestion to update embeddings."}


class RAGExhibitCreate(BaseModel):
    exhibit_id: str
    content: str
    qr_id: str = ""


@router.post("/rag-exhibits")
async def create_rag_exhibit(data: RAGExhibitCreate, authorized: bool = Depends(verify_token)):
    """Create a new RAG exhibit."""
    filepath = os.path.join(TED_MUSEUM_DIR, f"{data.exhibit_id}.txt")
    if os.path.exists(filepath):
        raise HTTPException(status_code=400, detail="Exhibit already exists")
    
    os.makedirs(TED_MUSEUM_DIR, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(data.content)
    
    # Update QR mapping if provided
    if data.qr_id:
        mapping = _load_qr_mapping()
        mapping[data.qr_id] = data.exhibit_id
        _save_qr_mapping(mapping)
    
    return {"status": "ok", "message": "Exhibit created. Run RAG ingestion to add to vector DB."}


@router.delete("/rag-exhibits/{exhibit_id}")
async def delete_rag_exhibit(exhibit_id: str, authorized: bool = Depends(verify_token)):
    """Delete a RAG exhibit."""
    filepath = os.path.join(TED_MUSEUM_DIR, f"{exhibit_id}.txt")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Exhibit not found")
    
    os.remove(filepath)
    
    # Remove from QR mapping
    mapping = _load_qr_mapping()
    qr_to_remove = None
    for qr, ex in mapping.items():
        if ex == exhibit_id:
            qr_to_remove = qr
            break
    if qr_to_remove:
        del mapping[qr_to_remove]
        _save_qr_mapping(mapping)
    
    return {"status": "ok", "message": "Exhibit deleted. Run RAG ingestion to update vector DB."}


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



