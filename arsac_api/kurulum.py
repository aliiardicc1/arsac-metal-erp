"""
Arsac Metal ERP — PostgreSQL Şema Kurulum Scripti
==================================================
Sadece bir kez çalıştırın: python kurulum.py
Mevcut tabloları bozmaz (IF NOT EXISTS).
"""
import os, sys, hashlib
import psycopg2
from datetime import datetime

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://arsac_user:arsac_pass@localhost:5432/arsac_db"
)

def sifre_hash(s):
    return hashlib.sha256(s.encode()).hexdigest()

TABLOLAR = """
CREATE TABLE IF NOT EXISTS kullanicilar (
    id               SERIAL PRIMARY KEY,
    kullanici_adi    TEXT UNIQUE NOT NULL,
    sifre_hash       TEXT NOT NULL,
    rol              TEXT DEFAULT 'personel',
    ad_soyad         TEXT,
    aktif            INTEGER DEFAULT 1,
    olusturma_tarihi TEXT
);

CREATE TABLE IF NOT EXISTS kullanici_izinler (
    id            SERIAL PRIMARY KEY,
    kullanici_adi TEXT NOT NULL,
    modul         TEXT NOT NULL,
    goruntule     INTEGER DEFAULT 0,
    duzenle       INTEGER DEFAULT 0,
    UNIQUE(kullanici_adi, modul)
);

CREATE TABLE IF NOT EXISTS kullanici_log (
    id        SERIAL PRIMARY KEY,
    kullanici TEXT,
    islem     TEXT,
    detay     TEXT,
    tarih     TEXT
);

CREATE TABLE IF NOT EXISTS tedarikciler (
    id          SERIAL PRIMARY KEY,
    firma_adi   TEXT UNIQUE NOT NULL,
    iban        TEXT,
    vergi_no    TEXT,
    telefon     TEXT,
    email       TEXT,
    adres       TEXT,
    notlar      TEXT,
    kredi_limit REAL DEFAULT 0,
    olusturma   TEXT
);

CREATE TABLE IF NOT EXISTS satinalma_kayitlari (
    id           SERIAL PRIMARY KEY,
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
);

CREATE TABLE IF NOT EXISTS tediye_makbuzlari (
    id           SERIAL PRIMARY KEY,
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
);

CREATE TABLE IF NOT EXISTS siparisler (
    id             SERIAL PRIMARY KEY,
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
);

CREATE TABLE IF NOT EXISTS siparis_kalemleri (
    id               SERIAL PRIMARY KEY,
    siparis_id       INTEGER NOT NULL REFERENCES siparisler(id) ON DELETE CASCADE,
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
);

CREATE TABLE IF NOT EXISTS isler (
    id        SERIAL PRIMARY KEY,
    is_no     TEXT UNIQUE,
    sip_no    TEXT,
    musteri   TEXT,
    tarih     TEXT,
    durum     TEXT DEFAULT 'Beklemede',
    termin    TEXT,
    toplam_kg REAL DEFAULT 0,
    ilerleme  INTEGER DEFAULT 0,
    notlar    TEXT
);

CREATE TABLE IF NOT EXISTS parcalar (
    id            SERIAL PRIMARY KEY,
    is_no         TEXT,
    parca_adi     TEXT,
    parca_kodu    TEXT,
    adet          INTEGER DEFAULT 1,
    birim_kg      REAL DEFAULT 0,
    durum         TEXT DEFAULT 'Beklemede',
    gorsel_base64 TEXT,
    biten_adet    INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS parca_sevk_bekliyor (
    id               SERIAL PRIMARY KEY,
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
);

CREATE TABLE IF NOT EXISTS sevkiyatlar (
    id              SERIAL PRIMARY KEY,
    plaka           TEXT,
    sofor           TEXT,
    telefon         TEXT,
    tarih           TEXT,
    siparis_listesi TEXT,
    notlar          TEXT,
    durum           TEXT DEFAULT 'Yolda'
);

CREATE TABLE IF NOT EXISTS sevkiyat_kalemleri (
    id          SERIAL PRIMARY KEY,
    sevkiyat_id INTEGER NOT NULL,
    siparis_id  INTEGER NOT NULL,
    kalem_id    INTEGER NOT NULL,
    urun_adi    TEXT,
    sevk_adet   REAL DEFAULT 0,
    tarih       TEXT
);

CREATE TABLE IF NOT EXISTS faturalar (
    id           SERIAL PRIMARY KEY,
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
);

CREATE TABLE IF NOT EXISTS fatura_kalemleri (
    id          SERIAL PRIMARY KEY,
    fatura_id   INTEGER NOT NULL,
    kalem_id    INTEGER,
    parca_adi   TEXT,
    adet        REAL DEFAULT 1,
    kg          REAL DEFAULT 0,
    birim_fiyat REAL DEFAULT 0,
    fiyat_turu  TEXT DEFAULT 'Adet',
    toplam      REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS stok (
    id        SERIAL PRIMARY KEY,
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
);

CREATE TABLE IF NOT EXISTS talepler (
    id          SERIAL PRIMARY KEY,
    talep_no    TEXT,
    kalite      TEXT,
    en          REAL,
    boy         REAL,
    kalinlik    REAL,
    adet_tabaka INTEGER,
    kg          REAL,
    durum       INTEGER DEFAULT 0,
    tarih       TEXT
);

CREATE TABLE IF NOT EXISTS teklifler (
    id           SERIAL PRIMARY KEY,
    teklif_no    TEXT,
    firma        TEXT,
    durum        TEXT DEFAULT 'Bekliyor',
    toplam_tutar REAL,
    nakliye      REAL,
    vade         TEXT,
    odeme_tipi   TEXT,
    tarih        TEXT,
    notlar       TEXT
);

CREATE TABLE IF NOT EXISTS teklif_kalemleri (
    id          SERIAL PRIMARY KEY,
    teklif_id   INTEGER,
    talep_id    INTEGER,
    kalite      TEXT,
    en          REAL,
    boy         REAL,
    kalinlik    REAL,
    kg          REAL,
    birim_fiyat REAL,
    tutar       REAL
);

CREATE TABLE IF NOT EXISTS yerlesim_raporlari (
    id              SERIAL PRIMARY KEY,
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
);

CREATE TABLE IF NOT EXISTS rapor_detaylari (
    id            SERIAL PRIMARY KEY,
    rapor_id      INTEGER,
    is_no         TEXT,
    parca_kodu    TEXT,
    parca_adi     TEXT,
    miktar        INTEGER,
    gorsel_base64 TEXT
);

CREATE TABLE IF NOT EXISTS notlar (
    id          SERIAL PRIMARY KEY,
    baslik      TEXT NOT NULL,
    tarih       TEXT,
    oncelik     TEXT DEFAULT 'Normal',
    not_metni   TEXT,
    hatirlatici TEXT,
    olusturma   TEXT
);
"""

def kur():
    print("Arsac Metal ERP — PostgreSQL Kurulum Başlıyor...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # Tabloları oluştur
        cursor.execute(TABLOLAR)
        conn.commit()
        print("✓ Tablolar oluşturuldu")

        # Varsayılan admin
        cursor.execute("SELECT COUNT(*) FROM kullanicilar")
        if cursor.fetchone()[0] == 0:
            now = datetime.now().strftime("%d.%m.%Y %H:%M")
            cursor.execute("""
                INSERT INTO kullanicilar (kullanici_adi, sifre_hash, rol, ad_soyad, aktif, olusturma_tarihi)
                VALUES (%s, %s, %s, %s, 1, %s)
            """, ("aliiardicc", sifre_hash("arsac2024"), "yonetici", "Ali Ardic", now))
            conn.commit()
            print("✓ Varsayılan admin oluşturuldu: aliiardicc / arsac2024")
        else:
            print("✓ Admin zaten var, atlandı")

        # Varsayılan izinler
        ROL_IZIN = {
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
        cursor.execute("SELECT kullanici_adi, rol FROM kullanicilar WHERE aktif=1")
        for kullanici_adi, rol in cursor.fetchall():
            for modul, rol_izinleri in ROL_IZIN.items():
                g, d = rol_izinleri.get(rol, (0, 0))
                cursor.execute("""
                    INSERT INTO kullanici_izinler (kullanici_adi, modul, goruntule, duzenle)
                    VALUES (%s,%s,%s,%s)
                    ON CONFLICT (kullanici_adi, modul) DO NOTHING
                """, (kullanici_adi, modul, g, d))
        conn.commit()
        print("✓ Varsayılan izinler yüklendi")

        cursor.close()
        conn.close()
        print("\n✅ Kurulum tamamlandı!")
        print("   Başlatmak için: uvicorn main:app --host 0.0.0.0 --port 8000")

    except Exception as e:
        print(f"\n❌ Hata: {e}")
        print("   DATABASE_URL ortam değişkenini kontrol edin.")
        sys.exit(1)

if __name__ == "__main__":
    kur()
