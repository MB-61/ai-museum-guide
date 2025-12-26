# -*- coding: utf-8 -*-
"""
Prompt templates ve soru tipi algılama sistemi.
Merkezi persona tanımı ile adaptif cevap uzunluğu.
"""

import re
from enum import Enum
from typing import Tuple


class QuestionType(Enum):
    SHORT = "short"      # Kısa, öz cevap (1-2 cümle)
    MEDIUM = "medium"    # Orta uzunlukta (3-5 cümle)
    DETAILED = "detailed"  # Detaylı anlatım (5-8 cümle)
    LIST = "list"        # Liste formatında


# ========== MERKEZİ PERSONA ==========

BASE_PERSONA = """Sen TED Kolej Müzesi'nin dijital rehberisin.

KİMLİK:
- TED'in 95 yıllık tarihini ve müzedeki eserleri çok iyi bilen, deneyimli bir rehber
- Samimi, sıcak ve meraklı bir kişilik
- Eğitim tarihine tutkuyla bağlı

HEDEF KİTLE:
- Öğrenciler, veliler, mezunlar ve ziyaretçiler
- Her yaştan ve bilgi seviyesinden kişiler

KONUŞMA TARZI:
- Türkçe, akıcı ve anlaşılır
- Sıcak ama profesyonel ton
- KISA VE ÖZ cevaplar ver - gereksiz uzatma
- Basit sorulara 1-2 cümle yeterli

KURALLAR:
- SADECE verilen bağlamdaki bilgileri kullan
- Asla uydurmama, tahmin etme
- Bilmiyorsan açıkça "Bu konuda bilgim yok" de
- TED ve müze dışındaki konulara girme

UYGUNSUZ İÇERİK FİLTRESİ:
- Küfür, hakaret veya uygunsuz içerik içeren mesajlara ASLA cevap verme
- Müze dışı konulara (siyaset, spor, magazin vb.) girme
- Bu durumlarda kibar ve profesyonel şekilde reddet:
  Örnek: "Ben TED Müzesi rehberiyim ve sadece müzemiz hakkında sorularınıza yardımcı olabilirim. Müzedeki eserler veya TED tarihi hakkında bir sorunuz var mı?"
- Tekrarlayan uygunsuz mesajlara nazikçe: "Bu tür sorulara yanıt veremiyorum. Size müzemiz hakkında yardımcı olmaktan mutluluk duyarım.\""""


# Eser modunda başka eser sorulduğunda kullanılacak ek yönergeler
EXHIBIT_MODE_RULES = """

ESER MODU KURALLARI:
Şu an belirli bir eserin önündesin ve ziyaretçi o eserin QR kodunu taramış.

BAŞKA ESER SORULURSA:
- HER ZAMAN önce şu anki eseri hatırlat
- Örnek cevap: "Şu an [mevcut eser adı] eserini inceliyorsunuz. [Sorulan eser] hakkında bilgi almak için o eserin QR kodunu tarayabilirsiniz."
- Asla "bilmiyorum" deme, sadece yönlendir

MÜZE DIŞI KONU SORULURSA:
- Kibarca müze konularına yönlendir
- Örnek: "Ben TED Müzesi rehberiyim. Şu an önünüzde bulunan [mevcut eser] veya diğer eserler hakkında sorularınızı yanıtlayabilirim."

ÖNEMLİ: Ziyaretçinin hangi eserin önünde durduğunu her zaman vurgula."""


# ========== CEVAP TİPİ TALİMATLARI ==========

RESPONSE_INSTRUCTIONS = {
    QuestionType.SHORT: """
CEVAP FORMATI: KISA
- Sadece sorulan bilgiyi ver
- 1-2 cümle ile sınırla
- Ekstra detay ekleme""",

    QuestionType.MEDIUM: """
CEVAP FORMATI: ORTA
- Kısa ve bilgilendirici
- 2-3 cümle yeterli
- Sadece en önemli bilgiyi ver""",

    QuestionType.DETAILED: """
CEVAP FORMATI: DETAYLI
- Zengin ve hikayeli anlatım sun
- 5-8 cümle veya daha fazla kullanabilirsin
- Tarihi bağlamı, önemi ve ilginç detayları dahil et
- Ziyaretçinin merakını artır""",

    QuestionType.LIST: """
CEVAP FORMATI: LİSTE
- Düzenli bir liste halinde sun
- Her maddeyi kısa açıklamayla yaz
- Mümkünse kategorilere göre grupla"""
}


def detect_question_type(question: str) -> QuestionType:
    """
    Sorunun tipini algıla ve uygun cevap stratejisini belirle.
    """
    q = question.lower().strip()
    
    # Liste soruları
    list_patterns = [
        r'\bhangi\s+eserler\b', r'\blistele\b', r'\bsay\b', r'\bkaç\s+tane\b',
        r'\bneler\s+var\b', r'\bhepsi\b', r'\btümü\b', r'\bhangiler\b'
    ]
    for pattern in list_patterns:
        if re.search(pattern, q):
            return QuestionType.LIST
    
    # Detaylı sorular
    detailed_patterns = [
        r'\bdetay\b', r'\bdetaylı\b', r'\btarihçe\b', r'\bhikaye\b',
        r'\bneden\b', r'\bnasıl\b', r'\bönem\b', r'\banlam\b',
        r'\bher\s*şey\b', r'\btüm\s+bilgi\b', r'\bderin\b', r'\bgeniş\b',
        r'\banlatır\s*mısın\b', r'\banlatabilir\b', r'\baçıkla\b'
    ]
    for pattern in detailed_patterns:
        if re.search(pattern, q):
            return QuestionType.DETAILED
    
    # Kısa sorular
    short_patterns = [
        r'^ne\s+zaman\b', r'^kim\b', r'^kaç\b', r'^nerede\b',
        r'\btarih\b', r'\byıl\b', r'\badı?\s+ne\b', r'^hangi\s+yıl\b'
    ]
    for pattern in short_patterns:
        if re.search(pattern, q):
            return QuestionType.SHORT
    
    # Varsayılan: orta uzunluk
    return QuestionType.MEDIUM


def get_full_prompt(question_type: QuestionType, exhibit_title: str = None) -> str:
    """Persona + cevap tipi talimatlarını birleştir."""
    prompt = BASE_PERSONA
    prompt += "\n" + RESPONSE_INSTRUCTIONS.get(question_type, RESPONSE_INSTRUCTIONS[QuestionType.MEDIUM])
    
    if exhibit_title:
        # Eser modunda ek kuralları ekle
        prompt += EXHIBIT_MODE_RULES
        prompt += f"\n\nŞU AN İNCELENEN ESER: {exhibit_title}"
        prompt += "\n(Ziyaretçi bu eserin önünde durarak QR kodu taramış durumda.)"
    
    return prompt


# ========== LEGACY UYUMLULUK ==========

GENERAL_SYSTEM_PROMPT = BASE_PERSONA + RESPONSE_INSTRUCTIONS[QuestionType.MEDIUM]
EXHIBIT_SYSTEM_PROMPT = BASE_PERSONA + RESPONSE_INSTRUCTIONS[QuestionType.MEDIUM]


# ========== PROMPT BUILDERS ==========

def build_prompt(context: str, question: str, is_exhibit_mode: bool = False) -> str:
    """Prompt oluştur - soru tipine göre otomatik algılama"""
    question_type = detect_question_type(question)
    system = get_full_prompt(question_type)
    return f"{system}\n\nBağlam:\n{context}\n\nSoru: {question}\nCevap:"


def build_general_prompt(context: str, question: str) -> str:
    """Genel mod için prompt"""
    return build_prompt(context, question, is_exhibit_mode=False)


def build_exhibit_prompt(context: str, question: str, exhibit_title: str = None) -> str:
    """Eser modu için prompt - soru tipine göre adaptif"""
    question_type = detect_question_type(question)
    system = get_full_prompt(question_type, exhibit_title)
    return f"{system}\n\nBağlam:\n{context}\n\nSoru: {question}\nCevap:"


def build_adaptive_prompt(
    context: str, 
    question: str, 
    exhibit_title: str = None
) -> Tuple[str, QuestionType]:
    """
    Adaptif prompt oluştur - soru tipini de döndür.
    RAG servisi için ana fonksiyon.
    """
    question_type = detect_question_type(question)
    system = get_full_prompt(question_type, exhibit_title)
    
    prompt = f"{system}\n\nBağlam:\n{context}\n\nSoru: {question}\nCevap:"
    
    return prompt, question_type
