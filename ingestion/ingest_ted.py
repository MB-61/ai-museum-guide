"""
TED Müze Verileri için Gelişmiş Ingest Script
Metadata zenginleştirmeli ChromaDB yükleme.

Kullanım:
  python ingestion/ingest_ted.py              # Tüm ted_museum/ klasörünü yükle
  python ingestion/ingest_ted.py --clear      # Önce eski verileri sil
"""
import argparse
import os
import sys
import re
import uuid

# Add current directory to path
sys.path.insert(0, os.getcwd())

from app.db.chroma import get_collection

def extract_year(text):
    """Metinden yıl çıkar"""
    match = re.search(r'\b(19\d{2}|20\d{2})\b', text)
    return match.group(1) if match else None

def extract_title(text):
    """İlk satırdan başlık çıkar"""
    lines = text.strip().split('\n')
    return lines[0].strip() if lines else "Bilinmeyen Eser"

def chunk_text(text, chunk_size=500, overlap=100):
    """Metni chunk'lara böl"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap
    return chunks

def detect_section(chunk):
    """Chunk'ın hangi bölüme ait olduğunu belirle"""
    chunk_lower = chunk.lower()
    if 'katalog açıklaması' in chunk_lower:
        return 'katalog'
    elif 'küratoryal analiz' in chunk_lower or 'tarihsel bağlam' in chunk_lower:
        return 'analiz'
    else:
        return 'genel'

def ingest_file(filepath, exhibit_id, collection):
    """Tek dosyayı ChromaDB'ye yükle"""
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    
    title = extract_title(text)
    year = extract_year(text)
    chunks = chunk_text(text, chunk_size=500, overlap=100)
    
    ids = []
    documents = []
    metadatas = []
    
    for i, chunk in enumerate(chunks):
        doc_id = str(uuid.uuid4())
        section = detect_section(chunk)
        
        metadata = {
            'exhibit_id': exhibit_id,
            'title': title,
            'section': section,
            'chunk_index': i,
            'source': os.path.basename(filepath)
        }
        if year:
            metadata['year'] = year
        
        ids.append(doc_id)
        documents.append(chunk)
        metadatas.append(metadata)
    
    if documents:
        collection.add(documents=documents, metadatas=metadatas, ids=ids)
    
    return len(documents)

def ingest_all(clear=False):
    """Tüm TED müze verilerini yükle"""
    source_dir = 'data/ted_museum'
    
    if not os.path.exists(source_dir):
        print(f"❌ Klasör bulunamadı: {source_dir}")
        print("   Önce convert_docx.py çalıştırın.")
        return
    
    col = get_collection()
    
    # Eski TED verilerini temizle
    if clear:
        print("[CLEAR] Eski veriler temizleniyor...")
        try:
            # Tüm TED exhibit'leri sil
            existing = col.get()
            if existing['ids']:
                ted_ids = [
                    id for id, meta in zip(existing['ids'], existing['metadatas'])
                    if meta and meta.get('source', '').endswith('.txt') and 
                       not meta.get('source', '').startswith(('mona_lisa', 'yildizli'))
                ]
                if ted_ids:
                    col.delete(ids=ted_ids)
                    print(f"   {len(ted_ids)} eski chunk silindi")
        except Exception as e:
            print(f"   Temizleme hatası (devam ediliyor): {e}")
    
    files = sorted([f for f in os.listdir(source_dir) if f.endswith('.txt')])
    total_chunks = 0
    
    print(f"[LOAD] {len(files)} eser yukleniyor...\n")
    
    for filename in files:
        filepath = os.path.join(source_dir, filename)
        exhibit_id = os.path.splitext(filename)[0]
        
        chunk_count = ingest_file(filepath, exhibit_id, col)
        total_chunks += chunk_count
        print(f"[OK] {exhibit_id}: {chunk_count} chunk")
    
    print(f"\n[DONE] Toplam {total_chunks} chunk yuklendi ({len(files)} eser)")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--clear', action='store_true', help='Önce eski TED verilerini sil')
    args = parser.parse_args()
    ingest_all(clear=args.clear)
