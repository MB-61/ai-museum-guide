# 🏛️ AI Museum Guide

Yapay zeka destekli interaktif müze rehberi. QR kod tarama, sesli sohbet ve kişiselleştirilmiş deneyim sunar.

## ✨ Özellikler

- **🔍 QR Kod Tarama**: Eserlerin QR kodlarını tarayarak bilgi alın
- **💬 Akıllı Sohbet**: RAG (Retrieval-Augmented Generation) ile doğru bilgiler
- **🎤 Sesli Giriş**: Web Speech API ile sesle soru sorun
- **🔊 Sesli Yanıt**: Text-to-Speech ile yanıtları dinleyin
- **🧠 Hafıza Sistemi**: İsminizi, ilgi alanlarınızı hatırlar
- **🌐 Çoklu Dil Desteği**: Soruyu hangi dilde sorarsanız o dilde yanıt

## 🖼️ Mevcut Eserler (15 adet)

| # | Eser | Sanatçı | QR Kodu |
|---|------|---------|---------|
| 1 | Mona Lisa | Leonardo da Vinci | qr_01 |
| 2 | Yıldızlı Gece | Vincent van Gogh | qr_02 |
| 3 | İnci Küpeli Kız | Johannes Vermeer | qr_03 |
| 4 | Son Akşam Yemeği | Leonardo da Vinci | qr_04 |
| 5 | Çığlık | Edvard Munch | qr_05 |
| 6 | Guernica | Pablo Picasso | qr_06 |
| 7 | Venüs'ün Doğuşu | Sandro Botticelli | qr_07 |
| 8 | Adem'in Yaratılışı | Michelangelo | qr_08 |
| 9 | Büyük Dalga | Katsushika Hokusai | qr_09 |
| 10 | Gece Devriyesi | Rembrandt | qr_10 |
| 11 | Belleğin Azmi | Salvador Dalí | qr_11 |
| 12 | Öpücük | Gustav Klimt | qr_12 |
| 13 | Su Zambakları | Claude Monet | qr_13 |
| 14 | Avignon'lu Kızlar | Pablo Picasso | qr_14 |
| 15 | Amerikan Gotiği | Grant Wood | qr_15 |

## 🚀 Kurulum

### Gereksinimler
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) paket yöneticisi

### Adımlar

```bash
# Repo'yu klonla
git clone https://github.com/MB-61/ai-museum-guide.git
cd ai-museum-guide

# Bağımlılıkları yükle
uv sync

# .env dosyasını oluştur
cp .env.example .env
# .env dosyasına Gemini API anahtarınızı ekleyin

# Veritabanını oluştur (eser verilerini yükle)
for exhibit in mona_lisa yildizli_gece inci_kupeli_kiz son_aksam_yemegi ciglik guernica venusun_dogusu ademin_yaratilisi buyuk_dalga gece_devriyesi bellegin_azmi opucuk su_zambaklari avignonlu_kizlar amerikan_gotigi; do
  uv run -m ingestion.ingest --exhibit "$exhibit" --source "data/curated/${exhibit}.txt"
done

# Sunucuyu başlat
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Ngrok ile Çalıştırma (Mobil Erişim)

```bash
ngrok http 8000
```

## 📁 Proje Yapısı

```
ai-museum-guide/
├── app/
│   ├── main.py              # FastAPI uygulaması
│   ├── routers/             # API endpoint'leri
│   │   ├── chat.py          # Sohbet API
│   │   ├── qr.py            # QR lookup API
│   │   └── voice.py         # Ses API
│   ├── services/            # İş mantığı
│   │   ├── rag.py           # RAG pipeline
│   │   ├── memory_service.py # Hafıza sistemi
│   │   ├── llm.py           # LLM entegrasyonu
│   │   └── key_rotation.py  # API key rotasyonu
│   └── models/              # Pydantic modelleri
├── data/
│   ├── curated/             # Eser bilgileri (txt)
│   ├── mappings/            # QR -> Eser eşleştirmesi
│   └── qr/                  # QR kod görselleri
├── web/
│   └── index.html           # Frontend (tek sayfa)
└── storage/
    ├── chroma/              # ChromaDB veritabanı
    └── memory/              # Kullanıcı hafızası (JSON)
```

## 🔧 API Endpoints

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| POST | `/api/v1/chat` | Sohbet mesajı gönder |
| POST | `/api/v1/qr/lookup` | QR koddan eser bilgisi al |
| POST | `/api/v1/voice/transcribe` | Ses dosyasını metne çevir |
| GET | `/` | Frontend sayfası |

### Örnek İstek

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "qr_id": "qr_01",
    "question": "Bu tablo ne zaman yapıldı?",
    "user_id": "visitor_123"
  }'
```

## 🧠 Hafıza Sistemi

Sistem, konuşmalardan önemli bilgileri otomatik olarak çıkarır ve saklar:

```json
{
  "user_id": "visitor_123",
  "name": "Ahmet",
  "interests": ["Empresyonizm", "Van Gogh"],
  "visited_exhibits": ["mona_lisa", "yildizli_gece"],
  "preferences": {"language": "tr"}
}
```

Sonraki konuşmalarda kişiselleştirilmiş yanıtlar verilir.

## 🔑 Çevre Değişkenleri

```env
# Gemini API anahtarları (en az 1 gerekli)
GOOGLE_API_KEY=your_primary_key
GOOGLE_API_KEY_1=your_backup_key  # opsiyonel

# Model
LLM_MODEL=gemini-2.5-flash
```

## 📱 Mobil Kullanım

1. Ngrok ile sunucuyu başlatın
2. Telefonunuzun tarayıcısından ngrok URL'sine gidin
3. QR kodları tarayın ve sesli sohbet edin

## 📄 Lisans

MIT License

## 👤 Geliştirici

Created with ❤️ and AI assistance
