"""Token usage tracking service."""
import json
import os
from datetime import datetime, date
from typing import Dict, Any
from threading import Lock

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "token_usage.json")
_lock = Lock()


def _ensure_data_file():
    """Ensure data file exists."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"daily": {}, "total": {"input": 0, "output": 0, "requests": 0}}, f)


def _load_data() -> Dict[str, Any]:
    """Load token data from file."""
    _ensure_data_file()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"daily": {}, "total": {"input": 0, "output": 0, "requests": 0}}


def _save_data(data: Dict[str, Any]):
    """Save token data to file."""
    _ensure_data_file()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def track_tokens(input_tokens: int, output_tokens: int):
    """Track token usage for a request."""
    with _lock:
        data = _load_data()
        today = str(date.today())
        
        # Update daily stats
        if today not in data["daily"]:
            data["daily"][today] = {"input": 0, "output": 0, "requests": 0}
        
        data["daily"][today]["input"] += input_tokens
        data["daily"][today]["output"] += output_tokens
        data["daily"][today]["requests"] += 1
        
        # Update total stats
        data["total"]["input"] += input_tokens
        data["total"]["output"] += output_tokens
        data["total"]["requests"] += 1
        
        _save_data(data)


def get_token_stats() -> Dict[str, Any]:
    """Get token usage statistics."""
    data = _load_data()
    today = str(date.today())
    today_data = data["daily"].get(today, {"input": 0, "output": 0, "requests": 0})
    
    # Get last 7 days
    last_7_days = {}
    for i in range(7):
        d = date.today()
        d = date(d.year, d.month, d.day - i) if d.day > i else d
        day_str = str(d)
        if day_str in data["daily"]:
            last_7_days[day_str] = data["daily"][day_str]
    
    return {
        "today": today_data,
        "total": data["total"],
        "daily_history": last_7_days,
        # Gemini 2.5 Flash pricing (per 1M tokens)
        # Input: $0.15 / 1M = $0.00000015 per token
        # Output: $0.60 / 1M = $0.0000006 per token
        "estimated_cost_usd": round((data["total"]["input"] * 0.00000015 + data["total"]["output"] * 0.0000006), 4)
    }


def reset_stats():
    """Reset all statistics."""
    with _lock:
        _save_data({"daily": {}, "total": {"input": 0, "output": 0, "requests": 0}})
