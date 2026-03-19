"""
Arsac Metal ERP — Bulut API İstemcisi
======================================
database.py ile aynı arayüzü sunar.
Arkada FastAPI sunucusuna HTTP istekleri atar.

Kullanım:
    from database_bulut import baglanti_kur, izin_yukle, izin_var
    conn, cursor = baglanti_kur()
"""

import json
import hashlib
import urllib.request as urlreq
import urllib.error as urlerr
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
#  AYARLAR
# ═══════════════════════════════════════════════════════════════
API_URL   = "http://213.159.6.166:8000"
_token    = None
_kullanici = None


def _sifre_hash(sifre):
    return hashlib.sha256(sifre.encode("utf-8")).hexdigest()


# ═══════════════════════════════════════════════════════════════
#  HTTP YARDIMCILARI
# ═══════════════════════════════════════════════════════════════
def _istek(method, endpoint, veri=None):
    url = API_URL + endpoint
    body = json.dumps(veri).encode("utf-8") if veri else None
    hdrs = {"Content-Type": "application/json"}
    if _token:
        hdrs["Authorization"] = "Bearer " + _token

    req = urlreq.Request(url, data=body, headers=hdrs, method=method)
    try:
        with urlreq.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))
    except urlerr.HTTPError as e:
        hata = json.loads(e.read().decode("utf-8"))
        raise Exception(hata.get("detail", str(e)))
    except Exception as e:
        raise Exception("API bağlantı hatası: {}".format(e))


def _get(endpoint):   return _istek("GET",  endpoint)
def _post(endpoint, veri): return _istek("POST", endpoint, veri)
def _put(endpoint, veri):  return _istek("PUT",  endpoint, veri)


# ═══════════════════════════════════════════════════════════════
#  SAHTE CURSOR / CONN  (database.py uyumluluğu için)
# ═══════════════════════════════════════════════════════════════
class BulutCursor:
    def __init__(self):
        self._sonuc = []
        self._tek   = None

    def execute(self, sql, params=()):
        sql_lower = sql.lower().strip()

        if "from kullanicilar" in sql_lower and "select" in sql_lower:
            try:
                self._sonuc = [dict(r) for r in _get("/kullanicilar_hepsi")]
            except:
                self._sonuc = []

        elif "from stok" in sql_lower and "select" in sql_lower:
            try:
                self._sonuc = [dict(r) for r in _get("/stok")]
            except:
                self._sonuc = []

        elif "from siparisler" in sql_lower and "select" in sql_lower:
            try:
                self._sonuc = [dict(r) for r in _get("/siparisler")]
            except:
                self._sonuc = []

        elif "from musteriler" in sql_lower and "select" in sql_lower:
            try:
                self._sonuc = [dict(r) for r in _get("/musteriler")]
            except:
                self._sonuc = []

        elif "from isler" in sql_lower and "select" in sql_lower:
            try:
                self._sonuc = [dict(r) for r in _get("/isler")]
            except:
                self._sonuc = []

        elif "from sevkiyatlar" in sql_lower and "select" in sql_lower:
            try:
                self._sonuc = [dict(r) for r in _get("/sevkiyatlar")]
            except:
                self._sonuc = []

        elif "count(*)" in sql_lower:
            try:
                ozet = _get("/ozet")
                if "from siparisler" in sql_lower:
                    self._tek = (ozet.get("toplam_siparis", 0),)
                elif "from stok" in sql_lower:
                    self._tek = (ozet.get("toplam_stok_kalemi", 0),)
                elif "from musteriler" in sql_lower:
                    self._tek = (ozet.get("toplam_musteri", 0),)
                elif "from isler" in sql_lower:
                    self._tek = (ozet.get("toplam_is", 0),)
                else:
                    self._tek = (0,)
            except:
                self._tek = (0,)
        else:
            self._sonuc = []

    def fetchall(self):
        return self._sonuc

    def fetchone(self):
        if self._tek is not None:
            t = self._tek
            self._tek = None
            return t
        return self._sonuc[0] if self._sonuc else None

    def __iter__(self):
        return iter(self._sonuc)


class BulutConn:
    def commit(self): pass
    def close(self):  pass
    def cursor(self): return BulutCursor()


# ═══════════════════════════════════════════════════════════════
#  ANA FONKSİYONLAR  (database.py ile aynı imza)
# ═══════════════════════════════════════════════════════════════
def baglanti_kur():
    try:
        sonuc = _get("/saglik")
        if sonuc.get("durum") == "ok":
            print("[BulutDB] API bağlantısı OK:", API_URL)
    except Exception as e:
        print("[BulutDB] UYARI: API'ye bağlanılamadı:", e)
    return BulutConn(), BulutCursor()


def baglanti_yenile(conn, cursor):
    return baglanti_kur()


def giris_yap(kullanici_adi, sifre):
    global _token, _kullanici
    sonuc = _post("/giris", {"kullanici_adi": kullanici_adi, "sifre": sifre})
    _token     = sonuc["token"]
    _kullanici = kullanici_adi
    print("[BulutDB] Giriş başarılı:", kullanici_adi)
    return sonuc


def cikis_yap():
    global _token, _kullanici
    try:
        _post("/cikis", {})
    except:
        pass
    _token = None
    _kullanici = None


# ═══════════════════════════════════════════════════════════════
#  İZİN SİSTEMİ
# ═══════════════════════════════════════════════════════════════
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

def izin_yukle(cursor, kullanici_adi):
    try:
        return _get("/izinler/{}".format(kullanici_adi))
    except:
        return {}

def izin_var(izinler, modul, tip="goruntule"):
    if modul not in izinler:
        return False
    g, d = izinler[modul]
    return d if tip == "duzenle" else g

def _izin_varsayilan_yukle(cursor, conn=None):
    pass  # API tarafında otomatik yapılıyor


# ═══════════════════════════════════════════════════════════════
#  API YARDIMCI FONKSİYONLARI
# ═══════════════════════════════════════════════════════════════
def siparis_listele():   return _get("/siparisler")
def siparis_detay(sid):  return _get("/siparisler/{}".format(sid))
def siparis_ekle(musteri_adi, teslim_tarihi=None, durum="Beklemede",
                 toplam_tutar=0, para_birimi="TL", notlar=None,
                 yetkili=None, kdv_oran=20):
    return _post("/siparisler", dict(musteri_adi=musteri_adi,
        teslim_tarihi=teslim_tarihi, durum=durum, toplam_tutar=toplam_tutar,
        para_birimi=para_birimi, notlar=notlar, yetkili=yetkili, kdv_oran=kdv_oran))

def stok_listele():  return _get("/stok")
def stok_ekle(ad, stok_kodu=None, kategori=None, birim="Adet",
              miktar=0, min_miktar=0, birim_fiyat=0,
              para_birimi="TL", depo=None, notlar=None):
    return _post("/stok", dict(ad=ad, stok_kodu=stok_kodu, kategori=kategori,
        birim=birim, miktar=miktar, min_miktar=min_miktar,
        birim_fiyat=birim_fiyat, para_birimi=para_birimi, depo=depo, notlar=notlar))

def musteri_listele():  return _get("/musteriler")
def musteri_ekle(ad, musteri_kodu=None, telefon=None, email=None,
                 adres=None, vergi_no=None, vergi_dairesi=None, notlar=None):
    return _post("/musteriler", dict(ad=ad, musteri_kodu=musteri_kodu,
        telefon=telefon, email=email, adres=adres,
        vergi_no=vergi_no, vergi_dairesi=vergi_dairesi, notlar=notlar))

def is_listele():  return _get("/isler")
def is_ekle(is_tanimi, siparis_id=None, sip_no=None, atanan=None,
            baslangic=None, bitis=None, durum="Beklemede",
            oncelik="Normal", notlar=None):
    return _post("/isler", dict(is_tanimi=is_tanimi, siparis_id=siparis_id,
        sip_no=sip_no, atanan=atanan, baslangic=baslangic, bitis=bitis,
        durum=durum, oncelik=oncelik, notlar=notlar))

def sevkiyat_listele():  return _get("/sevkiyatlar")
def sevkiyat_ekle(musteri_adi, siparis_id=None, tarih=None,
                  arac=None, sofor=None, durum="Hazırlanıyor",
                  toplam_kg=0, notlar=None):
    return _post("/sevkiyatlar", dict(musteri_adi=musteri_adi,
        siparis_id=siparis_id, tarih=tarih, arac=arac, sofor=sofor,
        durum=durum, toplam_kg=toplam_kg, notlar=notlar))

def ozet_al():  return _get("/ozet")


# ═══════════════════════════════════════════════════════════════
#  UYUMLULUK FONKSİYONLARI
# ═══════════════════════════════════════════════════════════════
def db_yolu_al():        return API_URL
def db_yolu_kaydet(yol): return True
def otomatik_yedekle(max_yedek=7): return True

def ayarlari_oku():
    try:
        import os, sys
        yol = os.path.join(
            os.path.dirname(sys.executable) if getattr(sys, 'frozen', False)
            else os.path.dirname(os.path.abspath(__file__)), "ayarlar.json")
        with open(yol, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def ayarlari_yaz(veri):
    try:
        import os, sys
        yol = os.path.join(
            os.path.dirname(sys.executable) if getattr(sys, 'frozen', False)
            else os.path.dirname(os.path.abspath(__file__)), "ayarlar.json")
        with open(yol, "w", encoding="utf-8") as f:
            json.dump(veri, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def db_saglik_kontrol(cursor):
    try:
        _get("/saglik")
        return True, "Bulut API sağlıklı: {}".format(API_URL)
    except Exception as e:
        return False, "API bağlantı hatası: {}".format(e)

def db_bilgi(cursor):
    try:
        return ozet_al()
    except:
        return {"hata": "API bağlantısı yok"}
