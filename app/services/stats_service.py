"""Statistics tracking service."""
import json
import os
from datetime import datetime, date
from typing import Dict, Any, List
from threading import Lock

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "stats.json")
_lock = Lock()


def _ensure_data_file():
    """Ensure data file exists."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "qr_scans": {},
                "questions": [],
                "daily_activity": {},
                "sessions": 0,
                "unique_ips": []
            }, f)


def _load_data() -> Dict[str, Any]:
    """Load stats from file."""
    _ensure_data_file()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure unique_ips exists for backward compatibility
            if "unique_ips" not in data:
                data["unique_ips"] = []
            return data
    except:
        return {"qr_scans": {}, "questions": [], "daily_activity": {}, "sessions": 0, "unique_ips": []}


def _save_data(data: Dict[str, Any]):
    """Save stats to file."""
    _ensure_data_file()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def track_qr_scan(qr_id: str, exhibit_name: str = ""):
    """Track a QR code scan."""
    with _lock:
        data = _load_data()
        today = str(date.today())
        
        # Track QR scan counts
        if qr_id not in data["qr_scans"]:
            data["qr_scans"][qr_id] = {"count": 0, "name": exhibit_name}
        data["qr_scans"][qr_id]["count"] += 1
        if exhibit_name:
            data["qr_scans"][qr_id]["name"] = exhibit_name
        
        # Track daily activity
        if today not in data["daily_activity"]:
            data["daily_activity"][today] = {"scans": 0, "chats": 0}
        data["daily_activity"][today]["scans"] += 1
        
        _save_data(data)


def track_question(question: str):
    """Track a user question."""
    with _lock:
        data = _load_data()
        today = str(date.today())
        
        # Store last 100 questions
        data["questions"].insert(0, {
            "text": question[:200],
            "time": datetime.now().isoformat()
        })
        data["questions"] = data["questions"][:100]
        
        # Track daily chats
        if today not in data["daily_activity"]:
            data["daily_activity"][today] = {"scans": 0, "chats": 0}
        data["daily_activity"][today]["chats"] += 1
        
        _save_data(data)


def track_session(ip_address: str = None):
    """Track a new session, optionally by IP address."""
    with _lock:
        data = _load_data()
        data["sessions"] += 1
        
        # Track unique IPs
        if ip_address and ip_address not in data["unique_ips"]:
            data["unique_ips"].append(ip_address)
        
        _save_data(data)


def get_stats() -> Dict[str, Any]:
    """Get all statistics."""
    data = _load_data()
    today = str(date.today())
    today_activity = data["daily_activity"].get(today, {"scans": 0, "chats": 0})
    
    # Get top QR codes
    top_qr = sorted(data["qr_scans"].items(), key=lambda x: x[1]["count"], reverse=True)[:10]
    
    return {
        "today": today_activity,
        "total_sessions": data["sessions"],
        "unique_visitors": len(data.get("unique_ips", [])),
        "unique_ips": data.get("unique_ips", [])[:50],  # Last 50 IPs
        "total_scans": sum(q["count"] for q in data["qr_scans"].values()),
        "total_chats": sum(d.get("chats", 0) for d in data["daily_activity"].values()),
        "top_qr_codes": [{"qr_id": k, "name": v["name"], "count": v["count"]} for k, v in top_qr],
        "recent_questions": data["questions"][:20],
        "daily_history": dict(list(data["daily_activity"].items())[-7:])
    }


def reset_stats():
    """Reset all statistics."""
    with _lock:
        _save_data({"qr_scans": {}, "questions": [], "daily_activity": {}, "sessions": 0, "unique_ips": []})

