"""
Arsac Metal ERP — Veritabanı Altyapısı
=======================================
• SQLite + WAL modu (4-10 eş zamanlı kullanıcı)
• Şema versiyonlama (SCHEMA_VERSION) — güncelleme güvenli
• Otomatik yedekleme (her gün 1 kez, son 7 yedek saklanır)
• Bağlantı kopması → otomatik yeniden bağlanma
• Her tablo tek CREATE — duplikasyon yok
• İlk kurulumda varsayılan admin + roller
"""

import sqlite3
import time
import sys
import os
import json
import shutil
import hashlib
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
#  ŞEMA VERSİYONU — her yapısal değişiklikte artır
# ═══════════════════════════════════════════════════════════════
SCHEMA_VERSION = 7


# ═══════════════════════════════════════════════════════════════
#  AYARLAR  (her PC'de yerel ayarlar.json)
# ═══════════════════════════════════════════════════════════════
def _ayarlar_yolu():
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), "ayarlar.json")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "ayarlar.json")

def ayarlari_oku():
    try:
        with open(_ayarlar_yolu(), "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def ayarlari_yaz(veri):
    try:
        with open(_ayarlar_yolu(), "w", encoding="utf-8") as f:
            json.dump(veri, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def _db_yolu():
    ayarlar = ayarlari_oku()
    yol = ayarlar.get("db_yolu", "")
    if yol:
        klasor = os.path.dirname(yol) if os.path.dirname(yol) else "."
        if os.path.exists(klasor):
            return yol
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), "arsac_metal.db")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "arsac_metal.db")

def db_yolu_kaydet(yol):
    ayarlar = ayarlari_oku()
    ayarlar["db_yolu"] = yol
    return ayarlari_yaz(ayarlar)

def db_yolu_al():
    return _db_yolu()


# ═══════════════════════════════════════════════════════════════
#  OTOMATİK YEDEKLEME
# ═══════════════════════════════════════════════════════════════
def _yedek_klasoru():
    db = _db_yolu()
    return os.path.join(os.path.dirname(db), "yedekler")

def otomatik_yedekle(max_yedek=7):
    """Bugün için yedek yoksa alır. Son max_yedek adedi dışındakileri siler."""
    try:
        db_yolu = _db_yolu()
        if not os.path.exists(db_yolu):
            return False

        yedek_kls = _yedek_klasoru()
        os.makedirs(yedek_kls, exist_ok=True)

        bugun = datetime.now().strftime("%Y-%m-%d")
        yedek_adi = "arsac_{}.db".format(bugun)
        yedek_tam = os.path.join(yedek_kls, yedek_adi)

        if os.path.exists(yedek_tam):
            return True  # Bugün zaten alındı

        shutil.copy2(db_yolu, yedek_tam)

        # Eski yedekleri temizle
        tum_yedekler = sorted([
            f for f in os.listdir(yedek_kls)
            if f.startswith("arsac_") and f.endswith(".db")
        ])
        while len(tum_yedekler) > max_yedek:
            sil = os.path.join(yedek_kls, tum_yedekler.pop(0))
            try: os.remove(sil)
            except: pass

        print("[DB] Yedek alindi:", yedek_tam)
        return True
    except Exception as e:
        print("[DB] Yedekleme hatasi:", e)
        return False

def yedekleri_listele():
    """Mevcut yedek dosyalarını listeler."""
    try:
        kls = _yedek_klasoru()
        if not os.path.exists(kls):
            return []
        return sorted([
            os.path.join(kls, f)
            for f in os.listdir(kls)
            if f.startswith("arsac_") and f.endswith(".db")
        ], reverse=True)
    except:
        return []

def yedekten_geri_yukle(yedek_yolu):
    """Seçilen yedeği aktif DB'nin üzerine kopyalar."""
    try:
        db_yolu = _db_yolu()
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(db_yolu, db_yolu + ".onceki_" + now)
        shutil.copy2(yedek_yolu, db_yolu)
        return True
    except Exception as e:
        print("[DB] Geri yukleme hatasi:", e)
        return False


# ═══════════════════════════════════════════════════════════════
#  YARDIMCI
# ═══════════════════════════════════════════════════════════════
def _sutun_ekle(cursor, tablo, sutun, tip):
    """Tablo varsa ve sütun yoksa ekler, hata fırlatmaz."""
    try:
        cursor.execute("ALTER TABLE {} ADD COLUMN {} {}".format(tablo, sutun, tip))
    except:
        pass

def _sifre_hash(sifre):
    return hashlib.sha256(sifre.encode("utf-8")).hexdigest()


# ═══════════════════════════════════════════════════════════════
#  ROL / İZİN SİSTEMİ
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

def _izin_varsayilan_yukle(cursor):
    try:
        cursor.execute("SELECT kullanici_adi, rol FROM kullanicilar WHERE aktif=1")
        for kullanici_adi, rol in cursor.fetchall():
            for modul, rol_izinleri in ROL_VARSAYILAN_IZIN.items():
                g, d = rol_izinleri.get(rol, (0, 0))
                cursor.execute("""
                    INSERT OR IGNORE INTO kullanici_izinler
                        (kullanici_adi, modul, goruntule, duzenle)
                    VALUES (?, ?, ?, ?)
                """, (kullanici_adi, modul, g, d))
    except Exception as e:
        print("[DB] Izin yukleme hatasi:", e)

def izin_yukle(cursor, kullanici_adi):
    try:
        cursor.execute(
            "SELECT modul, goruntule, duzenle FROM kullanici_izinler WHERE kullanici_adi=?",
            (kullanici_adi,))
        return {m: (bool(g), bool(d)) for m, g, d in cursor.fetchall()}
    except:
        return {}

def izin_var(izinler, modul, tip="goruntule"):
    if modul not in izinler:
        return False
    g, d = izinler[modul]
    return d if tip == "duzenle" else g


# ═══════════════════════════════════════════════════════════════
#  ŞEMA OLUŞTURMA  (tek seferlik, CREATE IF NOT EXISTS)
# ═══════════════════════════════════════════════════════════════
def _sema_olustur(cursor):
    """Tüm tabloları oluşturur. Mevcut tablolara dokunmaz."""

    cursor.execute("""CREATE TABLE IF NOT EXISTS db_meta (
        anahtar TEXT PRIMARY KEY,
        deger   TEXT
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS kullanicilar (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        kullanici_adi    TEXT UNIQUE NOT NULL,
        sifre_hash       TEXT NOT NULL,
        rol              TEXT DEFAULT 'personel',
        ad_soyad         TEXT,
        aktif            INTEGER DEFAULT 1,
        olusturma_tarihi TEXT
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS kullanici_izinler (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        kullanici_adi TEXT NOT NULL,
        modul         TEXT NOT NULL,
        goruntule     INTEGER DEFAULT 0,
        duzenle       INTEGER DEFAULT 0,
        UNIQUE(kullanici_adi, modul)
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS kullanici_log (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        kullanici TEXT,
        islem     TEXT,
        detay     TEXT,
        tarih     TEXT
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS tedarikciler (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        firma_adi   TEXT UNIQUE NOT NULL,
        iban        TEXT,
        vergi_no    TEXT,
        telefon     TEXT,
        email       TEXT,
        adres       TEXT,
        notlar      TEXT,
        kredi_limit REAL DEFAULT 0,
        olusturma   TEXT
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS satinalma_kayitlari (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        firma        TEXT,
        malzeme      TEXT,
        miktar       REAL,
        birim_fiyat  REAL,
        nakliye      REAL DEFAULT 0,
        toplam_tutar REAL,
        vade_tarihi  TEXT,
        odeme_tipi   TEXT,
        tarih        TEXT,
        odendi       INTEGER DEFAULT 0,
        odeme_tarihi TEXT
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS tediye_makbuzlari (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        makbuz_no    TEXT UNIQUE,
        tip          TEXT NOT NULL,
        firma        TEXT NOT NULL,
        tarih        TEXT,
        tutar        REAL DEFAULT 0,
        kalan_tutar  REAL DEFAULT 0,
        odeme_sekli  TEXT,
        aciklama     TEXT,
        siparis_no   TEXT,
        satinalma_id INTEGER,
        olusturan    TEXT,
        pdf_yolu     TEXT
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS siparisler (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        sip_no         TEXT UNIQUE,
        musteri        TEXT,
        yetkili        TEXT,
        telefon        TEXT,
        musteri_sip_no TEXT,
        tarih          TEXT,
        termin         TEXT,
        durum          TEXT DEFAULT 'Alindi',
        ara_toplam     REAL DEFAULT 0,
        kdv_oran       REAL DEFAULT 20,
        kdv_tutar      REAL DEFAULT 0,
        genel_toplam   REAL DEFAULT 0,
        odeme_sekli    TEXT,
        odeme_vadesi   TEXT,
        tahsil_edildi  INTEGER DEFAULT 0,
        arac           TEXT,
        sofor          TEXT,
        irsaliye_no    TEXT,
        fatura_no      TEXT,
        fatura_tarihi  TEXT,
        faturalandi    INTEGER DEFAULT 0,
        notlar         TEXT,
        olusturan      TEXT
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS siparis_kalemleri (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        siparis_id       INTEGER NOT NULL,
        urun_adi         TEXT,
        adet             REAL DEFAULT 1,
        birim            TEXT DEFAULT 'Adet',
        birim_fiyat      REAL DEFAULT 0,
        toplam_fiyat     REAL DEFAULT 0,
        kdv_oran         INTEGER DEFAULT 20,
        malzeme          TEXT,
        kalinlik         REAL DEFAULT 0,
        en               REAL DEFAULT 0,
        boy              REAL DEFAULT 0,
        kg               REAL DEFAULT 0,
        uretim_durumu    TEXT DEFAULT 'Beklemede',
        tamamlanan_adet  REAL DEFAULT 0,
        sevk_edilen_adet REAL DEFAULT 0,
        birim_fiyat2     REAL DEFAULT 0,
        fiyat_turu       TEXT DEFAULT 'Adet',
        yetkili          TEXT
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS isler (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        is_no      TEXT UNIQUE,
        sip_no     TEXT,
        musteri    TEXT,
        tarih      TEXT,
        durum      TEXT DEFAULT 'Beklemede',
        termin     TEXT,
        toplam_kg  REAL DEFAULT 0,
        ilerleme   INTEGER DEFAULT 0,
        notlar     TEXT
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS parcalar (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        is_no         TEXT,
        parca_adi     TEXT,
        parca_kodu    TEXT,
        adet          INTEGER DEFAULT 1,
        birim_kg      REAL DEFAULT 0,
        durum         TEXT DEFAULT 'Beklemede',
        gorsel_base64 TEXT,
        biten_adet    INTEGER DEFAULT 0
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS parca_sevk_bekliyor (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        siparis_id       INTEGER,
        sip_no           TEXT,
        musteri          TEXT,
        kalem_id         INTEGER,
        parca_adi        TEXT,
        tamamlanan_adet  REAL DEFAULT 0,
        sevk_edilen_adet REAL DEFAULT 0,
        bekleyen_adet    REAL DEFAULT 0,
        tarih            TEXT,
        durum            TEXT DEFAULT 'Bekliyor'
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS sevkiyatlar (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        plaka           TEXT,
        sofor           TEXT,
        telefon         TEXT,
        tarih           TEXT,
        siparis_listesi TEXT,
        notlar          TEXT,
        durum           TEXT DEFAULT 'Yolda'
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS sevkiyat_siparisler (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        sevkiyat_id INTEGER,
        siparis_id  INTEGER
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS sevkiyat_kalemleri (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        sevkiyat_id INTEGER NOT NULL,
        siparis_id  INTEGER NOT NULL,
        kalem_id    INTEGER NOT NULL,
        urun_adi    TEXT,
        sevk_adet   REAL DEFAULT 0,
        tarih       TEXT
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS faturalar (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        fatura_no    TEXT UNIQUE,
        sip_no       TEXT,
        musteri      TEXT,
        tarih        TEXT,
        kdv_oran     REAL DEFAULT 20,
        kdv_tutar    REAL DEFAULT 0,
        genel_toplam REAL DEFAULT 0,
        durum        TEXT DEFAULT 'Bekliyor',
        notlar       TEXT,
        olusturan    TEXT
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS fatura_kalemleri (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        fatura_id   INTEGER NOT NULL,
        kalem_id    INTEGER,
        parca_adi   TEXT,
        adet        REAL DEFAULT 1,
        kg          REAL DEFAULT 0,
        birim_fiyat REAL DEFAULT 0,
        fiyat_turu  TEXT DEFAULT 'Adet',
        toplam      REAL DEFAULT 0
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS stok (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        stok_kodu TEXT,
        malzeme   TEXT,
        adet      REAL,
        en        REAL,
        boy       REAL,
        kalinlik  REAL,
        kg        REAL,
        son_firma TEXT,
        son_tarih TEXT,
        durum     INTEGER DEFAULT 0
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS talepler (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        talep_no    TEXT,
        kalite      TEXT,
        en          REAL,
        boy         REAL,
        kalinlik    REAL,
        adet_tabaka INTEGER,
        kg          REAL,
        durum       INTEGER DEFAULT 0,
        tarih       TEXT
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS teklifler (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        teklif_no    TEXT,
        firma        TEXT,
        durum        TEXT DEFAULT 'Bekliyor',
        toplam_tutar REAL,
        nakliye      REAL,
        vade         TEXT,
        odeme_tipi   TEXT,
        tarih        TEXT,
        notlar       TEXT
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS teklif_kalemleri (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        teklif_id   INTEGER,
        talep_id    INTEGER,
        kalite      TEXT,
        en          REAL,
        boy         REAL,
        kalinlik    REAL,
        kg          REAL,
        birim_fiyat REAL,
        tutar       REAL
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS yerlesim_raporlari (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        tarih           TEXT,
        yerlesim_adi    TEXT UNIQUE,
        makine          TEXT,
        operator        TEXT,
        baslangic_saati TEXT,
        bitis_saati     TEXT,
        onay_durumu     INTEGER DEFAULT 0,
        verim           REAL DEFAULT 0,
        toplam_sure     TEXT,
        sure_verimi     REAL DEFAULT 0
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS rapor_detaylari (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        rapor_id      INTEGER,
        is_no         TEXT,
        parca_kodu    TEXT,
        parca_adi     TEXT,
        miktar        INTEGER,
        gorsel_base64 TEXT
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS notlar (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        baslik      TEXT NOT NULL,
        tarih       TEXT,
        oncelik     TEXT DEFAULT 'Normal',
        not_metni   TEXT,
        hatirlatici TEXT,
        olusturma   TEXT
    )""")


# ═══════════════════════════════════════════════════════════════
#  ŞEMA MİGRASYON  (eski DB'leri günceller)
# ═══════════════════════════════════════════════════════════════
def _migrasyon(cursor, mevcut_versiyon):
    """Her migrasyon bloğu sadece 1 kez çalışır."""

    if mevcut_versiyon < 2:
        for sutun, tip in [
            ("yetkili",        "TEXT"),
            ("musteri_sip_no", "TEXT"),
            ("arac",           "TEXT"),
            ("sofor",          "TEXT"),
            ("odeme_sekli",    "TEXT"),
            ("odeme_vadesi",   "TEXT"),
            ("tahsil_edildi",  "INTEGER DEFAULT 0"),
            ("fatura_tarihi",  "TEXT"),
            ("faturalandi",    "INTEGER DEFAULT 0"),
            ("kdv_oran",       "REAL DEFAULT 20"),
            ("kdv_tutar",      "REAL DEFAULT 0"),
        ]:
            _sutun_ekle(cursor, "siparisler", sutun, tip)

    if mevcut_versiyon < 3:
        for sutun, tip in [
            ("adet",             "REAL DEFAULT 1"),
            ("toplam_fiyat",     "REAL DEFAULT 0"),
            ("malzeme",          "TEXT"),
            ("kalinlik",         "REAL DEFAULT 0"),
            ("en",               "REAL DEFAULT 0"),
            ("boy",              "REAL DEFAULT 0"),
            ("kg",               "REAL DEFAULT 0"),
            ("uretim_durumu",    "TEXT DEFAULT 'Beklemede'"),
            ("tamamlanan_adet",  "REAL DEFAULT 0"),
            ("sevk_edilen_adet", "REAL DEFAULT 0"),
            ("yetkili",          "TEXT"),
            ("birim_fiyat2",     "REAL DEFAULT 0"),
            ("fiyat_turu",       "TEXT DEFAULT 'Adet'"),
        ]:
            _sutun_ekle(cursor, "siparis_kalemleri", sutun, tip)

    if mevcut_versiyon < 4:
        _sutun_ekle(cursor, "tedarikciler", "kredi_limit", "REAL DEFAULT 0")
        _sutun_ekle(cursor, "tedarikciler", "olusturma",   "TEXT")
        _sutun_ekle(cursor, "satinalma_kayitlari", "odendi",       "INTEGER DEFAULT 0")
        _sutun_ekle(cursor, "satinalma_kayitlari", "odeme_tarihi", "TEXT")

    if mevcut_versiyon < 5:
        _sutun_ekle(cursor, "isler", "sip_no", "TEXT")
        _sutun_ekle(cursor, "isler", "notlar", "TEXT")

    if mevcut_versiyon < 6:
        # faturalar tablosu _sema_olustur ile eklendi
        pass

    if mevcut_versiyon < 7:
        # tediye_makbuzlari tablosu _sema_olustur ile eklendi
        pass

    print("[DB] Migrasyon tamamlandi: v{} -> v{}".format(mevcut_versiyon, SCHEMA_VERSION))


# ═══════════════════════════════════════════════════════════════
#  VARSAYILAN VERİ  (ilk kurulum)
# ═══════════════════════════════════════════════════════════════
def _varsayilan_veri_yukle(cursor):
    """İlk kurulumda admin kullanıcısı oluşturur."""
    try:
        cursor.execute("SELECT COUNT(*) FROM kullanicilar")
        if cursor.fetchone()[0] == 0:
            now = datetime.now().strftime("%d.%m.%Y %H:%M")
            cursor.execute("""
                INSERT INTO kullanicilar
                    (kullanici_adi, sifre_hash, rol, ad_soyad, aktif, olusturma_tarihi)
                VALUES (?, ?, ?, ?, 1, ?)
            """, ("aliiardicc", _sifre_hash("arsac2024"),
                  "yonetici", "Ali Ardic", now))
            print("[DB] Varsayilan admin olusturuldu: aliiardicc / arsac2024")
    except Exception as e:
        print("[DB] Varsayilan veri hatasi:", e)


# ═══════════════════════════════════════════════════════════════
#  ANA BAĞLANTI FONKSİYONU
# ═══════════════════════════════════════════════════════════════
def baglanti_kur():
    """DB bağlantısı kurar, şemayı oluşturur/günceller. Döner: (conn, cursor)"""
    yol = _db_yolu()

    klasor = os.path.dirname(yol)
    if klasor and not os.path.exists(klasor):
        os.makedirs(klasor, exist_ok=True)

    # Ağ DB için retry mekanizması — kilitli ise 5 kez dener
    conn = None
    for deneme in range(5):
        try:
            conn = sqlite3.connect(yol, timeout=60, check_same_thread=False)
            break
        except sqlite3.OperationalError:
            if deneme < 4:
                time.sleep(2)
            else:
                raise

    cursor = conn.cursor()

    # ── SQLite performans ayarları (ağ klasörü için optimize) ──
    try: cursor.execute("PRAGMA journal_mode=WAL")
    except: cursor.execute("PRAGMA journal_mode=DELETE")  # ağda WAL sorun çıkarırsa
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=30000")   # 30 sn bekle
    cursor.execute("PRAGMA cache_size=5000")      # ağda az cache
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.execute("PRAGMA locking_mode=NORMAL")  # ağda EXCLUSIVE kullanma
    conn.commit()

    # ── Şema oluştur ──
    _sema_olustur(cursor)
    conn.commit()

    # ── Versiyon kontrol & migrasyon ──
    try:
        cursor.execute("SELECT deger FROM db_meta WHERE anahtar='schema_version'")
        r = cursor.fetchone()
        mevcut = int(r[0]) if r else 0
    except:
        mevcut = 0

    if mevcut < SCHEMA_VERSION:
        _migrasyon(cursor, mevcut)
        cursor.execute("""
            INSERT OR REPLACE INTO db_meta (anahtar, deger)
            VALUES ('schema_version', ?)
        """, (str(SCHEMA_VERSION),))
        cursor.execute("""
            INSERT OR REPLACE INTO db_meta (anahtar, deger)
            VALUES ('son_guncelleme', ?)
        """, (datetime.now().strftime("%d.%m.%Y %H:%M"),))
        conn.commit()

    # ── Varsayılan veri ──
    _varsayilan_veri_yukle(cursor)

    # ── İzinleri yükle ──
    _izin_varsayilan_yukle(cursor)

    conn.commit()

    # ── Otomatik yedek ──
    otomatik_yedekle(max_yedek=7)

    return conn, cursor


# ═══════════════════════════════════════════════════════════════
#  BAĞLANTI YENİLEME  (ağ kopması sonrası)
# ═══════════════════════════════════════════════════════════════
def baglanti_yenile(conn, cursor):
    """Bağlantı koptuğunda yeni bağlantı kurar."""
    try:
        conn.close()
    except:
        pass
    return baglanti_kur()


# ═══════════════════════════════════════════════════════════════
#  DB SAĞLIK KONTROLÜ
# ═══════════════════════════════════════════════════════════════
def db_saglik_kontrol(cursor):
    """DB bütünlüğünü kontrol eder. Döner: (ok: bool, mesaj: str)"""
    try:
        cursor.execute("PRAGMA integrity_check")
        sonuc = cursor.fetchone()
        if sonuc and sonuc[0] == "ok":
            cursor.execute("SELECT deger FROM db_meta WHERE anahtar='schema_version'")
            r = cursor.fetchone()
            v = r[0] if r else "?"
            return True, "Veritabani saglıklı (sema v{})".format(v)
        else:
            return False, "Butunluk hatasi: {}".format(sonuc)
    except Exception as e:
        return False, "Kontrol hatasi: {}".format(e)


# ═══════════════════════════════════════════════════════════════
#  DB BİLGİ / İSTATİSTİK
# ═══════════════════════════════════════════════════════════════
def db_bilgi(cursor):
    """DB istatistiklerini dict olarak döner."""
    try:
        bilgi = {"yol": _db_yolu()}
        tablolar = [
            "siparisler", "siparis_kalemleri", "isler", "parcalar",
            "sevkiyatlar", "faturalar", "tedarikciler",
            "satinalma_kayitlari", "tediye_makbuzlari",
            "kullanicilar", "kullanici_log"
        ]
        for t in tablolar:
            try:
                cursor.execute("SELECT COUNT(*) FROM {}".format(t))
                bilgi[t] = cursor.fetchone()[0]
            except:
                bilgi[t] = 0
        try:
            bilgi["boyut_mb"] = round(os.path.getsize(_db_yolu()) / 1_048_576, 2)
        except:
            bilgi["boyut_mb"] = 0
        return bilgi
    except Exception as e:
        return {"hata": str(e)}
