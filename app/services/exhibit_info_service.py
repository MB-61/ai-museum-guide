# -*- coding: utf-8 -*-
"""
Eser bilgi servisi - Müzedeki eser sayısını ve istatistiklerini hesaplar.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any

# Data paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
METADATA_FILE = os.path.join(DATA_DIR, "exhibit_metadata.json")
MUSEUM_INFO_FILE = os.path.join(DATA_DIR, "museum_info.txt")


def get_exhibit_stats() -> Dict[str, Any]:
    """
    Müzedeki eserlerin güncel istatistiklerini döndürür.
    
    Returns:
        {
            "total": 31,
            "categories": {"Belge": 7, "Fotoğraf": 4, ...},
            "category_list": ["Belge (7)", "Fotoğraf (4)", ...],
            "last_updated": "2 Ocak 2026"
        }
    """
    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "total": 0,
            "categories": {},
            "category_list": [],
            "last_updated": datetime.now().strftime("%d %B %Y")
        }
    
    exhibits = metadata.get("exhibits", {})
    total = len(exhibits)
    
    # Kategori dağılımını hesapla
    categories: Dict[str, int] = {}
    for exhibit_data in exhibits.values():
        category = exhibit_data.get("category", "").strip()
        if category:
            categories[category] = categories.get(category, 0) + 1
        else:
            categories["Kategorisiz"] = categories.get("Kategorisiz", 0) + 1
    
    # Kategori listesini oluştur (sayı sıralı)
    sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
    category_list = [f"{cat} ({count})" for cat, count in sorted_categories]
    
    # Türkçe tarih formatı
    months_tr = {
        1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
        7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
    }
    now = datetime.now()
    last_updated = f"{now.day} {months_tr[now.month]} {now.year}"
    
    return {
        "total": total,
        "categories": categories,
        "category_list": category_list,
        "last_updated": last_updated
    }


def get_exhibit_stats_context() -> str:
    """
    Müze istatistiklerini AI context'i olarak formatlar.
    
    Returns:
        Formatlı string (RAG context için)
    """
    stats = get_exhibit_stats()
    
    context = f"""TED Kolej Müzesi Güncel Bilgileri:

TOPLAM ESER SAYISI: {stats['total']} adet

KATEGORİ DAĞILIMI:
{chr(10).join(f"- {item}" for item in stats['category_list'])}

Son güncelleme: {stats['last_updated']}
"""
    return context


def get_museum_info_context() -> str:
    """
    Müze hakkında genel bilgiyi yükler.
    
    Returns:
        Müze özet bilgisi (RAG context için)
    """
    try:
        with open(MUSEUM_INFO_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        # Fallback if file doesn't exist
        stats = get_exhibit_stats()
        return f"""TED Kolej Müzesi Hakkında:
TED Kolej Müzesi, Türk Eğitim Derneği'nin eğitim mirasını sergileyen bir müzedir.
Koleksiyonda toplam {stats['total']} eser bulunmaktadır.
"""

