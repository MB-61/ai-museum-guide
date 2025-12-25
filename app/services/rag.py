from typing import List, Optional, Tuple

from app.services.llm import call_llm
from app.services.retriever import retrieve
from app.services.prompts import build_prompt, build_exhibit_prompt
from app.utils.ids import resolve_qr


def format_history(history: List) -> str:
    """Format conversation history for context"""
    if not history:
        return ""
    
    # Limit to last 5 messages to avoid context overflow
    recent = history[-5:] if len(history) > 5 else history
    
    lines = []
    for msg in recent:
        role = "Ziyaretçi" if msg.role == "user" else "Rehber"
        lines.append(f"{role}: {msg.content}")
    
    return "\n".join(lines)


def run_rag(
    question: str, 
    qr_id: Optional[str] = None,
    history: List = None
) -> Tuple[str, List[str]]:
    """
    Merkez RAG entry point.

    - qr_id varsa -> Eser modu (belirli eser hakkında, 4 chunk)
    - qr_id yoksa -> Genel mod (tüm müze, 8 chunk - eser listesi için daha fazla)
    - history: Önceki konuşmalar (son 5 mesaj saklanır)
    """
    if history is None:
        history = []

    exhibit_id: Optional[str] = None
    is_exhibit_mode = False
    
    if qr_id is not None:
        exhibit_id = resolve_qr(qr_id)
        is_exhibit_mode = True

    # Genel modda daha fazla chunk çek (eser listesi için)
    k = 4 if is_exhibit_mode else 8
    chunks = retrieve(question, exhibit_id=exhibit_id, k=k)

    # Context derleme
    context = "\n---\n".join(d for d, _m in chunks) if chunks else ""
    
    # Konuşma geçmişini ekle
    history_text = format_history(history)
    if history_text:
        context = f"ÖNCEKİ KONUŞMA:\n{history_text}\n\n---\n\nİLGİLİ BİLGİLER:\n{context}"

    # Mod'a göre farklı prompt kullan
    if is_exhibit_mode:
        prompt = build_exhibit_prompt(context, question)
        system = "Sen TED Kolej Müzesi rehberisin. Seçili eser hakkında detaylı bilgi ver. Önceki konuşmayı dikkate al. Türkçe cevap ver."
    else:
        prompt = build_prompt(context, question, is_exhibit_mode=False)
        system = "Sen TED Kolej Müzesi rehberisin. Tüm müze hakkında bilgi ver. Önceki konuşmayı dikkate al. Türkçe cevap ver."

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
