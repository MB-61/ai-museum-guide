"""
Recommendation Service for AI Museum Guide

Provides cross-exhibit search and similarity recommendations.
When a user asks "which artwork is similar?" or mentions another artwork by name,
this service searches across exhibits to find relevant matches.
"""

from typing import List, Tuple, Optional
from app.db.chroma import get_collection


# Mapping of exhibit_id to display name and aliases
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

# Alternative names/keywords for detecting artwork mentions
EXHIBIT_ALIASES = {
    "mona_lisa": ["mona lisa", "la gioconda", "gioconda"],
    "yildizli_gece": ["yıldızlı gece", "starry night", "yildizli gece"],
    "inci_kupeli_kiz": ["inci küpeli kız", "inci kupeli kiz", "pearl earring", "girl with pearl"],
    "son_aksam_yemegi": ["son akşam yemeği", "son aksam yemegi", "last supper", "ultima cena"],
    "ciglik": ["çığlık", "ciglik", "scream", "skrik"],
    "guernica": ["guernica"],
    "venusun_dogusu": ["venüs'ün doğuşu", "venusun dogusu", "birth of venus", "venüs"],
    "ademin_yaratilisi": ["adem'in yaratılışı", "ademin yaratilisi", "creation of adam"],
    "buyuk_dalga": ["büyük dalga", "buyuk dalga", "great wave", "kanagawa"],
    "gece_devriyesi": ["gece devriyesi", "night watch", "nachtwacht"],
    "bellegin_azmi": ["belleğin azmi", "bellegin azmi", "persistence of memory", "eriyen saatler"],
    "opucuk": ["öpücük", "opucuk", "the kiss", "klimt"],
    "su_zambaklari": ["su zambakları", "su zambaklari", "water lilies", "nympheas"],
    "avignonlu_kizlar": ["avignon'lu kızlar", "avignonlu kizlar", "demoiselles d'avignon"],
    "amerikan_gotigi": ["amerikan gotiği", "amerikan gotigi", "american gothic"],
}

# Keywords that indicate a cross-exhibit query
COMPARISON_KEYWORDS = [
    "benzer", "benziyor", "benzet", "karşılaştır", 
    "diğer eser", "başka eser", "öneri", "öner",
    "similar", "compare", "recommend", "like this",
    "aynı", "farklı", "ilişki", "bağlantı",
    "hangi eser", "which artwork", "other paintings"
]


def find_mentioned_exhibits(question: str, current_exhibit_id: Optional[str] = None) -> List[str]:
    """
    Find any exhibit names mentioned in the question.
    Returns list of exhibit_ids that are mentioned.
    """
    question_lower = question.lower()
    mentioned = []
    
    for exhibit_id, aliases in EXHIBIT_ALIASES.items():
        # Skip current exhibit
        if exhibit_id == current_exhibit_id:
            continue
        
        for alias in aliases:
            if alias in question_lower:
                if exhibit_id not in mentioned:
                    mentioned.append(exhibit_id)
                break
    
    return mentioned


def is_comparison_query(question: str) -> bool:
    """
    Check if the question is asking for comparison or recommendation.
    """
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in COMPARISON_KEYWORDS)


def get_exhibit_context(exhibit_id: str, k: int = 2) -> str:
    """
    Get context for a specific exhibit from ChromaDB.
    """
    col = get_collection()
    
    res = col.query(
        query_texts=[EXHIBIT_NAMES.get(exhibit_id, exhibit_id)],
        n_results=k,
        where={"exhibit_id": exhibit_id},
    )
    
    docs = res.get("documents", [[]])[0]
    if not docs:
        return ""
    
    return "\n".join(docs)


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
    
    This handles two cases:
    1. User mentions a specific artwork by name -> fetch that artwork's info
    2. User asks general comparison question -> search for related artworks
    """
    context_parts = []
    
    # Case 1: Check if user mentioned a specific artwork by name
    mentioned_exhibits = find_mentioned_exhibits(question, current_exhibit_id)
    
    if mentioned_exhibits:
        context_parts.append("\n\nInformation about mentioned artwork(s):")
        for exhibit_id in mentioned_exhibits:
            name = EXHIBIT_NAMES.get(exhibit_id, exhibit_id)
            exhibit_context = get_exhibit_context(exhibit_id)
            if exhibit_context:
                context_parts.append(f"\n\n{name}:\n{exhibit_context}")
    
    # Case 2: General comparison query -> search for related
    elif is_comparison_query(question):
        related = get_related_exhibits(question, current_exhibit_id, k=3)
        
        if related:
            context_parts.append("\n\nRelated artworks in the museum:")
            for exhibit_id, snippet, source in related:
                name = EXHIBIT_NAMES.get(exhibit_id, exhibit_id.replace("_", " ").title())
                context_parts.append(f"\n- {name}: {snippet}")
    
    return "".join(context_parts)

