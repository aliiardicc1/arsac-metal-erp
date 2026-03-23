"""
Arsac Metal ERP — Veri Modelleri
==================================
Tüm request/response modelleri burada.
Pydantic ile otomatik doğrulama ve dökümantasyon.
"""
from pydantic import BaseModel
from typing import Optional, List, Any


# ── Auth ──────────────────────────────────────────
class GirisIstek(BaseModel):
    kullanici_adi: str
    sifre: str

class GirisCevap(BaseModel):
    token: str
    kullanici_adi: str
    ad_soyad: Optional[str] = None
    rol: str


# ── Kullanıcı ─────────────────────────────────────
class KullaniciEkle(BaseModel):
    kullanici_adi: str
    sifre: str
    rol: str = "personel"
    ad_soyad: Optional[str] = ""

class SifreDegistir(BaseModel):
    kullanici_adi: str
    sifre: str

class RolDegistir(BaseModel):
    kullanici_adi: str
    rol: str

class DurumDegistir(BaseModel):
    kullanici_adi: str
    aktif: int = 1

class KullaniciSil(BaseModel):
    kullanici_adi: str


# ── Sipariş ───────────────────────────────────────
class SiparisIstek(BaseModel):
    musteri_adi: str
    teslim_tarihi: Optional[str] = None
    durum: Optional[str] = "Beklemede"

class SiparisDurumGuncelle(BaseModel):
    durum: str


# ── Stok ──────────────────────────────────────────
class StokIstek(BaseModel):
    stok_kodu: Optional[str] = None
    malzeme: str
    adet: int = 0
    en: Optional[float] = None
    boy: Optional[float] = None
    kalinlik: Optional[float] = None
    kg: Optional[float] = None

class StokGuncelle(BaseModel):
    adet: Optional[int] = None
    durum: Optional[int] = None


# ── İş Emri ───────────────────────────────────────
class IsEmriIstek(BaseModel):
    is_no: str
    musteri: str
    tarih: Optional[str] = None
    durum: Optional[str] = "Beklemede"
    termin: Optional[str] = None

class IsDurumGuncelle(BaseModel):
    durum: str
    ilerleme: Optional[int] = None


# ── Sevkiyat ──────────────────────────────────────
class SevkiyatIstek(BaseModel):
    plaka: Optional[str] = None
    sofor: Optional[str] = None
    telefon: Optional[str] = None
    siparis_listesi: Optional[str] = None
    notlar: Optional[str] = None


# ── Sorgu (generic SQL) ───────────────────────────
class SorguIstek(BaseModel):
    sql: str
    params: List[Any] = []
