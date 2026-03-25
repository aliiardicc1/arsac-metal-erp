"""
Arsac Metal ERP — Satın Alma & Finans Router
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from core.database import get_db
from core.auth import token_dogrula, token_bilgi
from models.schemas import SatinalmaGir, OdemeIsaretle

router = APIRouter(prefix="/satinalma", tags=["Satın Alma"])


def _log(cursor, conn, kullanici, islem, detay=""):
    try:
        cursor.execute(
            "INSERT INTO kullanici_log (kullanici, islem, detay, tarih) VALUES (%s,%s,%s,%s)",
            (kullanici, islem, detay, datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
        )
    except:
        pass


@router.get("")
def satinalmalari_listele(odendi: int = -1, db=Depends(get_db), _=Depends(token_dogrula)):
    conn, cursor = db
    if odendi >= 0:
        cursor.execute(
            "SELECT * FROM satinalma_kayitlari WHERE odendi=%s ORDER BY id DESC",
            (odendi,)
        )
    else:
        cursor.execute("SELECT * FROM satinalma_kayitlari ORDER BY id DESC")
    return cursor.fetchall()


@router.get("/ozet")
def finans_ozet(db=Depends(get_db), _=Depends(token_dogrula)):
    conn, cursor = db

    def _toplam(sql):
        try:
            cursor.execute(sql)
            r = cursor.fetchone()
            return float(list(r.values())[0] or 0)
        except:
            return 0.0

    def _say(sql):
        try:
            cursor.execute(sql)
            r = cursor.fetchone()
            return int(list(r.values())[0] or 0)
        except:
            return 0

    toplam_borc = _toplam("SELECT SUM(toplam_tutar) FROM satinalma_kayitlari WHERE odendi=0 OR odendi IS NULL")
    odendi_toplam = _toplam("SELECT SUM(toplam_tutar) FROM satinalma_kayitlari WHERE odendi=1")

    vadesi_gecmis = _toplam("""
        SELECT SUM(toplam_tutar) FROM satinalma_kayitlari
        WHERE (odendi=0 OR odendi IS NULL)
        AND vade_tarihi IS NOT NULL AND vade_tarihi != ''
        AND TO_DATE(vade_tarihi, 'DD.MM.YYYY') < CURRENT_DATE
    """)

    yaklasan = _toplam("""
        SELECT SUM(toplam_tutar) FROM satinalma_kayitlari
        WHERE (odendi=0 OR odendi IS NULL)
        AND vade_tarihi IS NOT NULL AND vade_tarihi != ''
        AND TO_DATE(vade_tarihi, 'DD.MM.YYYY') BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '3 days'
    """)

    return {
        "toplam_borc":    round(toplam_borc, 2),
        "odendi_toplam":  round(odendi_toplam, 2),
        "vadesi_gecmis":  round(vadesi_gecmis, 2),
        "yaklasan_3_gun": round(yaklasan, 2),
    }


@router.post("")
def satinalma_ekle(istek: SatinalmaGir, db=Depends(get_db), bilgi=Depends(token_bilgi)):
    conn, cursor = db
    toplam = round(
        (istek.miktar or 0) * (istek.birim_fiyat or 0) + (istek.nakliye or 0), 2
    )
    now = datetime.now().strftime("%d.%m.%Y")
    cursor.execute("""
        INSERT INTO satinalma_kayitlari
        (firma, malzeme, miktar, birim_fiyat, nakliye, toplam_tutar,
         vade_tarihi, odeme_tipi, tarih, odendi)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,0)
    """, (istek.firma, istek.malzeme, istek.miktar, istek.birim_fiyat,
          istek.nakliye, toplam, istek.vade_tarihi, istek.odeme_tipi,
          istek.tarih or now))
    _log(cursor, conn, bilgi["sub"], "SATINALMA_EKLE",
         f"{istek.firma} | {istek.malzeme} | {toplam} TL")
    conn.commit()
    return {"mesaj": "Satın alma kaydedildi", "toplam": toplam}


@router.post("/{kayit_id}/odendi")
def odeme_isaretle(kayit_id: int, istek: OdemeIsaretle, db=Depends(get_db), bilgi=Depends(token_bilgi)):
    conn, cursor = db
    cursor.execute("SELECT firma, toplam_tutar FROM satinalma_kayitlari WHERE id=%s", (kayit_id,))
    r = cursor.fetchone()
    if not r:
        raise HTTPException(404, "Kayıt bulunamadı")
    now = datetime.now().strftime("%d.%m.%Y")
    cursor.execute(
        "UPDATE satinalma_kayitlari SET odendi=1, odeme_tarihi=%s WHERE id=%s",
        (istek.odeme_tarihi or now, kayit_id)
    )
    _log(cursor, conn, bilgi["sub"], "ODEME_YAPILDI",
         f"{r['firma']} | {r['toplam_tutar']} TL")
    conn.commit()
    return {"mesaj": "Ödeme işaretlendi"}


@router.delete("/{kayit_id}")
def satinalma_sil(kayit_id: int, db=Depends(get_db), bilgi=Depends(token_bilgi)):
    conn, cursor = db
    cursor.execute("SELECT firma, malzeme FROM satinalma_kayitlari WHERE id=%s", (kayit_id,))
    r = cursor.fetchone()
    if not r:
        raise HTTPException(404, "Kayıt bulunamadı")
    cursor.execute("DELETE FROM satinalma_kayitlari WHERE id=%s", (kayit_id,))
    _log(cursor, conn, bilgi["sub"], "SATINALMA_SIL", f"{r['firma']} | {r['malzeme']}")
    conn.commit()
    return {"mesaj": "Silindi"}
