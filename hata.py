"""
Arsac Metal ERP — Merkezi Hata Yönetimi & Loglama
===================================================
Tüm hatalar buradan geçer.
"""
import logging
import traceback
from datetime import datetime
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

# ── Loglama ayarı ─────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("/opt/arsac/logs/api.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("arsac")


def log_islem(kullanici: str, islem: str, detay: str = "", hata: bool = False):
    """İşlem logu yazar."""
    seviye = logger.error if hata else logger.info
    seviye(f"{kullanici} | {islem} | {detay}")


def log_hata(endpoint: str, hata: Exception, kullanici: str = "?"):
    """Hata logu yazar."""
    logger.error(f"HATA | {kullanici} | {endpoint} | {type(hata).__name__}: {hata}")


# ── Özel hata sınıfları ───────────────────────────
class YetkiHatasi(HTTPException):
    def __init__(self, detay: str = "Bu işlem için yetkiniz yok"):
        super().__init__(status_code=403, detail=detay)


class BulunamadiHatasi(HTTPException):
    def __init__(self, kayit: str = "Kayıt"):
        super().__init__(status_code=404, detail=f"{kayit} bulunamadı")


class DogrulamaHatasi(HTTPException):
    def __init__(self, detay: str = "Geçersiz veri"):
        super().__init__(status_code=422, detail=detay)


# ── Global hata handler'ları ──────────────────────
async def genel_hata_handler(request: Request, exc: Exception):
    """Yakalanmayan tüm hatalar buraya düşer."""
    logger.error(f"BEKLENMEDIK HATA | {request.url.path} | {traceback.format_exc()[-500:]}")
    return JSONResponse(
        status_code=500,
        content={
            "hata": "Sunucu hatası",
            "detay": "Beklenmedik bir hata oluştu. Lütfen tekrar deneyin.",
            "zaman": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        }
    )


async def http_hata_handler(request: Request, exc: HTTPException):
    """HTTP hatalarını standart formatta döner."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "hata": exc.detail,
            "kod": exc.status_code,
            "zaman": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        }
    )
