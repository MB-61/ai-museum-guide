# -*- coding: utf-8 -*-
"""
RAG Service - Retrieval Augmented Generation with Memory
"""

from typing import List, Optional, Tuple

from app.services.llm import call_llm
from app.services.retriever import retrieve
from app.services.prompts import (
    build_adaptive_prompt,
    detect_question_type,
    QuestionType
)
from app.services.memory_service import enhance_question_with_context
from app.utils.ids import resolve_qr


def get_chunk_count(question_type: QuestionType, is_exhibit_mode: bool) -> int:
    """Soru tipine göre çekilecek chunk sayısını belirle."""
    if question_type == QuestionType.DETAILED:
        return 10  # Detaylı sorular için daha fazla context
    elif question_type == QuestionType.LIST:
        return 12  # Liste için tüm eserleri kapsamaya çalış
    elif is_exhibit_mode:
        return 4   # Eser modu için yeterli
    else:
        return 6   # Genel sorular için orta düzey


def build_system_prompt(question_type: QuestionType, exhibit_name: Optional[str] = None) -> str:
    """
    Soru tipine ve moda göre gelişmiş system prompt oluştur.
    """
    base = "Sen TED Kolej Müzesi'nin deneyimli dijital rehberisin."
    
    # Soru tipine göre uzunluk talimatı
    length_hints = {
        QuestionType.SHORT: "Kısa ve öz cevap ver (1-2 cümle). Doğrudan yanıtla.",
        QuestionType.MEDIUM: "Bilgilendirici cevap ver (2-4 cümle). Ana bilgi + kısa bağlam.",
        QuestionType.DETAILED: "Detaylı ve zengin anlatım sun (4-7 cümle). Tarihi bağlam, önem ve ilginç detayları dahil et.",
        QuestionType.LIST: "Liste formatında cevap ver. Her madde için kısa açıklama ekle."
    }
    
    parts = [base, length_hints.get(question_type, length_hints[QuestionType.MEDIUM])]
    
    # Eser modu için ek bağlam
    if exhibit_name:
        parts.append(f"Ziyaretçi şu an '{exhibit_name}' eserinin önünde. Bu eseri önceliklendir.")
    
    # Genel kurallar
    parts.append("Önceki konuşmayı dikkate al. Türkçe cevap ver. Sadece verilen bağlamdaki bilgileri kullan.")
    
    return " ".join(parts)


def run_rag(
    question: str, 
    qr_id: Optional[str] = None,
    history: List = None
) -> Tuple[str, List[str]]:
    """
    Merkez RAG entry point - Akıllı bellek sistemi ile.

    - Memory service ile referans çözümleme
    - Soru tipini algılar (SHORT/MEDIUM/DETAILED/LIST)
    - Tipe göre chunk sayısı ve prompt ayarlar
    """
    if history is None:
        history = []

    exhibit_id: Optional[str] = None
    exhibit_name: Optional[str] = None
    is_exhibit_mode = False
    
    if qr_id is not None:
        exhibit_id = resolve_qr(qr_id)
        is_exhibit_mode = True
        # exhibit_id'den okunabilir isim oluştur
        if exhibit_id:
            exhibit_name = exhibit_id.replace("_", " ").replace("-", " ").title()

    # Memory service ile soruyu zenginleştir
    enhanced_question, history_context, conv_context = enhance_question_with_context(
        question=question,
        history=history,
        qr_id=qr_id,
        exhibit_name=exhibit_name
    )
    
    # Zenginleştirilmiş soruyla soru tipini algıla
    question_type = detect_question_type(enhanced_question)
    
    # Soru tipine göre chunk sayısını belirle
    k = get_chunk_count(question_type, is_exhibit_mode)
    
    # Retrieval - zenginleştirilmiş soruyla
    chunks = retrieve(enhanced_question, exhibit_id=exhibit_id, k=k)

    # Context derleme
    rag_context = "\n---\n".join(d for d, _m in chunks) if chunks else ""
    
    # Konuşma geçmişini ekle
    if history_context:
        full_context = f"{history_context}\n\n---\n\nİLGİLİ BİLGİLER:\n{rag_context}"
    else:
        full_context = rag_context

    # Adaptif prompt oluştur
    prompt, detected_type = build_adaptive_prompt(
        context=full_context,
        question=enhanced_question,  # Zenginleştirilmiş soru
        exhibit_title=conv_context.current_exhibit
    )
    
    # Gelişmiş system prompt
    system = build_system_prompt(detected_type, conv_context.current_exhibit)

    answer = call_llm(system_prompt=system, user_prompt=prompt)
    sources = [m.get("source") for _d, m in chunks if m and m.get("source")]

    return answer, sources


class RAGService:
    """
    Eski kodla geriye dönük uyumluluk için bırakıldı.
    """

    def answer(self, qr_id: str, question: str):
        answer, sources = run_rag(question=question, qr_id=qr_id)
        return {"answer": answer, "sources": sources}
