from typing import List, Optional, Tuple

from app.services.llm import call_llm
from app.services.retriever import retrieve
from app.services.prompts import build_prompt
from app.utils.ids import resolve_qr


def run_rag(question: str, qr_id: Optional[str] = None) -> Tuple[str, List[str]]:
    """
    Merkez RAG entry point.

    Yeni multi-agent yapıda Chat Agent sadece bunu çağıracak.
    Eski davranışı korumak için:
    - qr_id varsa -> resolve_qr ile exhibit_id'ye çevir
    - qr_id yoksa -> global arama (retriever içinde filtre olmadan query)
    """

    exhibit_id: Optional[str] = None
    if qr_id is not None:
        exhibit_id = resolve_qr(qr_id)

    # exhibit_id None ise retriever global arama yapacak (aşağıda retriever.py'yi güncelledik)
    chunks = retrieve(question, exhibit_id=exhibit_id, k=4)

    # Context derleme
    context = "\n---\n".join(d for d, _m in chunks) if chunks else ""

    # Eski kodundaki pattern'i koruyorum:
    # - system_prompt parametresine kısa bir sistem mesajı
    # - user_prompt içine build_prompt (SYSTEM_PROMPT + context + question)
    system = "You are a museum guide. Use only the provided context. Respond in the same language as the question."
    prompt = build_prompt(context, question)

    answer = call_llm(system_prompt=system, user_prompt=prompt)
    sources = [m.get("source") for _d, m in chunks if m and m.get("source")]

    return answer, sources


class RAGService:
    """
    Eski kodla geriye dönük uyumluluk için bırakıldı.
    Eğer bir yerde hâlâ RAGService().answer(...) kullanıyorsan çalışmaya devam eder.
    Yeni kod doğrudan run_rag() kullanmalı.
    """

    def answer(self, qr_id: str, question: str):
        answer, sources = run_rag(question=question, qr_id=qr_id)
        return {"answer": answer, "sources": sources}
