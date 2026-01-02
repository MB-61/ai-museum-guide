#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST QUALITY V3: "THE ULTIMATE GUIDE TEST"
Author: Antigravity (Advanced AI Agent)
Date: 2026-01-02

Purpose: 
Comprehensive "Turing Test" for the Museum Guide.
Evaluates:
1. Context Retention (Multi-turn memory)
2. Persona Integrity (Are you an AI or a Guide?)
3. Boundary Management (Politics/Off-topic)
4. Hallucination Resistance (Fake facts)
5. Formatting Compliance (Lists vs Paragraphs)

Usage:
    python test_quality_v3.py
"""
import sys
import requests
import json
import re
import time

# Force UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8')

API_URL = "http://localhost:8000"

class GuideTesterV3:
    def __init__(self):
        self.total_score = 100
        self.session_history = [] # Simulates client-side history
        self.log = []

    def call_chat(self, qr_id, question):
        """Simulate a chat turn with history."""
        payload = {
            "qr_id": qr_id,
            "question": question,
            "history": self.session_history
        }
        
        try:
            start_time = time.time()
            resp = requests.post(f"{API_URL}/api/v1/chat", json=payload, timeout=30)
            latency = time.time() - start_time
            
            if resp.status_code != 200:
                print(f"❌ API ERROR: {resp.status_code}")
                return None
                
            data = resp.json()
            answer = data.get("answer", "")
            
            # Update history (User + Bot)
            self.session_history.append({"role": "user", "content": question})
            self.session_history.append({"role": "assistant", "content": answer})
            
            return answer, latency
        except Exception as e:
            print(f"❌ CONNECTION ERROR: {e}")
            return None, 0

    def evaluate_turn(self, name, qr_id, question, checks):
        """Run a single turn and evaluate against multiple checks."""
        print(f"\n🔹 TEST: {name}")
        print(f"   Q: {question}")
        
        answer, latency = self.call_chat(qr_id, question)
        if not answer:
            self.total_score -= 10
            return

        print(f"   A: {answer[:150]}... ({len(answer)} chars, {latency:.2f}s)")
        
        turn_passed = True
        for check_name, check_func in checks.items():
            result, note = check_func(answer)
            if result:
                print(f"      ✅ {check_name}: {note}")
            else:
                print(f"      ❌ {check_name}: {note}")
                self.total_score -= 5
                turn_passed = False
        
        if turn_passed:
            print("   ✨ TURN PASSED")
        else:
            print("   ⚠️ TURN FAILED")

    def run_suite(self):
        print("\n🚀 STARTING ULTIMATE GUIDE TEST (V3) 🚀")
        print("="*60)

        # --- SCENARIO 1: CONTEXT RETENTION ---
        # User looks at Ataturk Monument (qr_02), then asks "Who made it?" without naming it.
        self.session_history = [] 
        
        # Turn 1: Establish Context
        self.evaluate_turn(
            "Establish Context (Ataturk Monument)",
            "qr_02",
            "Bu anıt hakkında bilgi ver.",
            {
                "Relevance": lambda a: ("Atatürk" in a, "Mentioned Atatürk")
            }
        )
        
        # Turn 2: Follow-up (Implicit Subject)
        # Expected: System knows 'it' refers to the monument and mentions Sculptor Metin Yurdanur
        self.evaluate_turn(
            "Context Memory Check",
            "qr_02",
            "Peki bunu kim yaptı?",
            {
                "Identify Subject": lambda a: ("Metin Yurdanur" in a or "yontu" in a, "Identified sculptor/maker"),
                "No Repetition": lambda a: ("Hoşgeldiniz" not in a, "No robotic intro")
            }
        )

        # --- SCENARIO 2: BOUNDARY & PERSONA ---
        # User asks off-topic political question.
        self.session_history = []
        self.evaluate_turn(
            "Boundary Test (Politics)",
            "qr_01", # Charter
            "Sence önümüzdeki seçimleri kim kazanır?",
            {
                "Refusal": lambda a: (
                    ("seçim" not in a.lower() and "kazan" not in a.lower()) or "rehber" in a.lower(), 
                    "Politely declined/pivoted"
                ),
                "Persona": lambda a: ("robot" not in a.lower() and "yapay zeka" not in a.lower(), "Stayed in character")
            }
        )

        # --- SCENARIO 3: FORMATTING ---
        # User asks for a list.
        self.session_history = []
        self.evaluate_turn(
            "Formatting Test (List)",
            "qr_10", # 90th Year Relief
            "Bu eserdeki önemli figürleri maddeler halinde say.",
            {
                "Formatting": lambda a: ("\n-" in a or "\n*" in a or "1." in a, "Used list format"),
                "Content": lambda a: ("öğrenci" in a.lower() or "meşale" in a.lower(), "Relevant content")
            }
        )
        
        # --- SCENARIO 4: HALLUCINATION CHECK ---
        # Asking about something that doesn't exist in the context of the charter
        self.session_history = []
        self.evaluate_turn(
            "Hallucination Resistance",
            "qr_01", # Charter
            "Bu belgede uzaylılardan bahsediliyor mu?",
            {
                "Truthfulness": lambda a: ("hayır" in a.lower() or "bahsedilmez" in a.lower() or "yoktur" in a.lower(), "Correctly denied false claim")
            }
        )

        # --- SCENARIO 5: SPECIAL CONTENT (STATS & OVERVIEW) ---
        # Verifies the new RAG capabilities for museum stats and overview.
        self.session_history = []
        self.evaluate_turn(
            "Stats Query (System Metadata)",
            "qr_01",
            "Müzede toplam kaç eser var?",
            {
                "Numeric Check": lambda a: (any(c.isdigit() for c in a), "Contains number"),
                "Context Recall": lambda a: ("31" in a or "30" in a or "32" in a, "Accurate count (approx 31)")
            }
        )
        
        self.session_history = []
        self.evaluate_turn(
            "Overview Query (Museum Info)",
            "qr_01",
            "Müze hakkında genel bilgi ver.",
            {
                "Key Terms": lambda a: ("TED" in a and "Türk Eğitim Derneği" in a, "Mentions TED/Foundation"),
                "Content": lambda a: ("eğitim" in a.lower() or "tarih" in a.lower(), "Relevant content")
            }
        )

        print("="*60)
        print(f"🏆 FINAL SCORE: {max(0, self.total_score)}/100")
        
        if self.total_score >= 90:
            print("🌟 RATING: LEGENDARY GUIDE")
        elif self.total_score >= 80:
            print("✅ RATING: PROFESSIONAL")
        else:
            print("⚠️ RATING: NEEDS TRAINING")

if __name__ == "__main__":
    tester = GuideTesterV3()
    tester.run_suite()
