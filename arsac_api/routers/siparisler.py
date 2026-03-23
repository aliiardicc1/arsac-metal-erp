"""
Arsac Metal ERP — Sipariş Router
"""
from fastapi import APIRouter, Depends, HTTPException
from core.database import get_db
from core.auth import token_dogrula
from models.schemas import SiparisIstek, SiparisDurumGuncelle

router = APIRouter(prefix="/siparisler", tags=["Siparisler"])


@router.get("")
def siparisler_listele(
    kullanici: str = Depends(token_dogrula),
    db=Depends(get_db)
):
    conn, cursor = db
    cursor.execute(
        "SELECT * FROM siparisler ORDER BY id DESC LIMIT 500")
    return [dict(r) for r in cursor.fetchall()]


@router.get("/{siparis_id}")
def siparis_getir(
    siparis_id: int,
    kullanici: str = Depends(token_dogrula),
    db=Depends(get_db)
):
    conn, cursor = db
    cursor.execute("SELECT * FROM siparisler WHERE id=%s", (siparis_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı")
    return dict(row)


@router.post("")
def siparis_olustur(
    istek: SiparisIstek,
    kullanici: str = Depends(token_dogrula),
    db=Depends(get_db)
):
    conn, cursor = db
    cursor.execute(
        "INSERT INTO siparisler (musteri, durum, tarih) VALUES (%s,%s,NOW()) RETURNING id",
        (istek.musteri_adi, istek.durum))
    row = cursor.fetchone()
    conn.commit()
    return {"id": row["id"], "durum": "ok"}


@router.put("/{siparis_id}")
def siparis_guncelle(
    siparis_id: int,
    istek: SiparisDurumGuncelle,
    kullanici: str = Depends(token_dogrula),
    db=Depends(get_db)
):
    conn, cursor = db
    cursor.execute(
        "UPDATE siparisler SET durum=%s WHERE id=%s",
        (istek.durum, siparis_id))
    conn.commit()
    return {"durum": "ok"}
