"""
Arsac Metal ERP — FastAPI Sunucusu
===================================
• Kullanıcı girişi / token doğrulama
• Siparişler, üretim, sevkiyat, muhasebe, stok, cariler
• PostgreSQL üzerinde çalışır
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import hashlib
import secrets
import psycopg2
import psycopg2.extras
import os
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
#  UYGULAMA
# ═══════════════════════════════════════════════════════════════
app = FastAPI(title="Arsac Metal ERP API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════
#  VERİTABANI BAĞLANTISI
# ═══════════════════════════════════════════════════════════════
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
    "dbname": os.environ.get("DB_NAME", "arsac_db"),
    "user": os.environ.get("DB_USER", "arsac_user"),
    "password": os.environ.get("DB_PASS", "arsac2024"),
}

def get_db():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        yield conn, cursor
    finally:
        conn.close()

# ═══════════════════════════════════════════════════════════════
#  TOKEN DEPOSU (bellekte — yeniden başlatınca sıfırlanır)
# ═══════════════════════════════════════════════════════════════
_aktif_tokenlar = {}  # token -> kullanici_adi

def _sifre_hash(sifre):
    return hashlib.sha256(sifre.encode("utf-8")).hexdigest()

def token_dogrula(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "").strip()
    if token not in _aktif_tokenlar:
        raise HTTPException(status_code=401, detail="Geçersiz veya süresi dolmuş token")
    return _aktif_tokenlar[token]

# ═══════════════════════════════════════════════════════════════
#  MODELLER
# ═══════════════════════════════════════════════════════════════
class GirisIstek(BaseModel):
    kullanici_adi: str
    sifre: str

class SiparisIstek(BaseModel):
    musteri_adi: str
    teslim_tarihi: Optional[str] = None
    durum: Optional[str] = "Beklemede"
    toplam_tutar: Optional[float] = 0
    para_birimi: Optional[str] = "TL"
    notlar: Optional[str] = None
    yetkili: Optional[str] = None
    kdv_oran: Optional[float] = 20

class StokIstek(BaseModel):
    stok_kodu: Optional[str] = None
    ad: str
    kategori: Optional[str] = None
    birim: Optional[str] = "Adet"
    miktar: Optional[float] = 0
    min_miktar: Optional[float] = 0
    birim_fiyat: Optional[float] = 0
    para_birimi: Optional[str] = "TL"
    depo: Optional[str] = None
    notlar: Optional[str] = None

class MusteriIstek(BaseModel):
    musteri_kodu: Optional[str] = None
    ad: str
    telefon: Optional[str] = None
    email: Optional[str] = None
    adres: Optional[str] = None
    vergi_no: Optional[str] = None
    vergi_dairesi: Optional[str] = None
    notlar: Optional[str] = None

class IsIstek(BaseModel):
    siparis_id: Optional[int] = None
    sip_no: Optional[str] = None
    is_tanimi: str
    atanan: Optional[str] = None
    baslangic: Optional[str] = None
    bitis: Optional[str] = None
    durum: Optional[str] = "Beklemede"
    oncelik: Optional[str] = "Normal"
    notlar: Optional[str] = None

class SevkiyatIstek(BaseModel):
    siparis_id: Optional[int] = None
    musteri_adi: str
    tarih: Optional[str] = None
    arac: Optional[str] = None
    sofor: Optional[str] = None
    durum: Optional[str] = "Hazırlanıyor"
    toplam_kg: Optional[float] = 0
    notlar: Optional[str] = None

# ═══════════════════════════════════════════════════════════════
#  SAĞLIK KONTROLÜ
# ═══════════════════════════════════════════════════════════════
@app.get("/")
def anasayfa():
    return {"durum": "aktif", "uygulama": "Arsac Metal ERP API", "versiyon": "1.0.0"}

@app.get("/saglik")
def saglik():
    return {"durum": "ok", "zaman": datetime.now().strftime("%d.%m.%Y %H:%M:%S")}

# ═══════════════════════════════════════════════════════════════
#  GİRİŞ / ÇIKIŞ
# ═══════════════════════════════════════════════════════════════
@app.post("/giris")
def giris(istek: GirisIstek, db=Depends(get_db)):
    conn, cursor = db
    cursor.execute(
        "SELECT * FROM kullanicilar WHERE kullanici_adi=%s AND aktif=1",
        (istek.kullanici_adi,))
    kullanici = cursor.fetchone()
    if not kullanici or kullanici["sifre_hash"] != _sifre_hash(istek.sifre):
        raise HTTPException(status_code=401, detail="Kullanıcı adı veya şifre hatalı")

    token = secrets.token_hex(32)
    _aktif_tokenlar[token] = istek.kullanici_adi

    # Log
    cursor.execute(
        "INSERT INTO kullanici_log (tarih, kullanici, islem, detay) VALUES (%s, %s, %s, %s)",
        (datetime.now().strftime("%d.%m.%Y %H:%M"), istek.kullanici_adi, "giris", "Basarili giris"))
    conn.commit()

    return {
        "token": token,
        "kullanici_adi": kullanici["kullanici_adi"],
        "ad_soyad": kullanici["ad_soyad"],
        "rol": kullanici["rol"],
    }

@app.post("/cikis")
def cikis(kullanici: str = Depends(token_dogrula)):
    for t, k in list(_aktif_tokenlar.items()):
        if k == kullanici:
            del _aktif_tokenlar[t]
            break
    return {"mesaj": "Çıkış yapıldı"}

# ═══════════════════════════════════════════════════════════════
#  SİPARİŞLER
# ═══════════════════════════════════════════════════════════════
@app.get("/siparisler")
def siparisler_listele(kullanici: str = Depends(token_dogrula), db=Depends(get_db)):
    conn, cursor = db
    cursor.execute("SELECT * FROM siparisler ORDER BY id DESC")
    return cursor.fetchall()

@app.get("/siparisler/{siparis_id}")
def siparis_detay(siparis_id: int, kullanici: str = Depends(token_dogrula), db=Depends(get_db)):
    conn, cursor = db
    cursor.execute("SELECT * FROM siparisler WHERE id=%s", (siparis_id,))
    siparis = cursor.fetchone()
    if not siparis:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı")
    cursor.execute("SELECT * FROM siparis_kalemleri WHERE siparis_id=%s", (siparis_id,))
    kalemler = cursor.fetchall()
    return {"siparis": siparis, "kalemler": kalemler}

@app.post("/siparisler")
def siparis_ekle(istek: SiparisIstek, kullanici: str = Depends(token_dogrula), db=Depends(get_db)):
    conn, cursor = db
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    cursor.execute("SELECT COUNT(*) as sayi FROM siparisler")
    sayi = cursor.fetchone()["sayi"] + 1
    sip_no = "SIP-{:04d}".format(sayi)
    cursor.execute("""
        INSERT INTO siparisler
            (sip_no, musteri_adi, tarih, teslim_tarihi, durum, toplam_tutar,
             para_birimi, notlar, yetkili, kdv_oran, olusturma)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
    """, (sip_no, istek.musteri_adi, now, istek.teslim_tarihi, istek.durum,
          istek.toplam_tutar, istek.para_birimi, istek.notlar,
          istek.yetkili or kullanici, istek.kdv_oran, now))
    yeni_id = cursor.fetchone()["id"]
    conn.commit()
    return {"mesaj": "Sipariş eklendi", "id": yeni_id, "sip_no": sip_no}

@app.put("/siparisler/{siparis_id}")
def siparis_guncelle(siparis_id: int, istek: SiparisIstek,
                     kullanici: str = Depends(token_dogrula), db=Depends(get_db)):
    conn, cursor = db
    cursor.execute("""
        UPDATE siparisler SET
            musteri_adi=%s, teslim_tarihi=%s, durum=%s,
            toplam_tutar=%s, para_birimi=%s, notlar=%s, kdv_oran=%s
        WHERE id=%s
    """, (istek.musteri_adi, istek.teslim_tarihi, istek.durum,
          istek.toplam_tutar, istek.para_birimi, istek.notlar,
          istek.kdv_oran, siparis_id))
    conn.commit()
    return {"mesaj": "Sipariş güncellendi"}

# ═══════════════════════════════════════════════════════════════
#  STOK
# ═══════════════════════════════════════════════════════════════
@app.get("/stok")
def stok_listele(kullanici: str = Depends(token_dogrula), db=Depends(get_db)):
    conn, cursor = db
    cursor.execute("SELECT * FROM stok ORDER BY ad")
    return cursor.fetchall()

@app.post("/stok")
def stok_ekle(istek: StokIstek, kullanici: str = Depends(token_dogrula), db=Depends(get_db)):
    conn, cursor = db
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    cursor.execute("""
        INSERT INTO stok (stok_kodu, ad, kategori, birim, miktar, min_miktar,
                          birim_fiyat, para_birimi, depo, notlar, olusturma)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
    """, (istek.stok_kodu, istek.ad, istek.kategori, istek.birim,
          istek.miktar, istek.min_miktar, istek.birim_fiyat,
          istek.para_birimi, istek.depo, istek.notlar, now))
    yeni_id = cursor.fetchone()["id"]
    conn.commit()
    return {"mesaj": "Stok eklendi", "id": yeni_id}

@app.put("/stok/{stok_id}")
def stok_guncelle(stok_id: int, istek: StokIstek,
                  kullanici: str = Depends(token_dogrula), db=Depends(get_db)):
    conn, cursor = db
    cursor.execute("""
        UPDATE stok SET ad=%s, kategori=%s, birim=%s, miktar=%s,
            min_miktar=%s, birim_fiyat=%s, depo=%s, notlar=%s
        WHERE id=%s
    """, (istek.ad, istek.kategori, istek.birim, istek.miktar,
          istek.min_miktar, istek.birim_fiyat, istek.depo, istek.notlar, stok_id))
    conn.commit()
    return {"mesaj": "Stok güncellendi"}

# ═══════════════════════════════════════════════════════════════
#  MÜŞTERİLER
# ═══════════════════════════════════════════════════════════════
@app.get("/musteriler")
def musteriler_listele(kullanici: str = Depends(token_dogrula), db=Depends(get_db)):
    conn, cursor = db
    cursor.execute("SELECT * FROM musteriler WHERE aktif=1 ORDER BY ad")
    return cursor.fetchall()

@app.post("/musteriler")
def musteri_ekle(istek: MusteriIstek, kullanici: str = Depends(token_dogrula), db=Depends(get_db)):
    conn, cursor = db
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    cursor.execute("""
        INSERT INTO musteriler (musteri_kodu, ad, telefon, email, adres,
                                vergi_no, vergi_dairesi, notlar, aktif, olusturma)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,1,%s)
        RETURNING id
    """, (istek.musteri_kodu, istek.ad, istek.telefon, istek.email,
          istek.adres, istek.vergi_no, istek.vergi_dairesi, istek.notlar, now))
    yeni_id = cursor.fetchone()["id"]
    conn.commit()
    return {"mesaj": "Müşteri eklendi", "id": yeni_id}

# ═══════════════════════════════════════════════════════════════
#  ÜRETİM (İŞLER)
# ═══════════════════════════════════════════════════════════════
@app.get("/isler")
def isler_listele(kullanici: str = Depends(token_dogrula), db=Depends(get_db)):
    conn, cursor = db
    cursor.execute("SELECT * FROM isler ORDER BY id DESC")
    return cursor.fetchall()

@app.post("/isler")
def is_ekle(istek: IsIstek, kullanici: str = Depends(token_dogrula), db=Depends(get_db)):
    conn, cursor = db
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    cursor.execute("""
        INSERT INTO isler (siparis_id, sip_no, is_tanimi, atanan, baslangic,
                           bitis, durum, oncelik, notlar, olusturma)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
    """, (istek.siparis_id, istek.sip_no, istek.is_tanimi, istek.atanan,
          istek.baslangic, istek.bitis, istek.durum, istek.oncelik,
          istek.notlar, now))
    yeni_id = cursor.fetchone()["id"]
    conn.commit()
    return {"mesaj": "İş eklendi", "id": yeni_id}

@app.put("/isler/{is_id}/durum")
def is_durum_guncelle(is_id: int, durum: str,
                      kullanici: str = Depends(token_dogrula), db=Depends(get_db)):
    conn, cursor = db
    cursor.execute("UPDATE isler SET durum=%s WHERE id=%s", (durum, is_id))
    conn.commit()
    return {"mesaj": "İş durumu güncellendi"}

# ═══════════════════════════════════════════════════════════════
#  SEVKİYAT
# ═══════════════════════════════════════════════════════════════
@app.get("/sevkiyatlar")
def sevkiyatlar_listele(kullanici: str = Depends(token_dogrula), db=Depends(get_db)):
    conn, cursor = db
    cursor.execute("SELECT * FROM sevkiyatlar ORDER BY id DESC")
    return cursor.fetchall()

@app.post("/sevkiyatlar")
def sevkiyat_ekle(istek: SevkiyatIstek, kullanici: str = Depends(token_dogrula), db=Depends(get_db)):
    conn, cursor = db
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    cursor.execute("SELECT COUNT(*) as sayi FROM sevkiyatlar")
    sayi = cursor.fetchone()["sayi"] + 1
    sevk_no = "SEV-{:04d}".format(sayi)
    cursor.execute("""
        INSERT INTO sevkiyatlar (sevk_no, siparis_id, musteri_adi, tarih,
                                  arac, sofor, durum, toplam_kg, notlar, olusturma)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
    """, (sevk_no, istek.siparis_id, istek.musteri_adi,
          istek.tarih or now, istek.arac, istek.sofor,
          istek.durum, istek.toplam_kg, istek.notlar, now))
    yeni_id = cursor.fetchone()["id"]
    conn.commit()
    return {"mesaj": "Sevkiyat eklendi", "id": yeni_id, "sevk_no": sevk_no}

# ═══════════════════════════════════════════════════════════════
#  ÖZET / DASHBOARD
# ═══════════════════════════════════════════════════════════════
@app.get("/ozet")
def ozet(kullanici: str = Depends(token_dogrula), db=Depends(get_db)):
    conn, cursor = db
    def say(tablo, kosul=""):
        try:
            cursor.execute("SELECT COUNT(*) as sayi FROM {} {}".format(tablo, kosul))
            return cursor.fetchone()["sayi"]
        except:
            return 0

    return {
        "toplam_siparis":       say("siparisler"),
        "bekleyen_siparis":     say("siparisler", "WHERE durum='Beklemede'"),
        "toplam_is":            say("isler"),
        "devam_eden_is":        say("isler", "WHERE durum='Devam Ediyor'"),
        "toplam_sevkiyat":      say("sevkiyatlar"),
        "toplam_stok_kalemi":   say("stok"),
        "kritik_stok":          say("stok", "WHERE miktar <= min_miktar AND min_miktar > 0"),
        "toplam_musteri":       say("musteriler", "WHERE aktif=1"),
    }

@app.get("/kullanicilar_hepsi")
def kullanicilar_hepsi(token: str = Header(None, alias="Authorization"), db=Depends(get_db)):
    token_dogrula(token)
    conn, cursor = db
    cursor.execute("SELECT id, kullanici_adi, ad_soyad, rol, aktif FROM kullanicilar ORDER BY id")
    return {"kullanicilar": cursor.fetchall()}

@app.post("/kullanici_ekle")
def kullanici_ekle(istek: dict, token: str = Header(None, alias="Authorization"), db=Depends(get_db)):
    token_dogrula(token)
    conn, cursor = db
    kadi = istek.get("kullanici_adi")
    sifre = istek.get("sifre")
    rol = istek.get("rol", "personel")
    ad = istek.get("ad_soyad", "")
    h = _sifre_hash(sifre)
    cursor.execute("INSERT INTO kullanicilar (kullanici_adi, sifre_hash, rol, ad_soyad, aktif) VALUES (%s,%s,%s,%s,1)", (kadi, h, rol, ad))
    conn.commit()
    return {"durum": "ok"}

@app.post("/sifre_degistir")
def sifre_degistir(istek: dict, token: str = Header(None, alias="Authorization"), db=Depends(get_db)):
    token_dogrula(token)
    conn, cursor = db
    kadi = istek.get("kullanici_adi")
    sifre = istek.get("sifre")
    h = _sifre_hash(sifre)
    cursor.execute("UPDATE kullanicilar SET sifre_hash=%s WHERE kullanici_adi=%s", (h, kadi))
    conn.commit()
    return {"durum": "ok"}

@app.post("/rol_degistir")
def rol_degistir(istek: dict, token: str = Header(None, alias="Authorization"), db=Depends(get_db)):
    token_dogrula(token)
    conn, cursor = db
    cursor.execute("UPDATE kullanicilar SET rol=%s WHERE kullanici_adi=%s", (istek.get("rol"), istek.get("kullanici_adi")))
    conn.commit()
    return {"durum": "ok"}

@app.post("/durum_degistir")
def durum_degistir(istek: dict, token: str = Header(None, alias="Authorization"), db=Depends(get_db)):
    token_dogrula(token)
    conn, cursor = db
    cursor.execute("UPDATE kullanicilar SET aktif=%s WHERE kullanici_adi=%s", (istek.get("aktif"), istek.get("kullanici_adi")))
    conn.commit()
    return {"durum": "ok"}

@app.post("/kullanici_sil")
def kullanici_sil(istek: dict, token: str = Header(None, alias="Authorization"), db=Depends(get_db)):
    token_dogrula(token)
    conn, cursor = db
    cursor.execute("DELETE FROM kullanicilar WHERE kullanici_adi=%s", (istek.get("kullanici_adi"),))
    conn.commit()
    return {"durum": "ok"}
