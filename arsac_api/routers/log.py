"""
Arsac Metal ERP — Log Router
"""
from datetime import datetime
from fastapi import APIRouter, Depends
from core.database import get_db
from core.auth import token_dogrula, yonetici_dogrula
from models.schemas import LogGir

router = APIRouter(prefix="/log", tags=["Log"])


@router.get("")
def log_listele(limit: int = 200, kullanici: str = "", db=Depends(get_db), _=Depends(yonetici_dogrula)):
    conn, cursor = db
    if kullanici:
        cursor.execute(
            "SELECT * FROM kullanici_log WHERE kullanici=%s ORDER BY id DESC LIMIT %s",
            (kullanici, limit)
        )
    else:
        cursor.execute(
            "SELECT * FROM kullanici_log ORDER BY id DESC LIMIT %s", (limit,)
        )
    return cursor.fetchall()


@router.post("")
def log_yaz(istek: LogGir, db=Depends(get_db), bilgi=Depends(token_dogrula)):
    conn, cursor = db
    cursor.execute(
        "INSERT INTO kullanici_log (kullanici, islem, detay, tarih) VALUES (%s,%s,%s,%s)",
        (bilgi, istek.islem, istek.detay, datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
    )
    conn.commit()
    return {"mesaj": "Log yazıldı"}
