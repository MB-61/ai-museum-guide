"""

  uv run python ingestion/ingest.py --exhibit mona_lisa --source data/curated/mona_lisa.txt
"""
import argparse, os, uuid
from app.db.chroma import get_collection

def upsert_text(exhibit_id: str, text_path: str, chunk_size=600, overlap=100):
    with open(text_path, "r", encoding="utf-8") as f:
        text = f.read()
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size-overlap)]
    col = get_collection()
    # metadata: exhibit_id + source file
    ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = [{"exhibit_id": exhibit_id, "source": os.path.basename(text_path)} for _ in chunks]
    col.add(documents=chunks, metadatas=metadatas, ids=ids)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--exhibit", required=True)
    parser.add_argument("--source", required=True)
    args = parser.parse_args()
    upsert_text(args.exhibit, args.source)
    print("Ingestion complete.")
