"""Utility functions for exhibit ID management."""
import json
import os
from typing import Optional, Dict, Any, List


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
METADATA_FILE = os.path.join(DATA_DIR, "exhibit_metadata.json")


def _load_metadata() -> dict:
    """Load exhibit metadata."""
    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"categories": [], "exhibits": {}}


def _save_metadata(data: dict):
    """Save exhibit metadata."""
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_all_exhibits() -> Dict[str, Any]:
    """Get all exhibits from metadata."""
    return _load_metadata().get("exhibits", {})


def get_exhibit_by_id(exhibit_id: str) -> Optional[Dict[str, Any]]:
    """Get exhibit by ID (e.g., ID_01)."""
    return get_all_exhibits().get(exhibit_id)


def get_exhibit_by_qr(qr_code: str) -> Optional[tuple]:
    """Get exhibit by QR code. Returns (exhibit_id, exhibit_data) or None."""
    for exhibit_id, data in get_all_exhibits().items():
        if data.get("qr") == qr_code:
            return (exhibit_id, data)
    return None


def get_content_file_path(exhibit_id: str) -> str:
    """Get path to content file for an exhibit.
    
    Args:
        exhibit_id: Can be ID_XX format or just the number
    
    Returns:
        Full path to ESER_DATA_XX.txt
    """
    # Extract number
    if exhibit_id.startswith("ID_"):
        num = exhibit_id.replace("ID_", "")
    else:
        num = exhibit_id
    
    return os.path.join(DATA_DIR, "ted_museum", f"ESER_DATA_{num}.txt")


def get_next_available_id() -> str:
    """Get next available exhibit ID, filling gaps first.
    
    If ID_01 and ID_03 exist, returns ID_02.
    If ID_01, ID_02, ID_03 exist, returns ID_04.
    """
    exhibits = get_all_exhibits()
    
    # Extract all existing numbers
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


def id_to_number(exhibit_id: str) -> str:
    """Extract number from exhibit ID (ID_01 -> 01)."""
    if exhibit_id.startswith("ID_"):
        return exhibit_id.replace("ID_", "")
    return exhibit_id


def number_to_id(num: str) -> str:
    """Convert number to exhibit ID (01 -> ID_01)."""
    return f"ID_{num.zfill(2)}"


# Legacy function compatibility
def resolve_qr(qr_code: str) -> str:
    """Legacy: Resolve QR code to content file path."""
    result = get_exhibit_by_qr(qr_code)
    if result:
        exhibit_id, data = result
        return get_content_file_path(exhibit_id)
    
    return ""
