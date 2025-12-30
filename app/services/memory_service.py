# -*- coding: utf-8 -*-
"""
Memory Service - Akıllı Konuşma Belleği

Konuşma geçmişini yönetir, referansları çözümler ve 
konu takibi yapar.
"""

import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class ConversationContext:
    """Konuşma bağlamını tutan sınıf"""
    current_exhibit: Optional[str] = None  # Aktif eser adı
    current_exhibit_id: Optional[str] = None  # Aktif eser ID
    discussed_topics: List[str] = field(default_factory=list)  # Konuşulan konular
    last_entities: List[str] = field(default_factory=list)  # Son bahsedilen varlıklar
    

# Türkçe referans kelimeleri
REFERENCE_PATTERNS = [
    (r'\b(bunun|bunu|buna|bunda|bundan)\b', 'bu'),
    (r'\b(onun|onu|ona|onda|ondan)\b', 'o'),
    (r'\b(şunun|şunu|şuna|şunda|şundan)\b', 'şu'),
    (r'\b(bu\s+eser)\b', 'bu_eser'),
    (r'\b(o\s+eser)\b', 'o_eser'),
    (r'\b(bu\s+belge)\b', 'bu_belge'),
    (r'\b(bu\s+kupa)\b', 'bu_kupa'),
]

# Konu çıkarma kalıpları
TOPIC_PATTERNS = [
    r'(?:hakkında|konusunda|ile\s+ilgili)\s+(.+?)(?:\?|$)',
    r'(.+?)\s+(?:ne\s+zaman|nedir|nerede|kimdir)',
]


def has_reference(question: str) -> bool:
    """Soruda referans kelimesi var mı kontrol et"""
    q = question.lower()
    for pattern, _ in REFERENCE_PATTERNS:
        if re.search(pattern, q):
            return True
    return False


def resolve_references(
    question: str, 
    context: ConversationContext, 
    history: List[Any]
) -> str:
    """
    Soruda geçen referans kelimelerini çözümle.
    
    Örn: "bunun önemi ne?" → "Türk Maarif Cemiyeti Tüzüğü'nün önemi ne?"
    """
    if not has_reference(question):
        return question
    
    # Referans olarak kullanılacak varlığı bul
    reference_entity = None
    
    # 1. Önce aktif esere bak
    if context.current_exhibit:
        reference_entity = context.current_exhibit
    
    # 2. Son bahsedilen varlıklara bak
    elif context.last_entities:
        reference_entity = context.last_entities[-1]
    
    # 3. Konuşma geçmişinden çıkar
    elif history:
        reference_entity = extract_entity_from_history(history)
    
    if not reference_entity:
        return question
    
    # Referansları değiştir
    resolved = question
    
    # "bunun" → "X'in", "bunu" → "X'i" vb.
    replacements = [
        (r'\bbunun\b', f"{reference_entity}'ın"),
        (r'\bonun\b', f"{reference_entity}'ın"),
        (r'\bbunu\b', f"{reference_entity}'ı"),
        (r'\bonu\b', f"{reference_entity}'ı"),
        (r'\bbuna\b', f"{reference_entity}'a"),
        (r'\bona\b', f"{reference_entity}'a"),
        (r'\bbu\s+eser\b', reference_entity),
        (r'\bo\s+eser\b', reference_entity),
        (r'\bbu\s+belge\b', reference_entity),
    ]
    
    for pattern, replacement in replacements:
        resolved = re.sub(pattern, replacement, resolved, flags=re.IGNORECASE)
    
    return resolved


def extract_entity_from_history(history: List[Any]) -> Optional[str]:
    """Konuşma geçmişinden son bahsedilen varlığı çıkar"""
    if not history:
        return None
    
    # Son asistan cevabından eser/belge adını bul
    for msg in reversed(history):
        if hasattr(msg, 'role') and msg.role == 'assistant':
            content = msg.content
            # Tırnak içindeki isimleri ara
            quotes = re.findall(r'"([^"]+)"', content)
            if quotes:
                return quotes[0]
            # "... adlı eser" kalıbını ara
            named = re.search(r'([A-ZÇĞİÖŞÜ][^.]+?)\s+(?:adlı|isimli)', content)
            if named:
                return named.group(1).strip()
    
    return None


def extract_topics_from_history(history: List[Any]) -> List[str]:
    """Konuşma geçmişinden konuları çıkar"""
    topics = []
    
    for msg in history:
        if hasattr(msg, 'role') and msg.role == 'user':
            content = msg.content.lower()
            for pattern in TOPIC_PATTERNS:
                matches = re.findall(pattern, content)
                topics.extend(matches)
    
    return list(set(topics))[-5:]  # Son 5 benzersiz konu


def build_smart_context(
    history: List[Any], 
    qr_id: Optional[str] = None,
    exhibit_name: Optional[str] = None
) -> tuple:
    """
    Akıllı konuşma bağlamı oluştur.
    
    Returns:
        (context_string, ConversationContext)
    """
    context = ConversationContext(
        current_exhibit=exhibit_name,
        current_exhibit_id=qr_id
    )
    
    if not history:
        return "", context
    
    # Konuları çıkar
    context.discussed_topics = extract_topics_from_history(history)
    
    # Son varlıkları çıkar
    entity = extract_entity_from_history(history)
    if entity:
        context.last_entities.append(entity)
    
    # Son 5 mesajı formatla
    recent = history[-5:] if len(history) > 5 else history
    
    lines = []
    for msg in recent:
        role = "Ziyaretçi" if msg.role == "user" else "Rehber"
        lines.append(f"{role}: {msg.content}")
    
    history_text = "\n".join(lines)
    
    # Bağlam özeti oluştur
    context_parts = ["ÖNCEKİ KONUŞMA:"]
    
    if context.current_exhibit:
        context_parts.append(f"[Aktif Eser: {context.current_exhibit}]")
    
    if context.discussed_topics:
        context_parts.append(f"[Konuşulan Konular: {', '.join(context.discussed_topics[:3])}]")
    
    context_parts.append(history_text)
    
    return "\n".join(context_parts), context


def enhance_question_with_context(
    question: str,
    history: List[Any],
    qr_id: Optional[str] = None,
    exhibit_name: Optional[str] = None
) -> tuple:
    """
    Soruyu bağlam bilgisiyle zenginleştir.
    
    Returns:
        (enhanced_question, history_context, ConversationContext)
    """
    # Smart context oluştur
    history_context, conv_context = build_smart_context(
        history, qr_id, exhibit_name
    )
    
    # Referansları çözümle
    enhanced_question = resolve_references(question, conv_context, history)
    
    return enhanced_question, history_context, conv_context
