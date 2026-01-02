#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test 2: Sayısal / Tarih / Hassas Veri Soruları
Amaç: Sayıları "düzeltmeye" çalışıyor mu?
"""
import sys
import os
sys.path.insert(0, os.getcwd())
sys.stdout.reconfigure(encoding='utf-8')

from app.services.prompts import detect_question_type, QuestionType, build_adaptive_prompt, BASE_PERSONA

# Kritik test: Context'te "yanlış gibi görünen" sayılar var
# Model bunları düzeltmeden aynen döndürmeli
SAMPLE_CONTEXT_WITH_NUMBERS = """
TED Kolej Müzesi Eseri: Tarihi Laboratuvar Akusu

Envanter No: TM-1928-047
Tarih: 1928 (spesifik olarak 31 Ocak 1928)
Boyutlar: 47 cm x 32 cm x 18 cm
Ağırlık: 2.7 kg

Teknik Detaylar:
- Akü kapasitesi: 6 volt, 12 amper-saat
- Üretim numarası: 3847-B
- Üretim yeri: Ankara
- Toplam üretim adedi: 127 adet

Tarihi Not:
Bu akü 1928 yılında TED'in kuruluşunda kullanılan ilk laboratuvar ekipmanlarından biridir.
Okulda 43 yıl boyunca (1928-1971) aktif olarak kullanılmıştır.

ÖNEMLİ: Bu eserin boyutları ve tarihi kesin ölçümlere dayanmaktadır.
"""

# Test soruları - beklenen cevaplar exact match olmalı
TEST_QUESTIONS = [
    {
        "question": "Bu eser kaç yılında yapılmıştır?",
        "expected_type": QuestionType.SHORT,
        "exact_match_values": ["1928", "31 Ocak 1928"],
        "should_NOT_contain": ["1929", "1927", "tahmin", "muhtemelen"]
    },
    {
        "question": "Boyutları nedir?",
        "expected_type": QuestionType.SHORT,
        "exact_match_values": ["47 cm x 32 cm x 18 cm", "47", "32", "18"],
        "should_NOT_contain": ["50 cm", "yaklaşık", "civarında"]
    },
    {
        "question": "Kaç yıl kullanılmıştır?",
        "expected_type": QuestionType.SHORT,
        "exact_match_values": ["43 yıl", "1928-1971"],
        "should_NOT_contain": ["40 yıl", "45 yıl", "yaklaşık"]
    },
    {
        "question": "Kaç adet üretilmiştir?",
        "expected_type": QuestionType.SHORT,
        "exact_match_values": ["127 adet", "127"],
        "should_NOT_contain": ["100", "130", "yüzden fazla"]
    },
]

print("=" * 70)
print("TEST 2: SAYISAL / TARİH / HASSAS VERİ SORULARI")
print("Amaç: Sayıları 'düzeltmeye' çalışıyor mu?")
print("=" * 70)

# Prompt'ta sayı koruma talimatı var mı kontrol et
print("\n📋 PROMPT ANALİZİ:")
if "uydurma" in BASE_PERSONA.lower() or "tahmin" in BASE_PERSONA.lower():
    print("  ✅ Prompt'ta 'uydurma/tahmin etme' talimatı var")
else:
    print("  ⚠️ Prompt'ta açık 'uydurma' yasağı bulunamadı")

if "bağlam" in BASE_PERSONA.lower() or "context" in BASE_PERSONA.lower():
    print("  ✅ Prompt'ta bağlam kullanma talimatı var")
else:
    print("  ⚠️ Prompt'ta açık bağlam talimatı bulunamadı")

print("\n" + "-" * 70)

all_passed = True
for i, test in enumerate(TEST_QUESTIONS, 1):
    question = test["question"]
    expected_type = test["expected_type"]
    exact_values = test["exact_match_values"]
    
    print(f"\n--- Test {i} ---")
    print(f"Soru: {question}")
    
    # Soru tipini algıla
    q_type = detect_question_type(question)
    type_ok = q_type == expected_type
    print(f"Soru tipi: {q_type.value} {'✅' if type_ok else '❌'}")
    
    # Prompt oluştur
    prompt, _ = build_adaptive_prompt(
        context=SAMPLE_CONTEXT_WITH_NUMBERS,
        question=question,
        exhibit_title="Tarihi Laboratuvar Akusu"
    )
    
    # Context'te beklenen değerler var mı?
    print(f"\nContext'te beklenen değerler:")
    for val in exact_values:
        if val in SAMPLE_CONTEXT_WITH_NUMBERS:
            print(f"  ✅ '{val}' context'te mevcut")
        else:
            print(f"  ❌ '{val}' context'te YOK")
            all_passed = False
    
    # Prompt'ta KISA talimat var mı?
    if q_type == QuestionType.SHORT:
        if "KISA" in prompt or "1-2 cümle" in prompt:
            print("  ✅ Kısa cevap talimatı prompt'ta")
        else:
            print("  ⚠️ Kısa cevap talimatı eksik olabilir")

print("\n" + "=" * 70)
print("🧨 KRİTİK KONTROL: Sayı Koruma Talimatları")
print("=" * 70)

# Prompt'taki sayı koruma ifadelerini kontrol et
protection_phrases = [
    ("asla uydurmama", BASE_PERSONA),
    ("tahmin etme", BASE_PERSONA),
    ("bağlamdaki bilgileri kullan", BASE_PERSONA),
    ("kesin bilgi", BASE_PERSONA),
]

print("\nPrompt'ta sayı koruma ifadeleri:")
for phrase, text in protection_phrases:
    if phrase.lower() in text.lower():
        print(f"  ✅ '{phrase}' bulundu")
    else:
        print(f"  ❌ '{phrase}' bulunamadı")

print("\n" + "=" * 70)
print("📊 SONUÇ:")
if all_passed:
    print("  ✅ Tüm beklenen değerler context'te mevcut")
else:
    print("  ⚠️ Bazı değerler eksik - düzeltme gerekebilir")

print("\n🔬 LLM ile gerçek test için:")
print("  1. Sunucuyu başlat: uvicorn app.main:app --reload")
print("  2. Bir eser QR kodu tara")
print("  3. 'Boyutları nedir?' gibi sorular sor")
print("  4. Cevaptaki sayıların context ile AYNI olduğunu doğrula")
print("=" * 70)
