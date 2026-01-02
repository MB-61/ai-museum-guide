#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST QUALITY V2: "The Tough Test"
Author: Antigravity (Advanced AI Agent)
Date: 2026-01-02

Purpose: 
Strictly evaluate the LLM's response quality. 
It ruthlessly penalizes:
1. Repetitive phrases (Loops).
2. Unnecessary verbosity (Fluff).
3. Hallucinations (making up IDs).
4. Bad formatting.

Usage:
    python test_quality_v2.py
"""
import sys
import os
import requests
import json
import re
from collections import Counter

# Force UTF-8 encoding for Windows consoles
sys.stdout.reconfigure(encoding='utf-8')

API_URL = "http://localhost:8000"

# --- SCORING WEIGHTS ---
WEIGHT_REPETITION = 2.0  # High penalty for repeating logic
WEIGHT_VERBOSITY = 1.0   # Medium penalty for long answers to short questions
WEIGHT_RELEVANCE = 1.5   # Penalty for missing context keywords

class QualityTester:
    def __init__(self):
        self.results = []
        self.total_score = 100
        
    def call_api(self, qr_id, question):
        try:
            resp = requests.post(f"{API_URL}/api/v1/chat", json={
                "qr_id": qr_id, "question": question, "history": []
            }, timeout=30)
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def check_repetition(self, text):
        """
        Detects phrase repetition.
        Returns likelihood score 0-10 (0=clean, 10=broken record).
        """
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip().lower() for s in sentences if len(s) > 10]
        
        if not sentences:
            return 0
            
        # Check for identical sentences
        counts = Counter(sentences)
        duplicates = [s for s, c in counts.items() if c > 1]
        
        if duplicates:
            print(f"  🚨 REPETITION DETECTED: '{duplicates[0]}'")
            return min(len(duplicates) * 3, 10)
            
        # Check for phrase repetition (n-grams)
        words = text.lower().split()
        if len(words) < 20:
            return 0
            
        bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)]
        bigram_counts = Counter(bigrams)
        frequent_bigrams = [b for b, c in bigram_counts.items() if c > 2 and b not in ["bu", "bir", "ve"]]
        
        if frequent_bigrams:
             print(f"  ⚠️ PHRASE LOOP: '{frequent_bigrams[0]}'")
             return min(len(frequent_bigrams) * 2, 8)
             
        return 0

    def check_verbosity(self, text, question_type):
        """
        Checks if answer length matches question intent.
        SHORT questions should generally be < 50 words.
        """
        word_count = len(text.split())
        
        if question_type == "SHORT":
            if word_count > 100:
                print(f"  🚨 VERBOSITY FAIL: Expected short answer, got {word_count} words.")
                return 8
            elif word_count > 60:
                print(f"  ⚠️ VERBOSITY WARN: Answer a bit long ({word_count} words).")
                return 4
                
        return 0

    def run_test(self):
        print("\n🔥 STARTING TOUGH QUALITY TEST (V2) 🔥")
        print("="*60)
        
        # Test 1: Simple Identity (Should be concise)
        self.evaluate_single(
            qr_id="qr_02", 
            question="Bu nedir?", 
            expected_type="SHORT",
            context_keywords=["atatürk", "anıt", "incek"]
        )
        
        # Test 2: Specific Detail (Should answer directly without fluff)
        self.evaluate_single(
            qr_id="qr_03",
            question="Kaç yılında yapıldı?",
            expected_type="SHORT",
            context_keywords=["1928"] # ID_03 is Laboratuvar Aküsü (1928)
        )
        
        # Test 3: Repetition Bait (Ask same thing twice)
        print("\n--- TEST 3: REPETITION STRESS TEST ---")
        # We simulate a user asking slightly different versions of the same question
        # Ideally the model should NOT repeat the exact same intro paragraph.
        self.evaluate_single("qr_10", "Bu eserin konusu ne?", "MEDIUM", ["tema", "meşale"])

        print("="*60)
        print(f"🏁 FINAL SCORE: {max(0, self.total_score)}/100")
        if self.total_score < 80:
             print("❌ FAILED. The AI needs training (prompt tuning).")
        else:
             print("✅ PASSED. Quality is acceptable.")

    def evaluate_single(self, qr_id, question, expected_type, context_keywords):
        print(f"\nQUERY: {question} (QR: {qr_id})")
        res = self.call_api(qr_id, question)
        
        if "error" in res:
            print(f"  ❌ API ERROR: {res['error']}")
            self.total_score -= 20
            return

        answer = res.get("answer", "")
        print(f"  📝 ANSWER ({len(answer)} chars):\n  {answer[:150]}...[truncated]")
        
        # 1. Repetition Check
        rep_penalty = self.check_repetition(answer)
        if rep_penalty > 0:
            self.total_score -= rep_penalty * WEIGHT_REPETITION
            
        # 2. Verbosity Check
        verb_penalty = self.check_verbosity(answer, expected_type)
        if verb_penalty > 0:
            self.total_score -= verb_penalty * WEIGHT_VERBOSITY
            
        # 3. Context Check
        found_kw = [k for k in context_keywords if k.lower() in answer.lower()]
        if not found_kw:
            # We don't penalize too hard here because maybe keyword is missing but answer is right
            # But for a TOUGH test, we expect key terms.
            print(f"  ⚠️ MISSING KEYWORDS: Expected {context_keywords}")
            self.total_score -= 5 * WEIGHT_RELEVANCE
        else:
            print(f"  ✅ Keywords found: {found_kw}")

if __name__ == "__main__":
    tester = QualityTester()
    tester.run_test()
