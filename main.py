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

# ── Bulut / Lokal mod seçimi ──
import json as _json
def _bulut_mu():
    try:
        import os as _o, sys as _s
        yol = _o.path.join(
            _o.path.dirname(_s.executable) if getattr(_s,'frozen',False)
            else _o.path.dirname(_o.path.abspath(__file__)), "ayarlar.json")
        with open(yol,"r",encoding="utf-8") as f:
            return _json.load(f).get("bulut_modu", False)
    except: return False

BULUT_MODU = _bulut_mu()
if BULUT_MODU:
    from database_bulut import baglanti_kur, izin_yukle, izin_var, _izin_varsayilan_yukle
    print("[main] BULUT MODU aktif")
else:
    from database import baglanti_kur, izin_yukle, izin_var, _izin_varsayilan_yukle
    print("[main] LOKAL MODU aktif")

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
        # Izinleri yukle (yonetici her seyi gorebilir)
        if user_role == "yonetici":
            self.izinler = {m: (True, True) for m in
                ["ozet","stok","talepler","siparisler","uretim",
                 "sevkiyat","muhasebe","satinalma","cariler","analiz","piyasa"]}
        else:
            _izin_varsayilan_yukle(self.cursor)
            self.conn.commit()
            self.izinler = izin_yukle(self.cursor, kullanici_adi)
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        import updater as _u; _surum = getattr(_u, 'SURUM', '1.0.0')
        self.setWindowTitle('ARSAC METAL ERP v{} - [{}]'.format(_surum, 'YÖNETİCİ' if self.user_role == 'yonetici' else 'PERSONEL'))
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

        # --- ÜST PANEL (2 satır) ---
        self.nav_panel = QFrame()
        self.nav_panel.setObjectName("NavPanel")
        self.nav_panel.setFixedHeight(75)
        nav_main = QVBoxLayout(self.nav_panel)
        nav_main.setContentsMargins(20, 0, 20, 0)
        nav_main.setSpacing(0)

        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(6)
        nav_main.addLayout(nav_layout)

        # Logo
        self.logo_label = QLabel()
        if os.path.exists("logo.jpg"):
            pix = QPixmap("logo.jpg")
            self.logo_label.setPixmap(pix.scaled(220, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.logo_label.setText("ARSAC METAL")
            self.logo_label.setStyleSheet("font-size:18px;font-weight:900;color:#c0392b;")
        nav_layout.addWidget(self.logo_label)
        nav_layout.addSpacing(15)

        # Nav bar — izin bazlı dinamik
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

        # Kullanıcı adı
        lbl_kullanici = QLabel(f"👤 {self.ad_soyad or self.kullanici_adi}")
        lbl_kullanici.setStyleSheet("font-size:12px;color:#7f8c8d;font-weight:bold;background:transparent;")
        nav_layout.addWidget(lbl_kullanici)
        nav_layout.addSpacing(8)

        # Arama kutusu
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

        # ⚙️ Admin açılır menüsü
        self.btn_admin_menu = QPushButton("⚙️ YÖNETİCİ  ▾" if self.user_role == "yonetici" else "⚙️ AYARLAR")
        self.btn_admin_menu.setFixedHeight(40)
        self.btn_admin_menu.setStyleSheet("""
            QPushButton {
                background: #2c3e50; color: white;
                border-radius: 6px; padding: 6px 16px;
                font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background: #34495e; }
            QPushButton::menu-indicator { width: 0; }
        """)

        admin_menu = QMenu(self.btn_admin_menu)
        admin_menu.setStyleSheet("""
            QMenu {
                background: white; border: 1px solid #dcdde1;
                border-radius: 8px; padding: 6px;
                font-size: 13px; font-family: 'Segoe UI';
            }
            QMenu::item {
                padding: 10px 20px; border-radius: 4px; color: #2c3e50;
            }
            QMenu::item:selected { background: #f4f6f9; color: #c0392b; }
            QMenu::separator { height: 1px; background: #dcdde1; margin: 4px 8px; }
        """)

        if self.user_role == "yonetici":
            act_kullanici = admin_menu.addAction("👥  Kullanıcı Yönetimi")
            act_log       = admin_menu.addAction("📋  İşlem Geçmişi (Log)")
            admin_menu.addSeparator()
            act_kullanici.triggered.connect(self._kullanici_yonetimi_ac)
            act_log.triggered.connect(self._log_ac)

        act_ayarlar = admin_menu.addAction("⚙️  Program Ayarları")
        act_ayarlar.triggered.connect(self._ayarlar_ac)
        if METALIX_VAR:
            act_metalix = admin_menu.addAction("🏭  Metalix Ayarları")
            act_metalix.triggered.connect(self._metalix_ayar_ac)

        admin_menu.addSeparator()
        # Versiyon bilgisi
        try:
            import updater as _u2; _v = getattr(_u2, "SURUM", "1.0.0")
        except:
            _v = "1.0.0"
        act_guncelle = admin_menu.addAction("🔄  Güncelleme Kontrol Et  (v{})".format(_v))
        act_guncelle.triggered.connect(self._guncelleme_kontrol)

        self.btn_admin_menu.setMenu(admin_menu)
        nav_layout.addWidget(self.btn_admin_menu)

        self.main_layout.addWidget(self.nav_panel)

        # Ticker bandı
        self.ticker = TickerBand()
        self.main_layout.addWidget(self.ticker)

        # --- SAYFALAR (rol bazlı dinamik index) ---
        self.pages = QStackedWidget()
        self.sayfa_index = {}
        _idx = [0]

        def _ekle(sayfa, anahtar):
            self.pages.addWidget(sayfa)
            self.sayfa_index[anahtar] = _idx[0]
            _idx[0] += 1

        IZ = self.izinler  # kisaltma

        # Dashboard — herkes gorur
        self.s_dash = DashboardSayfasi(self.cursor, self.tazele)
        _ekle(self.s_dash, "dash")

        if izin_var(IZ, "stok"):
            self.s_stok = StokListeSayfasi(self.cursor, self.conn, self.user_role)
            _ekle(self.s_stok, "stok")

        if izin_var(IZ, "talepler"):
            self.s_talep = HammaddeSayfasi(self.cursor, self.conn, self.tazele, self.user_role)
            _ekle(self.s_talep, "talep")

        if izin_var(IZ, "siparisler"):
            self.s_siparis = SiparisSayfasi(self.cursor, self.conn, self.user_role, self.kullanici_adi)
            _ekle(self.s_siparis, "siparis")

        if izin_var(IZ, "uretim"):
            # Goruntule ama duzenleyemez — read-only mod
            _rol = self.user_role if izin_var(IZ, "uretim", "duzenle") else "readonly"
            self.s_uretim = UretimSayfasi(self.cursor, self.conn, _rol)
            _ekle(self.s_uretim, "uretim")

        if izin_var(IZ, "sevkiyat"):
            _rol = self.user_role if izin_var(IZ, "sevkiyat", "duzenle") else "readonly"
            self.s_sevkiyat = SevkiyatSayfasi(self.cursor, self.conn, _rol)
            _ekle(self.s_sevkiyat, "sevkiyat")

        if izin_var(IZ, "muhasebe"):
            _rol = self.user_role if izin_var(IZ, "muhasebe", "duzenle") else "readonly"
            self.s_muhasebe = MuhasebeSayfasi(self.cursor, self.conn, _rol)
            _ekle(self.s_muhasebe, "muhasebe")

        if izin_var(IZ, "satinalma"):
            self.s_satin = SatinalmaSayfasi(self.cursor, self.conn, self.tazele, self.user_role)
            _ekle(self.s_satin, "satinalma")

        if izin_var(IZ, "cariler"):
            self.s_cari = TedarikciSayfasi(self.cursor, self.conn, self.user_role)
            _ekle(self.s_cari, "cari")

        if izin_var(IZ, "analiz"):
            self.s_analiz = AnalizSayfasi(self.cursor)
            _ekle(self.s_analiz, "analiz")

        if izin_var(IZ, "piyasa"):
            self.s_piyasa = PiyasaSayfasi(self.cursor, self.conn)
            _ekle(self.s_piyasa, "piyasa")

        self.main_layout.addWidget(self.pages)

        # --- BAĞLANTILAR ---
        def _git(anahtar, extra=None):
            if anahtar in self.sayfa_index:
                self.pages.setCurrentIndex(self.sayfa_index[anahtar])
                if extra: extra()

        # Buton bağlantıları — sadece var olanları bağla
        self.btn_dash.clicked.connect(lambda: _git("dash"))
        for attr, anahtar, extra in [
            ("btn_stok",     "stok",      None),
            ("btn_talep",    "talep",     None),
            ("btn_siparis",  "siparis",   None),
            ("btn_uretim",   "uretim",    None),
            ("btn_sevkiyat", "sevkiyat",  None),
            ("btn_muhasebe", "muhasebe",  None),
            ("btn_satin",    "satinalma", None),
            ("btn_cari",     "cari",      None),
            ("btn_analiz",   "analiz",    lambda: self.s_analiz.yenile() if hasattr(self,"s_analiz") else None),
            ("btn_piyasa",   "piyasa",    None),
        ]:
            if hasattr(self, attr):
                if extra:
                    getattr(self, attr).clicked.connect(lambda _, k=anahtar, e=extra: (_git(k), e()))
                else:
                    getattr(self, attr).clicked.connect(lambda _, k=anahtar: _git(k))

        self.tazele()

    def _arama_tetikle(self):
        self._arama_yap(self.arama_kutusu.text())

    def _arama_yap(self, metin):
        metin = metin.strip()
        if len(metin) < 3:
            return
        try:
            sonuclar = []

            # Stok ara
            self.cursor.execute("""
                SELECT stok_kodu, malzeme, en, boy, kalinlik, kg, son_firma
                FROM stok
                WHERE stok_kodu LIKE ? OR malzeme LIKE ? OR son_firma LIKE ?
                LIMIT 10
            """, (f"%{metin}%", f"%{metin}%", f"%{metin}%"))
            for row in self.cursor.fetchall():
                sonuclar.append({
                    "tip": "📦 Stok",
                    "baslik": f"{row[0]} — {row[1]}",
                    "detay": f"{row[2]}x{row[3]}x{row[4]} mm | {float(row[5] or 0):,.1f} KG | {row[6] or '-'}",
                    "sayfa": 1
                })

            # Tedarikçi ara
            self.cursor.execute("""
                SELECT firma_adi, telefon, email
                FROM tedarikciler
                WHERE firma_adi LIKE ? OR vergi_no LIKE ? OR telefon LIKE ?
                LIMIT 5
            """, (f"%{metin}%", f"%{metin}%", f"%{metin}%"))
            for row in self.cursor.fetchall():
                sonuclar.append({
                    "tip": "🏢 Cari",
                    "baslik": row[0],
                    "detay": f"{row[1] or '-'} | {row[2] or '-'}",
                    "sayfa": 4
                })

            # Finans ara
            self.cursor.execute("""
                SELECT firma, malzeme, toplam_tutar, vade_tarihi, odendi
                FROM satinalma_kayitlari
                WHERE firma LIKE ? OR malzeme LIKE ?
                LIMIT 5
            """, (f"%{metin}%", f"%{metin}%"))
            for row in self.cursor.fetchall():
                durum = "✅ Ödendi" if row[4] else "⏳ Bekliyor"
                sonuclar.append({
                    "tip": "💳 Finans",
                    "baslik": f"{row[0]} — {row[1]}",
                    "detay": f"{float(row[2] or 0):,.0f} TL | Vade: {row[3] or '-'} | {durum}",
                    "sayfa": 5
                })

            # Talepler ara
            self.cursor.execute("""
                SELECT kalite, en, boy, kalinlik, kg, tarih
                FROM talepler
                WHERE kalite LIKE ?
                LIMIT 5
            """, (f"%{metin}%",))
            for row in self.cursor.fetchall():
                sonuclar.append({
                    "tip": "🏗️ Talep",
                    "baslik": f"{row[0]} — {row[1]}x{row[2]}x{row[3]} mm",
                    "detay": f"{float(row[4] or 0):,.1f} KG | {row[5] or '-'}",
                    "sayfa": 2
                })

            if not sonuclar:
                return

            self._arama_popup(metin, sonuclar)
        except Exception as e:
            print(f"Arama hatası: {e}")

    def _arama_popup(self, metin, sonuclar):
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Arama Sonuclari: {metin}")
        dlg.setMinimumWidth(620)
        dlg.setMinimumHeight(400)
        dlg.setStyleSheet("""
            QDialog { background: #f4f6f9; font-family: 'Segoe UI'; }
            QListWidget { background: white; border: 1px solid #dcdde1;
                          border-radius: 8px; font-size: 13px; }
            QListWidget::item { padding: 10px 14px; border-bottom: 1px solid #f0f0f0; }
            QListWidget::item:selected { background: #c0392b; color: white; border-radius: 4px; }
            QListWidget::item:hover { background: #fde8e8; }
            QLabel { font-size: 13px; color: #2c3e50; }
        """)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(15, 15, 15, 15)
        lay.setSpacing(10)

        ust = QHBoxLayout()
        lbl = QLabel(f"<b>{len(sonuclar)}</b> sonuç bulundu")
        lbl.setStyleSheet("font-size: 14px; color: #2c3e50;")
        ust.addWidget(lbl)
        ust.addStretch()
        btn_kapat = QPushButton("✕ Kapat")
        btn_kapat.setStyleSheet("background: #dcdde1; color: #2c3e50; border-radius: 6px; padding: 6px 14px; font-size: 12px;")
        btn_kapat.clicked.connect(dlg.accept)
        ust.addWidget(btn_kapat)
        lay.addLayout(ust)

        liste = QListWidget()
        for s in sonuclar:
            item = QListWidgetItem(f"{s['tip']}   {s['baslik']}\n         {s['detay']}")
            item.setData(Qt.UserRole, s['sayfa'])
            liste.addItem(item)

        def git(item):
            sayfa = item.data(Qt.UserRole)
            if self.user_role != "yonetici" and sayfa > 4:
                return
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
        """Alt satır — ana navigasyon butonları."""
        btn = QPushButton(text)
        btn.setObjectName("NavButton")
        btn.setFixedHeight(36)
        btn.setStyleSheet("QPushButton { background:white;color:#2c3e50;border:1px solid #dcdde1;border-radius:4px;font-weight:bold;font-size:12px;padding:4px 10px; }")
        return btn

    def tazele(self):
        try:
            # Sadece aktif sayfayı yenile - performans optimizasyonu
            aktif = self.pages.currentIndex()
            self.s_dash.yenile()
            if hasattr(self, "s_stok") and aktif == self.sayfa_index.get("stok", -1):
                self.s_stok.yenile()
            if hasattr(self, "s_uretim") and aktif == self.sayfa_index.get("uretim", -1):
                self.s_uretim.yenile()
            if hasattr(self, "s_siparis") and aktif == self.sayfa_index.get("siparis", -1):
                self.s_siparis.yenile()
            if self.user_role == "yonetici":
                self.s_satin.tablo_yenile()
                self.s_cari.yenile()
        except:
            pass


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Global palette — yazı rengi tüm programda zorla düzelt
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

    # DB yolu kontrolü — sadece lokal modda
    import os as _os
    if BULUT_MODU:
        from database_bulut import ayarlari_oku
    else:
        from database import db_yolu_al, db_yolu_kaydet, ayarlari_oku

    ayarlar = ayarlari_oku()
    db_yolu = ayarlar.get("db_yolu", "")
    db_hazir = BULUT_MODU or (db_yolu and _os.path.exists(_os.path.dirname(db_yolu) if _os.path.dirname(db_yolu) else "."))

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
        txt_yol.setStyleSheet("border:1.5px solid #dcdde1;border-radius:7px;padding:5px 10px;"
                               "font-size:13px;background:white;color:#2c3e50;")

        # Varsayılan yolu öner
        if getattr(sys, 'frozen', False):
            _varsayilan = _os.path.join(_os.path.dirname(sys.executable), "arsac_metal.db")
        else:
            _varsayilan = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "arsac_metal.db")
        txt_yol.setText(_varsayilan)

        btn_sec = QPushButton("Gozat...")
        btn_sec.setFixedHeight(36)
        btn_sec.setStyleSheet("background:#2980b9;color:white;border-radius:7px;"
                               "padding:5px 14px;font-weight:bold;border:none;")
        def _gozat():
            yol, _ = QFD.getSaveFileName(dlg, "Veritabani Dosyasi",
                                          txt_yol.text(), "SQLite DB (*.db)")
            if yol: txt_yol.setText(yol)
        btn_sec.clicked.connect(_gozat)
        yol_lay.addWidget(txt_yol); yol_lay.addWidget(btn_sec)
        lay.addLayout(yol_lay)

        btn_lay = QHBoxLayout(); btn_lay.addStretch()
        btn_tamam = QPushButton("Baslat")
        btn_tamam.setFixedHeight(40)
        btn_tamam.setStyleSheet("background:#c0392b;color:white;border-radius:8px;"
                                 "padding:8px 24px;font-weight:bold;font-size:14px;border:none;")
        btn_tamam.clicked.connect(dlg.accept)
        btn_lay.addWidget(btn_tamam)
        lay.addLayout(btn_lay)

        dlg.exec_()
        secilen_yol = txt_yol.text().strip()
        if secilen_yol:
            db_yolu_kaydet(secilen_yol)

    # ── Güncelleme kontrolü (arka planda, sessiz) ──
    try:
        from updater import guncelleme_kontrol
        _guncelleme_timer = QTimer()
        _guncelleme_timer.setSingleShot(True)
        _guncelleme_timer.timeout.connect(lambda: guncelleme_kontrol(parent=None, sessiz=True))
        _guncelleme_timer.start(1800000)
    except Exception as _ge:
        print("[Güncelleme] Modül yüklenemedi:", _ge)

    _conn, _cursor = baglanti_kur()
    if not BULUT_MODU:
        varsayilan_admin_olustur(_cursor, _conn)

    giris = GirisEkrani(_cursor, _conn)
    if giris.exec_() != QDialog.Accepted or not giris.sonuc:
        sys.exit(0)

    rol, kullanici_adi, ad_soyad = giris.sonuc
    kullanici_ayarla(kullanici_adi)
    window = ArsacMetalApp(user_role=rol, kullanici_adi=kullanici_adi, ad_soyad=ad_soyad)
    window.show()

    # Açılışta kritik stok kontrolü
    QTimer.singleShot(800, window.s_dash.kritik_uyari_goster)

    # Açılışta günlük rapor
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