"""
Arsac Metal ERP — Cariler / Tedarikçiler Router
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from core.database import get_db
from core.auth import token_dogrula, token_bilgi
from models.schemas import CariGir, CariGuncelle

router = APIRouter(prefix="/cariler", tags=["Cariler"])


def _log(cursor, conn, kullanici, islem, detay=""):
    try:
        cursor.execute(
            "INSERT INTO kullanici_log (kullanici, islem, detay, tarih) VALUES (%s,%s,%s,%s)",
            (kullanici, islem, detay, datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
        )
    except:
        pass


@router.get("")
def carileri_listele(db=Depends(get_db), _=Depends(token_dogrula)):
    conn, cursor = db
    cursor.execute("SELECT * FROM tedarikciler ORDER BY firma_adi")
    return cursor.fetchall()


@router.get("/{cari_id}")
def cari_detay(cari_id: int, db=Depends(get_db), _=Depends(token_dogrula)):
    conn, cursor = db
    cursor.execute("SELECT * FROM tedarikciler WHERE id=%s", (cari_id,))
    cari = cursor.fetchone()
    if not cari:
        raise HTTPException(404, "Cari bulunamadı")

    cursor.execute(
        "SELECT * FROM satinalma_kayitlari WHERE firma=%s ORDER BY id DESC LIMIT 20",
        (cari["firma_adi"],)
    )
    islemler = cursor.fetchall()
    return {**dict(cari), "islemler": islemler}


@router.post("")
def cari_ekle(istek: CariGir, db=Depends(get_db), bilgi=Depends(token_bilgi)):
    conn, cursor = db
    now = datetime.now().strftime("%d.%m.%Y")
    try:
        cursor.execute("""
            INSERT INTO tedarikciler
            (firma_adi, iban, vergi_no, telefon, email, adres, notlar, kredi_limit, olusturma)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (istek.firma_adi, istek.iban, istek.vergi_no, istek.telefon,
              istek.email, istek.adres, istek.notlar, istek.kredi_limit, now))
        _log(cursor, conn, bilgi["sub"], "CARI_EKLE", istek.firma_adi)
        conn.commit()
        return {"mesaj": "Cari eklendi"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(400, f"Firma adı zaten kayıtlı: {e}")


@router.put("/{cari_id}")
def cari_guncelle(cari_id: int, istek: CariGuncelle, db=Depends(get_db), bilgi=Depends(token_bilgi)):
    conn, cursor = db
    alanlar, degerler = [], []
    for alan, deger in istek.dict(exclude_none=True).items():
        alanlar.append(f"{alan}=%s")
        degerler.append(deger)
    if not alanlar:
        raise HTTPException(400, "Güncellenecek alan yok")
    degerler.append(cari_id)
    cursor.execute(f"UPDATE tedarikciler SET {', '.join(alanlar)} WHERE id=%s", degerler)
    _log(cursor, conn, bilgi["sub"], "CARI_GUNCELLE", f"ID:{cari_id}")
    conn.commit()
    return {"mesaj": "Güncellendi"}


@router.delete("/{cari_id}")
def cari_sil(cari_id: int, db=Depends(get_db), bilgi=Depends(token_bilgi)):
    conn, cursor = db
    cursor.execute("SELECT firma_adi FROM tedarikciler WHERE id=%s", (cari_id,))
    r = cursor.fetchone()
    if not r:
        raise HTTPException(404, "Cari bulunamadı")
    cursor.execute("DELETE FROM tedarikciler WHERE id=%s", (cari_id,))
    _log(cursor, conn, bilgi["sub"], "CARI_SIL", r["firma_adi"])
    conn.commit()
    return {"mesaj": "Silindi"}
