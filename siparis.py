"""
Arsac Metal ERP — Siparis Modulu v2
Akis: Yeni siparis kaydet → klasor olustur → Metalix ac → DXF izle → parcalar otomatik islenir
"""
from styles import BTN_BLUE, BTN_GRAY, BTN_GREEN, BTN_ORANGE, BTN_PRIMARY, BTN_PURPLE, DIALOG_QSS, DURUM_RENK, GROUPBOX_QSS, INPUT, INPUT_QSS, LIST_QSS, SAYFA_QSS, TABLO_QSS, make_badge, make_buton, tab_qss, tablo_sag_tik_menu_ekle
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QDate, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QColor
from datetime import datetime
import os, re

try:
    from log import log_yaz
except:
    def log_yaz(c, n, i, d=""): pass

try:
    from metalix import (siparis_klasoru_olustur, siparis_klasor_yolu,
                         metalix_ac, _ayar_al, DwgYukleDialog)
    METALIX_OK = True
except Exception as e:
    METALIX_OK = False
    print("metalix.py yuklenemedi:", e)

DURUM_RENK = {
    "Alindi":      ("#f39c12", "#fef9e7"),
    "Uretimde":    ("#2980b9", "#eaf4fb"),
    "Hazir":       ("#8e44ad", "#f5eef8"),
    "Sevk Edildi": ("#27ae60", "#eafaf1"),
    "Iptal":       ("#e74c3c", "#fde8e8"),
}
STL = {
    "input":       "border:1.5px solid #dcdde1;border-radius:7px;padding:6px 10px;font-size:13px;background:white;color:#2c3e50;",
    "btn_primary": "background:#c0392b;color:white;border-radius:8px;padding:8px 20px;font-weight:bold;font-size:13px;border:none;",
    "btn_blue":    "background:#2980b9;color:white;border-radius:8px;padding:8px 16px;font-weight:bold;font-size:13px;border:none;",
    "btn_green":   "background:#27ae60;color:white;border-radius:8px;padding:8px 16px;font-weight:bold;font-size:13px;border:none;",
    "btn_gray":    "background:#dcdde1;color:#2c3e50;border-radius:8px;padding:8px 16px;font-weight:bold;font-size:13px;",
    "btn_purple":  "background:#8e44ad;color:white;border-radius:8px;padding:8px 16px;font-weight:bold;font-size:13px;border:none;",
}


# ─── DXF Klasör İzleyici (arka plan thread) ───────────────────
class KlasorIzleyici(QThread):
    """Verilen klasörü izler, yeni DXF/DWG gelince sinyal atar."""
    yeni_dosya = pyqtSignal(str)   # tam yol

    def __init__(self, klasor, interval_ms=2000):
        super().__init__()
        self.klasor     = klasor
        self.interval   = interval_ms / 1000.0
        self._dur       = False
        self._bilinenler = set()
        # Baslangicta mevcut dosyalari kaydet (onlari isleme)
        try:
            self._bilinenler = self._dxf_listesi()
        except: pass

    def _dxf_listesi(self):
        sonuc = set()
        for f in os.listdir(self.klasor):
            if f.lower().endswith(('.dxf', '.dwg')):
                sonuc.add(os.path.join(self.klasor, f))
        # Alt klasör DWG/
        dwg_alt = os.path.join(self.klasor, "DWG")
        if os.path.isdir(dwg_alt):
            for f in os.listdir(dwg_alt):
                if f.lower().endswith(('.dxf', '.dwg')):
                    sonuc.add(os.path.join(dwg_alt, f))
        return sonuc

    def run(self):
        import time
        while not self._dur:
            time.sleep(self.interval)
            if self._dur: break
            try:
                simdiki = self._dxf_listesi()
                yeniler = simdiki - self._bilinenler
                for yol in yeniler:
                    self.yeni_dosya.emit(yol)
                self._bilinenler = simdiki
            except: pass

    def durdur(self):
        self._dur = True


# ─── DXF Parse ────────────────────────────────────────────────
def dxf_parse(dosya_yolu):
    """Dosya adından parça bilgilerini çıkarır."""
    dosya = os.path.basename(dosya_yolu)
    ad = re.sub(r'\.(dxf|dwg)$', '', dosya, flags=re.IGNORECASE).strip()
    en_i = 0; boy_i = 0; kal = 0.0; adet = 1; malzeme = "ST37"

    # Format 1: 120X100-ST37_10_5  → en=120, boy=100, malzeme=ST37, kal=10, adet=5
    m1 = re.match(r'(\d+)[Xx](\d+)-([A-Za-z0-9]+)_(\d+(?:\.\d+)?)_(\d+)', ad)
    if m1:
        try: en_i   = int(m1.group(1))
        except: pass
        try: boy_i  = int(m1.group(2))
        except: pass
        malzeme = m1.group(3).upper()
        try: kal    = float(m1.group(4))
        except: pass
        try: adet   = int(m1.group(5))
        except: pass
    else:
        # Format 2: 25mm_200ADET
        m2 = re.search(r'(\d+(?:[.,]\d+)?)\s*mm[_\s]+(\d+)\s*[Aa][Dd][Ee][Tt]', ad)
        if m2:
            try: kal    = float(m2.group(1).replace(',', '.'))
            except: pass
            try: adet   = int(m2.group(2))
            except: pass
        else:
            m3 = re.search(r'(\d+(?:[.,]\d+)?)\s*mm', ad)
            if m3:
                try: kal = float(m3.group(1).replace(',', '.'))
                except: pass

    kg = round(en_i * boy_i * kal * 7.85 / 1_000_000 * adet, 3) if en_i and boy_i and kal else 0.0
    return {
        'parca_adi': ad, 'malzeme': malzeme,
        'kalinlik': kal, 'en': en_i, 'boy': boy_i,
        'adet': adet, 'kg': kg,
        'dosya_yolu': dosya_yolu,
    }


# ─── Yeni Sipariş Dialog ──────────────────────────────────────
class YeniSiparisDialog(QDialog):
    def __init__(self, cursor, conn, olusturan, parent=None):
        super().__init__(parent)
        self.cursor = cursor; self.conn = conn; self.olusturan = olusturan
        self.setWindowTitle("Yeni Siparis")
        self.setMinimumSize(640, 480)
        self.setStyleSheet(DIALOG_QSS)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(20, 16, 20, 16); lay.setSpacing(12)

        t = QLabel("Yeni Siparis Olustur")
        t.setStyleSheet("font-size:16px;font-weight:bold;color:#c0392b;")
        lay.addWidget(t)

        info = QLabel(
            "Siparis kaydedilince:\n"
            "  1. Z:\\\\YILI\\\\ISLER\\\\ARSC-NO-Musteri klasoru otomatik olusturulur\n"
            "  2. Metalix otomatik acilir — DXF'leri o klasore kaydedin\n"
            "  3. Sistem DXF'leri algilayip parcalara otomatik isler")
        info.setStyleSheet(
            "background:#eaf4fb;border:1px solid #aed6f1;border-radius:8px;"
            "padding:10px;font-size:12px;color:#2c3e50;line-height:1.5;")
        info.setWordWrap(True)
        lay.addWidget(info)

        # Form
        gb = QGroupBox("Siparis Bilgileri")
        fg = QGridLayout(gb); fg.setSpacing(8)

        def le(ph):
            w = QLineEdit(); w.setPlaceholderText(ph); w.setFixedHeight(36)
            w.setStyleSheet(INPUT); return w
        def dt():
            w = QDateEdit(); w.setCalendarPopup(True); w.setDate(QDate.currentDate())
            w.setDisplayFormat("dd.MM.yyyy"); w.setFixedHeight(36)
            w.setStyleSheet(INPUT); return w

        self.txt_musteri  = le("Musteri adi *")
        self.txt_yetkili  = le("Yetkili kisi")
        self.txt_telefon  = le("Telefon")
        self.txt_mus_sip  = le("Musterinin kendi siparis kodu (varsa)")
        self.dt_termin    = dt()
        self.txt_notlar   = QTextEdit()
        self.txt_notlar.setPlaceholderText("Notlar, ozel istekler...")
        self.txt_notlar.setFixedHeight(60); self.txt_notlar.setStyleSheet(INPUT)

        for row, (lbl_txt, wgt) in enumerate([
            ("Musteri *:",      self.txt_musteri),
            ("Yetkili:",        self.txt_yetkili),
            ("Telefon:",        self.txt_telefon),
            ("Musteri Sip.No:", self.txt_mus_sip),
            ("Termin:",         self.dt_termin),
            ("Notlar:",         self.txt_notlar),
        ]):
            fg.addWidget(QLabel(lbl_txt), row, 0)
            fg.addWidget(wgt, row, 1)
        lay.addWidget(gb)

        # Butonlar
        bh = QHBoxLayout(); bh.addStretch()
        bi = QPushButton("Iptal"); bi.setStyleSheet(STL["btn_gray"]); bi.clicked.connect(self.reject)
        bk = QPushButton("Siparisi Kaydet & Metalix Ac")
        bk.setFixedHeight(42); bk.setStyleSheet(STL["btn_primary"])
        bk.clicked.connect(self._kaydet)
        bh.addWidget(bi); bh.addWidget(bk); lay.addLayout(bh)

    def _sip_no_uret(self):
        yil = datetime.now().strftime("%Y")
        self.cursor.execute(
            "SELECT COUNT(*) FROM siparisler WHERE sip_no LIKE ?",
            ("ARSC-{}-%" .format(yil),))
        n = self.cursor.fetchone()[0]
        return "ARSC-{}-{:04d}".format(yil, n + 1)

    def _kaydet(self):
        musteri = self.txt_musteri.text().strip()
        if not musteri:
            QMessageBox.warning(self, "Eksik", "Musteri adi zorunlu!"); return
        try:
            sip_no     = self._sip_no_uret()
            tarih      = datetime.now().strftime("%d.%m.%Y")
            termin     = self.dt_termin.date().toString("dd.MM.yyyy")
            yetkili    = self.txt_yetkili.text().strip()
            telefon    = self.txt_telefon.text().strip()
            mus_sip_no = self.txt_mus_sip.text().strip()
            notlar     = self.txt_notlar.toPlainText().strip()

            # musteri_sip_no kolonu yoksa ekle
            try:
                self.cursor.execute("ALTER TABLE siparisler ADD COLUMN musteri_sip_no TEXT")
                self.conn.commit()
            except: pass

            self.cursor.execute("""
                INSERT INTO siparisler
                    (sip_no,musteri,telefon,tarih,termin,durum,genel_toplam,
                     notlar,olusturan,yetkili,musteri_sip_no)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (sip_no, musteri, telefon, tarih, termin,
                  'Alindi', 0.0, notlar, self.olusturan, yetkili, mus_sip_no))
            sip_id = self.cursor.lastrowid
            self.conn.commit()
            self.sip_id  = sip_id   # CSV'den önce set et
            self.sip_no  = sip_no

            log_yaz(self.cursor, self.conn, "SIPARIS_OLUSTURULDU",
                    "{} | {} | Mus.SipNo:{}".format(sip_no, musteri, mus_sip_no or "-"))

            # Klasör oluştur + CSV + Metalix aç
            self._klasor_olustur_ve_metalix_ac(sip_no, musteri, yetkili, telefon,
                                                tarih, termin, notlar)
            self.accept()

        except Exception as e:
            if "UNIQUE" in str(e):
                QMessageBox.warning(self, "Hata", "Siparis no cakisiyor, tekrar deneyin.")
            else:
                QMessageBox.critical(self, "Hata", str(e))

    def _klasor_olustur_ve_metalix_ac(self, sip_no, musteri, yetkili,
                                        telefon, tarih, termin, notlar):
        try:
            if not METALIX_OK:
                QMessageBox.information(
                    self, "Bilgi",
                    "{} kaydedildi.\n\nmetalix.py bulunamadigi icin klasor "
                    "otomatik olusturulamadi.".format(sip_no))
                return

            klasor, hata = siparis_klasoru_olustur(
                sip_no, musteri, yetkili, telefon,
                tarih, termin, notlar, [], 0.0)

            if hata:
                QMessageBox.warning(
                    self, "Klasor Uyarisi",
                    "{} kaydedildi.\n\nKlasor olusturulamadi:\n{}".format(sip_no, hata))
                return

            # CSV oluştur — Metalix için
            self._csv_olustur(klasor, sip_no, musteri, tarih, termin)

            # Metalix aç
            try:
                basarili, hata2 = metalix_ac(klasor)
            except Exception as me:
                basarili = False
                hata2 = str(me)

            if not basarili:
                try:
                    import subprocess
                    subprocess.Popen(["explorer", klasor])
                except: pass
                QMessageBox.information(
                    self, "Tamam",
                    "{} kaydedildi.\n\nKlasor olusturuldu:\n{}\n\n"
                    "Metalix acilamadi:\n{}".format(sip_no, klasor, hata2))
            else:
                QMessageBox.information(
                    self, "Tamam",
                    "{} kaydedildi.\n\nMetalix aciliyor...\n\n"
                    "DXF dosyalarini su klasore kaydedin:\n{}".format(sip_no, klasor))

        except Exception as e:
            import traceback
            hata_detay = traceback.format_exc()
            print("Klasor/Metalix hatasi:", hata_detay)
            QMessageBox.warning(
                self, "Uyari",
                "{} kaydedildi.\n\n"
                "Klasor olusturma sirasinda hata olustu:\n{}\n\n"
                "Siparis sisteme islendi, manuel klasor olusturabilirsiniz.".format(
                    sip_no, str(e)))

    def _csv_olustur(self, klasor, sip_no, musteri, tarih, termin):
        """Metalix formatında CSV oluşturur."""
        try:
            import csv, os
            # DOSYALAR alt klasörü
            dosyalar_klasor = os.path.join(klasor, "DOSYALAR")
            os.makedirs(dosyalar_klasor, exist_ok=True)

            csv_yol = os.path.join(klasor, "{}.csv".format(sip_no))

            # Sipariş kalemlerini al
            self.cursor.execute("""
                SELECT urun_adi, malzeme, kalinlik, en, boy, adet
                FROM siparis_kalemleri WHERE siparis_id=?
            """, (self.sip_id,))
            kalemler = self.cursor.fetchall()

            with open(csv_yol, "w", newline="", encoding="utf-8-sig") as f:
                yazar = csv.writer(f, delimiter=";")
                # Metalix başlık satırı
                yazar.writerow([
                    "Parça Adresi", "Klasör", "Parça Adı", "Malzeme",
                    "Kalınlık", "Min. Adet", "Maks. Adet",
                    "İş Sırası", "İş 2", "İş 3", "Sonraki",
                    "Kutu", "Öncelik", "Yönler", "Açı",
                    "Müşteri", "Proje", "CizimNo"
                ])
                for urun, mal, kal, en_v, boy, adet in kalemler:
                    mal  = mal or "ST37"
                    kal  = int(float(kal or 0))
                    adet = int(float(adet or 1))
                    # Parça adı: ENxBOY-MALZEME_KALINLIK_ADET.dxf
                    if en_v and boy:
                        parca_ad = "{:g}X{:g}-{}_{}_{}".format(
                            float(en_v), float(boy), mal, kal, adet)
                    else:
                        # En/boy yoksa parça adını kullan
                        parca_ad = str(urun or "PARCA").replace(" ", "_")
                    dosya_adi = parca_ad + ".dxf"
                    dosya_yolu = "{}\\{}".format(dosyalar_klasor, dosya_adi)

                    yazar.writerow([
                        dosya_yolu,          # Parça Adresi
                        dosyalar_klasor,     # Klasör
                        dosya_adi,           # Parça Adı
                        mal,                 # Malzeme
                        kal,                 # Kalınlık
                        adet,                # Min. Adet
                        adet,                # Maks. Adet
                        1,                   # İş Sırası
                        "", "", "",          # İş 2, 3, Sonraki
                        0,                   # Kutu
                        15,                  # Öncelik
                        0,                   # Yönler
                        0,                   # Açı
                        musteri,             # Müşteri
                        sip_no,              # Proje
                        parca_ad,            # CizimNo
                    ])
        except Exception as e:
            print("CSV olusturulamadi:", e)


# ─── Sipariş Detay Dialog ─────────────────────────────────────
class SiparisDetayDialog(QDialog):
    def __init__(self, cursor, conn, sip_id, user_role, parent=None):
        super().__init__(parent)
        self.cursor = cursor; self.conn = conn
        self.sip_id = sip_id; self.user_role = user_role
        self._izleyici = None
        self._sip_no = ""; self._musteri = ""
        self.setWindowTitle("Siparis Detay")
        self.setMinimumSize(860, 600)
        self.setStyleSheet(DIALOG_QSS + TABLO_QSS)
        self._build()
        self.yenile()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(16, 16, 16, 16); lay.setSpacing(10)

        # Bilgi kutusu
        info = QGroupBox("Siparis Bilgileri")
        ig = QGridLayout(info); ig.setSpacing(8)
        self.lbl_no  = QLabel(); self.lbl_mus = QLabel()
        self.lbl_tar = QLabel(); self.lbl_ter = QLabel()
        self.lbl_top = QLabel(); self.lbl_olu = QLabel()
        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems(list(DURUM_RENK.keys()))
        self.cmb_durum.setFixedHeight(34); self.cmb_durum.setStyleSheet(INPUT)

        for row, (l1, w1, l2, w2) in enumerate([
            ("Siparis No:", self.lbl_no,  "Musteri:",   self.lbl_mus),
            ("Tarih:",      self.lbl_tar, "Termin:",    self.lbl_ter),
            ("Olusturan:",  self.lbl_olu, "Toplam:",    self.lbl_top),
        ]):
            ig.addWidget(QLabel(l1), row, 0); ig.addWidget(w1, row, 1)
            ig.addWidget(QLabel(l2), row, 2); ig.addWidget(w2, row, 3)

        if self.user_role in ("yonetici", "satis", "uretim", "sevkiyat"):
            ig.addWidget(QLabel("Durum:"), 3, 0); ig.addWidget(self.cmb_durum, 3, 1)
            btn_g = QPushButton("Guncelle"); btn_g.setFixedHeight(34)
            btn_g.setStyleSheet(STL["btn_blue"])
            btn_g.clicked.connect(self._durum_guncelle); ig.addWidget(btn_g, 3, 2)
        lay.addWidget(info)

        # Izleme durum bandı
        self.lbl_izleme = QLabel("DXF izleme: Pasif")
        self.lbl_izleme.setStyleSheet(
            "background:#f0f0f0;border-radius:6px;padding:6px 12px;"
            "color:#7f8c8d;font-size:12px;")
        lay.addWidget(self.lbl_izleme)

        # Sekmeler
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane{border:1px solid #dcdde1;border-radius:8px;background:white;
            color: #2c3e50;}
            QTabBar::tab{background:#ecf0f1;color:#2c3e50;padding:8px 20px;
                         border-radius:6px 6px 0 0;font-weight:bold;}
            QTabBar::tab:selected{background:#c0392b;color:white;}
        """)
        self.tabs.currentChanged.connect(self._sekme_degisti)

        # Sekme 1: Parcalar
        t1 = QWidget(); t1l = QVBoxLayout(t1); t1l.setContentsMargins(8, 8, 8, 8)
        # Araçlar
        th = QHBoxLayout()
        self.lbl_parca_ozet = QLabel()
        self.lbl_parca_ozet.setStyleSheet("color:#7f8c8d;font-size:12px;")
        th.addWidget(self.lbl_parca_ozet); th.addStretch()

        if self.user_role in ("yonetici", "satis"):
            btn_parca_ekle = QPushButton("+ Manuel Parca Ekle")
            btn_parca_ekle.setFixedHeight(32); btn_parca_ekle.setStyleSheet(STL["btn_green"])
            btn_parca_ekle.clicked.connect(self._manuel_parca_ekle); th.addWidget(btn_parca_ekle)

            btn_izle = QPushButton("DXF Izlemeyi Baslat")
            btn_izle.setFixedHeight(32); btn_izle.setStyleSheet(STL["btn_purple"])
            btn_izle.clicked.connect(self._izlemeyi_baslat); th.addWidget(btn_izle)

            btn_csv = QPushButton("CSV Olustur")
            btn_csv.setFixedHeight(32)
            btn_csv.setStyleSheet("background:#e67e22;color:white;border-radius:6px;"
                                   "padding:4px 12px;font-weight:bold;border:none;")
            btn_csv.clicked.connect(self._csv_manuel_olustur); th.addWidget(btn_csv)

            btn_klasor = QPushButton("Klasoru Ac")
            btn_klasor.setFixedHeight(32); btn_klasor.setStyleSheet(STL["btn_blue"])
            btn_klasor.clicked.connect(self._klasoru_ac); th.addWidget(btn_klasor)

        t1l.addLayout(th)
        self.tbl_parca = self._tablo(
            ["Parca Adi", "Kalinlik", "En", "Boy", "Adet", "Kg", "Durum", "Islem"])
        self.tbl_parca.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for c in range(1, 7):
            self.tbl_parca.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeToContents)
        self.tbl_parca.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)
        self.tbl_parca.setColumnWidth(7, 140)
        t1l.addWidget(self.tbl_parca)
        self.tabs.addTab(t1, "Parcalar / DXF")

        # Sekme 2: Üretim takibi
        t2 = QWidget(); t2l = QVBoxLayout(t2); t2l.setContentsMargins(8, 8, 8, 8)
        self.lbl_ur_ozet = QLabel()
        self.lbl_ur_ozet.setStyleSheet("color:#7f8c8d;font-size:12px;padding:4px;")
        t2l.addWidget(self.lbl_ur_ozet)
        self.tbl_uretim = self._tablo(
            ["Parca Adi", "Adet", "Tamamlanan", "Kalan", "Durum", "Islem"])
        self.tbl_uretim.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for c in range(1, 6):
            self.tbl_uretim.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeToContents)
        t2l.addWidget(self.tbl_uretim)
        self.tabs.addTab(t2, "Uretim Takibi")

        # Sekme 3: Sevkiyat
        t3 = QWidget(); t3l = QVBoxLayout(t3); t3l.setContentsMargins(8, 8, 8, 8)
        h3 = QHBoxLayout()
        self.lbl_sv_ozet = QLabel()
        self.lbl_sv_ozet.setStyleSheet("color:#7f8c8d;font-size:12px;")
        h3.addWidget(self.lbl_sv_ozet); h3.addStretch()
        if self.user_role in ("yonetici", "sevkiyat"):
            btn_ks = QPushButton("Kismi Sevkiyat"); btn_ks.setStyleSheet(STL["btn_blue"])
            btn_ks.setFixedHeight(32); btn_ks.clicked.connect(self._kismi_sevkiyat)
            h3.addWidget(btn_ks)
        t3l.addLayout(h3)
        self.tbl_sevk = self._tablo(
            ["Parca Adi", "Toplam", "Sevk Edilen", "Kalan", "Son Sevk"])
        self.tbl_sevk.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        t3l.addWidget(self.tbl_sevk)
        self.tabs.addTab(t3, "Sevkiyat Takibi")

        lay.addWidget(self.tabs)

        # Alt butonlar
        bh = QHBoxLayout(); bh.addStretch()
        bk = QPushButton("Kapat"); bk.setFixedHeight(36); bk.setStyleSheet(STL["btn_gray"])
        bk.clicked.connect(self.accept); bh.addWidget(bk)
        lay.addLayout(bh)

    def _tablo(self, headers):
        t = QTableWidget(0, len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.setEditTriggers(QTableWidget.NoEditTriggers)
        t.setAlternatingRowColors(True); t.setShowGrid(False)
        t.verticalHeader().setVisible(False)
        t.verticalHeader().setDefaultSectionSize(40)
        t.setSelectionBehavior(QTableWidget.SelectRows)
        t.setWordWrap(False)
        return t

    def _item(self, text, align=Qt.AlignCenter, fg=None, bg=None):
        it = QTableWidgetItem(str(text))
        it.setTextAlignment(align)
        it.setForeground(QColor(fg or "#2c3e50"))
        if bg: it.setBackground(QColor(bg))
        return it

    def yenile(self):
        try:
            self.cursor.execute(
                "SELECT sip_no,musteri,tarih,termin,durum,genel_toplam,olusturan "
                "FROM siparisler WHERE id=?", (self.sip_id,))
            row = self.cursor.fetchone()
            if not row: return
            sip_no, musteri, tarih, termin, durum, toplam, olustu = row
            self._sip_no = sip_no; self._musteri = musteri
            self.lbl_no.setText("<b>{}</b>".format(sip_no))
            self.lbl_mus.setText("<b>{}</b>".format(musteri or "-"))
            self.lbl_tar.setText(tarih or "-")
            self.lbl_ter.setText(termin or "-")
            self.lbl_olu.setText(olustu or "-")
            self.lbl_top.setText(
                "<b style='color:#c0392b'>{:,.2f} TL</b>".format(float(toplam or 0)))
            self.cmb_durum.setCurrentText(durum or "Alindi")

            self.cursor.execute(
                "SELECT id,urun_adi,kalinlik,en,boy,adet,kg,uretim_durumu "
                "FROM siparis_kalemleri WHERE siparis_id=?", (self.sip_id,))
            self._kalemler = self.cursor.fetchall()
            self._parca_tablosu_doldur()

            idx = self.tabs.currentIndex()
            if idx == 1: self._uretim_yukle()
            elif idx == 2: self._sevkiyat_yukle()
        except Exception as e:
            import traceback; traceback.print_exc()

    def _parca_tablosu_doldur(self):
        self.tbl_parca.setRowCount(0)
        # Inline düzenleme açık
        self.tbl_parca.setEditTriggers(
            QTableWidget.DoubleClicked | QTableWidget.SelectedClicked)
        DUR_RENK_L = {
            "Beklemede": "#f39c12", "Uretimde": "#2980b9",
            "Tamamlandi": "#27ae60", "Iptal": "#e74c3c"
        }
        for i, (kid, urun, kal, en, boy, adet, kg, ud) in enumerate(self._kalemler):
            self.tbl_parca.insertRow(i); self.tbl_parca.setRowHeight(i, 38)
            kal_str = "{:.0f}".format(float(kal)) if kal else ""
            en_str  = str(int(float(en))) if en else ""
            boy_str = str(int(float(boy))) if boy else ""
            kg_str  = "{:.3f}".format(float(kg)) if kg else "-"
            ud      = ud or "Beklemede"
            renk    = DUR_RENK_L.get(ud, "#7f8c8d")

            # Düzenlenebilir hücreler
            def _edit_item(val, align=Qt.AlignCenter):
                it = QTableWidgetItem(str(val))
                it.setTextAlignment(align)
                it.setData(Qt.UserRole, kid)
                return it

            self.tbl_parca.setItem(i, 0, _edit_item(urun or "", Qt.AlignLeft | Qt.AlignVCenter))
            self.tbl_parca.setItem(i, 1, _edit_item(kal_str))
            self.tbl_parca.setItem(i, 2, _edit_item(en_str))
            self.tbl_parca.setItem(i, 3, _edit_item(boy_str))
            self.tbl_parca.setItem(i, 4, _edit_item(str(int(float(adet or 1)))))

            # Kg — salt okunur (otomatik hesap)
            kg_it = QTableWidgetItem(kg_str)
            kg_it.setTextAlignment(Qt.AlignCenter)
            kg_it.setFlags(kg_it.flags() & ~Qt.ItemIsEditable)
            kg_it.setForeground(__import__("PyQt5.QtGui", fromlist=["QColor"]).QColor("#7f8c8d"))
            self.tbl_parca.setItem(i, 5, kg_it)

            self.tbl_parca.setItem(i, 6, self._item(ud, fg=renk))

            # Sadece Sil butonu
            bw = QWidget(); bl = QHBoxLayout(bw)
            bl.setContentsMargins(2, 2, 2, 2)
            btn_sil = QPushButton("Sil"); btn_sil.setFixedHeight(28)
            btn_sil.setMinimumWidth(40)
            btn_sil.setStyleSheet("background:#e74c3c;color:white;border-radius:4px;"
                                   "font-size:11px;border:none;padding:2px 8px;")
            btn_sil.clicked.connect(lambda _, k=kid: self._parca_sil(k))
            bl.addWidget(btn_sil)
            self.tbl_parca.setCellWidget(i, 7, bw)

        # Hücre değişince otomatik kaydet
        try: self.tbl_parca.itemChanged.disconnect()
        except: pass
        self.tbl_parca.itemChanged.connect(self._parca_inline_kaydet)

        toplam_kg = sum(float(k[6] or 0) for k in self._kalemler)
        self.lbl_parca_ozet.setText(
            "{} parca  |  Toplam ~{:.2f} kg".format(
                len(self._kalemler), toplam_kg))

    def _parca_inline_kaydet(self, item):
        """Tabloda hücre değişince DB'ye kaydet, kg otomatik hesapla."""
        try:
            kid = item.data(Qt.UserRole)
            if not kid: return
            row = item.row()

            def _cell(col):
                it = self.tbl_parca.item(row, col)
                return it.text().strip() if it else ""

            ad   = _cell(0)
            kal  = float(_cell(1).replace(",", ".") or 0)
            en_v = float(_cell(2).replace(",", ".") or 0)
            boy  = float(_cell(3).replace(",", ".") or 0)
            adet = int(float(_cell(4) or 1))
            kg   = round(en_v * boy * kal * 7.85 / 1_000_000 * adet, 3) \
                   if en_v and boy and kal else 0.0

            self.cursor.execute("""
                UPDATE siparis_kalemleri
                SET urun_adi=?, kalinlik=?, en=?, boy=?, adet=?, kg=?
                WHERE id=?
            """, (ad, kal, en_v, boy, adet, kg, kid))
            self.conn.commit()

            # Kg hücresini güncelle (sinyali geçici kes)
            self.tbl_parca.itemChanged.disconnect()
            kg_it = self.tbl_parca.item(row, 5)
            if kg_it and kg > 0:
                kg_it.setText("{:.3f}".format(kg))
            self.tbl_parca.itemChanged.connect(self._parca_inline_kaydet)

            # Özet güncelle
            self.cursor.execute(
                "SELECT COALESCE(SUM(kg),0) FROM siparis_kalemleri WHERE siparis_id=?",
                (self.sip_id,))
            tkq = self.cursor.fetchone()[0]
            self.lbl_parca_ozet.setText(
                "{} parca  |  Toplam ~{:.2f} kg".format(
                    self.tbl_parca.rowCount(), float(tkq)))
        except Exception as e:
            print("Inline kaydet hatasi:", e)

    def _csv_olustur(self, klasor, sip_no, musteri, tarih, termin):
        """Metalix formatında CSV oluşturur."""
        try:
            import csv
            dosyalar_klasor = os.path.join(klasor, "DOSYALAR")
            os.makedirs(dosyalar_klasor, exist_ok=True)
            csv_yol = os.path.join(klasor, "{}.csv".format(sip_no))
            self.cursor.execute("""
                SELECT urun_adi, malzeme, kalinlik, en, boy, adet
                FROM siparis_kalemleri WHERE siparis_id=?
            """, (self.sip_id,))
            kalemler = self.cursor.fetchall()
            with open(csv_yol, "w", newline="", encoding="utf-8-sig") as f:
                yazar = csv.writer(f, delimiter=";")
                yazar.writerow([
                    "Parça Adresi", "Klasör", "Parça Adı", "Malzeme",
                    "Kalınlık", "Min. Adet", "Maks. Adet",
                    "İş Sırası", "İş 2", "İş 3", "Sonraki",
                    "Kutu", "Öncelik", "Yönler", "Açı",
                    "Müşteri", "Proje", "CizimNo"
                ])
                for urun, mal, kal, en_v, boy, adet in kalemler:
                    mal  = mal or "ST37"
                    kal  = int(float(kal or 0))
                    adet = int(float(adet or 1))
                    if en_v and boy:
                        parca_ad = "{:g}X{:g}-{}_{}_{}" .format(
                            float(en_v), float(boy), mal, kal, adet)
                    else:
                        parca_ad = str(urun or "PARCA").replace(" ", "_")
                    dosya_adi = parca_ad + ".dxf"
                    dosya_yolu = "{}\\{}".format(dosyalar_klasor, dosya_adi)
                    yazar.writerow([
                        dosya_yolu, dosyalar_klasor, dosya_adi,
                        mal, kal, adet, adet,
                        1, "", "", "", 0, 15, 0, 0,
                        musteri, sip_no, parca_ad,
                    ])
        except Exception as e:
            print("CSV olusturulamadi:", e)

    def _csv_manuel_olustur(self):
        """Parçalar sekmesindeki butona basınca CSV oluştur."""
        try:
            if not METALIX_OK:
                QMessageBox.warning(self, "Bilgi", "metalix.py bulunamadi."); return
            from metalix import siparis_klasor_yolu
            klasor = siparis_klasor_yolu(self._sip_no, self._musteri)
            if not os.path.exists(klasor):
                os.makedirs(klasor, exist_ok=True)

            # Sipariş bilgilerini al
            self.cursor.execute(
                "SELECT tarih, termin FROM siparisler WHERE id=?", (self.sip_id,))
            row = self.cursor.fetchone()
            tarih  = row[0] if row else ""
            termin = row[1] if row else ""

            self._csv_olustur(klasor, self._sip_no, self._musteri, tarih, termin)
            QMessageBox.information(
                self, "Tamam",
                "CSV olusturuldu:\n{}\\{}.csv".format(klasor, self._sip_no))
        except Exception as e:
            QMessageBox.critical(self, "Hata", "CSV olusturulamadi:\n{}".format(str(e)))

    def _manuel_parca_ekle(self):
        """Elle parça ekle."""
        self._parca_dialog_ac(None)

    def _parca_duzenle(self, kid):
        """Mevcut parçayı düzenle."""
        self._parca_dialog_ac(kid)

    def _parca_dialog_ac(self, kid):
        dlg = QDialog(self)
        dlg.setWindowTitle("Parca Ekle" if kid is None else "Parca Duzenle")
        dlg.setMinimumWidth(420)
        dlg.setStyleSheet(DIALOG_QSS)
        lay = QVBoxLayout(dlg)

        fg = QGridLayout(); fg.setSpacing(8)

        def le(ph, val=""):
            w = QLineEdit(); w.setPlaceholderText(ph)
            w.setFixedHeight(34); w.setStyleSheet(INPUT)
            w.setText(str(val) if val else ""); return w

        txt_ad   = le("Parca adi *")
        txt_kal  = le("Kalinlik mm", "")
        txt_en   = le("En mm", "")
        txt_boy  = le("Boy mm", "")
        txt_adet = le("Adet *", "1")
        txt_mal  = le("Malzeme", "ST37")

        # Mevcut kayıt varsa DB'den direkt oku
        if kid:
            try:
                self.cursor.execute(
                    "SELECT urun_adi, kalinlik, en, boy, adet, malzeme "
                    "FROM siparis_kalemleri WHERE id=?", (kid,))
                row = self.cursor.fetchone()
                if row:
                    ad, kal, en_v, boy, adet, mal = row
                    txt_ad.setText(str(ad or ""))
                    txt_kal.setText(str(kal).rstrip("0").rstrip(".") if kal else "")
                    txt_en.setText(str(int(float(en_v))) if en_v else "")
                    txt_boy.setText(str(int(float(boy))) if boy else "")
                    txt_adet.setText(str(int(float(adet or 1))))
                    txt_mal.setText(str(mal or "ST37"))
            except Exception as e:
                print("Parca dialog doldurma hatasi:", e)

        for r, (lbl, w) in enumerate([
            ("Parca Adi *:", txt_ad),
            ("Kalinlik (mm):", txt_kal),
            ("En (mm):", txt_en),
            ("Boy (mm):", txt_boy),
            ("Adet *:", txt_adet),
            ("Malzeme:", txt_mal),
        ]):
            fg.addWidget(QLabel(lbl), r, 0)
            fg.addWidget(w, r, 1)
        lay.addLayout(fg)

        bh = QHBoxLayout(); bh.addStretch()
        bi = QPushButton("Iptal"); bi.setFixedHeight(34)
        bi.setStyleSheet(STL["btn_gray"]); bi.clicked.connect(dlg.reject)
        bk = QPushButton("Kaydet"); bk.setFixedHeight(34)
        bk.setStyleSheet(STL["btn_primary"]); bk.clicked.connect(dlg.accept)
        bh.addWidget(bi); bh.addWidget(bk); lay.addLayout(bh)

        if dlg.exec_() != QDialog.Accepted: return

        try:
            ad   = txt_ad.text().strip()
            if not ad: QMessageBox.warning(self, "Eksik", "Parca adi zorunlu!"); return
            kal  = float(txt_kal.text().replace(",",".") or 0)
            en_v = float(txt_en.text().replace(",",".") or 0)
            boy  = float(txt_boy.text().replace(",",".") or 0)
            adet = int(float(txt_adet.text() or 1))
            mal  = txt_mal.text().strip() or "ST37"
            kg   = round(en_v * boy * kal * 7.85 / 1_000_000 * adet, 3) if en_v and boy and kal else 0.0

            if kid:
                self.cursor.execute("""
                    UPDATE siparis_kalemleri
                    SET urun_adi=?,kalinlik=?,en=?,boy=?,adet=?,kg=?,malzeme=?
                    WHERE id=?
                """, (ad, kal, en_v, boy, adet, kg, mal, kid))
            else:
                self.cursor.execute("""
                    INSERT INTO siparis_kalemleri
                        (siparis_id,urun_adi,kalinlik,en,boy,adet,kg,malzeme,
                         birim,birim_fiyat,toplam_fiyat,uretim_durumu)
                    VALUES (?,?,?,?,?,?,?,?,'Adet',0,0,'Beklemede')
                """, (self.sip_id, ad, kal, en_v, boy, adet, kg, mal))
            self.conn.commit()
            self.yenile()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _parca_sil(self, kid):
        if QMessageBox.question(self, "Sil", "Bu parçayi silmek istiyor musunuz?",
                                 QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        try:
            self.cursor.execute("DELETE FROM siparis_kalemleri WHERE id=?", (kid,))
            self.conn.commit(); self.yenile()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _senkronize_et(self):
        """Tüm parçalar sevk edildiyse sipariş durumunu otomatik güncelle."""
        try:
            # Tüm kalemler sevk edildi mi?
            self.cursor.execute(
                "SELECT COUNT(*) FROM siparis_kalemleri WHERE siparis_id=?",
                (self.sip_id,))
            toplam = self.cursor.fetchone()[0]
            if toplam == 0: return

            self.cursor.execute("""
                SELECT COUNT(*) FROM sevkiyat_kalemleri sk
                JOIN siparis_kalemleri sk2 ON sk.kalem_id=sk2.id
                WHERE sk2.siparis_id=?
                GROUP BY sk.kalem_id
            """, (self.sip_id,))

            # Daha basit kontrol — parca_sevk_bekliyor tablosundan
            self.cursor.execute("""
                SELECT COUNT(*) FROM parca_sevk_bekliyor
                WHERE siparis_id=? AND durum='Bekliyor'
            """, (self.sip_id,))
            bekleyen = self.cursor.fetchone()[0]

            self.cursor.execute("""
                SELECT COUNT(*) FROM parca_sevk_bekliyor
                WHERE siparis_id=? AND durum='Sevk Edildi'
            """, (self.sip_id,))
            sevkedilen = self.cursor.fetchone()[0]

            if sevkedilen > 0 and bekleyen == 0:
                # Hepsi sevk edildi
                self.cursor.execute(
                    "UPDATE siparisler SET durum='Sevk Edildi' WHERE id=? AND durum!='Iptal'",
                    (self.sip_id,))
                self.conn.commit()
                log_yaz(self.cursor, self.conn, "SIPARIS_OTOMATIK_SEVK",
                        "ID:{} otomatik Sevk Edildi yapildi".format(self.sip_id))
        except Exception as e:
            print("Senkronizasyon hatasi:", e)
        if idx == 1: self._uretim_yukle()
        elif idx == 2: self._sevkiyat_yukle()

    def _sekme_degisti(self, idx):
        if idx == 1: self._uretim_yukle()
        elif idx == 2: self._sevkiyat_yukle()

    def _uretim_yukle(self):
        if not hasattr(self, '_kalemler'): return
        try:
            ids = [k[0] for k in self._kalemler]
            if not ids: return
            ph = ",".join("?" * len(ids))
            self.cursor.execute(
                "SELECT id,uretim_durumu,tamamlanan_adet FROM siparis_kalemleri "
                "WHERE id IN (" + ph + ")", ids)
            umap = {r[0]: r for r in self.cursor.fetchall()}
            DUR_STL = {
                "Beklemede":  ("#f39c12", "#fef9e7"),
                "Uretimde":   ("#2980b9", "#eaf4fb"),
                "Tamamlandi": ("#27ae60", "#eafaf1"),
            }
            self.tbl_uretim.setRowCount(0)
            tam_sayac = 0
            for i, (kid, urun, kal, en, boy, adet, kg, _) in enumerate(self._kalemler):
                ur = umap.get(kid)
                durum = (ur[1] or "Beklemede") if ur else "Beklemede"
                tam   = float(ur[2] or 0) if ur else 0.0
                af    = float(adet or 1); kalan = max(0.0, af - tam)
                if durum == "Tamamlandi": tam_sayac += 1
                self.tbl_uretim.insertRow(i); self.tbl_uretim.setRowHeight(i, 36)
                self.tbl_uretim.setItem(
                    i, 0, self._item(urun or "-", Qt.AlignLeft | Qt.AlignVCenter))
                for col, val in [(1, "{:g}".format(af)),
                                  (2, "{:g}".format(tam)),
                                  (3, "{:g}".format(kalan))]:
                    self.tbl_uretim.setItem(i, col, self._item(val))
                fc, bg = DUR_STL.get(durum, ("#7f8c8d","white"))
                self.tbl_uretim.setItem(i, 4, self._item(durum, fg=fc, bg=bg))
                # Butonlar
                bw = QWidget(); bl = QHBoxLayout(bw)
                bl.setContentsMargins(2, 2, 2, 2); bl.setSpacing(3)
                for txt, rk, nd in [("Uretimde", "#2980b9", "Uretimde"),
                                     ("Tamamlandi", "#27ae60", "Tamamlandi")]:
                    b = QPushButton(txt); b.setFixedHeight(32); b.setMinimumWidth(90)
                    b.setStyleSheet(
                        "background:{};color:white;border-radius:4px;"
                        "font-size:12px;border:none;padding:4px 10px;".format(rk))
                    b.clicked.connect(lambda _, k=kid, d=nd: self._kalem_durum(k, d))
                    bl.addWidget(b)
                self.tbl_uretim.setCellWidget(i, 5, bw)
            n = len(self._kalemler)
            self.lbl_ur_ozet.setText(
                "Toplam {} kalem | {} tamamlandi | {} devam".format(
                    n, tam_sayac, n - tam_sayac))
        except Exception as e:
            print("Uretim yukle hatasi:", e)

    def _kalem_durum(self, kid, durum):
        try:
            if durum == "Tamamlandi":
                self.cursor.execute(
                    "UPDATE siparis_kalemleri SET uretim_durumu=?,tamamlanan_adet=adet WHERE id=?",
                    (durum, kid))
            else:
                self.cursor.execute(
                    "UPDATE siparis_kalemleri SET uretim_durumu=? WHERE id=?",
                    (durum, kid))
            self.conn.commit(); self._uretim_yukle()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _sevkiyat_yukle(self):
        if not hasattr(self, '_kalemler'): return
        try:
            ids = [k[0] for k in self._kalemler]
            if not ids: return
            ph = ",".join("?" * len(ids))
            self.cursor.execute(
                "SELECT kalem_id,COALESCE(SUM(sevk_adet),0),MAX(tarih) "
                "FROM sevkiyat_kalemleri WHERE kalem_id IN (" + ph + ") "
                "GROUP BY kalem_id", ids)
            smap = {r[0]: r for r in self.cursor.fetchall()}
            self.tbl_sevk.setRowCount(0)
            top_a = 0.0; top_s = 0.0
            for i, (kid, urun, kal, en, boy, adet, kg, _) in enumerate(self._kalemler):
                af   = float(adet or 1); sr = smap.get(kid)
                sevk = float(sr[1] or 0) if sr else 0.0
                son  = str(sr[2]) if sr and sr[2] else "-"
                kalan = max(0.0, af - sevk); top_a += af; top_s += sevk
                self.tbl_sevk.insertRow(i); self.tbl_sevk.setRowHeight(i, 36)
                self.tbl_sevk.setItem(
                    i, 0, self._item(urun or "-", Qt.AlignLeft | Qt.AlignVCenter))
                self.tbl_sevk.setItem(i, 1, self._item("{:g}".format(af)))
                self.tbl_sevk.setItem(i, 2, self._item("{:g}".format(sevk)))
                fg = "#27ae60" if kalan == 0 else "#e67e22"
                bg = "#eafaf1" if kalan == 0 else None
                self.tbl_sevk.setItem(i, 3, self._item("{:g}".format(kalan), fg=fg, bg=bg))
                self.tbl_sevk.setItem(i, 4, self._item(son))
            self.lbl_sv_ozet.setText(
                "Toplam {:g} | Sevk {:g} | Bekleyen {:g}".format(
                    top_a, top_s, top_a - top_s))
        except Exception as e:
            print("Sevk yukle hatasi:", e)

    def _kismi_sevkiyat(self):
        try:
            self.cursor.execute(
                "SELECT id,urun_adi,adet,sevk_edilen_adet FROM siparis_kalemleri "
                "WHERE siparis_id=?", (self.sip_id,))
            kalemler = self.cursor.fetchall()
            if not kalemler: return
            dlg = KismiSevkDialog(kalemler, self._sip_no, self)
            if dlg.exec_() == QDialog.Accepted and dlg.sevk_listesi:
                tarih = datetime.now().strftime("%d.%m.%Y")
                for kid, sadet in dlg.sevk_listesi:
                    self.cursor.execute(
                        "INSERT INTO sevkiyat_kalemleri "
                        "(sevkiyat_id,siparis_id,kalem_id,sevk_adet,tarih) "
                        "VALUES (0,?,?,?,?)",
                        (self.sip_id, kid, sadet, tarih))
                    self.cursor.execute(
                        "UPDATE siparis_kalemleri SET sevk_edilen_adet=sevk_edilen_adet+? "
                        "WHERE id=?", (sadet, kid))
                self.conn.commit()
                QMessageBox.information(
                    self, "Tamam",
                    "{} kalem sevkiyati kaydedildi.".format(len(dlg.sevk_listesi)))
                self._senkronize_et()
                self._sevkiyat_yukle()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _durum_guncelle(self):
        try:
            yeni = self.cmb_durum.currentText()
            self.cursor.execute(
                "UPDATE siparisler SET durum=? WHERE id=?", (yeni, self.sip_id))
            self.conn.commit()
            log_yaz(self.cursor, self.conn, "SIPARIS_DURUM",
                    "ID:{} - {}".format(self.sip_id, yeni))
            if self.parent() and hasattr(self.parent(), 'yenile'):
                self.parent().yenile()
            # Uretimde secilince otomatik is emri ac
            if yeni == "Uretimde":
                self._otomatik_is_emri()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _otomatik_is_emri(self):
        """Siparis Uretimde yapilinca uretim modulunde otomatik is emri olustur."""
        try:
            # Zaten bu siparis icin is emri var mi?
            self.cursor.execute(
                "SELECT id FROM isler WHERE is_no LIKE ?",
                ("%{}%".format(self._sip_no),))
            if self.cursor.fetchone():
                return  # Zaten var, tekrar açma

            # Termin bilgisini al
            self.cursor.execute(
                "SELECT termin FROM siparisler WHERE id=?", (self.sip_id,))
            ter_row = self.cursor.fetchone()
            termin = ter_row[0] if ter_row else ""

            # Siparis kalemlerini al
            self.cursor.execute(
                "SELECT urun_adi, adet, kalinlik FROM siparis_kalemleri WHERE siparis_id=?",
                (self.sip_id,))
            kalemler = self.cursor.fetchall()

            # Is emri no uret: IE-ARSC-2026-0001
            is_no = "IE-{}".format(self._sip_no)
            tarih = datetime.now().strftime("%d.%m.%Y")

            self.cursor.execute(
                "INSERT INTO isler (is_no,musteri,tarih,durum,termin,toplam_kg,ilerleme) "
                "VALUES (?,?,?,'Uretimde',?,0,0)",
                (is_no, self._musteri, tarih, termin or ""))

            # Parcalari ekle
            for urun, adet, kal in kalemler:
                self.cursor.execute(
                    "INSERT INTO parcalar (is_no,parca_adi,adet,birim_kg,durum,biten_adet) "
                    "VALUES (?,?,?,0,'Beklemede',0)",
                    (is_no, urun or "-", int(float(adet or 1))))

            self.conn.commit()
            log_yaz(self.cursor, self.conn, "IS_EMRI_OTOMATIK",
                    "{} → {}".format(self._sip_no, is_no))

            QMessageBox.information(
                self, "Is Emri Olusturuldu",
                "{} numarali siparis icin\n"
                "uretim is emri otomatik olusturuldu:\n\n"
                "Is No: {}".format(self._sip_no, is_no))
        except Exception as e:
            print("Otomatik is emri hatasi:", e)

    # ─── DXF İzleme ──────────────────────────────────────────
    def _klasoru_ac(self):
        try:
            if not METALIX_OK:
                QMessageBox.warning(self, "Bilgi", "metalix.py bulunamadi."); return
            klasor = siparis_klasor_yolu(self._sip_no, self._musteri)
            if os.path.exists(klasor):
                import subprocess; subprocess.Popen(["explorer", klasor])
            else:
                QMessageBox.warning(self, "Yok",
                    "Klasor bulunamadi:\n{}\n\nSiparisi yeniden olusturun.".format(klasor))
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _izlemeyi_baslat(self):
        if not METALIX_OK:
            QMessageBox.warning(self, "Bilgi", "metalix.py bulunamadi."); return
        if self._izleyici and self._izleyici.isRunning():
            QMessageBox.information(self, "Bilgi", "Izleme zaten aktif."); return
        try:
            klasor = siparis_klasor_yolu(self._sip_no, self._musteri)
            if not os.path.exists(klasor):
                QMessageBox.warning(self, "Yok",
                    "Klasor bulunamadi:\n{}\n\nOnce Metalix'i acin ve dosyalari orada olusturun.".format(klasor))
                return
            self._izleyici = KlasorIzleyici(klasor)
            self._izleyici.yeni_dosya.connect(self._yeni_dxf_islendi)
            self._izleyici.start()
            self.lbl_izleme.setText(
                "DXF izleme: AKTIF — {}".format(os.path.basename(klasor)))
            self.lbl_izleme.setStyleSheet(
                "background:#eafaf1;border:1px solid #27ae60;border-radius:6px;"
                "padding:6px 12px;color:#27ae60;font-size:12px;font-weight:bold;")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _yeni_dxf_islendi(self, dosya_yolu):
        """Yeni DXF geldi → parse et → DB'ye ekle → tabloyu yenile."""
        try:
            parca = dxf_parse(dosya_yolu)
            self.cursor.execute("""
                INSERT INTO siparis_kalemleri
                    (siparis_id,urun_adi,kalinlik,en,boy,adet,kg,
                     birim,birim_fiyat,toplam_fiyat,uretim_durumu)
                VALUES (?,?,?,?,?,?,?,'Adet',0,0,'Beklemede')
            """, (self.sip_id,
                  parca['parca_adi'], parca['kalinlik'],
                  parca['en'], parca['boy'],
                  parca['adet'], parca['kg']))
            self.conn.commit()
            # UI thread'den güncelle
            QTimer.singleShot(0, self.yenile)
            self.lbl_izleme.setText(
                "DXF izleme: AKTIF — Son: {}".format(
                    os.path.basename(dosya_yolu)))
        except Exception as e:
            print("DXF isleme hatasi:", e)

    def closeEvent(self, event):
        if self._izleyici:
            self._izleyici.durdur()
            self._izleyici.wait(4000)  # interval(3s) + buffer
            self._izleyici = None
        super().closeEvent(event)


# ─── Kısmi Sevk Dialog ────────────────────────────────────────
class KismiSevkDialog(QDialog):
    def __init__(self, kalemler, sip_no, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kismi Sevkiyat — " + str(sip_no))
        self.setMinimumSize(560, 400)
        self.sevk_listesi = []; self._spinler = []
        self._build(kalemler)

    def _build(self, kalemler):
        lay = QVBoxLayout(self); lay.setContentsMargins(16, 14, 16, 14); lay.setSpacing(10)
        lay.addWidget(QLabel("Sevk edilecek adetleri girin (0 = sevk etme):"))
        t = QTableWidget(0, 4)
        t.setHorizontalHeaderLabels(["Parca Adi", "Siparis", "Onceki Sevk", "Simdi"])
        t.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for c in [1, 2, 3]:
            t.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeToContents)
        t.verticalHeader().setVisible(False)
        t.setEditTriggers(QTableWidget.NoEditTriggers)
        t.setStyleSheet(
            "QTableWidget{color:#2c3e50;}"
            "QHeaderView::section{background:#2c3e50;color:white;padding:6px;border:none;}")
        for kid, urun, adet, onceki in kalemler:
            r = t.rowCount(); t.insertRow(r); t.setRowHeight(r, 36)
            af = float(adet or 1); of = float(onceki or 0); kalan = max(0.0, af - of)
            t.setItem(r, 0, QTableWidgetItem(urun or "-"))
            t.setItem(r, 1, QTableWidgetItem("{:g}".format(af)))
            t.setItem(r, 2, QTableWidgetItem("{:g}".format(of)))
            spn = QDoubleSpinBox(); spn.setRange(0, kalan); spn.setValue(0)
            spn.setDecimals(0); spn.setFixedHeight(30); spn.setStyleSheet(INPUT)
            if kalan == 0: spn.setEnabled(False)
            t.setCellWidget(r, 3, spn); self._spinler.append((kid, spn))
        lay.addWidget(t)
        bh = QHBoxLayout(); bh.addStretch()
        bi = QPushButton("Iptal"); bi.setStyleSheet(STL["btn_gray"]); bi.clicked.connect(self.reject)
        bk = QPushButton("Kaydet"); bk.setStyleSheet(STL["btn_primary"])
        bk.clicked.connect(self._kaydet)
        bh.addWidget(bi); bh.addWidget(bk); lay.addLayout(bh)

    def _kaydet(self):
        self.sevk_listesi = [(k, s.value()) for k, s in self._spinler if s.value() > 0]
        if not self.sevk_listesi:
            QMessageBox.warning(self, "Uyari", "En az bir kalem icin adet girin."); return
        self.accept()


# ─── Ana Sipariş Sayfası ──────────────────────────────────────
class SiparisSayfasi(QWidget):
    def __init__(self, cursor, conn, user_role, kullanici_adi):
        super().__init__()
        self.cursor = cursor; self.conn = conn
        self.user_role = user_role; self.kullanici_adi = kullanici_adi
        self.setStyleSheet("QWidget{background:#f4f6f9;font-family:'Segoe UI';}")
        self._build()
        self.yenile()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(20, 16, 20, 16); lay.setSpacing(12)

        # Başlık + butonlar
        hdr = QHBoxLayout()
        lbl = QLabel("SİPARİŞLER")
        lbl.setStyleSheet("font-size:18px;font-weight:900;color:#2c3e50;")
        hdr.addWidget(lbl); hdr.addStretch()
        if self.user_role in ("yonetici", "satis"):
            btn_y = QPushButton("+ Yeni Siparis"); btn_y.setFixedHeight(38)
            btn_y.setStyleSheet(STL["btn_primary"]); btn_y.clicked.connect(self._yeni)
            hdr.addWidget(btn_y)
        btn_r = QPushButton("Yenile"); btn_r.setFixedHeight(38); btn_r.setStyleSheet(STL["btn_gray"])
        btn_r.clicked.connect(self.yenile); hdr.addWidget(btn_r)
        lay.addLayout(hdr)

        # Özet kartlar
        klay = QHBoxLayout(); klay.setSpacing(10)
        self.k_toplam = self._kart("TOPLAM",      "0", "#2c3e50")
        self.k_alindi = self._kart("ALINDI",       "0", "#f39c12")
        self.k_uretim = self._kart("URETIMDE",     "0", "#2980b9")
        self.k_hazir  = self._kart("HAZIR",        "0", "#8e44ad")
        self.k_sevk   = self._kart("SEVK EDILDI",  "0", "#27ae60")
        for k in [self.k_toplam, self.k_alindi, self.k_uretim, self.k_hazir, self.k_sevk]:
            klay.addWidget(k)
        lay.addLayout(klay)

        # Filtre
        flay = QHBoxLayout(); flay.setSpacing(8)
        self.txt_ara = QLineEdit(); self.txt_ara.setPlaceholderText("Siparis no veya musteri ara...")
        self.txt_ara.setFixedHeight(36); self.txt_ara.setStyleSheet(INPUT)
        self.txt_ara.textChanged.connect(self._filtrele)
        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems(["Tumu", "Alindi", "Uretimde", "Hazir", "Sevk Edildi", "Iptal"])
        self.cmb_durum.setFixedHeight(36); self.cmb_durum.setStyleSheet(INPUT)
        self.cmb_durum.setFixedWidth(140); self.cmb_durum.currentTextChanged.connect(self._filtrele)
        flay.addWidget(self.txt_ara); flay.addWidget(self.cmb_durum)
        lay.addLayout(flay)

        # Tablo
        self.tablo = QTableWidget(0, 7)
        tablo_sag_tik_menu_ekle(self.tablo)
        self.tablo.setHorizontalHeaderLabels(
            ["Siparis No", "Tarih", "Musteri", "Yetkili", "Durum", "Termin", "Tutar (TL)"])
        self.tablo.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        for c in [0, 1, 3, 4, 5, 6]:
            self.tablo.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeToContents)
        self.tablo.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tablo.setAlternatingRowColors(True); self.tablo.setShowGrid(False)
        self.tablo.verticalHeader().setVisible(False)
        self.tablo.setSelectionBehavior(QTableWidget.SelectRows)
        self.tablo.setStyleSheet("""
            QTableWidget{background:white;border-radius:10px;border:1px solid #dcdde1;color:#2c3e50;}
            QTableWidget::item{color:#2c3e50;padding:6px;}
            QTableWidget::item:selected{background:#2980b9;color:white;}
            QHeaderView::section{background:#2c3e50;color:white;padding:8px;font-weight:bold;border:none;}
            QTableWidget::item:alternate{background:#f8f9fa;}
        """)
        self.tablo.doubleClicked.connect(
            lambda idx: self._detay(self.tablo.item(idx.row(), 0).data(Qt.UserRole)))
        lay.addWidget(self.tablo)

    def _kart(self, baslik, deger, renk):
        f = QFrame(); f.setFixedHeight(68)
        f.setStyleSheet(
            "QFrame{{background:white;border-radius:10px;border:1px solid #dcdde1;"
            "border-left:5px solid {r};}}".format(r=renk))
        v = QVBoxLayout(f); v.setContentsMargins(12, 6, 12, 6); v.setSpacing(2)
        lb = QLabel(baslik)
        lb.setStyleSheet("color:#7f8c8d;font-size:10px;font-weight:bold;background:transparent;")
        ld = QLabel(deger)
        ld.setStyleSheet(
            "color:{};font-size:18px;font-weight:900;background:transparent;".format(renk))
        ld.setObjectName("val")
        v.addWidget(lb); v.addWidget(ld); return f

    def _set_kart(self, k, v):
        k.findChild(QLabel, "val").setText(str(v))

    def yenile(self):
        try:
            self.cursor.execute("SELECT durum, COUNT(*) FROM siparisler GROUP BY durum")
            sc = dict(self.cursor.fetchall())
            self._set_kart(self.k_toplam, sum(sc.values()))
            self._set_kart(self.k_alindi, sc.get("Alindi", 0))
            self._set_kart(self.k_uretim, sc.get("Uretimde", 0))
            self._set_kart(self.k_hazir,  sc.get("Hazir", 0))
            self._set_kart(self.k_sevk,   sc.get("Sevk Edildi", 0))

            self.cursor.execute("""
                SELECT id,sip_no,tarih,musteri,yetkili,durum,termin,genel_toplam
                FROM siparisler ORDER BY id DESC
            """)
            self.tablo.setRowCount(0)
            for i, (sid, sno, tarih, mus, yet, durum, ter, top) in enumerate(
                    self.cursor.fetchall()):
                self.tablo.insertRow(i); self.tablo.setRowHeight(i, 38)
                fc, bg = DURUM_RENK.get(durum, ("#2c3e50", "white"))
                vals = [sno or "-", tarih or "-", mus or "-",
                        yet or "-", "", ter or "-",
                        "{:,.2f}".format(float(top or 0))]
                for j, v in enumerate(vals):
                    if j == 4: continue
                    it = QTableWidgetItem(v)
                    it.setTextAlignment(Qt.AlignCenter)
                    it.setData(Qt.UserRole, sid)
                    self.tablo.setItem(i, j, it)
                # Durum badge
                db = QLabel("  {}  ".format(durum or "-"))
                db.setAlignment(Qt.AlignCenter)
                db.setMinimumWidth(110)
                db.setFixedHeight(26)
                db.setStyleSheet(
                    "color:{fc};background:{bg};font-weight:bold;font-size:12px;"
                    "border-radius:6px;border:1px solid {fc};".format(fc=fc, bg=bg))
                self.tablo.setCellWidget(i, 4, db)
            self._filtrele()
        except Exception as e:
            print("Siparis yenile hatasi:", e)

    def _filtrele(self):
        txt   = self.txt_ara.text().lower()
        durum = self.cmb_durum.currentText()
        for r in range(self.tablo.rowCount()):
            sno = (self.tablo.item(r, 0).text() if self.tablo.item(r, 0) else "").lower()
            mus = (self.tablo.item(r, 2).text() if self.tablo.item(r, 2) else "").lower()
            dw  = self.tablo.cellWidget(r, 4)
            dur = ""
            if dw:
                lbs = dw.findChildren(QLabel)
                if lbs: dur = lbs[0].text()
            esle = (not txt or txt in sno or txt in mus) and (durum == "Tumu" or durum == dur)
            self.tablo.setRowHidden(r, not esle)

    def _yeni(self):
        dlg = YeniSiparisDialog(self.cursor, self.conn, self.kullanici_adi, self)
        if dlg.exec_() == QDialog.Accepted:
            self.yenile()
            # Yeni açılan sipariş için hemen izleme başlat
            if hasattr(dlg, 'sip_id') and METALIX_OK:
                self._detay_ve_izle(dlg.sip_id)

    def _detay_ve_izle(self, sip_id):
        dlg = SiparisDetayDialog(self.cursor, self.conn, sip_id, self.user_role, self)
        # İzlemeyi otomatik başlat
        QTimer.singleShot(500, dlg._izlemeyi_baslat)
        dlg.exec_(); self.yenile()

    def _detay(self, sid):
        if not sid: return
        dlg = SiparisDetayDialog(self.cursor, self.conn, sid, self.user_role, self)
        dlg.exec_(); self.yenile()
