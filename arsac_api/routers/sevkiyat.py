"""
Arsac Metal ERP — Sevkiyat & Özet Router
"""
from fastapi import APIRouter, Depends
from core.database import get_db
from core.auth import token_dogrula
from models.schemas import SevkiyatIstek

sevkiyat_router = APIRouter(prefix="/sevkiyatlar", tags=["Sevkiyat"])

@sevkiyat_router.get("")
def sevkiyatlar_listele(kullanici: str = Depends(token_dogrula), db=Depends(get_db)):
    conn, cursor = db
    cursor.execute("SELECT * FROM sevkiyatlar ORDER BY id DESC LIMIT 200")
    return [dict(r) for r in cursor.fetchall()]

@sevkiyat_router.post("")
def sevkiyat_olustur(istek: SevkiyatIstek, kullanici: str = Depends(token_dogrula), db=Depends(get_db)):
    conn, cursor = db
    from datetime import datetime
    cursor.execute(
        "INSERT INTO sevkiyatlar (plaka, sofor, telefon, tarih, durum, siparis_listesi, notlar) VALUES (%s,%s,%s,%s,'Yolda',%s,%s) RETURNING id",
        (istek.plaka, istek.sofor, istek.telefon,
         datetime.now().strftime("%d.%m.%Y"),
         istek.siparis_listesi, istek.notlar))
    row = cursor.fetchone()
    conn.commit()
    return {"id": row["id"], "durum": "ok"}


# ── Özet ──────────────────────────────────────────
ozet_router = APIRouter(tags=["Ozet"])

@ozet_router.get("/ozet")
def ozet(kullanici: str = Depends(token_dogrula), db=Depends(get_db)):
    conn, cursor = db
    result = {}
    sorgular = [
        ("toplam_siparis",    "SELECT COUNT(*) FROM siparisler"),
        ("bekleyen_siparis",  "SELECT COUNT(*) FROM siparisler WHERE durum='Beklemede'"),
        ("toplam_is",         "SELECT COUNT(*) FROM isler"),
        ("devam_eden_is",     "SELECT COUNT(*) FROM isler WHERE durum='Uretimde'"),
        ("toplam_sevkiyat",   "SELECT COUNT(*) FROM sevkiyatlar"),
        ("toplam_stok_kalemi","SELECT COUNT(*) FROM stok"),
        ("kritik_stok",       "SELECT COUNT(*) FROM stok WHERE durum=1 OR adet=0"),
        ("toplam_musteri",    "SELECT COUNT(DISTINCT musteri) FROM siparisler WHERE musteri IS NOT NULL"),
        ("bekleyen_sevk",     "SELECT COUNT(*) FROM parca_sevk_bekliyor WHERE durum='Bekliyor'"),
    ]
    for key, sql in sorgular:
        try:
            cursor.execute(sql)
            row = cursor.fetchone()
            result[key] = list(row.values())[0] if row else 0
        except Exception:
            result[key] = 0
    return result
