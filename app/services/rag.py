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
    is_museum_stats_question,
    is_museum_overview_question,
    QuestionType
)
from app.services.memory_service import enhance_question_with_context
from app.services.exhibit_info_service import get_exhibit_stats_context, get_museum_info_context
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
        from app.utils.ids import get_exhibit_by_qr
        
        result = get_exhibit_by_qr(qr_id)
        if result:
            id_str, metadata = result
            # Convert ID_XX to ESER_DATA_XX for retriever
            num = id_str.replace("ID_", "") if id_str.startswith("ID_") else id_str
            exhibit_id = f"ESER_DATA_{num}"
            is_exhibit_mode = True
            
            # exhibit_id'den okunabilir isim oluştur
            exhibit_name = metadata.get("title", id_str)
        else:
            # Fallback (log warning ideally)
            pass

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
    
    # Müze istatistik sorusu ise, eser sayısı bilgisini context'e ekle
    if is_museum_stats_question(enhanced_question):
        stats_context = get_exhibit_stats_context()
        full_context = f"{stats_context}\n\n---\n\n{full_context}"
    
    # Müze genel bilgi sorusu ise, müze özetini context'e ekle
    if is_museum_overview_question(enhanced_question):
        museum_context = get_museum_info_context()
        full_context = f"{museum_context}\n\n---\n\n{full_context}"

    # Adaptif prompt oluştur
    prompt, detected_type = build_adaptive_prompt(
        context=full_context,
        question=enhanced_question,  # Zenginleştirilmiş soru
        exhibit_title=conv_context.current_exhibit
    )
    
    # System prompt - soru tipine göre
    type_hints = {
        QuestionType.SHORT: "Kısa ve öz cevap ver (1-2 cümle).",
        QuestionType.MEDIUM: "Bilgilendirici cevap ver (3-5 cümle).",
        QuestionType.DETAILED: "Detaylı ve zengin anlatım sun (5+ cümle).",
        QuestionType.LIST: "Liste formatında cevap ver."
    }
    
    system = f"Sen TED Kolej Müzesi rehberisin. {type_hints.get(detected_type, '')} Önceki konuşmayı dikkate al. Türkçe cevap ver."

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
