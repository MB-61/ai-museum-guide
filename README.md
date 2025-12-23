AI MUSEUM GUIDE - KOMUT LİSTESİ / COMMAND CHEAT SHEET

--------------------------------------------------------------------------------
1. KURULUM / SETUP
--------------------------------------------------------------------------------

### Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Eğer requirements.txt yoksa:
pip install fastapi uvicorn python-dotenv chromadb google-genai langchain langchain-google-genai sentence-transformers

### macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Manuel kurulum:
pip install fastapi uvicorn python-dotenv chromadb google-genai langchain langchain-google-genai sentence-transformers


--------------------------------------------------------------------------------
2. SUNUCUYU BAŞLATMA / RUN SERVER
--------------------------------------------------------------------------------

### Windows
# Sadece kendi bilgisayarınız için (localhost):
python -m uvicorn app.main:app --reload --port 8000

# Aynı ağdaki diğer cihazlar (telefon vb.) erişebilsin diye:
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

taskkill /f /im python.exe 2>$null; Start-Sleep -Seconds 2; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

### macOS / Linux
# Localhost:
python3 -m uvicorn app.main:app --reload --port 8000

# Network access:
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

DOSYANIN AÇILACAĞI YER: http://localhost:8000/

--------------------------------------------------------------------------------
3. VERİ YÜKLEME (RAG) / INGESTION
--------------------------------------------------------------------------------
Yeni bir eser metni eklediğinizde ChromaDB'ye yüklemek için bu komutları kullanın.

### Windows (PowerShell)
$env:PYTHONPATH = "."
python ingestion/ingest.py --exhibit mona_lisa --source data/curated/mona_lisa.txt
python ingestion/ingest.py --exhibit yildizli_gece --source data/curated/yildizli_gece.txt

### macOS / Linux
export PYTHONPATH=.
python3 ingestion/ingest.py --exhibit mona_lisa --source data/curated/mona_lisa.txt
python3 ingestion/ingest.py --exhibit yildizli_gece --source data/curated/yildizli_gece.txt


--------------------------------------------------------------------------------
4. VERİ SİLME & KONTROL / MANAGE DATA
--------------------------------------------------------------------------------

### Windows (PowerShell) - Silme & Kontrol Scripti
# Aşağıdaki kodu bir python dosyasına kaydedip çalıştırabilirsiniz veya terminalde:
python -c "from app.db.chroma import get_collection; col=get_collection(); col.delete(where={'exhibit_id': 'mona_lisa'}); print('Silindi.')"

# Kontrol etme (Kaç doküman var?):
python -c "from app.db.chroma import get_collection; print(len(get_collection().get()['ids']))"

### macOS / Linux
python3 -c "from app.db.chroma import get_collection; col=get_collection(); col.delete(where={'exhibit_id': 'mona_lisa'}); print('Deleted.')"


--------------------------------------------------------------------------------
5. TEST (CURL)
--------------------------------------------------------------------------------

### Windows (PowerShell)
# Not: Windows'ta curl kullanımı bazen karışıktır, Invoke-RestMethod daha iyidir.

# Basit Chat Testi:
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/chat" -Method Post -ContentType "application/json" -Body '{"question":"Mona Lisa kimin eseri?", "qr_id":"qr_01"}'

# cURL kullanacaksanız (CMD/Git Bash):
curl -X POST "http://localhost:8000/api/v1/chat" ^
     -H "Content-Type: application/json" ^
     -d "{\"question\": \"Mona Lisa kimin eseri?\", \"qr_id\": \"qr_01\"}"

### macOS / Linux
curl -X POST http://localhost:8000/api/v1/chat \
     -H "Content-Type: application/json" \
     -d '{"question": "Mona Lisa kimin eseri?", "qr_id": "qr_01"}'


--------------------------------------------------------------------------------
6. MOBİL TEST (NGROK)
--------------------------------------------------------------------------------
Telefondan HTTPS (Mikrofon izni) ile bağlanmak için.

### Windows & Mac (Aynı komut)
# 1. Terminalde sunucuyu başlatın (Port 8000)
# 2. Yeni terminalde:
./ngrok http 8000

NGROG ÖLDÜRME: taskkill /f /im ngrok.exe 2>$null

# Size verilen https://....ngrok-free.dev adresini telefonda açın.
# Örn: https://random-id.ngrok-free.dev/static/avatar-guide.html
