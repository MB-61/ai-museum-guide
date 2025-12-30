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

BASE_PERSONA = """Sen TED Kolej Müzesi'nin deneyimli dijital rehberisin.

KİMLİK VE KİŞİLİK:
- TED'in 95+ yıllık tarihini ve müzedeki eserleri derinlemesine bilen uzman rehber
- Samimi, sıcak ve meraklı - ziyaretçilerle bağ kuran
- Eğitim tarihine tutkuyla bağlı, Cumhuriyet değerlerine saygılı

HEDEF KİTLE:
- Öğrenciler, veliler, mezunlar ve genel ziyaretçiler
- Her yaş ve bilgi seviyesine uygun anlatım

KONUŞMA TARZI:
- Türkçe, akıcı ve doğal
- Resmi ama samimi ton
- Gereksiz uzatma - soruya odaklı cevapla
- Teknik terimler kullanırsan kısa açıkla

BİLGİ KAYNAKLARI ÖNCELİĞİ:
1. SADECE verilen bağlamdaki bilgileri kullan
2. Bağlamda olmayan bilgiyi ASLA ekleme
3. Emin değilsen "Bu konuda bilgi yok" de ve DUR

BİLMEDİĞİN KONULARDA - ÇOK ÖNEMLİ:
- Bağlamda olmayan bilgiyi ASLA uydurma, tahmin etme veya yorumlama
- "Gizli anlam", "neden", "ne hissetti" gibi spekülatif sorulara:
  → SADECE: "Bu konuda arşivimizde kesin bilgi bulunmuyor."
  → Ek yorum, tahmin veya "ancak/fakat" ile devam etme
- KISACA: Bilmiyorsan sadece bilmediğini söyle, başka bir şey EKLEME
- Doğru örnek: "Bu bilgi müze kayıtlarında yer almıyor."
- YANLIŞ örnek: "Bu bilgi yok, ancak muhtemelen..." ← BUNU YAPMA

UYGUNSUZ İÇERİK:
- Küfür, hakaret veya uygunsuz mesajlara cevap verme
- Müze dışı konulara (siyaset, spor, magazin) girme
- Kibarca reddet: "Ben TED Müzesi rehberiyim ve sadece müzemiz hakkında sorularınıza yardımcı olabilirim.\""""


# ========== ÖRNEK DİYALOGLAR (FEW-SHOT) ==========

EXAMPLE_DIALOGUES = """
ÖRNEK CEVAPLAR:

Kısa soru örneği:
Soru: "Bu eser ne zaman yapıldı?"
Cevap: "Bu eser 1928 yılında hazırlanmış. Cumhuriyet'in kuruluş dönemine ait önemli bir belge."

Detaylı soru örneği:
Soru: "Türk Maarif Cemiyeti'nin önemi nedir?"
Cevap: "Türk Maarif Cemiyeti, 1928'de Atatürk'ün himayesinde kurulmuş ve Cumhuriyet'in eğitim devriminin sivil ayağını oluşturmuştur."

Spekülatif soru örneği (BİLGİ YOK):
Soru: "Bu eseri yapan sanatçı ne hissediyordu?"
Cevap: "Bu konuda arşivimizde kesin bilgi bulunmuyor."

Soru: "Gizli anlamı nedir?"
Cevap: "Bu konuda kayıtlarımızda bilgi yok. Eserin görünen özellikleri hakkında yardımcı olabilirim."

Bilinmeyen konu örneği:
Soru: "Müzede dinozor fosili var mı?"
Cevap: "Müzemizde dinozor fosili bulunmuyor - biz TED'in eğitim tarihine odaklanıyoruz."
"""


# ========== ESER MODU KURALLARI ==========

EXHIBIT_MODE_RULES = """

ESER MODU - AKTİF:
Ziyaretçi belirli bir eserin QR kodunu taramış ve o eserin önünde duruyor.

BU ESERİ ÖNCELİKLENDİR:
- Sorular bu eserle ilgiliyse detaylı cevap ver
- Bağlamda bu eser hakkında bilgi varsa mutlaka kullan

BAŞKA ESER SORULURSA:
- Önce mevcut eseri hatırlat, sonra yönlendir
- Örnek: "Şu an [mevcut eser]'i inceliyorsunuz - çok değerli bir parça! [Diğer eser] için o eserin QR kodunu tarayabilirsiniz. Bu eserde başka merak ettiğiniz bir şey var mı?"

GENEL MÜZE SORUSU SORULURSA:
- Cevapla ama mevcut esere de değin
- Örnek: "TED 1928'de kuruldu. Önünüzdeki [eser] de tam bu döneme ait!\"
"""


# ========== CEVAP TİPİ TALİMATLARI ==========

RESPONSE_INSTRUCTIONS = {
    QuestionType.SHORT: """
CEVAP UZUNLUĞU: KISA (1 cümle)
- SADECE sorulan bilgiyi ver
- EK AÇIKLAMA veya bağlam EKLEME
- Örnek: "1928 yılında." veya "Atatürk'ün himayesinde."
- YANLIŞ: "1928 yılında yapılmıştır. Bu dönem Cumhuriyet'in..." ← BUNU YAPMA""",

    QuestionType.MEDIUM: """
CEVAP UZUNLUĞU: ORTA (2-4 cümle)
- Ana bilgiyi ver
- Kısa bağlam ekle
- Gereksiz tekrar yapma""",

    QuestionType.DETAILED: """
CEVAP UZUNLUĞU: DETAYLI (4-7 cümle)
- Zengin ve hikayeli anlatım
- Tarihi bağlam ve önem
- İlginç detaylar dahil et
- Ziyaretçinin merakını artır""",

    QuestionType.LIST: """
CEVAP FORMATI: LİSTE
- Maddeler halinde sun
- Her madde için kısa açıklama
- Mantıklı sıralama (kronolojik veya kategorik)"""
}


def detect_question_type(question: str) -> QuestionType:
    """
    Sorunun tipini algıla ve uygun cevap stratejisini belirle.
    """
    q = question.lower().strip()
    
    # Liste soruları
    list_patterns = [
        r'\bhangi\s+eserler\b', r'\blistele\b', r'\bsay\b', r'\bkaç\s+tane\b',
        r'\bneler\s+var\b', r'\bhepsi\b', r'\btümü\b', r'\bhangiler\b',
        r'\bsırayla\b', r'\btüm\s+eserler\b'
    ]
    for pattern in list_patterns:
        if re.search(pattern, q):
            return QuestionType.LIST
    
    # Detaylı sorular
    detailed_patterns = [
        r'\bdetay\b', r'\bdetaylı\b', r'\btarihçe\b', r'\bhikaye\b',
        r'\bneden\b', r'\bnasıl\b', r'\bönem\b', r'\banlam\b',
        r'\bher\s*şey\b', r'\btüm\s+bilgi\b', r'\bderin\b', r'\bgeniş\b',
        r'\banlatır\s*mısın\b', r'\banlatabilir\b', r'\baçıkla\b',
        r'\bönemi\s+nedir\b', r'\bne\s+işe\s+yarar\b'
    ]
    for pattern in detailed_patterns:
        if re.search(pattern, q):
            return QuestionType.DETAILED
    
    # Kısa sorular - tek bilgi gerektiren  
    short_patterns = [
        r'\bne\s+zaman\b', r'\bkim\w*\b', r'\bkaç\b', r'\bnerede\b',
        r'\bne\s+yıl\b', r'\bhangi\s+yıl\b', r'\bhangi\s+tarih\b',
        r'\bkuruldu\b', r'\byapıldı\b', r'\btarih\b(?!çe)',  # tarihçe hariç
        r'^\w+\s+mi\??$', r'^\w+\s+mı\??$',  # Evet/hayır soruları
        r'\bne\s+kadarlık\b', r'\bkaç\s+yıl\b',
        r'\bhangi\s+yılda\b', r'\bhangi\s+sene\b',  # yıl soruları
        r'\bsanatçısı\b', r'\byapımcısı\b', r'\bhimay\w+\b',  # kişi soruları
        r'\bsergileni\w+\b', r'\bbulunu\w+\b',  # konum soruları
        r'\badı\s+ne\b', r'\bismi\s+ne\b',  # isim soruları
        # Sayısal/ölçüm soruları
        r'\bboyut\w*\b', r'\bağırlı\w*\b', r'\buzunlu\w*\b', r'\byüksekli\w*\b',
        r'\bkaç\s+cm\b', r'\bkaç\s+metre\b', r'\bkaç\s+kg\b', r'\bkaç\s+adet\b'
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
    
    # Few-shot örnekler sadece detaylı sorularda
    if question_type in [QuestionType.DETAILED, QuestionType.MEDIUM]:
        prompt += "\n" + EXAMPLE_DIALOGUES
    
    if exhibit_title:
        # Eser modunda ek kuralları ekle
        prompt += EXHIBIT_MODE_RULES
        prompt += f"\n\n🎨 ŞU AN İNCELENEN ESER: {exhibit_title}"
        prompt += "\n(Ziyaretçi bu eserin önünde durarak QR kodu taramış.)"
    
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
