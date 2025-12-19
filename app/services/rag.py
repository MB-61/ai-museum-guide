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


def run_rag(
    question: str,
    qr_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> Tuple[str, List[str]]:
    """
    Merkez RAG entry point with memory support.

    - qr_id varsa -> resolve_qr ile exhibit_id'ye çevir
    - qr_id yoksa -> global arama
    - user_id varsa -> hafıza sistemi aktif
    """

    exhibit_id: Optional[str] = None
    if qr_id is not None:
        exhibit_id = resolve_qr(qr_id)
        # Record exhibit visit if we have a user
        if user_id and exhibit_id:
            add_visited_exhibit(user_id, exhibit_id)

    # Retrieve relevant chunks
    chunks = retrieve(question, exhibit_id=exhibit_id, k=4)

    # Build context from chunks
    context = "\n---\n".join(d for d, _m in chunks) if chunks else ""

    # Get memory context if user_id provided
    memory_context = ""
    if user_id:
        memory_context = get_memory_context(user_id)

    # Build prompt with memory
    system = "You are a museum guide. Use only the provided context. Respond in the same language as the question."
    prompt = build_prompt(context, question, memory_context)

    # Get LLM response
    answer = call_llm(system_prompt=system, user_prompt=prompt)
    sources = [m.get("source") for _d, m in chunks if m and m.get("source")]

    # Extract and save important data if user_id provided
    if user_id:
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
