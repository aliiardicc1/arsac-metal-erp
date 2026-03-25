"""
Arsac Metal ERP — Muhasebe Router
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from core.database import get_db
from core.auth import token_dogrula, token_bilgi
from models.schemas import MakbuzGir

router = APIRouter(prefix="/muhasebe", tags=["Muhasebe"])


def _log(cursor, conn, kullanici, islem, detay=""):
    try:
        cursor.execute(
            "INSERT INTO kullanici_log (kullanici, islem, detay, tarih) VALUES (%s,%s,%s,%s)",
            (kullanici, islem, detay, datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
        )
    except:
        pass


def _makbuz_no_uret(cursor) -> str:
    cursor.execute("SELECT COUNT(*) FROM tediye_makbuzlari")
    r = cursor.fetchone()
    sayi = list(r.values())[0] + 1
    return f"MKB-{datetime.now().strftime('%Y%m')}-{sayi:04d}"


@router.get("/makbuzlar")
def makbuzlari_listele(tip: str = "", db=Depends(get_db), _=Depends(token_dogrula)):
    conn, cursor = db
    if tip:
        cursor.execute("SELECT * FROM tediye_makbuzlari WHERE tip=%s ORDER BY id DESC", (tip,))
    else:
        cursor.execute("SELECT * FROM tediye_makbuzlari ORDER BY id DESC")
    return cursor.fetchall()


@router.post("/makbuzlar")
def makbuz_olustur(istek: MakbuzGir, db=Depends(get_db), bilgi=Depends(token_bilgi)):
    conn, cursor = db
    makbuz_no = _makbuz_no_uret(cursor)
    now = datetime.now().strftime("%d.%m.%Y")
    cursor.execute("""
        INSERT INTO tediye_makbuzlari
        (makbuz_no, tip, firma, tarih, tutar, kalan_tutar, odeme_sekli,
         aciklama, siparis_no, olusturan)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (makbuz_no, istek.tip, istek.firma, istek.tarih or now,
          istek.tutar, istek.tutar, istek.odeme_sekli,
          istek.aciklama, istek.siparis_no, bilgi["sub"]))
    _log(cursor, conn, bilgi["sub"], "MAKBUZ_OLUSTUR",
         f"{makbuz_no} | {istek.firma} | {istek.tutar} TL")
    conn.commit()
    return {"mesaj": "Makbuz oluşturuldu", "makbuz_no": makbuz_no}


@router.get("/faturalar")
def faturalari_listele(db=Depends(get_db), _=Depends(token_dogrula)):
    conn, cursor = db
    cursor.execute("SELECT * FROM faturalar ORDER BY id DESC")
    return cursor.fetchall()


@router.get("/ozet")
def muhasebe_ozet(db=Depends(get_db), _=Depends(token_dogrula)):
    conn, cursor = db

    def _toplam(sql):
        try:
            cursor.execute(sql)
            r = cursor.fetchone()
            return float(list(r.values())[0] or 0)
        except:
            return 0.0

    tahsilat = _toplam("SELECT SUM(tutar) FROM tediye_makbuzlari WHERE tip='tahsilat'")
    tediye   = _toplam("SELECT SUM(tutar) FROM tediye_makbuzlari WHERE tip='tediye'")
    borc     = _toplam("SELECT SUM(toplam_tutar) FROM satinalma_kayitlari WHERE odendi=0 OR odendi IS NULL")

    return {
        "toplam_tahsilat": round(tahsilat, 2),
        "toplam_tediye":   round(tediye, 2),
        "acik_borc":       round(borc, 2),
        "net":             round(tahsilat - tediye, 2),
    }
