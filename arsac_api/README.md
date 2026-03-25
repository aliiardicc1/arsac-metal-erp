# Arsac Metal ERP — API v3.0

## Klasör Yapısı

```
arsac_api/
├── main.py              ← FastAPI uygulaması, tüm router'lar
├── kurulum.py           ← PostgreSQL şema + admin kurulumu
├── requirements.txt     ← Python paketleri
├── .env.example         ← Ortam değişkenleri şablonu
│
├── core/
│   ├── database.py      ← PostgreSQL bağlantı havuzu
│   └── auth.py          ← JWT token üretimi ve doğrulaması
│
├── models/
│   └── schemas.py       ← Tüm Pydantic şemaları
│
└── routers/
    ├── kullanicilar.py  ← Giriş, kullanıcı yönetimi, izinler
    ├── ozet.py          ← Dashboard verileri
    ├── stok.py          ← Stok listesi, depo girişi
    ├── talepler.py      ← Hammadde talepleri
    ├── siparisler.py    ← Sipariş yönetimi
    ├── uretim.py        ← İşler, parçalar, yerleşim
    ├── sevkiyat.py      ← Sevkiyat yönetimi
    ├── satinalma.py     ← Satın alma, ödeme takibi
    ├── cariler.py       ← Tedarikçi / cari yönetimi
    ├── muhasebe.py      ← Makbuz, fatura
    ├── log.py           ← İşlem geçmişi
    └── sorgu.py         ← Güvenli ham sorgu (PyQt5 uyumluluğu)
```

## Kurulum (Turhost sunucusunda)

### 1. Paketleri yükle
```bash
pip install -r requirements.txt
```

### 2. Ortam değişkenlerini ayarla
```bash
cp .env.example .env
nano .env   # DATABASE_URL ve SECRET_KEY'i düzenle
```

### 3. Veritabanını kur (sadece ilk seferinde)
```bash
python kurulum.py
```

### 4. Sunucuyu başlat
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Arka planda çalıştırmak için:
```bash
nohup uvicorn main:app --host 0.0.0.0 --port 8000 &
```

---

## API Endpoint'leri

| Yol | Metod | Açıklama |
|-----|-------|----------|
| `/giris` | POST | Kullanıcı girişi → token |
| `/saglik` | GET | Sunucu sağlık kontrolü |
| `/ozet` | GET | Dashboard verileri |
| `/stok` | GET/POST | Stok listesi / ekleme |
| `/stok/{id}/depo-giris` | POST | Depo kabul |
| `/talepler` | GET/POST | Hammadde talepleri |
| `/siparisler` | GET/POST | Siparişler |
| `/siparisler/{id}` | GET/PUT/DELETE | Sipariş detay |
| `/uretim/isler` | GET/POST | Üretim işleri |
| `/uretim/parcalar` | POST | Parça ekleme |
| `/sevkiyat` | GET/POST | Sevkiyatlar |
| `/satinalma` | GET/POST | Satın alma |
| `/satinalma/{id}/odendi` | POST | Ödeme işaretle |
| `/cariler` | GET/POST | Tedarikçiler |
| `/muhasebe/makbuzlar` | GET/POST | Makbuzlar |
| `/muhasebe/ozet` | GET | Finansal özet |
| `/kullanicilar` | GET/POST | Kullanıcı yönetimi |
| `/izinler/{kullanici}` | GET/PUT | İzin yönetimi |
| `/log` | GET | İşlem geçmişi |
| `/sorgu` | POST | Ham SQL sorgu (PyQt5 uyumluluk) |

## Kimlik Doğrulama

Her istekte header ekle:
```
Authorization: Bearer <token>
```

Token almak için:
```json
POST /giris
{
  "kullanici_adi": "aliiardicc",
  "sifre": "arsac2024"
}
```

## PyQt5 Masaüstü Uyumluluğu

`database_bulut.py` tüm SQL sorgularını `/sorgu` endpoint'ine gönderiyor.
Bu sayede masaüstü uygulama hiç değişmeden bu API ile çalışır.
