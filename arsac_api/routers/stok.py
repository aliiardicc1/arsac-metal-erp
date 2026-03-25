"""
Arsac Metal ERP — Stok Router
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from core.database import get_db
from core.auth import token_dogrula, token_bilgi
from models.schemas import StokGir, StokGuncelle

stok_router   = APIRouter(prefix="/stok",    tags=["Stok"])
musteri_router = APIRouter(prefix="/musteriler", tags=["Müşteriler"])


@stok_router.get("")
def stok_listele(durum: int = -1, db=Depends(get_db), _=Depends(token_dogrula)):
    conn, cursor = db
    if durum >= 0:
        cursor.execute("SELECT * FROM stok WHERE durum=%s ORDER BY id DESC", (durum,))
    else:
        cursor.execute("SELECT * FROM stok ORDER BY id DESC")
    return cursor.fetchall()


@stok_router.post("")
def stok_ekle(istek: StokGir, db=Depends(get_db), bilgi=Depends(token_bilgi)):
    conn, cursor = db
    now = datetime.now().strftime("%d.%m.%Y")
    cursor.execute("""
        INSERT INTO stok (stok_kodu, malzeme, adet, en, boy, kalinlik, kg, son_firma, son_tarih, durum)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (istek.stok_kodu, istek.malzeme, istek.adet, istek.en, istek.boy,
          istek.kalinlik, istek.kg, istek.son_firma, istek.son_tarih or now, istek.durum))
    _log(cursor, conn, bilgi["sub"], "STOK_EKLE", f"{istek.stok_kodu} | {istek.malzeme}")
    conn.commit()
    return {"mesaj": "Stok eklendi"}


@stok_router.put("/{stok_id}")
def stok_guncelle(stok_id: int, istek: StokGuncelle, db=Depends(get_db), bilgi=Depends(token_bilgi)):
    conn, cursor = db
    alanlar, degerler = [], []
    if istek.durum is not None:
        alanlar.append("durum=%s"); degerler.append(istek.durum)
    if istek.kg is not None:
        alanlar.append("kg=%s"); degerler.append(istek.kg)
    if istek.son_firma is not None:
        alanlar.append("son_firma=%s"); degerler.append(istek.son_firma)
    if istek.son_tarih is not None:
        alanlar.append("son_tarih=%s"); degerler.append(istek.son_tarih)
    if not alanlar:
        raise HTTPException(400, "Güncellenecek alan yok")
    degerler.append(stok_id)
    cursor.execute(f"UPDATE stok SET {', '.join(alanlar)} WHERE id=%s", degerler)
    _log(cursor, conn, bilgi["sub"], "STOK_GUNCELLE", f"ID:{stok_id}")
    conn.commit()
    return {"mesaj": "Güncellendi"}


@stok_router.delete("/{stok_id}")
def stok_sil(stok_id: int, db=Depends(get_db), bilgi=Depends(token_bilgi)):
    conn, cursor = db
    cursor.execute("SELECT stok_kodu, malzeme FROM stok WHERE id=%s", (stok_id,))
    r = cursor.fetchone()
    if not r:
        raise HTTPException(404, "Stok bulunamadı")
    cursor.execute("DELETE FROM stok WHERE id=%s", (stok_id,))
    _log(cursor, conn, bilgi["sub"], "STOK_SIL", f"{r['stok_kodu']} | {r['malzeme']}")
    conn.commit()
    return {"mesaj": "Silindi"}


@stok_router.post("/{stok_id}/depo-giris")
def depo_giris(stok_id: int, db=Depends(get_db), bilgi=Depends(token_bilgi)):
    conn, cursor = db
    cursor.execute("SELECT stok_kodu, malzeme, kg FROM stok WHERE id=%s", (stok_id,))
    r = cursor.fetchone()
    if not r:
        raise HTTPException(404, "Stok bulunamadı")
    cursor.execute("UPDATE stok SET durum=1 WHERE id=%s", (stok_id,))
    _log(cursor, conn, bilgi["sub"], "STOK_DEPO_GIRIS",
         f"{r['stok_kodu']} | {r['malzeme']} | {r['kg']} KG")
    conn.commit()
    return {"mesaj": "Depo girişi yapıldı"}


# ── Müşteriler (tedarikciler tablosu) ──────────────────
@musteri_router.get("")
def musterileri_listele(db=Depends(get_db), _=Depends(token_dogrula)):
    conn, cursor = db
    cursor.execute("SELECT * FROM tedarikciler ORDER BY firma_adi")
    return cursor.fetchall()


def _log(cursor, conn, kullanici, islem, detay=""):
    try:
        cursor.execute(
            "INSERT INTO kullanici_log (kullanici, islem, detay, tarih) VALUES (%s,%s,%s,%s)",
            (kullanici, islem, detay, datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
        )
    except:
        pass
