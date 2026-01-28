# -*- coding: utf-8 -*-
"""Azure TTS usage tracking service."""
import json
import os
from datetime import datetime, date
from typing import Dict, Any
from threading import Lock

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "tts_usage.json")
_lock = Lock()


def _ensure_data_file():
    """Ensure data file exists."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"daily": {}, "total": {"characters": 0, "requests": 0}}, f)


def _load_data() -> Dict[str, Any]:
    """Load TTS data from file."""
    _ensure_data_file()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"daily": {}, "total": {"characters": 0, "requests": 0}}


def _save_data(data: Dict[str, Any]):
    """Save TTS data to file."""
    _ensure_data_file()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def track_tts_usage(character_count: int):
    """Track TTS character usage for a request."""
    with _lock:
        data = _load_data()
        today = str(date.today())
        
        # Update daily stats
        if today not in data["daily"]:
            data["daily"][today] = {"characters": 0, "requests": 0}
        
        data["daily"][today]["characters"] += character_count
        data["daily"][today]["requests"] += 1
        
        # Update total stats
        data["total"]["characters"] += character_count
        data["total"]["requests"] += 1
        
        _save_data(data)


def get_tts_stats() -> Dict[str, Any]:
    """Get TTS usage statistics."""
    data = _load_data()
    today = str(date.today())
    today_data = data["daily"].get(today, {"characters": 0, "requests": 0})
    
    total_chars = data["total"]["characters"]
    
    # Azure Neural TTS pricing (Turkish - tr-TR-AhmetNeural)
    # Standard tier: $16 per 1M characters = $0.000016 per character
    # Neural tier: $16 per 1M characters = $0.000016 per character
    estimated_cost = total_chars * 0.000016
    
    return {
        "today": today_data,
        "total": data["total"],
        "daily_history": data["daily"],
        "estimated_cost_usd": round(estimated_cost, 4)
    }


def reset_tts_stats():
    """Reset all TTS statistics."""
    with _lock:
        _save_data({"daily": {}, "total": {"characters": 0, "requests": 0}})
