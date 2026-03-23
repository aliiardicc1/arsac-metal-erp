"""
Arsac Metal ERP — Stok & Müşteri Router
"""
from fastapi import APIRouter, Depends, HTTPException
from core.database import get_db
from core.auth import token_dogrula
from models.schemas import StokIstek, StokGuncelle

router = APIRouter(tags=["Stok"])


# ── Stok ──────────────────────────────────────────
stok_router = APIRouter(prefix="/stok", tags=["Stok"])

@stok_router.get("")
def stok_listele(kullanici: str = Depends(token_dogrula), db=Depends(get_db)):
    conn, cursor = db
    cursor.execute("SELECT * FROM stok ORDER BY malzeme")
    return [dict(r) for r in cursor.fetchall()]

@stok_router.post("")
def stok_ekle(istek: StokIstek, kullanici: str = Depends(token_dogrula), db=Depends(get_db)):
    conn, cursor = db
    cursor.execute(
        "INSERT INTO stok (stok_kodu, malzeme, adet, en, boy, kalinlik, kg) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id",
        (istek.stok_kodu, istek.malzeme, istek.adet, istek.en, istek.boy, istek.kalinlik, istek.kg))
    row = cursor.fetchone()
    conn.commit()
    return {"id": row["id"], "durum": "ok"}

@stok_router.put("/{stok_id}")
def stok_guncelle(stok_id: int, istek: StokGuncelle, kullanici: str = Depends(token_dogrula), db=Depends(get_db)):
    conn, cursor = db
    if istek.adet is not None:
        cursor.execute("UPDATE stok SET adet=%s WHERE id=%s", (istek.adet, stok_id))
    if istek.durum is not None:
        cursor.execute("UPDATE stok SET durum=%s WHERE id=%s", (istek.durum, stok_id))
    conn.commit()
    return {"durum": "ok"}


# ── Müşteriler ────────────────────────────────────
musteri_router = APIRouter(prefix="/musteriler", tags=["Musteriler"])

@musteri_router.get("")
def musteriler_listele(kullanici: str = Depends(token_dogrula), db=Depends(get_db)):
    conn, cursor = db
    cursor.execute("SELECT DISTINCT musteri FROM siparisler WHERE musteri IS NOT NULL ORDER BY musteri")
    return [r["musteri"] for r in cursor.fetchall()]

@musteri_router.post("")
def musteri_ekle(istek: dict, kullanici: str = Depends(token_dogrula), db=Depends(get_db)):
    return {"durum": "ok"}
