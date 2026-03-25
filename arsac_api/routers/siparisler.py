"""
Arsac Metal ERP — Siparişler Router
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from core.database import get_db
from core.auth import token_dogrula, token_bilgi
from models.schemas import SiparisGir, SiparisGuncelle

router = APIRouter(prefix="/siparisler", tags=["Siparişler"])


def _log(cursor, conn, kullanici, islem, detay=""):
    try:
        cursor.execute(
            "INSERT INTO kullanici_log (kullanici, islem, detay, tarih) VALUES (%s,%s,%s,%s)",
            (kullanici, islem, detay, datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
        )
    except:
        pass


def _sip_no_uret(cursor) -> str:
    cursor.execute("SELECT COUNT(*) FROM siparisler")
    r = cursor.fetchone()
    sayi = list(r.values())[0] + 1
    return f"SIP-{datetime.now().strftime('%Y%m')}-{sayi:04d}"


@router.get("")
def siparisleri_listele(durum: str = "", db=Depends(get_db), _=Depends(token_dogrula)):
    conn, cursor = db
    if durum:
        cursor.execute("SELECT * FROM siparisler WHERE durum=%s ORDER BY id DESC", (durum,))
    else:
        cursor.execute("SELECT * FROM siparisler ORDER BY id DESC")
    return cursor.fetchall()


@router.get("/{siparis_id}")
def siparis_detay(siparis_id: int, db=Depends(get_db), _=Depends(token_dogrula)):
    conn, cursor = db
    cursor.execute("SELECT * FROM siparisler WHERE id=%s", (siparis_id,))
    siparis = cursor.fetchone()
    if not siparis:
        raise HTTPException(404, "Sipariş bulunamadı")
    cursor.execute("SELECT * FROM siparis_kalemleri WHERE siparis_id=%s", (siparis_id,))
    kalemleri = cursor.fetchall()
    return {**dict(siparis), "kalemleri": kalemleri}


@router.post("")
def siparis_olustur(istek: SiparisGir, db=Depends(get_db), bilgi=Depends(token_bilgi)):
    conn, cursor = db
    sip_no = _sip_no_uret(cursor)
    now = datetime.now().strftime("%d.%m.%Y")

    # KDV hesapla
    ara_toplam = sum(
        k.adet * k.birim_fiyat for k in istek.kalemleri
    ) if istek.kalemleri else 0
    kdv_oran  = istek.kdv_oran or 20
    kdv_tutar = round(ara_toplam * kdv_oran / 100, 2)
    genel_toplam = round(ara_toplam + kdv_tutar, 2)

    cursor.execute("""
        INSERT INTO siparisler
        (sip_no, musteri, yetkili, telefon, musteri_sip_no, tarih, termin,
         durum, ara_toplam, kdv_oran, kdv_tutar, genel_toplam,
         odeme_sekli, notlar, olusturan)
        VALUES (%s,%s,%s,%s,%s,%s,%s,'Alindi',%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
    """, (sip_no, istek.musteri, istek.yetkili, istek.telefon, istek.musteri_sip_no,
          now, istek.termin, round(ara_toplam,2), kdv_oran, kdv_tutar, genel_toplam,
          istek.odeme_sekli, istek.notlar, bilgi["sub"]))

    siparis_id = cursor.fetchone()["id"]

    for k in (istek.kalemleri or []):
        toplam = round(k.adet * k.birim_fiyat, 2)
        cursor.execute("""
            INSERT INTO siparis_kalemleri
            (siparis_id, urun_adi, adet, birim, birim_fiyat, toplam_fiyat,
             kdv_oran, malzeme, kalinlik, en, boy, kg, fiyat_turu)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (siparis_id, k.urun_adi, k.adet, k.birim, k.birim_fiyat, toplam,
              k.kdv_oran, k.malzeme, k.kalinlik, k.en, k.boy, k.kg, k.fiyat_turu))

    _log(cursor, conn, bilgi["sub"], "SIPARIS_OLUSTUR",
         f"{sip_no} | {istek.musteri} | {genel_toplam} TL")
    conn.commit()
    return {"mesaj": "Sipariş oluşturuldu", "sip_no": sip_no, "id": siparis_id}


@router.put("/{siparis_id}")
def siparis_guncelle(siparis_id: int, istek: SiparisGuncelle, db=Depends(get_db), bilgi=Depends(token_bilgi)):
    conn, cursor = db
    alanlar, degerler = [], []
    for alan, deger in istek.dict(exclude_none=True).items():
        alanlar.append(f"{alan}=%s")
        degerler.append(deger)
    if not alanlar:
        raise HTTPException(400, "Güncellenecek alan yok")
    degerler.append(siparis_id)
    cursor.execute(f"UPDATE siparisler SET {', '.join(alanlar)} WHERE id=%s", degerler)
    _log(cursor, conn, bilgi["sub"], "SIPARIS_GUNCELLE", f"ID:{siparis_id}")
    conn.commit()
    return {"mesaj": "Güncellendi"}


@router.delete("/{siparis_id}")
def siparis_sil(siparis_id: int, db=Depends(get_db), bilgi=Depends(token_bilgi)):
    conn, cursor = db
    cursor.execute("SELECT sip_no, musteri FROM siparisler WHERE id=%s", (siparis_id,))
    r = cursor.fetchone()
    if not r:
        raise HTTPException(404, "Sipariş bulunamadı")
    cursor.execute("DELETE FROM siparis_kalemleri WHERE siparis_id=%s", (siparis_id,))
    cursor.execute("DELETE FROM siparisler WHERE id=%s", (siparis_id,))
    _log(cursor, conn, bilgi["sub"], "SIPARIS_SIL", f"{r['sip_no']} | {r['musteri']}")
    conn.commit()
    return {"mesaj": "Silindi"}
