"""
Arsac Metal ERP — Kimlik Doğrulama
===================================
Token yönetimi tek bir yerden.
"""
import hashlib
import secrets
from fastapi import HTTPException, Header

# Bellek içi token deposu
# Üretimde Redis veya veritabanı kullanılabilir
_aktif_tokenlar: dict[str, str] = {}  # token -> kullanici_adi


def sifre_hashle(sifre: str) -> str:
    return hashlib.sha256(sifre.encode("utf-8")).hexdigest()


def token_olustur(kullanici_adi: str) -> str:
    token = secrets.token_hex(32)
    _aktif_tokenlar[token] = kullanici_adi
    return token


def token_sil(token: str):
    _aktif_tokenlar.pop(token, None)


def token_dogrula(authorization: str = Header(...)) -> str:
    """
    FastAPI Depends ile kullanılır.
    Bearer token'ı doğrular, kullanıcı adını döner.
    """
    token = authorization.replace("Bearer ", "").strip()
    if token not in _aktif_tokenlar:
        raise HTTPException(status_code=401, detail="Geçersiz veya süresi dolmuş token")
    return _aktif_tokenlar[token]


def token_kullanici(authorization: str = Header(...)) -> str:
    """Token'dan kullanıcı adını döner."""
    return token_dogrula(authorization)
