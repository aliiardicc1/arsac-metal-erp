"""
Arsac Metal ERP — FastAPI Ana Uygulama v2.0
============================================
Katmanlı mimari:
  core/       → Veritabanı, auth, hata yönetimi
  models/     → Pydantic şemaları
  routers/    → Endpoint grupları

Yeni endpoint eklemek:
  1. routers/ altına dosya ekle
  2. include_router satırı ekle
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.requests import Request
from datetime import datetime
import os, logging

from routers.kullanicilar import router as kullanici_router
from routers.siparisler   import router as siparis_router
from routers.uretim       import router as uretim_router
from routers.stok         import stok_router, musteri_router
from routers.sevkiyat     import sevkiyat_router, ozet_router
from routers.sorgu        import router as sorgu_router

# Loglama
os.makedirs("/opt/arsac/logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("/opt/arsac/logs/api.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("arsac")

app = FastAPI(
    title="Arsac Metal ERP API",
    version="2.0.0",
    description="Katmanlı mimari — Arsac Metal ERP",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global hata handler
@app.exception_handler(Exception)
async def genel_hata(request: Request, exc: Exception):
    logger.error(f"HATA | {request.url.path} | {type(exc).__name__}: {exc}")
    return JSONResponse(status_code=500, content={"hata": "Sunucu hatasi", "detay": str(exc)})

@app.exception_handler(HTTPException)
async def http_hata(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"hata": exc.detail, "kod": exc.status_code})

# Router'lar
app.include_router(kullanici_router)
app.include_router(siparis_router)
app.include_router(uretim_router)
app.include_router(stok_router)
app.include_router(musteri_router)
app.include_router(sevkiyat_router)
app.include_router(ozet_router)
app.include_router(sorgu_router)

@app.get("/")
def root():
    return {"durum": "aktif", "uygulama": "Arsac Metal ERP API", "versiyon": "2.0.0", "mimari": "katmanli", "zaman": datetime.now().strftime("%d.%m.%Y %H:%M:%S")}

@app.get("/saglik")
def saglik():
    return {"durum": "ok", "zaman": datetime.now().strftime("%d.%m.%Y %H:%M:%S")}

@app.get("/mobile", response_class=HTMLResponse)
def mobile_app():
    yol = "/opt/arsac/static/mobile_app.html"
    try:
        with open(yol, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Mobil uygulama bulunamadi</h1>"
