"""
Arsac Metal ERP — JWT Kimlik Doğrulama
=======================================
• HS256 JWT token — 12 saat geçerli
• SECRET_KEY ortam değişkeninden okunur
• token_dogrula() FastAPI Depends ile kullanılır
• Rol ve izin kontrolü helpers
"""
import os
import hashlib
import jwt
from datetime import datetime, timedelta
from fastapi import Header, HTTPException, Depends

SECRET_KEY = os.getenv("SECRET_KEY", "arsac-metal-super-secret-key-2024")
ALGORITMA  = "HS256"
TOKEN_SURE = 12  # saat


def sifre_hash(sifre: str) -> str:
    return hashlib.sha256(sifre.encode("utf-8")).hexdigest()


def token_uret(kullanici_adi: str, rol: str, ad_soyad: str = "") -> str:
    payload = {
        "sub":       kullanici_adi,
        "rol":       rol,
        "ad_soyad":  ad_soyad,
        "exp":       datetime.utcnow() + timedelta(hours=TOKEN_SURE),
        "iat":       datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITMA)


def token_coz(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITMA])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token süresi doldu, tekrar giriş yapın")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Geçersiz token")


def token_dogrula(authorization: str = Header(None)) -> str:
    """
    Depends ile kullanılır.
    Header: Authorization: Bearer <token>
    Döner: kullanici_adi
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Yetkilendirme başlığı eksik")
    token = authorization.split(" ", 1)[1]
    payload = token_coz(token)
    return payload.get("sub", "")


def token_bilgi(authorization: str = Header(None)) -> dict:
    """Tam payload döner (kullanici_adi, rol, ad_soyad)."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Yetkilendirme başlığı eksik")
    token = authorization.split(" ", 1)[1]
    return token_coz(token)


def yonetici_dogrula(bilgi: dict = Depends(token_bilgi)) -> dict:
    """Sadece yönetici rolüne izin verir."""
    if bilgi.get("rol") != "yonetici":
        raise HTTPException(status_code=403, detail="Bu işlem için yönetici yetkisi gerekli")
    return bilgi
