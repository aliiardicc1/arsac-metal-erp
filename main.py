import sys, os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap

SURUM = "1.0.0"
UPDATER_VAR = False
try:
    import updater as _upd
    guncelleme_kontrol = _upd.guncelleme_kontrol
    SURUM = _upd.SURUM
    UPDATER_VAR = True
except Exception:
    def guncelleme_kontrol(parent=None, sessiz=True): pass

if getattr(sys, 'frozen', False):
    CALISMA_DIZIN = os.path.dirname(sys.executable)
else:
    CALISMA_DIZIN = os.path.dirname(os.path.abspath(__file__))
os.chdir(CALISMA_DIZIN)

# ═══════════════════════════════════════════════════════════════
#  BULUT / LOKAL MOD SEÇİMİ
# ═══════════════════════════════════════════════════════════════
def _ayarlar_oku():
    try:
        import json
        yol = os.path.join(CALISMA_DIZIN, "ayarlar.json")
        with open(yol, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

_ayarlar = _ayarlar_oku()
BULUT_MODU = _ayarlar.get("bulut_modu", False)

if BULUT_MODU:
    from database_bulut import (baglanti_kur, izin_yukle, izin_var,
                                 _izin_varsayilan_yukle, giris_yap,
                                 db_yolu_al, ayarlari_oku)
    print("[main] BULUT MODU aktif — API:", _ayarlar.get("api_url", "http://213.159.6.166:8000"))
else:
    from database import (baglanti_kur, izin_yukle, izin_var,
                           _izin_varsayilan_yukle, db_yolu_al,
                           db_yolu_kaydet, ayarlari_oku)
    print("[main] LOKAL MODU aktif — SQLite")

# Modüller
from gunluk_rapor import gunluk_rapor_olustur
from hammadde import HammaddeSayfasi
from satinalma import SatinalmaSayfasi
from stok_liste import StokListeSayfasi
from cariler import TedarikciSayfasi
from dashboard import DashboardSayfasi
from finans import FinansSayfasi
from analiz import AnalizSayfasi
from ayarlar import AyarlarDialog, ayar_al
from log import kullanici_ayarla, LogGecmisiDialog
from kullanici import GirisEkrani, KullaniciYonetimiDialog, varsayilan_admin_olustur
from piyasa import PiyasaSayfasi, TickerBand
from uretim import UretimSayfasi
try:
    from metalix import MetalixAyarDialog
    METALIX_VAR = True
except:
    METALIX_VAR = False
from siparis import SiparisSayfasi
from sevkiyat import SevkiyatSayfasi
from muhasebe import MuhasebeSayfasi

class ArsacMetalApp(QWidget):
    def __init__(self, user_role="personel", kullanici_adi="", ad_soyad=""):
        super().__init__()
        self.user_role     = user_role
        self.kullanici_adi = kullanici_adi
        self.ad_soyad      = ad_soyad
        self.conn, self.cursor = baglanti_kur()
        if user_role == "yonetici":
            self.izinler = {m: (True, True) for m in
                ["ozet","stok","talepler","siparisler","uretim",
                 "sevkiyat","muhasebe","satinalma","cariler","analiz","piyasa"]}
        else:
            _izin_varsayilan_yukle(self.cursor)
            if not BULUT_MODU:
                self.conn.commit()
            self.izinler = izin_yukle(self.cursor, kullanici_adi)
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        import updater as _u; _surum = getattr(_u, 'SURUM', '1.0.0')
        mod_etiket = '☁ BULUT' if BULUT_MODU else '💾 LOKAL'
        self.setWindowTitle('ARSAC METAL ERP v{} - [{}] {}'.format(
            _surum, 'YÖNETİCİ' if self.user_role == 'yonetici' else 'PERSONEL', mod_etiket))
        self.setGeometry(50, 50, 1500, 900)

        self.setStyleSheet("""
            QWidget { 
                background-color: #ebedef; 
                font-family: 'Segoe UI', Arial; 
            }
            #NavPanel { 
                background-color: white; 
                border-bottom: 5px solid #c0392b; 
            }
            QLineEdit, QComboBox {
                border: 2px solid #bdc3c7; 
                border-radius: 4px;
                padding: 12px;
                background-color: #ffffff;
                font-size: 14px;
                color: #2c3e50;
            }
            QLineEdit:focus { border: 2px solid #c0392b; }
            QLabel { 
                font-size: 18px; 
                font-weight: bold; 
                color: #2c3e50; 
            }
            #NavButton {
                background-color: white;
                color: #2c3e50;
                border: 1px solid #dcdde1;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton {
                background-color: #c0392b; 
                color: white;
                border-radius: 4px;
                padding: 12px;
                font-weight: bold;
                font-size: 15px;
            }
            QPushButton:hover { background-color: #a93226; }
        """)

        self.nav_panel = QFrame()
        self.nav_panel.setObjectName("NavPanel")
        self.nav_panel.setFixedHeight(75)
        nav_main = QVBoxLayout(self.nav_panel)
        nav_main.setContentsMargins(20, 0, 20, 0)
        nav_main.setSpacing(0)

        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(6)
        nav_main.addLayout(nav_layout)

        self.logo_label = QLabel()
        if os.path.exists("logo.jpg"):
            pix = QPixmap("logo.jpg")
            self.logo_label.setPixmap(pix.scaled(220, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.logo_label.setText("ARSAC METAL")
            self.logo_label.setStyleSheet("font-size:18px;font-weight:900;color:#c0392b;")
        nav_layout.addWidget(self.logo_label)
        nav_layout.addSpacing(15)

        IZ = self.izinler

        def _nav(attr, etiket, renk=None):
            btn = self.create_nav_btn(etiket)
            if renk:
                btn.setStyleSheet(
                    "QPushButton {{ background:{r};color:white;border:none;"
                    "border-radius:4px;font-weight:bold;font-size:12px;padding:4px 10px;}}".format(r=renk))
            setattr(self, attr, btn)
            nav_layout.addWidget(btn)

        _nav("btn_dash",     u"📊 OZET")

        if izin_var(IZ, "stok"):
            _nav("btn_stok",    u"📦 STOK")
        if izin_var(IZ, "talepler"):
            _nav("btn_talep",   u"🏗 TALEPLER")
        if izin_var(IZ, "siparisler"):
            _nav("btn_siparis", u"🛒 SIPARIS", "#e67e22")
        if izin_var(IZ, "uretim"):
            _nav("btn_uretim",  u"🏭 URETIM", "#8e44ad")
        if izin_var(IZ, "sevkiyat"):
            _nav("btn_sevkiyat",u"🚚 SEVKIYAT", "#e67e22")
        if izin_var(IZ, "muhasebe"):
            _nav("btn_muhasebe",u"💼 MUHASEBE", "#2c3e50")
        if izin_var(IZ, "satinalma"):
            _nav("btn_satin",   u"💰 SATINALMA")
        if izin_var(IZ, "cariler"):
            _nav("btn_cari",    u"🏢 CARILER")
        if izin_var(IZ, "analiz"):
            _nav("btn_analiz",  u"📈 ANALIZ")
        if izin_var(IZ, "piyasa"):
            _nav("btn_piyasa",  u"💹 PIYASA", "#27ae60")

        nav_layout.addStretch()

        lbl_kullanici = QLabel(f"👤 {self.ad_soyad or self.kullanici_adi}")
        lbl_kullanici.setStyleSheet("font-size:12px;color:#7f8c8d;font-weight:bold;background:transparent;")
        nav_layout.addWidget(lbl_kullanici)
        nav_layout.addSpacing(8)

        self.arama_kutusu = QLineEdit()
        self.arama_kutusu.setPlaceholderText("🔍  Ara...")
        self.arama_kutusu.setFixedWidth(220)
        self.arama_kutusu.setFixedHeight(36)
        self.arama_kutusu.setStyleSheet("""
            QLineEdit {
                border: 2px solid #dcdde1; border-radius: 18px;
                padding: 6px 14px; background: #f4f6f9;
                font-size: 12px; color: #2c3e50;
            }
            QLineEdit:focus { border: 2px solid #c0392b; background: white; }
        """)
        self.arama_timer = QTimer()
        self.arama_timer.setSingleShot(True)
        self.arama_timer.timeout.connect(self._arama_tetikle)
        self.arama_kutusu.textChanged.connect(lambda: self.arama_timer.start(600))
        self.arama_kutusu.returnPressed.connect(self._arama_tetikle)
        nav_layout.addWidget(self.arama_kutusu)
        nav_layout.addSpacing(8)

        self.btn_admin_menu = QPushButton("⚙️ YÖNETİCİ  ▾" if self.user_role == "yonetici" else "⚙️ AYARLAR")
        self.btn_admin_menu.setFixedHeight(40)
        self.btn_admin_menu.setStyleSheet("""
            QPushButton {
                background: #2c3e50; color: white;
                border-radius: 6px; padding: 6px 16px;
                font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background: #1a252f; }
        """)
        self.btn_admin_menu.clicked.connect(self._admin_menu_ac)
        nav_layout.addWidget(self.btn_admin_menu)

        self.main_layout.addWidget(self.nav_panel)

        self.pages = QStackedWidget()
        self.main_layout.addWidget(self.pages)

        self.s_dash    = DashboardSayfasi(self.cursor, self.conn)
        self.s_stok    = StokListeSayfasi(self.cursor, self.conn)
        self.s_hammadde= HammaddeSayfasi(self.cursor, self.conn)
        self.s_siparis = SiparisSayfasi(self.cursor, self.conn)
        self.s_uretim  = UretimSayfasi(self.cursor, self.conn)
        self.s_sevkiyat= SevkiyatSayfasi(self.cursor, self.conn)
        self.s_muhasebe= MuhasebeSayfasi(self.cursor, self.conn)
        self.s_satin   = SatinalmaSayfasi(self.cursor, self.conn)
        self.s_cari    = TedarikciSayfasi(self.cursor, self.conn)
        self.s_analiz  = AnalizSayfasi(self.cursor, self.conn)
        self.s_piyasa  = PiyasaSayfasi()
        self.s_finans  = FinansSayfasi(self.cursor, self.conn)

        for s in [self.s_dash, self.s_stok, self.s_hammadde, self.s_siparis,
                  self.s_uretim, self.s_sevkiyat, self.s_muhasebe,
                  self.s_satin, self.s_cari, self.s_analiz, self.s_piyasa, self.s_finans]:
            self.pages.addWidget(s)

        self.btn_dash.clicked.connect(lambda: self.pages.setCurrentIndex(0))
        if hasattr(self, 'btn_stok'):
            self.btn_stok.clicked.connect(lambda: self.pages.setCurrentIndex(1))
        if hasattr(self, 'btn_talep'):
            self.btn_talep.clicked.connect(lambda: self.pages.setCurrentIndex(2))
        if hasattr(self, 'btn_siparis'):
            self.btn_siparis.clicked.connect(lambda: self.pages.setCurrentIndex(3))
        if hasattr(self, 'btn_uretim'):
            self.btn_uretim.clicked.connect(lambda: self.pages.setCurrentIndex(4))
        if hasattr(self, 'btn_sevkiyat'):
            self.btn_sevkiyat.clicked.connect(lambda: self.pages.setCurrentIndex(5))
        if hasattr(self, 'btn_muhasebe'):
            self.btn_muhasebe.clicked.connect(lambda: self.pages.setCurrentIndex(6))
        if hasattr(self, 'btn_satin'):
            self.btn_satin.clicked.connect(lambda: self.pages.setCurrentIndex(7))
        if hasattr(self, 'btn_cari'):
            self.btn_cari.clicked.connect(lambda: self.pages.setCurrentIndex(8))
        if hasattr(self, 'btn_analiz'):
            self.btn_analiz.clicked.connect(lambda: self.pages.setCurrentIndex(9))
        if hasattr(self, 'btn_piyasa'):
            self.btn_piyasa.clicked.connect(lambda: self.pages.setCurrentIndex(10))

        # Ticker band
        try:
            self.ticker = TickerBand()
            self.main_layout.addWidget(self.ticker)
        except:
            pass

    def _admin_menu_ac(self):
        menu = QMenu(self)
        if self.user_role == "yonetici":
            menu.addAction("👥 Kullanıcı Yönetimi", self._kullanici_yonetimi_ac)
            menu.addAction("📋 Log Geçmişi",        self._log_ac)
            menu.addSeparator()
        menu.addAction("⚙️ Ayarlar",               self._ayarlar_ac)
        menu.addAction("🔄 Güncelleme Kontrol",     self._guncelleme_kontrol)
        if METALIX_VAR:
            menu.addAction("🔩 Metalix Ayarları",   self._metalix_ayar_ac)
        menu.addSeparator()
        menu.addAction("🚪 Çıkış",                  self.close)
        menu.exec_(self.btn_admin_menu.mapToGlobal(
            self.btn_admin_menu.rect().bottomLeft()))

    def _arama_tetikle(self):
        metin = self.arama_kutusu.text().strip()
        if len(metin) < 2:
            return
        sonuclar = []
        try:
            self.cursor.execute(
                "SELECT id, sip_no, musteri_adi FROM siparisler WHERE musteri_adi LIKE ? OR sip_no LIKE ?",
                (f"%{metin}%", f"%{metin}%"))
            for r in self.cursor.fetchall():
                sonuclar.append({"tip": "🛒 Sipariş", "baslik": r[1] if isinstance(r, tuple) else r.get("sip_no",""),
                                  "detay": r[2] if isinstance(r, tuple) else r.get("musteri_adi",""), "sayfa": 3})
        except:
            pass

        dlg = QDialog(self)
        dlg.setWindowTitle(f'Arama: "{metin}"')
        dlg.setMinimumSize(500, 350)
        lay = QVBoxLayout(dlg)
        ust = QHBoxLayout()
        ust.addWidget(QLabel(f"🔍  \"{metin}\" için {len(sonuclar)} sonuç"))
        ust.addStretch()
        lay.addLayout(ust)

        liste = QListWidget()
        for s in sonuclar:
            item = QListWidgetItem(f"{s['tip']}   {s['baslik']}\n         {s['detay']}")
            item.setData(Qt.UserRole, s['sayfa'])
            liste.addItem(item)

        def git(item):
            sayfa = item.data(Qt.UserRole)
            self.pages.setCurrentIndex(sayfa)
            self.arama_kutusu.clear()
            dlg.accept()

        liste.itemDoubleClicked.connect(git)
        lay.addWidget(liste)
        bilgi = QLabel("💡 Sonuca çift tıklayarak ilgili sayfaya gidin")
        bilgi.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        lay.addWidget(bilgi)
        dlg.exec_()

    def _kullanici_yonetimi_ac(self):
        dlg = KullaniciYonetimiDialog(self.cursor, self.conn, self)
        dlg.exec_()

    def _log_ac(self):
        dlg = LogGecmisiDialog(self.cursor, self)
        dlg.exec_()

    def _guncelleme_kontrol(self):
        try:
            from updater import guncelleme_kontrol
            guncelleme_kontrol(parent=self, sessiz=False)
        except Exception as e:
            QMessageBox.warning(self, "Güncelleme",
                "Güncelleme modülü yüklenemedi:\n{}".format(e))

    def _ayarlar_ac(self):
        dlg = AyarlarDialog(self)
        dlg.exec_()

    def _metalix_ayar_ac(self):
        if METALIX_VAR:
            dlg = MetalixAyarDialog(self)
            dlg.exec_()

    def create_nav_btn(self, text):
        btn = QPushButton(text)
        btn.setObjectName("NavButton")
        btn.setFixedHeight(36)
        btn.setStyleSheet("QPushButton { background:white;color:#2c3e50;border:1px solid #dcdde1;"
                          "border-radius:4px;font-weight:bold;font-size:12px;padding:4px 10px; }")
        return btn

    def tazele(self):
        try:
            self.s_dash.yenile()
            self.s_stok.yenile()
            self.s_uretim.yenile()
            self.s_siparis.yenile()
            if self.user_role == "yonetici":
                self.s_satin.tablo_yenile()
                self.s_cari.yenile()
        except:
            pass


if __name__ == '__main__':
    app = QApplication(sys.argv)

    from PyQt5.QtGui import QPalette, QColor as QC
    palette = app.palette()
    palette.setColor(QPalette.Text,           QC("#2c3e50"))
    palette.setColor(QPalette.WindowText,     QC("#2c3e50"))
    palette.setColor(QPalette.Base,           QC("#ffffff"))
    palette.setColor(QPalette.AlternateBase,  QC("#f4f6f9"))
    palette.setColor(QPalette.Window,         QC("#f4f6f9"))
    palette.setColor(QPalette.Button,         QC("#f4f6f9"))
    palette.setColor(QPalette.ButtonText,     QC("#2c3e50"))
    palette.setColor(QPalette.Highlight,      QC("#2980b9"))
    palette.setColor(QPalette.HighlightedText,QC("#ffffff"))
    palette.setColor(QPalette.PlaceholderText,QC("#95a5a6"))
    app.setPalette(palette)

    from styles import APP_QSS
    app.setStyleSheet(APP_QSS)

    # ── Mod seçimi — bulut modu aktifse DB yolu sorma ──
    if not BULUT_MODU:
        from database import db_yolu_al, db_yolu_kaydet, ayarlari_oku
        import os as _os
        ayarlar = ayarlari_oku()
        db_yolu = ayarlar.get("db_yolu", "")
        db_hazir = db_yolu and _os.path.exists(
            _os.path.dirname(db_yolu) if _os.path.dirname(db_yolu) else ".")

        if not db_hazir:
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QFileDialog as QFD
            dlg = QDialog()
            dlg.setWindowTitle("Arsac Metal ERP — Veritabani Kurulumu")
            dlg.setMinimumWidth(520)
            dlg.setStyleSheet("QDialog{background:#f4f6f9;} QLabel{color:#2c3e50;font-size:13px;}")
            lay = QVBoxLayout(dlg); lay.setSpacing(14); lay.setContentsMargins(24,20,24,20)

            lbl_baslik = QLabel("Veritabani Konumu Secin")
            lbl_baslik.setStyleSheet("font-size:16px;font-weight:bold;color:#c0392b;")
            lay.addWidget(lbl_baslik)

            lbl_info = QLabel(
                "Bu bilgisayarda mi yoksa ag uzerinde mi calisacak?\n\n"
                "• Tek bilgisayar: EXE'nin yanindaki arsac_metal.db kullanilir\n"
                "• Ag (ortak): Sunucudaki klasoru secin (\\\\SUNUCU\\ArsacDB\\)")
            lbl_info.setWordWrap(True)
            lbl_info.setStyleSheet(
                "background:#eaf4fb;border:1px solid #aed6f1;border-radius:8px;"
                "padding:12px;font-size:12px;color:#2c3e50;")
            lay.addWidget(lbl_info)

            yol_lay = QHBoxLayout()
            txt_yol = QLineEdit()
            txt_yol.setPlaceholderText("Veritabani dosya yolu...")
            txt_yol.setFixedHeight(36)
            if getattr(sys, 'frozen', False):
                _varsayilan = _os.path.join(_os.path.dirname(sys.executable), "arsac_metal.db")
            else:
                _varsayilan = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "arsac_metal.db")
            txt_yol.setText(_varsayilan)

            btn_sec = QPushButton("Gozat...")
            btn_sec.setFixedHeight(36)
            def _gozat():
                yol, _ = QFD.getSaveFileName(dlg, "Veritabani Dosyasi", txt_yol.text(), "SQLite DB (*.db)")
                if yol: txt_yol.setText(yol)
            btn_sec.clicked.connect(_gozat)
            yol_lay.addWidget(txt_yol); yol_lay.addWidget(btn_sec)
            lay.addLayout(yol_lay)

            btn_lay = QHBoxLayout(); btn_lay.addStretch()
            btn_tamam = QPushButton("Baslat")
            btn_tamam.setFixedHeight(40)
            btn_tamam.clicked.connect(dlg.accept)
            btn_lay.addWidget(btn_tamam)
            lay.addLayout(btn_lay)

            dlg.exec_()
            secilen_yol = txt_yol.text().strip()
            if secilen_yol:
                db_yolu_kaydet(secilen_yol)

    # ── Güncelleme kontrolü ──
    try:
        from updater import guncelleme_kontrol
        _guncelleme_timer = QTimer()
        _guncelleme_timer.setSingleShot(True)
        _guncelleme_timer.timeout.connect(lambda: guncelleme_kontrol(parent=None, sessiz=True))
        _guncelleme_timer.start(4000)
    except Exception as _ge:
        print("[Güncelleme] Modül yüklenemedi:", _ge)

    _conn, _cursor = baglanti_kur()

    if not BULUT_MODU:
        varsayilan_admin_olustur(_cursor, _conn)

    giris = GirisEkrani(_cursor, _conn)
    if giris.exec_() != QDialog.Accepted or not giris.sonuc:
        sys.exit(0)

    rol, kullanici_adi, ad_soyad = giris.sonuc

    # Bulut modunda token al
    if BULUT_MODU:
        try:
            from database_bulut import giris_yap
            giris_yap(kullanici_adi, giris._sifre)
        except Exception as e:
            print("[BulutDB] Token alınamadı:", e)

    kullanici_ayarla(kullanici_adi)
    window = ArsacMetalApp(user_role=rol, kullanici_adi=kullanici_adi, ad_soyad=ad_soyad)
    window.show()

    QTimer.singleShot(800, window.s_dash.kritik_uyari_goster)

    def rapor_olustur():
        try:
            bugun = __import__('datetime').datetime.now().strftime('%Y%m%d')
            dosya = f"Gunluk Raporlar/Rapor_{bugun}.pdf"
            if not os.path.exists(dosya):
                pdf_yolu, veri = gunluk_rapor_olustur(window.cursor)
                ozet  = "Günlük rapor hazırlandı!\n\n"
                ozet += f"📦 Bekleyen talep: {veri.get('bekleyen_talep', 0)}\n"
                ozet += f"🚨 Kritik stok: {veri.get('kritik_stok', 0)}\n"
                ozet += f"💳 Açık borç: {veri.get('toplam_borc', 0):,.0f} TL\n\n"
                ozet += f"📄 {pdf_yolu}"
                QMessageBox.information(None, "📊 Günlük Rapor", ozet)
                os.startfile(pdf_yolu)
        except Exception as e:
            print(f"Rapor hatası: {e}")

    QTimer.singleShot(1500, rapor_olustur)
    sys.exit(app.exec_())
