"""
Arsac Metal ERP — Kullanıcı & İzin Router
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from core.database import get_db
from core.auth import sifre_hash, token_uret, token_dogrula, token_bilgi, yonetici_dogrula
from models.schemas import GirisIstek, KullaniciOlustur, KullaniciGuncelle, IzinGuncelle

router = APIRouter(tags=["Kullanıcılar"])

ROL_VARSAYILAN_IZIN = {
    "ozet":       {"yonetici":(1,1),"satis":(1,0),"uretim":(1,0),"sevkiyat":(1,0),"muhasebe":(1,0),"personel":(1,0)},
    "stok":       {"yonetici":(1,1),"satis":(1,1),"uretim":(1,1),"sevkiyat":(1,0),"muhasebe":(1,0),"personel":(1,0)},
    "talepler":   {"yonetici":(1,1),"satis":(1,1),"uretim":(1,1),"sevkiyat":(1,0),"muhasebe":(1,0),"personel":(1,1)},
    "siparisler": {"yonetici":(1,1),"satis":(1,1),"uretim":(1,0),"sevkiyat":(1,0),"muhasebe":(1,0),"personel":(0,0)},
    "uretim":     {"yonetici":(1,1),"satis":(1,0),"uretim":(1,1),"sevkiyat":(1,0),"muhasebe":(1,0),"personel":(1,0)},
    "sevkiyat":   {"yonetici":(1,1),"satis":(0,0),"uretim":(0,0),"sevkiyat":(1,1),"muhasebe":(0,0),"personel":(0,0)},
    "muhasebe":   {"yonetici":(1,1),"satis":(0,0),"uretim":(0,0),"sevkiyat":(0,0),"muhasebe":(1,1),"personel":(0,0)},
    "satinalma":  {"yonetici":(1,1),"satis":(0,0),"uretim":(0,0),"sevkiyat":(0,0),"muhasebe":(1,0),"personel":(0,0)},
    "cariler":    {"yonetici":(1,1),"satis":(1,0),"uretim":(0,0),"sevkiyat":(0,0),"muhasebe":(1,1),"personel":(0,0)},
    "analiz":     {"yonetici":(1,1),"satis":(0,0),"uretim":(0,0),"sevkiyat":(0,0),"muhasebe":(1,0),"personel":(0,0)},
    "piyasa":     {"yonetici":(1,1),"satis":(0,0),"uretim":(0,0),"sevkiyat":(0,0),"muhasebe":(0,0),"personel":(0,0)},
}


def _varsayilan_izin_yukle(cursor, conn, kullanici_adi: str, rol: str):
    for modul, rol_izinleri in ROL_VARSAYILAN_IZIN.items():
        g, d = rol_izinleri.get(rol, (0, 0))
        cursor.execute("""
            INSERT INTO kullanici_izinler (kullanici_adi, modul, goruntule, duzenle)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (kullanici_adi, modul) DO NOTHING
        """, (kullanici_adi, modul, g, d))
    conn.commit()


@router.post("/giris")
def giris_yap(istek: GirisIstek, db=Depends(get_db)):
    conn, cursor = db
    cursor.execute(
        "SELECT kullanici_adi, rol, ad_soyad, aktif FROM kullanicilar WHERE kullanici_adi=%s AND sifre_hash=%s",
        (istek.kullanici_adi, sifre_hash(istek.sifre))
    )
    kullanici = cursor.fetchone()
    if not kullanici:
        raise HTTPException(status_code=401, detail="Kullanıcı adı veya şifre hatalı")
    if not kullanici["aktif"]:
        raise HTTPException(status_code=403, detail="Hesabınız devre dışı")

    token = token_uret(kullanici["kullanici_adi"], kullanici["rol"], kullanici.get("ad_soyad", ""))

    cursor.execute(
        "INSERT INTO kullanici_log (kullanici, islem, detay, tarih) VALUES (%s,%s,%s,%s)",
        (kullanici["kullanici_adi"], "GIRIS", "Başarılı giriş", datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
    )
    conn.commit()

    return {
        "token":         token,
        "kullanici_adi": kullanici["kullanici_adi"],
        "rol":           kullanici["rol"],
        "ad_soyad":      kullanici.get("ad_soyad", ""),
    }


@router.get("/kullanicilar")
def kullanicilari_listele(db=Depends(get_db), _=Depends(yonetici_dogrula)):
    conn, cursor = db
    cursor.execute("SELECT id, kullanici_adi, rol, ad_soyad, aktif, olusturma_tarihi FROM kullanicilar ORDER BY id")
    return cursor.fetchall()


@router.post("/kullanicilar")
def kullanici_olustur(istek: KullaniciOlustur, db=Depends(get_db), _=Depends(yonetici_dogrula)):
    conn, cursor = db
    try:
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        cursor.execute("""
            INSERT INTO kullanicilar (kullanici_adi, sifre_hash, rol, ad_soyad, aktif, olusturma_tarihi)
            VALUES (%s, %s, %s, %s, 1, %s)
        """, (istek.kullanici_adi, sifre_hash(istek.sifre), istek.rol, istek.ad_soyad, now))
        conn.commit()
        _varsayilan_izin_yukle(cursor, conn, istek.kullanici_adi, istek.rol)
        return {"mesaj": f"{istek.kullanici_adi} oluşturuldu"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Kullanıcı adı zaten var: {e}")


@router.put("/kullanicilar/{kullanici_adi}")
def kullanici_guncelle(kullanici_adi: str, istek: KullaniciGuncelle, db=Depends(get_db), _=Depends(yonetici_dogrula)):
    conn, cursor = db
    alanlar, degerler = [], []
    if istek.ad_soyad is not None:
        alanlar.append("ad_soyad=%s"); degerler.append(istek.ad_soyad)
    if istek.rol is not None:
        alanlar.append("rol=%s"); degerler.append(istek.rol)
    if istek.aktif is not None:
        alanlar.append("aktif=%s"); degerler.append(istek.aktif)
    if istek.sifre is not None:
        alanlar.append("sifre_hash=%s"); degerler.append(sifre_hash(istek.sifre))
    if not alanlar:
        raise HTTPException(status_code=400, detail="Güncellenecek alan yok")
    degerler.append(kullanici_adi)
    cursor.execute(f"UPDATE kullanicilar SET {', '.join(alanlar)} WHERE kullanici_adi=%s", degerler)
    conn.commit()
    return {"mesaj": "Güncellendi"}


@router.get("/izinler/{kullanici_adi}")
def izinleri_getir(kullanici_adi: str, db=Depends(get_db), _=Depends(token_dogrula)):
    conn, cursor = db
    cursor.execute(
        "SELECT modul, goruntule, duzenle FROM kullanici_izinler WHERE kullanici_adi=%s",
        (kullanici_adi,)
    )
    satirlar = cursor.fetchall()
    return {r["modul"]: [bool(r["goruntule"]), bool(r["duzenle"])] for r in satirlar}


@router.put("/izinler/{kullanici_adi}")
def izin_guncelle(kullanici_adi: str, istek: IzinGuncelle, db=Depends(get_db), _=Depends(yonetici_dogrula)):
    conn, cursor = db
    cursor.execute("""
        INSERT INTO kullanici_izinler (kullanici_adi, modul, goruntule, duzenle)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (kullanici_adi, modul) DO UPDATE
        SET goruntule=EXCLUDED.goruntule, duzenle=EXCLUDED.duzenle
    """, (kullanici_adi, istek.modul, istek.goruntule, istek.duzenle))
    conn.commit()
    return {"mesaj": "İzin güncellendi"}
