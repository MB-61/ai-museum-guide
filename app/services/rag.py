from typing import List, Optional, Tuple

from app.services.llm import call_llm
from app.services.retriever import retrieve
from app.services.prompts import build_prompt
from app.utils.ids import resolve_qr
from app.services.memory_service import (
    get_memory_context,
    extract_important_data,
    update_memory,
    add_visited_exhibit,
)
from app.services.conversation_history import (
    get_conversation_history,
    add_message,
    format_history_for_prompt,
)
from app.services.recommendations import (
    is_comparison_query,
    format_recommendations_context,
)


def run_rag(
    question: str,
    qr_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> Tuple[str, List[str]]:
    """
    Merkez RAG entry point with memory, conversation history, and recommendations.

    - qr_id varsa -> resolve_qr ile exhibit_id'ye çevir
    - qr_id yoksa -> global arama
    - user_id varsa -> hafıza sistemi + sohbet geçmişi aktif
    - karşılaştırma sorusu -> diğer eserleri de dahil et
    """

    exhibit_id: Optional[str] = None
    if qr_id is not None:
        exhibit_id = resolve_qr(qr_id)
        # Record exhibit visit if we have a user
        if user_id and exhibit_id:
            add_visited_exhibit(user_id, exhibit_id)

    # Retrieve relevant chunks for current exhibit
    chunks = retrieve(question, exhibit_id=exhibit_id, k=4)

    # Build context from chunks
    context = "\n---\n".join(d for d, _m in chunks) if chunks else ""

    # Check if user mentions another artwork by name OR asks comparison question
    # If so, add context from related exhibits
    from app.services.recommendations import find_mentioned_exhibits
    mentioned = find_mentioned_exhibits(question, exhibit_id)
    if mentioned or is_comparison_query(question):
        recommendations_context = format_recommendations_context(question, exhibit_id)
        context += recommendations_context

    # Get memory context and conversation history if user_id provided
    memory_context = ""
    history_context = ""
    if user_id:
        memory_context = get_memory_context(user_id)
        history_context = format_history_for_prompt(user_id, max_messages=6)
        # Add user's current question to history
        add_message(user_id, "user", question)

    # Get exhibit name for system prompt
    from app.services.recommendations import EXHIBIT_NAMES
    current_exhibit_name = EXHIBIT_NAMES.get(exhibit_id, exhibit_id) if exhibit_id else "bilinmeyen eser"

    # Build prompt with memory and history
    system = f"""You are a museum guide. Use ONLY the provided context to answer.
The visitor is currently viewing: "{current_exhibit_name}"

IMPORTANT RULES:
1. If the visitor asks about a DIFFERENT artwork that is NOT in your context, politely redirect them:
   "Şu anda {current_exhibit_name} eserini inceliyorsunuz. Lütfen bu eserle ilgili sorular sorun. Diğer eserler için o eserin QR kodunu tarayabilirsiniz."
2. When asked about similar artworks or comparisons, use the 'Related artworks' section if available.
3. Respond in the same language as the question.
4. Be helpful and friendly."""
    prompt = build_prompt(context, question, memory_context, history_context)

    # Get LLM response
    answer = call_llm(system_prompt=system, user_prompt=prompt)
    sources = [m.get("source") for _d, m in chunks if m and m.get("source")]

    # Save assistant response to history
    if user_id:
        add_message(user_id, "assistant", answer)
        # Extract and save important data
        extraction = extract_important_data(question, answer)
        if extraction.is_important:
            update_memory(user_id, extraction)

    return answer, sources


class RAGService:
    """
    Eski kodla geriye dönük uyumluluk için bırakıldı.
    Yeni kod doğrudan run_rag() kullanmalı.
    """

    def answer(self, qr_id: str, question: str):
        answer, sources = run_rag(question=question, qr_id=qr_id)
        return {"answer": answer, "sources": sources}
