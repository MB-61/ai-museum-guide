import json, os

def resolve_qr(qr_id: str) -> str:
    path = os.path.join("data", "mappings", "qr_to_exhibit.json")
    with open(path, "r", encoding="utf-8") as f:
        m = json.load(f)
    return m.get(qr_id, qr_id)  # fall back to same id
