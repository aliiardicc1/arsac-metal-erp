"""
Arsac Metal ERP — Kullanıcı Router
=====================================
Tüm kullanıcı yönetimi endpoint'leri.
"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime

from core.database import get_db
from core.auth import sifre_hashle, token_olustur, token_sil, token_dogrula
from models.schemas import (
    GirisIstek, KullaniciEkle, SifreDegistir,
    RolDegistir, DurumDegistir, KullaniciSil
)

router = APIRouter(tags=["Kullanicilar"])


@router.post("/giris")
def giris(istek: GirisIstek, db=Depends(get_db)):
    conn, cursor = db
    cursor.execute(
        "SELECT * FROM kullanicilar WHERE kullanici_adi=%s AND aktif=1",
        (istek.kullanici_adi,))
    kullanici = cursor.fetchone()
    if not kullanici or kullanici["sifre_hash"] != sifre_hashle(istek.sifre):
        raise HTTPException(status_code=401, detail="Kullanıcı adı veya şifre hatalı")
    token = token_olustur(istek.kullanici_adi)
    # Log
    try:
        cursor.execute(
            "INSERT INTO kullanici_log (tarih, kullanici, islem, detay) VALUES (%s,%s,%s,%s)",
            (datetime.now().strftime("%d.%m.%Y %H:%M"), istek.kullanici_adi, "giris", "Başarılı giriş"))
        conn.commit()
    except Exception:
        conn.rollback()
    return {
        "token": token,
        "kullanici_adi": kullanici["kullanici_adi"],
        "ad_soyad": kullanici.get("ad_soyad", ""),
        "rol": kullanici["rol"]
    }


@router.post("/cikis")
def cikis(authorization: str = Depends(token_dogrula)):
    # token_dogrula içinde zaten doğrulandı
    return {"durum": "ok"}


@router.get("/kullanicilar_hepsi")
def kullanicilar_hepsi(
    kullanici: str = Depends(token_dogrula),
    db=Depends(get_db)
):
    conn, cursor = db
    cursor.execute(
        "SELECT id, kullanici_adi, ad_soyad, rol, aktif FROM kullanicilar ORDER BY id")
    return {"kullanicilar": [dict(r) for r in cursor.fetchall()]}


@router.post("/kullanici_ekle")
def kullanici_ekle(
    istek: KullaniciEkle,
    kullanici: str = Depends(token_dogrula),
    db=Depends(get_db)
):
    conn, cursor = db
    h = sifre_hashle(istek.sifre)
    cursor.execute(
        "INSERT INTO kullanicilar (kullanici_adi, sifre_hash, rol, ad_soyad, aktif) VALUES (%s,%s,%s,%s,1)",
        (istek.kullanici_adi, h, istek.rol, istek.ad_soyad))
    conn.commit()
    return {"durum": "ok"}


@router.post("/sifre_degistir")
def sifre_degistir(
    istek: SifreDegistir,
    kullanici: str = Depends(token_dogrula),
    db=Depends(get_db)
):
    conn, cursor = db
    h = sifre_hashle(istek.sifre)
    cursor.execute(
        "UPDATE kullanicilar SET sifre_hash=%s WHERE kullanici_adi=%s",
        (h, istek.kullanici_adi))
    conn.commit()
    return {"durum": "ok"}


@router.post("/rol_degistir")
def rol_degistir(
    istek: RolDegistir,
    kullanici: str = Depends(token_dogrula),
    db=Depends(get_db)
):
    conn, cursor = db
    cursor.execute(
        "UPDATE kullanicilar SET rol=%s WHERE kullanici_adi=%s",
        (istek.rol, istek.kullanici_adi))
    conn.commit()
    return {"durum": "ok"}


@router.post("/durum_degistir")
def durum_degistir(
    istek: DurumDegistir,
    kullanici: str = Depends(token_dogrula),
    db=Depends(get_db)
):
    conn, cursor = db
    cursor.execute(
        "UPDATE kullanicilar SET aktif=%s WHERE kullanici_adi=%s",
        (istek.aktif, istek.kullanici_adi))
    conn.commit()
    return {"durum": "ok"}


@router.post("/kullanici_sil")
def kullanici_sil(
    istek: KullaniciSil,
    kullanici: str = Depends(token_dogrula),
    db=Depends(get_db)
):
    conn, cursor = db
    cursor.execute(
        "DELETE FROM kullanicilar WHERE kullanici_adi=%s",
        (istek.kullanici_adi,))
    conn.commit()
    return {"durum": "ok"}


@router.get("/izinler/{kullanici_adi}")
def izinler_getir(
    kullanici_adi: str,
    kullanici: str = Depends(token_dogrula),
    db=Depends(get_db)
):
    conn, cursor = db
    cursor.execute(
        "SELECT modul, goruntule, duzenle FROM kullanici_izinler WHERE kullanici_adi=%s",
        (kullanici_adi,))
    rows = cursor.fetchall()
    return {r["modul"]: [r["goruntule"], r["duzenle"]] for r in rows}


@router.post("/izinler/{kullanici_adi}")
def izinler_kaydet(
    kullanici_adi: str,
    istek: dict,
    kullanici: str = Depends(token_dogrula),
    db=Depends(get_db)
):
    conn, cursor = db
    for modul, val in istek.items():
        g = int(val[0]) if isinstance(val, (list, tuple)) else int(val)
        d = int(val[1]) if isinstance(val, (list, tuple)) and len(val) > 1 else 0
        cursor.execute("""
            INSERT INTO kullanici_izinler (kullanici_adi, modul, goruntule, duzenle)
            VALUES (%s,%s,%s,%s)
            ON CONFLICT (kullanici_adi, modul) DO UPDATE SET goruntule=%s, duzenle=%s
        """, (kullanici_adi, modul, g, d, g, d))
    conn.commit()
    return {"durum": "ok"}
