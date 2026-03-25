"""
Arsac Metal ERP — Hammadde Talepler Router
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from core.database import get_db
from core.auth import token_dogrula, token_bilgi
from models.schemas import TalepGir, TalepGuncelle

router = APIRouter(prefix="/talepler", tags=["Talepler"])


def _log(cursor, conn, kullanici, islem, detay=""):
    try:
        cursor.execute(
            "INSERT INTO kullanici_log (kullanici, islem, detay, tarih) VALUES (%s,%s,%s,%s)",
            (kullanici, islem, detay, datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
        )
    except:
        pass


@router.get("")
def talepler_listele(durum: int = -1, db=Depends(get_db), _=Depends(token_dogrula)):
    conn, cursor = db
    if durum >= 0:
        cursor.execute("SELECT * FROM talepler WHERE durum=%s ORDER BY id DESC", (durum,))
    else:
        cursor.execute("SELECT * FROM talepler ORDER BY id DESC")
    return cursor.fetchall()


@router.post("")
def talep_ekle(istek: TalepGir, db=Depends(get_db), bilgi=Depends(token_bilgi)):
    conn, cursor = db
    now = datetime.now().strftime("%d.%m.%Y")

    # KG hesapla
    kg = istek.kg
    if not kg or kg == 0:
        kg = (istek.en * istek.boy * istek.kalinlik * 7.85) / 1_000_000 * (istek.adet_tabaka or 1)

    # Talep no
    cursor.execute("SELECT COUNT(*) FROM talepler")
    r = cursor.fetchone()
    sayi = list(r.values())[0] + 1
    talep_no = f"T{datetime.now().strftime('%Y%m%d')}-{sayi:04d}"

    cursor.execute("""
        INSERT INTO talepler (talep_no, kalite, en, boy, kalinlik, adet_tabaka, kg, durum, tarih)
        VALUES (%s,%s,%s,%s,%s,%s,%s,0,%s)
    """, (talep_no, istek.kalite, istek.en, istek.boy, istek.kalinlik,
          istek.adet_tabaka or 1, round(kg, 2), istek.tarih or now))

    _log(cursor, conn, bilgi["sub"], "TALEP_GIRIS",
         f"{istek.kalite} | {istek.en}x{istek.boy}x{istek.kalinlik}mm | {round(kg,2)} KG")
    conn.commit()
    return {"mesaj": "Talep eklendi", "talep_no": talep_no}


@router.put("/{talep_id}")
def talep_guncelle(talep_id: int, istek: TalepGuncelle, db=Depends(get_db), bilgi=Depends(token_bilgi)):
    conn, cursor = db
    cursor.execute("UPDATE talepler SET durum=%s WHERE id=%s", (istek.durum, talep_id))
    _log(cursor, conn, bilgi["sub"], "TALEP_GUNCELLE", f"ID:{talep_id} durum:{istek.durum}")
    conn.commit()
    return {"mesaj": "Güncellendi"}


@router.delete("/{talep_id}")
def talep_sil(talep_id: int, db=Depends(get_db), bilgi=Depends(token_bilgi)):
    conn, cursor = db
    cursor.execute("SELECT kalite, kg FROM talepler WHERE id=%s", (talep_id,))
    r = cursor.fetchone()
    if not r:
        raise HTTPException(404, "Talep bulunamadı")
    cursor.execute("DELETE FROM talepler WHERE id=%s", (talep_id,))
    _log(cursor, conn, bilgi["sub"], "TALEP_SIL", f"ID:{talep_id} | {r['kalite']}")
    conn.commit()
    return {"mesaj": "Silindi"}
