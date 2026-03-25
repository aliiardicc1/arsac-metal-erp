"""
Arsac Metal ERP — Üretim Router
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from core.database import get_db
from core.auth import token_dogrula, token_bilgi
from models.schemas import IsGir, ParcaGir, ParcaGuncelle, YerlesimGir

router = APIRouter(prefix="/uretim", tags=["Üretim"])


def _log(cursor, conn, kullanici, islem, detay=""):
    try:
        cursor.execute(
            "INSERT INTO kullanici_log (kullanici, islem, detay, tarih) VALUES (%s,%s,%s,%s)",
            (kullanici, islem, detay, datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
        )
    except:
        pass


# ── İşler ────────────────────────────────────────────
@router.get("/isler")
def isleri_listele(durum: str = "", db=Depends(get_db), _=Depends(token_dogrula)):
    conn, cursor = db
    if durum:
        cursor.execute("SELECT * FROM isler WHERE durum=%s ORDER BY id DESC", (durum,))
    else:
        cursor.execute("SELECT * FROM isler ORDER BY id DESC")
    isler = cursor.fetchall()
    sonuc = []
    for is_ in isler:
        cursor.execute("SELECT * FROM parcalar WHERE is_no=%s", (is_["is_no"],))
        parcalar = cursor.fetchall()
        sonuc.append({**dict(is_), "parcalar": parcalar})
    return sonuc


@router.post("/isler")
def is_olustur(istek: IsGir, db=Depends(get_db), bilgi=Depends(token_bilgi)):
    conn, cursor = db
    cursor.execute("SELECT COUNT(*) FROM isler")
    r = cursor.fetchone()
    sayi = list(r.values())[0] + 1
    is_no = f"IS-{datetime.now().strftime('%Y%m%d')}-{sayi:04d}"
    now = datetime.now().strftime("%d.%m.%Y")
    cursor.execute("""
        INSERT INTO isler (is_no, sip_no, musteri, tarih, durum, termin, notlar)
        VALUES (%s,%s,%s,%s,'Beklemede',%s,%s)
    """, (is_no, istek.sip_no, istek.musteri, now, istek.termin, istek.notlar))
    _log(cursor, conn, bilgi["sub"], "IS_OLUSTUR", f"{is_no} | {istek.musteri}")
    conn.commit()
    return {"mesaj": "İş oluşturuldu", "is_no": is_no}


@router.put("/isler/{is_id}/durum")
def is_durum_guncelle(is_id: int, durum: str, db=Depends(get_db), bilgi=Depends(token_bilgi)):
    conn, cursor = db
    ilerleme = {"Beklemede": 0, "Devam Ediyor": 50, "Tamamlandı": 100}.get(durum, 0)
    cursor.execute("UPDATE isler SET durum=%s, ilerleme=%s WHERE id=%s", (durum, ilerleme, is_id))
    _log(cursor, conn, bilgi["sub"], "IS_DURUM", f"ID:{is_id} → {durum}")
    conn.commit()
    return {"mesaj": "Güncellendi"}


# ── Parçalar ─────────────────────────────────────────
@router.post("/parcalar")
def parca_ekle(istek: ParcaGir, db=Depends(get_db), bilgi=Depends(token_bilgi)):
    conn, cursor = db
    cursor.execute("""
        INSERT INTO parcalar (is_no, parca_adi, parca_kodu, adet, birim_kg, durum, gorsel_base64)
        VALUES (%s,%s,%s,%s,%s,'Beklemede',%s)
    """, (istek.is_no, istek.parca_adi, istek.parca_kodu, istek.adet,
          istek.birim_kg, istek.gorsel_base64))
    _log(cursor, conn, bilgi["sub"], "PARCA_EKLE", f"{istek.is_no} | {istek.parca_adi}")
    conn.commit()
    return {"mesaj": "Parça eklendi"}


@router.put("/parcalar/{parca_id}")
def parca_guncelle(parca_id: int, istek: ParcaGuncelle, db=Depends(get_db), bilgi=Depends(token_bilgi)):
    conn, cursor = db
    alanlar, degerler = [], []
    if istek.durum is not None:
        alanlar.append("durum=%s"); degerler.append(istek.durum)
    if istek.biten_adet is not None:
        alanlar.append("biten_adet=%s"); degerler.append(istek.biten_adet)
    if not alanlar:
        raise HTTPException(400, "Güncellenecek alan yok")
    degerler.append(parca_id)
    cursor.execute(f"UPDATE parcalar SET {', '.join(alanlar)} WHERE id=%s", degerler)
    _log(cursor, conn, bilgi["sub"], "PARCA_GUNCELLE", f"ID:{parca_id}")
    conn.commit()
    return {"mesaj": "Güncellendi"}


# ── Yerleşim Raporları ───────────────────────────────
@router.get("/yerlesimler")
def yerlesimler_listele(db=Depends(get_db), _=Depends(token_dogrula)):
    conn, cursor = db
    cursor.execute("SELECT * FROM yerlesim_raporlari ORDER BY id DESC")
    return cursor.fetchall()


@router.post("/yerlesimler")
def yerlesim_ekle(istek: YerlesimGir, db=Depends(get_db), bilgi=Depends(token_bilgi)):
    conn, cursor = db
    now = datetime.now().strftime("%d.%m.%Y")
    cursor.execute("""
        INSERT INTO yerlesim_raporlari
        (tarih, yerlesim_adi, makine, operator, baslangic_saati, bitis_saati, verim)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (now, istek.yerlesim_adi, istek.makine, istek.operator,
          istek.baslangic_saati, istek.bitis_saati, istek.verim))
    _log(cursor, conn, bilgi["sub"], "YERLESIM_EKLE", istek.yerlesim_adi)
    conn.commit()
    return {"mesaj": "Yerleşim eklendi"}
