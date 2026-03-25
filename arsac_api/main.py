"""
Arsac Metal ERP — FastAPI Ana Uygulama v3.0
============================================
Tüm router'lar kayıtlı, CORS açık, sağlık endpoint'i var.

Başlatmak için:
  pip install fastapi uvicorn psycopg2-binary pyjwt python-dotenv
  uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Ortam değişkenleri (.env):
  DATABASE_URL=postgresql://kullanici:sifre@host:5432/arsac_db
  SECRET_KEY=gizli-anahtar
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from datetime import datetime
import logging, os

from core.database import db_saglik
from routers.kullanicilar import router as kullanici_router
from routers.ozet         import router as ozet_router
from routers.stok         import stok_router, musteri_router
from routers.talepler     import router as talep_router
from routers.siparisler   import router as siparis_router
from routers.uretim       import router as uretim_router
from routers.sevkiyat     import sevkiyat_router, ozet_router as sevk_ozet_router
from routers.satinalma    import router as satinalma_router
from routers.cariler      import router as cari_router
from routers.muhasebe     import router as muhasebe_router
from routers.log          import router as log_router
from routers.sorgu        import router as sorgu_router

# ── Loglama ──────────────────────────────────────────
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

# ── Uygulama ─────────────────────────────────────────
app = FastAPI(
    title="Arsac Metal ERP API",
    version="3.0.0",
    description="Arsac Metal ERP — Tam iskelet, tüm modüller kayıtlı",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global hata handler'ları ──────────────────────────
@app.exception_handler(Exception)
async def genel_hata(request: Request, exc: Exception):
    logger.error(f"HATA | {request.url.path} | {type(exc).__name__}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"hata": "Sunucu hatası", "detay": str(exc),
                 "zaman": datetime.now().strftime("%d.%m.%Y %H:%M:%S")}
    )

# ── Router kayıtları ──────────────────────────────────
app.include_router(kullanici_router)
app.include_router(ozet_router)
app.include_router(stok_router)
app.include_router(musteri_router)
app.include_router(talep_router)
app.include_router(siparis_router)
app.include_router(uretim_router)
app.include_router(sevkiyat_router)
app.include_router(sevk_ozet_router)
app.include_router(satinalma_router)
app.include_router(cari_router)
app.include_router(muhasebe_router)
app.include_router(log_router)
app.include_router(sorgu_router)

# ── Temel endpoint'ler ────────────────────────────────
@app.get("/")
def root():
    return {
        "uygulama": "Arsac Metal ERP API",
        "versiyon": "3.0.0",
        "durum":    "aktif",
        "zaman":    datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
    }

@app.get("/saglik")
def saglik():
    db = db_saglik()
    return {
        "durum":      db["durum"],
        "veritabani": db.get("veritabani", "?"),
        "zaman":      datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
    }

@app.get("/endpoints")
def endpoint_listesi():
    """Tüm kayıtlı endpoint'leri listeler."""
    return [
        {"yol": r.path, "metodlar": list(r.methods)}
        for r in app.routes
        if hasattr(r, "methods")
    ]
