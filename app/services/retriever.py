from typing import Optional, List, Tuple, Dict, Any
from app.db.chroma import get_collection


def retrieve(query: str, exhibit_id: Optional[str], k: int = 4):
    """
    Chroma'dan context döndürür.

    - exhibit_id doluysa  -> sadece o sergiye ait chunk'lar
    - exhibit_id None ise -> global arama (where filtresi yok)
    """
    col = get_collection()

    if exhibit_id:
        res = col.query(
            query_texts=[query],
            n_results=k,
            where={"exhibit_id": exhibit_id},
        )
    else:
        res = col.query(
            query_texts=[query],
            n_results=k,
        )

    docs = res.get("documents", [[]])[0]
    metadatas = res.get("metadatas", [[]])[0]
    return list(zip(docs, metadatas))
