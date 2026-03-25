"""
Arsac Metal ERP — Sevkiyat Router
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from core.database import get_db
from core.auth import token_dogrula, token_bilgi
from models.schemas import SevkiyatGir, SevkiyatGuncelle

sevkiyat_router = APIRouter(prefix="/sevkiyat", tags=["Sevkiyat"])
ozet_router     = APIRouter(tags=["Sevkiyat Özet"])


def _log(cursor, conn, kullanici, islem, detay=""):
    try:
        cursor.execute(
            "INSERT INTO kullanici_log (kullanici, islem, detay, tarih) VALUES (%s,%s,%s,%s)",
            (kullanici, islem, detay, datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
        )
    except:
        pass


@sevkiyat_router.get("")
def sevkiyatlari_listele(db=Depends(get_db), _=Depends(token_dogrula)):
    conn, cursor = db
    cursor.execute("SELECT * FROM sevkiyatlar ORDER BY id DESC")
    return cursor.fetchall()


@sevkiyat_router.post("")
def sevkiyat_olustur(istek: SevkiyatGir, db=Depends(get_db), bilgi=Depends(token_bilgi)):
    conn, cursor = db
    now = datetime.now().strftime("%d.%m.%Y")
    cursor.execute("""
        INSERT INTO sevkiyatlar (plaka, sofor, telefon, tarih, siparis_listesi, notlar, durum)
        VALUES (%s,%s,%s,%s,%s,%s,'Yolda')
        RETURNING id
    """, (istek.plaka, istek.sofor, istek.telefon,
          istek.tarih or now, istek.siparis_listesi, istek.notlar))
    sevk_id = cursor.fetchone()["id"]
    _log(cursor, conn, bilgi["sub"], "SEVKIYAT_OLUSTUR",
         f"Plaka:{istek.plaka} | {istek.sofor}")
    conn.commit()
    return {"mesaj": "Sevkiyat oluşturuldu", "id": sevk_id}


@sevkiyat_router.put("/{sevk_id}")
def sevkiyat_guncelle(sevk_id: int, istek: SevkiyatGuncelle, db=Depends(get_db), bilgi=Depends(token_bilgi)):
    conn, cursor = db
    cursor.execute("UPDATE sevkiyatlar SET durum=%s WHERE id=%s", (istek.durum, sevk_id))
    _log(cursor, conn, bilgi["sub"], "SEVKIYAT_DURUM", f"ID:{sevk_id} → {istek.durum}")
    conn.commit()
    return {"mesaj": "Güncellendi"}


@sevkiyat_router.get("/bekleyenler")
def sevk_bekleyenleri_listele(db=Depends(get_db), _=Depends(token_dogrula)):
    conn, cursor = db
    cursor.execute("""
        SELECT p.*, s.sip_no, s.musteri
        FROM parca_sevk_bekliyor p
        LEFT JOIN siparisler s ON p.siparis_id = s.id
        WHERE p.durum='Bekliyor'
        ORDER BY p.id DESC
    """)
    return cursor.fetchall()


@ozet_router.get("/sevkiyat/ozet")
def sevkiyat_ozet(db=Depends(get_db), _=Depends(token_dogrula)):
    conn, cursor = db
    cursor.execute("SELECT COUNT(*) FROM sevkiyatlar WHERE durum='Yolda'")
    yolda = list(cursor.fetchone().values())[0]
    cursor.execute("SELECT COUNT(*) FROM sevkiyatlar WHERE durum='Teslim Edildi'")
    teslim = list(cursor.fetchone().values())[0]
    cursor.execute("SELECT COUNT(*) FROM parca_sevk_bekliyor WHERE durum='Bekliyor'")
    bekliyor = list(cursor.fetchone().values())[0]
    return {"yolda": yolda, "teslim_edildi": teslim, "bekleyen_parcalar": bekliyor}
