"""
Arsac Metal ERP — Üretim Router
"""
from fastapi import APIRouter, Depends, HTTPException
from core.database import get_db
from core.auth import token_dogrula
from models.schemas import IsEmriIstek, IsDurumGuncelle

router = APIRouter(prefix="/isler", tags=["Uretim"])


@router.get("")
def isler_listele(
    kullanici: str = Depends(token_dogrula),
    db=Depends(get_db)
):
    conn, cursor = db
    cursor.execute(
        "SELECT * FROM isler ORDER BY id DESC LIMIT 500")
    return [dict(r) for r in cursor.fetchall()]


@router.post("")
def is_olustur(
    istek: IsEmriIstek,
    kullanici: str = Depends(token_dogrula),
    db=Depends(get_db)
):
    conn, cursor = db
    from datetime import datetime
    cursor.execute(
        "INSERT INTO isler (is_no, musteri, tarih, durum, termin, ilerleme) VALUES (%s,%s,%s,%s,%s,0) RETURNING id",
        (istek.is_no, istek.musteri,
         istek.tarih or datetime.now().strftime("%d.%m.%Y"),
         istek.durum, istek.termin))
    row = cursor.fetchone()
    conn.commit()
    return {"id": row["id"], "durum": "ok"}


@router.put("/{is_id}/durum")
def is_durum_guncelle(
    is_id: int,
    istek: IsDurumGuncelle,
    kullanici: str = Depends(token_dogrula),
    db=Depends(get_db)
):
    conn, cursor = db
    if istek.ilerleme is not None:
        cursor.execute(
            "UPDATE isler SET durum=%s, ilerleme=%s WHERE id=%s",
            (istek.durum, istek.ilerleme, is_id))
    else:
        cursor.execute(
            "UPDATE isler SET durum=%s WHERE id=%s",
            (istek.durum, is_id))
    conn.commit()
    return {"durum": "ok"}
