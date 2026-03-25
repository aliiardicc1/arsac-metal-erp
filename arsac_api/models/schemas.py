"""
Arsac Metal ERP — Pydantic Şemaları
=====================================
Tüm request/response modelleri burada tanımlıdır.
"""
from pydantic import BaseModel
from typing import Optional, List, Any


# ── Genel ───────────────────────────────────────────
class SorguIstek(BaseModel):
    sql:    str
    params: Optional[List[Any]] = []


# ── Kullanıcı ────────────────────────────────────────
class GirisIstek(BaseModel):
    kullanici_adi: str
    sifre:         str

class KullaniciOlustur(BaseModel):
    kullanici_adi: str
    sifre:         str
    rol:           str = "personel"
    ad_soyad:      Optional[str] = ""

class KullaniciGuncelle(BaseModel):
    ad_soyad:  Optional[str] = None
    rol:       Optional[str] = None
    aktif:     Optional[int] = None
    sifre:     Optional[str] = None

class IzinGuncelle(BaseModel):
    modul:     str
    goruntule: int = 0
    duzenle:   int = 0


# ── Stok ─────────────────────────────────────────────
class StokGir(BaseModel):
    stok_kodu: str
    malzeme:   str
    adet:      Optional[float] = 1
    en:        Optional[float] = 0
    boy:       Optional[float] = 0
    kalinlik:  Optional[float] = 0
    kg:        Optional[float] = 0
    son_firma: Optional[str]   = ""
    son_tarih: Optional[str]   = ""
    durum:     Optional[int]   = 0

class StokGuncelle(BaseModel):
    durum:     Optional[int]   = None
    kg:        Optional[float] = None
    son_firma: Optional[str]   = None
    son_tarih: Optional[str]   = None


# ── Talep ─────────────────────────────────────────────
class TalepGir(BaseModel):
    kalite:      str
    en:          float
    boy:         float
    kalinlik:    float
    adet_tabaka: Optional[int]   = 1
    kg:          Optional[float] = 0
    tarih:       Optional[str]   = ""

class TalepGuncelle(BaseModel):
    durum: int  # 0=bekliyor 1=tamamlandı


# ── Sipariş ───────────────────────────────────────────
class SiparisKalemGir(BaseModel):
    urun_adi:    str
    adet:        float = 1
    birim:       str   = "Adet"
    birim_fiyat: float = 0
    kdv_oran:    int   = 20
    malzeme:     Optional[str]   = ""
    kalinlik:    Optional[float] = 0
    en:          Optional[float] = 0
    boy:         Optional[float] = 0
    kg:          Optional[float] = 0
    fiyat_turu:  Optional[str]   = "Adet"

class SiparisGir(BaseModel):
    musteri:       str
    yetkili:       Optional[str] = ""
    telefon:       Optional[str] = ""
    musteri_sip_no:Optional[str] = ""
    termin:        Optional[str] = ""
    odeme_sekli:   Optional[str] = ""
    notlar:        Optional[str] = ""
    kdv_oran:      Optional[float] = 20
    kalemleri:     Optional[List[SiparisKalemGir]] = []

class SiparisGuncelle(BaseModel):
    durum:         Optional[str] = None
    termin:        Optional[str] = None
    arac:          Optional[str] = None
    sofor:         Optional[str] = None
    irsaliye_no:   Optional[str] = None
    fatura_no:     Optional[str] = None
    fatura_tarihi: Optional[str] = None
    faturalandi:   Optional[int] = None
    tahsil_edildi: Optional[int] = None
    notlar:        Optional[str] = None


# ── Üretim ────────────────────────────────────────────
class IsGir(BaseModel):
    sip_no:    Optional[str] = ""
    musteri:   Optional[str] = ""
    termin:    Optional[str] = ""
    notlar:    Optional[str] = ""

class ParcaGir(BaseModel):
    is_no:         str
    parca_adi:     str
    parca_kodu:    Optional[str]  = ""
    adet:          Optional[int]  = 1
    birim_kg:      Optional[float]= 0
    gorsel_base64: Optional[str]  = ""

class ParcaGuncelle(BaseModel):
    durum:      Optional[str] = None
    biten_adet: Optional[int] = None

class YerlesimGir(BaseModel):
    yerlesim_adi:    str
    makine:          Optional[str] = ""
    operator:        Optional[str] = ""
    baslangic_saati: Optional[str] = ""
    bitis_saati:     Optional[str] = ""
    verim:           Optional[float] = 0


# ── Sevkiyat ──────────────────────────────────────────
class SevkiyatGir(BaseModel):
    plaka:           str
    sofor:           Optional[str] = ""
    telefon:         Optional[str] = ""
    tarih:           Optional[str] = ""
    siparis_listesi: Optional[str] = ""
    notlar:          Optional[str] = ""

class SevkiyatGuncelle(BaseModel):
    durum: str


# ── Satın Alma / Finans ───────────────────────────────
class SatinalmaGir(BaseModel):
    firma:       str
    malzeme:     str
    miktar:      Optional[float] = 0
    birim_fiyat: Optional[float] = 0
    nakliye:     Optional[float] = 0
    vade_tarihi: Optional[str]   = ""
    odeme_tipi:  Optional[str]   = ""
    tarih:       Optional[str]   = ""

class OdemeIsaretle(BaseModel):
    odeme_tarihi: Optional[str] = ""


# ── Cariler / Tedarikçiler ────────────────────────────
class CariGir(BaseModel):
    firma_adi:   str
    iban:        Optional[str]   = ""
    vergi_no:    Optional[str]   = ""
    telefon:     Optional[str]   = ""
    email:       Optional[str]   = ""
    adres:       Optional[str]   = ""
    notlar:      Optional[str]   = ""
    kredi_limit: Optional[float] = 0

class CariGuncelle(BaseModel):
    iban:        Optional[str]   = None
    vergi_no:    Optional[str]   = None
    telefon:     Optional[str]   = None
    email:       Optional[str]   = None
    adres:       Optional[str]   = None
    notlar:      Optional[str]   = None
    kredi_limit: Optional[float] = None


# ── Muhasebe ──────────────────────────────────────────
class MakbuzGir(BaseModel):
    tip:         str   # "tahsilat" | "tediye"
    firma:       str
    tutar:       float
    odeme_sekli: Optional[str] = ""
    aciklama:    Optional[str] = ""
    siparis_no:  Optional[str] = ""
    tarih:       Optional[str] = ""


# ── Log ───────────────────────────────────────────────
class LogGir(BaseModel):
    islem: str
    detay: Optional[str] = ""
