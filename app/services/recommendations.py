"""
Recommendation Service for AI Museum Guide

Provides cross-exhibit search and similarity recommendations.
When a user asks "which artwork is similar?", this service searches
across ALL exhibits to find relevant matches.
"""

from typing import List, Tuple, Optional
from app.db.chroma import get_collection


# Keywords that indicate a cross-exhibit query
COMPARISON_KEYWORDS = [
    "benzer", "benziyor", "benzet", "karşılaştır", 
    "diğer eser", "başka eser", "öneri", "öner",
    "similar", "compare", "recommend", "like this",
    "aynı", "farklı", "ilişki", "bağlantı",
    "hangi eser", "which artwork", "other paintings"
]


def is_comparison_query(question: str) -> bool:
    """
    Check if the question is asking for comparison or recommendation.
    """
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in COMPARISON_KEYWORDS)


def get_related_exhibits(
    question: str, 
    current_exhibit_id: Optional[str] = None,
    k: int = 3
) -> List[Tuple[str, str, str]]:
    """
    Search across ALL exhibits to find related artworks.
    
    Returns list of (exhibit_id, content_snippet, source_file) tuples.
    Excludes the current exhibit from results.
    """
    col = get_collection()
    
    # Search across all exhibits
    res = col.query(
        query_texts=[question],
        n_results=k * 2,  # Get more results to filter
    )
    
    docs = res.get("documents", [[]])[0]
    metadatas = res.get("metadatas", [[]])[0]
    
    results = []
    seen_exhibits = set()
    
    for doc, meta in zip(docs, metadatas):
        if not meta:
            continue
            
        exhibit_id = meta.get("exhibit_id", "")
        source = meta.get("source", "")
        
        # Skip current exhibit and duplicates
        if exhibit_id == current_exhibit_id:
            continue
        if exhibit_id in seen_exhibits:
            continue
            
        seen_exhibits.add(exhibit_id)
        
        # Take first 200 chars as snippet
        snippet = doc[:200] + "..." if len(doc) > 200 else doc
        results.append((exhibit_id, snippet, source))
        
        if len(results) >= k:
            break
    
    return results


def format_recommendations_context(
    question: str,
    current_exhibit_id: Optional[str] = None
) -> str:
    """
    Format related exhibits as additional context for the LLM.
    """
    if not is_comparison_query(question):
        return ""
    
    related = get_related_exhibits(question, current_exhibit_id, k=3)
    
    if not related:
        return ""
    
    lines = ["\n\nRelated artworks in the museum:"]
    for exhibit_id, snippet, source in related:
        # Convert exhibit_id to readable name
        name = exhibit_id.replace("_", " ").title()
        lines.append(f"\n- {name}: {snippet}")
    
    return "".join(lines)


# Mapping of exhibit_id to display name
EXHIBIT_NAMES = {
    "mona_lisa": "Mona Lisa",
    "yildizli_gece": "Yıldızlı Gece",
    "inci_kupeli_kiz": "İnci Küpeli Kız",
    "son_aksam_yemegi": "Son Akşam Yemeği",
    "ciglik": "Çığlık",
    "guernica": "Guernica",
    "venusun_dogusu": "Venüs'ün Doğuşu",
    "ademin_yaratilisi": "Adem'in Yaratılışı",
    "buyuk_dalga": "Büyük Dalga",
    "gece_devriyesi": "Gece Devriyesi",
    "bellegin_azmi": "Belleğin Azmi",
    "opucuk": "Öpücük",
    "su_zambaklari": "Su Zambakları",
    "avignonlu_kizlar": "Avignon'lu Kızlar",
    "amerikan_gotigi": "Amerikan Gotiği",
}
