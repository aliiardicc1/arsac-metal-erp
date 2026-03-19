"""
Arsac Metal ERP — Bulut API İstemcisi
======================================
database.py ile aynı arayüzü sunar.
Arkada FastAPI sunucusuna HTTP istekleri atar.
BulutCursor tüm SQL sorgularını /sorgu endpoint'ine iletir.
"""

import json
import hashlib
import urllib.request as urlreq
import urllib.error as urlerr
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
#  AYARLAR
# ═══════════════════════════════════════════════════════════════
API_URL    = "http://213.159.6.166:8000"
_token     = None
_kullanici = None


def _sifre_hash(sifre):
    return hashlib.sha256(sifre.encode("utf-8")).hexdigest()


# ═══════════════════════════════════════════════════════════════
#  HTTP YARDIMCILARI
# ═══════════════════════════════════════════════════════════════
def _istek(method, endpoint, veri=None):
    url  = API_URL + endpoint
    body = json.dumps(veri).encode("utf-8") if veri is not None else None
    hdrs = {"Content-Type": "application/json"}
    if _token:
        hdrs["Authorization"] = "Bearer " + _token

    req = urlreq.Request(url, data=body, headers=hdrs, method=method)
    try:
        with urlreq.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except urlerr.HTTPError as e:
        try:
            hata = json.loads(e.read().decode("utf-8"))
            raise Exception(hata.get("detail", str(e)))
        except:
            raise Exception("HTTP {}: {}".format(e.code, e.reason))
    except Exception as e:
        raise Exception("API bağlantı hatası: {}".format(e))


def _get(endpoint):        return _istek("GET",  endpoint)
def _post(endpoint, veri): return _istek("POST", endpoint, veri)
def _put(endpoint, veri):  return _istek("PUT",  endpoint, veri)


# ═══════════════════════════════════════════════════════════════
#  BULUT CURSOR — tüm SQL sorgularını API'ye iletir
# ═══════════════════════════════════════════════════════════════
class BulutCursor:
    """
    SQLite cursor ile birebir aynı arayüz.
    Her execute() çağrısını /sorgu endpoint'ine gönderir.
    Modüllere hiç dokunmadan çalışır.
    """
    def __init__(self):
        self._rows    = []
        self._rowcount = 0
        self.lastrowid = None

    def execute(self, sql, params=()):
        try:
            sonuc = _post("/sorgu", {
                "sql":    sql,
                "params": list(params)
            })
            self._rows     = sonuc.get("rows", [])
            self._rowcount = sonuc.get("rowcount", 0)
            self.lastrowid = sonuc.get("lastrowid", None)
        except Exception as e:
            print("[BulutCursor] Sorgu hatası:", e)
            print("  SQL:", sql[:120])
            self._rows     = []
            self._rowcount = 0

    def executemany(self, sql, param_list):
        for params in param_list:
            self.execute(sql, params)

    def fetchall(self):
        rows = self._rows
        # Modüller tuple bekliyorsa dict değerleri tuple'a çevir
        return [_dict_to_row(r) for r in rows]

    def fetchone(self):
        if not self._rows:
            return None
        return _dict_to_row(self._rows[0])

    def __iter__(self):
        return iter(self.fetchall())

    @property
    def rowcount(self):
        return self._rowcount


def _dict_to_row(r):
    """
    Dict satırını DictRow gibi hem index hem key ile erişilebilir yapar.
    Modüller row[0], row['alan'] veya row.get() kullanabilir.
    """
    if isinstance(r, dict):
        return _SmartRow(r)
    return r


class _SmartRow:
    """Dict'i hem tuple hem dict gibi kullanmayı sağlar."""
    def __init__(self, d):
        self._d    = d
        self._vals = list(d.values())
        self._keys = list(d.keys())

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._vals[key]
        return self._d[key]

    def __iter__(self):
        return iter(self._vals)

    def __len__(self):
        return len(self._vals)

    def get(self, key, default=None):
        return self._d.get(key, default)

    def keys(self):
        return self._d.keys()

    def values(self):
        return self._d.values()

    def items(self):
        return self._d.items()

    def __repr__(self):
        return repr(self._d)

    def __contains__(self, key):
        return key in self._d


class BulutConn:
    """SQLite conn ile aynı arayüz."""
    def commit(self): pass
    def close(self):  pass
    def cursor(self): return BulutCursor()
    def __enter__(self): return self
    def __exit__(self, *a): pass


# ═══════════════════════════════════════════════════════════════
#  ANA FONKSİYONLAR
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
    sonuc = _post("/giris", {
        "kullanici_adi": kullanici_adi,
        "sifre":         sifre
    })
    _token     = sonuc["token"]
    _kullanici = kullanici_adi
    print("[BulutDB] Giriş başarılı:", kullanici_adi)
    return sonuc


def cikis_yap():
    global _token, _kullanici
    try: _post("/cikis", {})
    except: pass
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
    v = izinler[modul]
    g, d = (v[0], v[1]) if isinstance(v, (list, tuple)) else (False, False)
    return bool(d) if tip == "duzenle" else bool(g)

def _izin_varsayilan_yukle(cursor, conn=None):
    pass  # API tarafında otomatik


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
        return _get("/ozet")
    except:
        return {"hata": "API bağlantısı yok"}

def yedekleri_listele():   return []
def yedekten_geri_yukle(y): return False
