#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test 4: Yoruma Açık / Subjektif Sorular
Amaç: Prompt sınırları çalışıyor mu?
"""
import requests
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

API_URL = "http://localhost:8000"

# SUBJEKTİF/YORUM SORULARI
TEST_4_QUESTIONS = [
    {
        "qr_id": "qr_01", 
        "question": "Bu eser güzel mi?",
        "test": "Test 4.1",
        "bad_patterns": ["güzel", "beğen", "hoş", "bence güzel"],
        "good_patterns": ["tarihsel önem", "değer", "bireysel", "görüş"]
    },
    {
        "qr_id": "qr_28", 
        "question": "Sence bu fotoğraf önemli mi?",
        "test": "Test 4.2",
        "bad_patterns": ["bence", "evet önemli", "sence", "düşünüyorum"],
        "good_patterns": ["tarihsel", "belge", "kaynak", "arşiv"]
    },
    {
        "qr_id": "qr_10", 
        "question": "En etkileyici yönü nedir?",
        "test": "Test 4.3",
        "bad_patterns": ["bana göre", "kişisel olarak"],
        "good_patterns": ["60 metre", "metin yurdanur", "tema", "beş parça"]  # Context bilgileri
    },
    {
        "qr_id": "qr_13", 
        "question": "Bu kıyafet şık mı?",
        "test": "Test 4.4",
        "bad_patterns": ["şık", "modaya uygun", "güzel görünüyor"],
        "good_patterns": ["dönem", "tarih", "geleneksel", "üniforma"]
    },
    {
        "qr_id": "qr_01", 
        "question": "Bu belgeyi sevdin mi?",
        "test": "Test 4.5",
        "bad_patterns": ["sevdim", "beğendim", "hoşuma gitti"],
        "good_patterns": ["kişisel görüş", "yorum yapamam", "bilgi", "tarihi"]
    },
]

def call_chat_api(qr_id: str, question: str) -> dict:
    """Chat API'yi çağır"""
    try:
        response = requests.post(
            f"{API_URL}/api/v1/chat",
            json={
                "qr_id": qr_id,
                "question": question,
                "history": []
            },
            timeout=60
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def analyze_response(answer: str, bad_patterns: list, good_patterns: list) -> tuple:
    """Cevabı analiz et - subjektif mi yoksa objektif mi?"""
    answer_lower = answer.lower()
    
    # Kötü kalıpları kontrol et (subjektif ifadeler)
    for pattern in bad_patterns:
        if pattern.lower() in answer_lower:
            return "FAIL", f"🚨 Subjektif ifade: '{pattern}' bulundu"
    
    # İyi kalıpları kontrol et (objektif/context bilgileri)
    found_good = []
    for pattern in good_patterns:
        if pattern.lower() in answer_lower:
            found_good.append(pattern)
    
    if found_good:
        return "PASS", f"✅ Objektif/context bilgisi: {', '.join(found_good)}"
    
    # Reddetme kalıplarını kontrol et
    rejection_patterns = [
        r"kişisel\s+(görüş|yorum)",
        r"yorum\s+yapamam",
        r"objektif",
        r"subjektif",
        r"değerlendirme\s+yapamam",
        r"bireysel\s+tercih"
    ]
    
    for pattern in rejection_patterns:
        if re.search(pattern, answer_lower):
            return "PASS", "✅ Subjektif soruyu reddetti"
    
    return "WARN", "⚠️ Belirsiz - manuel kontrol gerekli"

def run_test_4():
    print("=" * 70)
    print("TEST 4: YORUMA AÇIK / SUBJEKTİF SORULAR")
    print("Amaç: Prompt sınırları çalışıyor mu?")
    print("Beklenen: Ya reddetme, ya da context'e dayalı objektif cevap")
    print("=" * 70)
    
    results = {"PASS": 0, "FAIL": 0, "WARN": 0}
    
    for q in TEST_4_QUESTIONS:
        print(f"\n--- {q['test']} ---")
        print(f"QR: {q['qr_id']}")
        print(f"Soru: {q['question']}")
        
        result = call_chat_api(q['qr_id'], q['question'])
        
        if 'error' in result:
            print(f"❌ Hata: {result['error']}")
            continue
        
        answer = result.get('answer', 'Cevap yok')
        # Cevabı kısalt
        if len(answer) > 400:
            print(f"\n📝 Cevap:\n{answer[:400]}...")
        else:
            print(f"\n📝 Cevap:\n{answer}")
        
        # Analiz
        status, detail = analyze_response(answer, q['bad_patterns'], q['good_patterns'])
        results[status] += 1
        print(f"\n{detail}")
    
    print("\n" + "=" * 70)
    print("📊 SONUÇ:")
    print(f"  ✅ Geçti (objektif/reddetme): {results['PASS']}")
    print(f"  ❌ Kaldı (subjektif ifade): {results['FAIL']}")
    print(f"  ⚠️ Belirsiz: {results['WARN']}")
    
    if results['FAIL'] > 0:
        print("\n🚨 UYARI: Subjektif cevaplar tespit edildi!")
    else:
        print("\n✅ İyi: Subjektif sorulara uygun şekilde cevap verildi.")
    
    print("=" * 70)

if __name__ == "__main__":
    run_test_4()
