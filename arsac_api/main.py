"""
Arsac Metal ERP — FastAPI Ana Uygulama
========================================
Katmanlı mimari:
  core/       → Veritabanı bağlantısı, auth
  models/     → Pydantic şemaları
  routers/    → Endpoint grupları
  services/   → İş mantığı (ileride)

Yeni endpoint eklemek için:
  1. routers/ altına yeni dosya ekle
  2. Aşağıdaki include_router satırına ekle
  3. Bitti!
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from datetime import datetime
import os

# Router'ları import et
from routers.kullanicilar import router as kullanici_router
from routers.siparisler   import router as siparis_router
from routers.uretim       import router as uretim_router
from routers.stok         import stok_router, musteri_router
from routers.sevkiyat     import sevkiyat_router, ozet_router
from routers.sorgu        import router as sorgu_router

# ── Uygulama ──────────────────────────────────────
app = FastAPI(
    title="Arsac Metal ERP API",
    version="2.0.0",
    description="Katmanlı mimari — Arsac Metal ERP REST API",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Router'ları kaydet ────────────────────────────
app.include_router(kullanici_router)
app.include_router(siparis_router)
app.include_router(uretim_router)
app.include_router(stok_router)
app.include_router(musteri_router)
app.include_router(sevkiyat_router)
app.include_router(ozet_router)
app.include_router(sorgu_router)

# ── Temel endpoint'ler ────────────────────────────
@app.get("/")
def root():
    return {
        "durum": "aktif",
        "uygulama": "Arsac Metal ERP API",
        "versiyon": "2.0.0",
        "mimari": "katmanli",
        "zaman": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    }

@app.get("/saglik")
def saglik():
    return {
        "durum": "ok",
        "zaman": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    }

# ── Mobil uygulama ────────────────────────────────
@app.get("/mobile", response_class=HTMLResponse)
def mobile_app():
    yol = "/opt/arsac/static/mobile_app.html"
    try:
        with open(yol, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Mobil uygulama bulunamadı</h1>"
