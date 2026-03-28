# -*- coding: utf-8 -*-
import sys
import os
os.environ["PYTHONIOENCODING"] = "utf-8"
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

import json as _json

def _bulut_mu():
    try:
        import os as _o, sys as _s
        yol = _o.path.join(
            _o.path.dirname(_s.executable) if getattr(_s, 'frozen', False)
            else _o.path.dirname(_o.path.abspath(__file__)), "ayarlar.json")
        with open(yol, "r", encoding="utf-8") as f:
            return _json.load(f).get("bulut_modu", False)
    except:
        return False

BULUT_MODU = _bulut_mu()

if BULUT_MODU:
    from database_bulut import baglanti_kur, izin_yukle, izin_var, _izin_varsayilan_yukle
    print("[main] BULUT MODU aktif")
else:
    from database import baglanti_kur, izin_yukle, izin_var, _izin_varsayilan_yukle
    print("[main] LOKAL MODU aktif")

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


# ── Sol Sidebar Buton ──────────────────────────────────────────
class SidebarBtn(QPushButton):
    def __init__(self, icon, text, parent=None):
        super().__init__(parent)
        self.setText(f"{icon}\n{text}")
        self.setFixedHeight(58)
        self.setMinimumWidth(140)
        self._aktif = False
        self._apply_style(False)

    def _apply_style(self, aktif):
        if aktif:
            self.setStyleSheet("""
                QPushButton {
                    background: #c0392b;
                    color: white;
                    border: none;
                    border-left: 4px solid #922b21;
                    border-radius: 0px;
                    font-weight: bold;
                    font-size: 11px;
                    text-align: center;
                    padding: 4px 8px;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #ecf0f1;
                    border: none;
                    border-left: 4px solid transparent;
                    border-radius: 0px;
                    font-weight: bold;
                    font-size: 11px;
                    text-align: center;
                    padding: 4px 8px;
                }
                QPushButton:hover {
                    background: rgba(255,255,255,0.1);
                    border-left: 4px solid #e74c3c;
                }
            """)

    def set_aktif(self, aktif):
        self._aktif = aktif
        self._apply_style(aktif)


# ── Grup Başlığı (Sipariş&Üretim gibi) ─────────────────────────
class SidebarGrupBtn(QPushButton):
    """Tıklanınca alt butonları göster/gizle"""
    def __init__(self, icon, text, parent=None):
        super().__init__(parent)
        self._acik = False
        self._ikon = icon
        self._metin = text
        self._guncelle_metin()
        self.setFixedHeight(48)
        self.setMinimumWidth(140)
        self.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.08);
                color: #bdc3c7;
                border: none;
                border-left: 4px solid transparent;
                border-radius: 0px;
                font-weight: bold;
                font-size: 11px;
                text-align: center;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.15);
                color: white;
            }
        """)

    def _guncelle_metin(self):
        ok = "▾" if self._acik else "▸"
        self.setText(f"{self._ikon} {self._metin}  {ok}")

    def toggle(self):
        self._acik = not self._acik
        self._guncelle_metin()
        return self._acik


# ── Ana Uygulama ───────────────────────────────────────────────
class ArsacMetalApp(QWidget):
    def __init__(self, user_role="personel", kullanici_adi="", ad_soyad=""):
        super().__init__()
        self.user_role = user_role
        self.kullanici_adi = kullanici_adi
        self.ad_soyad = ad_soyad
        self.conn, self.cursor = baglanti_kur()

        if user_role == "yonetici":
            self.izinler = {m: (True, True) for m in
                            ["ozet", "stok", "talepler", "siparisler", "uretim",
                             "sevkiyat", "muhasebe", "satinalma", "cariler", "analiz", "piyasa"]}
        else:
            _izin_varsayilan_yukle(self.cursor)
            self.conn.commit()
            self.izinler = izin_yukle(self.cursor, kullanici_adi)

        self._aktif_btn = None  # aktif sidebar butonu takibi
        self._grup_butonlari = {}  # grup adı → [alt_butonlar]
        self.init_ui()

    def init_ui(self):
        try:
            import updater as _u
            _surum = getattr(_u, 'SURUM', '1.0.0')
        except:
            _surum = '1.0.0'

        self.setWindowTitle('ARSAC METAL ERP v{} - [{}]'.format(
            _surum, 'YÖNETİCİ' if self.user_role == 'yonetici' else 'PERSONEL'))
        self.setGeometry(50, 50, 1500, 900)

        # Ana layout: dikey (üst bar + içerik)
        ana_layout = QVBoxLayout(self)
        ana_layout.setContentsMargins(0, 0, 0, 0)
        ana_layout.setSpacing(0)

        # ── ÜST BAR (ince) ────────────────────────────────────
        top_bar = QFrame()
        top_bar.setFixedHeight(52)
        top_bar.setStyleSheet("""
            QFrame {
                background: white;
                border-bottom: 3px solid #c0392b;
            }
        """)
        top_lay = QHBoxLayout(top_bar)
        top_lay.setContentsMargins(16, 0, 16, 0)
        top_lay.setSpacing(10)

        # Ticker bandı (USD/TRY vs)
        self.ticker = TickerBand()
        top_lay.addWidget(self.ticker, 1)

        top_lay.addStretch()

        # Kullanıcı adı
        lbl_kullanici = QLabel(f"👤 {self.ad_soyad or self.kullanici_adi}")
        lbl_kullanici.setStyleSheet("font-size:12px;color:#7f8c8d;font-weight:bold;")
        top_lay.addWidget(lbl_kullanici)

        # Arama kutusu
        self.arama_kutusu = QLineEdit()
        self.arama_kutusu.setPlaceholderText("🔍 Ara...")
        self.arama_kutusu.setFixedWidth(220)
        self.arama_kutusu.setFixedHeight(34)
        self.arama_kutusu.setStyleSheet("""
            QLineEdit {
                border: 2px solid #dcdde1; border-radius: 17px;
                padding: 4px 14px; background: #f4f6f9;
                font-size: 12px; color: #2c3e50;
            }
            QLineEdit:focus { border: 2px solid #c0392b; background: white; }
        """)
        self.arama_timer = QTimer()
        self.arama_timer.setSingleShot(True)
        self.arama_timer.timeout.connect(self._arama_tetikle)
        self.arama_kutusu.textChanged.connect(lambda: self.arama_timer.start(600))
        self.arama_kutusu.returnPressed.connect(self._arama_tetikle)
        top_lay.addWidget(self.arama_kutusu)

        # ⚙️ Admin menüsü
        self.btn_admin_menu = QPushButton(
            "⚙️ YÖNETİCİ ▾" if self.user_role == "yonetici" else "⚙️ AYARLAR")
        self.btn_admin_menu.setFixedHeight(36)
        self.btn_admin_menu.setStyleSheet("""
            QPushButton {
                background: #2c3e50; color: white;
                border-radius: 6px; padding: 6px 14px;
                font-weight: bold; font-size: 12px;
            }
            QPushButton:hover { background: #34495e; }
            QPushButton::menu-indicator { width: 0; }
        """)
        admin_menu = QMenu(self.btn_admin_menu)
        admin_menu.setStyleSheet("""
            QMenu {
                background: white; border: 1px solid #dcdde1;
                border-radius: 8px; padding: 6px; font-size: 13px;
            }
            QMenu::item { padding: 10px 20px; border-radius: 4px; color: #2c3e50; }
            QMenu::item:selected { background: #f4f6f9; color: #c0392b; }
            QMenu::separator { height: 1px; background: #dcdde1; margin: 4px 8px; }
        """)
        if self.user_role == "yonetici":
            act_kullanici = admin_menu.addAction("👥 Kullanıcı Yönetimi")
            act_log = admin_menu.addAction("📋 İşlem Geçmişi (Log)")
            admin_menu.addSeparator()
            act_kullanici.triggered.connect(self._kullanici_yonetimi_ac)
            act_log.triggered.connect(self._log_ac)

        act_ayarlar = admin_menu.addAction("⚙️ Program Ayarları")
        act_ayarlar.triggered.connect(self._ayarlar_ac)
        if METALIX_VAR:
            act_metalix = admin_menu.addAction("🏭 Metalix Ayarları")
            act_metalix.triggered.connect(self._metalix_ayar_ac)
        admin_menu.addSeparator()
        try:
            import updater as _u2
            _v = getattr(_u2, "SURUM", "1.0.0")
        except:
            _v = "1.0.0"
        act_guncelle = admin_menu.addAction("🔄 Güncelleme Kontrol Et (v{})".format(_v))
        act_guncelle.triggered.connect(self._guncelleme_kontrol)
        self.btn_admin_menu.setMenu(admin_menu)
        top_lay.addWidget(self.btn_admin_menu)

        ana_layout.addWidget(top_bar)

        # ── GÖVDE: Sol sidebar + Sağ içerik ───────────────────
        govde = QWidget()
        govde_lay = QHBoxLayout(govde)
        govde_lay.setContentsMargins(0, 0, 0, 0)
        govde_lay.setSpacing(0)

        # ── SOL SİDEBAR ───────────────────────────────────────
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(148)
        self.sidebar.setStyleSheet("""
            QFrame {
                background: #2c3e50;
                border-right: 1px solid #1a252f;
            }
        """)
        self.sidebar_lay = QVBoxLayout(self.sidebar)
        self.sidebar_lay.setContentsMargins(0, 0, 0, 0)
        self.sidebar_lay.setSpacing(0)

        # Logo alanı
        logo_frame = QFrame()
        logo_frame.setFixedHeight(70)
        logo_frame.setStyleSheet("background: #1a252f; border-bottom: 2px solid #c0392b;")
        logo_lay = QVBoxLayout(logo_frame)
        logo_lay.setContentsMargins(8, 8, 8, 8)

        if os.path.exists("logo.jpg"):
            lbl_logo = QLabel()
            pix = QPixmap("logo.jpg")
            lbl_logo.setPixmap(pix.scaled(130, 54, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            lbl_logo.setAlignment(Qt.AlignCenter)
            logo_lay.addWidget(lbl_logo)
        else:
            lbl_logo = QLabel("ARSAC\nMETAL")
            lbl_logo.setAlignment(Qt.AlignCenter)
            lbl_logo.setStyleSheet("font-size:14px;font-weight:900;color:#c0392b;background:transparent;")
            logo_lay.addWidget(lbl_logo)

        self.sidebar_lay.addWidget(logo_frame)

        # Sayfa indexleri
        self.pages = QStackedWidget()
        self.sayfa_index = {}
        _idx = [0]

        def _ekle(sayfa, anahtar):
            self.pages.addWidget(sayfa)
            self.sayfa_index[anahtar] = _idx[0]
            _idx[0] += 1

        IZ = self.izinler

        # ── SAYFALARI OLUŞTUR ──────────────────────────────────
        self.s_dash = DashboardSayfasi(self.cursor, self.tazele)
        _ekle(self.s_dash, "dash")

        if izin_var(IZ, "stok"):
            self.s_stok = StokListeSayfasi(self.cursor, self.conn, self.user_role)
            _ekle(self.s_stok, "stok")

        if izin_var(IZ, "talepler"):
            self.s_talep = HammaddeSayfasi(self.cursor, self.conn, self.tazele, self.user_role)
            _ekle(self.s_talep, "talep")

        if izin_var(IZ, "satinalma"):
            self.s_satin = SatinalmaSayfasi(self.cursor, self.conn, self.tazele, self.user_role)
            _ekle(self.s_satin, "satinalma")

        if izin_var(IZ, "siparisler"):
            self.s_siparis = SiparisSayfasi(self.cursor, self.conn, self.user_role, self.kullanici_adi, self.izinler)
            _ekle(self.s_siparis, "siparis")

        if izin_var(IZ, "uretim"):
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

        if izin_var(IZ, "cariler"):
            self.s_cari = TedarikciSayfasi(self.cursor, self.conn, self.user_role)
            _ekle(self.s_cari, "cari")

        if izin_var(IZ, "analiz"):
            self.s_analiz = AnalizSayfasi(self.cursor)
            _ekle(self.s_analiz, "analiz")

        if izin_var(IZ, "piyasa"):
            self.s_piyasa = PiyasaSayfasi(self.cursor, self.conn)
            _ekle(self.s_piyasa, "piyasa")

        # ── SİDEBAR BUTONLARINI EKLE ───────────────────────────
        def _sidebar_btn(icon, metin, anahtar, extra=None):
            """Tekil sidebar butonu ekle"""
            if anahtar not in self.sayfa_index:
                return None
            btn = SidebarBtn(icon, metin)
            btn.clicked.connect(lambda: self._sayfa_git(anahtar, btn, extra))
            self.sidebar_lay.addWidget(btn)
            return btn

        def _sidebar_grup(icon, grup_adi, alt_liste):
            """
            Birleşik grup butonu: tıklayınca alt butonlar açılır/kapanır
            alt_liste: [(icon, metin, anahtar), ...]
            """
            # Ana grup butonu
            grup_btn = SidebarGrupBtn(icon, grup_adi)

            # Alt butonları oluştur
            alt_butonlar = []
            alt_widget = QWidget()
            alt_lay = QVBoxLayout(alt_widget)
            alt_lay.setContentsMargins(0, 0, 0, 0)
            alt_lay.setSpacing(0)
            alt_widget.setVisible(False)
            alt_widget.setStyleSheet("background: #243342;")

            for a_icon, a_metin, a_anahtar in alt_liste:
                if a_anahtar not in self.sayfa_index:
                    continue
                alt_btn = SidebarBtn(a_icon, a_metin)
                alt_btn.setFixedHeight(50)
                alt_btn.setStyleSheet("""
                    QPushButton {
                        background: transparent;
                        color: #bdc3c7;
                        border: none;
                        border-left: 4px solid transparent;
                        font-weight: bold;
                        font-size: 10px;
                        text-align: center;
                        padding: 4px 8px;
                    }
                    QPushButton:hover {
                        background: rgba(255,255,255,0.1);
                        border-left: 4px solid #e74c3c;
                        color: white;
                    }
                """)
                alt_btn.clicked.connect(
                    lambda _, k=a_anahtar, b=alt_btn: self._sayfa_git(k, b))
                alt_lay.addWidget(alt_btn)
                alt_butonlar.append(alt_btn)

            def _toggle():
                acik = grup_btn.toggle()
                alt_widget.setVisible(acik)

            grup_btn.clicked.connect(_toggle)
            self.sidebar_lay.addWidget(grup_btn)
            self.sidebar_lay.addWidget(alt_widget)
            return grup_btn, alt_butonlar

        # Butonları sıraya ekle
        self.btn_dash = _sidebar_btn("📊", "ÖZET", "dash")

        if izin_var(IZ, "stok"):
            self.btn_stok = _sidebar_btn("📦", "STOK", "stok")

        # ── TALEP & SATINALMA grubu ──
        talep_satin_alts = []
        if izin_var(IZ, "talepler"):
            talep_satin_alts.append(("🏗", "TALEPLER", "talep"))
        if izin_var(IZ, "satinalma"):
            talep_satin_alts.append(("💰", "SATINALMA", "satinalma"))

        if len(talep_satin_alts) == 2:
            # Her ikisi de var → grup
            _sidebar_grup("📋", "TALEP & SATIN", talep_satin_alts)
        elif len(talep_satin_alts) == 1:
            # Sadece biri var → tekil buton
            ic, mt, ak = talep_satin_alts[0]
            _sidebar_btn(ic, mt, ak)

        # ── SİPARİŞ & ÜRETİM grubu ──
        siparis_uretim_alts = []
        if izin_var(IZ, "siparisler"):
            siparis_uretim_alts.append(("🛒", "SİPARİŞ", "siparis"))
        if izin_var(IZ, "uretim"):
            siparis_uretim_alts.append(("🏭", "ÜRETİM", "uretim"))

        if len(siparis_uretim_alts) == 2:
            _sidebar_grup("⚙️", "SİP & ÜRETİM", siparis_uretim_alts)
        elif len(siparis_uretim_alts) == 1:
            ic, mt, ak = siparis_uretim_alts[0]
            _sidebar_btn(ic, mt, ak)

        if izin_var(IZ, "sevkiyat"):
            _sidebar_btn("🚚", "SEVKİYAT", "sevkiyat")

        if izin_var(IZ, "muhasebe"):
            _sidebar_btn("💼", "MUHASEBE", "muhasebe")

        if izin_var(IZ, "cariler"):
            _sidebar_btn("🏢", "CARİLER", "cari")

        if izin_var(IZ, "analiz"):
            _sidebar_btn("📈", "ANALİZ", "analiz",
                         extra=lambda: self.s_analiz.yenile() if hasattr(self, "s_analiz") else None)

        if izin_var(IZ, "piyasa"):
            _sidebar_btn("💹", "PİYASA", "piyasa")

        self.sidebar_lay.addStretch()

        # Versiyon etiketi
        try:
            import updater as _u3
            _sv = getattr(_u3, "SURUM", "1.0.0")
        except:
            _sv = "1.0.0"
        lbl_ver = QLabel(f"v{_sv}")
        lbl_ver.setAlignment(Qt.AlignCenter)
        lbl_ver.setStyleSheet("color:#566573;font-size:10px;padding:6px;background:transparent;")
        self.sidebar_lay.addWidget(lbl_ver)

        govde_lay.addWidget(self.sidebar)
        govde_lay.addWidget(self.pages, 1)
        ana_layout.addWidget(govde, 1)

        # Başlangıçta özet sayfası aktif
        self.pages.setCurrentIndex(0)
        if self.btn_dash:
            self.btn_dash.set_aktif(True)
            self._aktif_btn = self.btn_dash

        self.tazele()

    def _sayfa_git(self, anahtar, btn=None, extra=None):
        if anahtar not in self.sayfa_index:
            return
        # Önceki aktif butonu pasif yap
        if self._aktif_btn and self._aktif_btn is not btn:
            self._aktif_btn.set_aktif(False)
        # Yeni butonu aktif yap
        if btn:
            btn.set_aktif(True)
            self._aktif_btn = btn
        self.pages.setCurrentIndex(self.sayfa_index[anahtar])
        if extra:
            extra()

    def _arama_tetikle(self):
        self._arama_yap(self.arama_kutusu.text())

    def _arama_yap(self, metin):
        metin = metin.strip()
        if len(metin) < 3:
            return
        try:
            sonuclar = []
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
                    "sayfa": self.sayfa_index.get("stok", 0)
                })
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
                    "sayfa": self.sayfa_index.get("cari", 0)
                })
            if not sonuclar:
                return
            self._arama_popup(metin, sonuclar)
        except Exception as e:
            print(f"Arama hatası: {e}")

    def _arama_popup(self, metin, sonuclar):
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Arama Sonuçları: {metin}")
        dlg.setMinimumWidth(620)
        dlg.setMinimumHeight(400)
        dlg.setStyleSheet("""
            QDialog { background: #f4f6f9; font-family: 'Segoe UI'; }
            QListWidget { background: white; border: 1px solid #dcdde1;
                border-radius: 8px; font-size: 13px; }
            QListWidget::item { padding: 10px 14px; border-bottom: 1px solid #f0f0f0; }
            QListWidget::item:selected { background: #c0392b; color: white; }
            QListWidget::item:hover { background: #fde8e8; }
        """)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(15, 15, 15, 15)
        lay.setSpacing(10)
        ust = QHBoxLayout()
        lbl = QLabel(f"<b>{len(sonuclar)}</b> sonuç bulundu")
        lbl.setStyleSheet("font-size:14px;color:#2c3e50;")
        ust.addWidget(lbl)
        ust.addStretch()
        btn_kapat = QPushButton("✕ Kapat")
        btn_kapat.setStyleSheet("background:#dcdde1;color:#2c3e50;border-radius:6px;padding:6px 14px;font-size:12px;")
        btn_kapat.clicked.connect(dlg.accept)
        ust.addWidget(btn_kapat)
        lay.addLayout(ust)
        liste = QListWidget()
        for s in sonuclar:
            item = QListWidgetItem(f"{s['tip']}  {s['baslik']}\n  {s['detay']}")
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
        bilgi.setStyleSheet("color:#7f8c8d;font-size:11px;")
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

    def tazele(self):
        try:
            aktif = self.pages.currentIndex()
            self.s_dash.yenile()
            if hasattr(self, "s_stok") and aktif == self.sayfa_index.get("stok", -1):
                self.s_stok.yenile()
            if hasattr(self, "s_uretim") and aktif == self.sayfa_index.get("uretim", -1):
                self.s_uretim.yenile()
            if hasattr(self, "s_siparis") and aktif == self.sayfa_index.get("siparis", -1):
                self.s_siparis.yenile()
            if self.user_role == "yonetici":
                if hasattr(self, "s_satin"):
                    self.s_satin.tablo_yenile()
                if hasattr(self, "s_cari"):
                    self.s_cari.yenile()
        except:
            pass


# ── Giriş & Başlatma ──────────────────────────────────────────
if __name__ == '__main__':
    app = QApplication(sys.argv)

    from PyQt5.QtGui import QPalette, QColor as QC
    palette = app.palette()
    palette.setColor(QPalette.Text, QC("#2c3e50"))
    palette.setColor(QPalette.WindowText, QC("#2c3e50"))
    palette.setColor(QPalette.Base, QC("#ffffff"))
    palette.setColor(QPalette.AlternateBase, QC("#f4f6f9"))
    palette.setColor(QPalette.Window, QC("#f4f6f9"))
    palette.setColor(QPalette.Button, QC("#f4f6f9"))
    palette.setColor(QPalette.ButtonText, QC("#2c3e50"))
    palette.setColor(QPalette.Highlight, QC("#2980b9"))
    palette.setColor(QPalette.HighlightedText, QC("#ffffff"))
    palette.setColor(QPalette.PlaceholderText, QC("#95a5a6"))
    app.setPalette(palette)

    from styles import APP_QSS
    app.setStyleSheet(APP_QSS)

    import os as _os
    if BULUT_MODU:
        from database_bulut import ayarlari_oku
    else:
        from database import db_yolu_al, db_yolu_kaydet, ayarlari_oku

    ayarlar = ayarlari_oku()
    db_yolu = ayarlar.get("db_yolu", "")
    db_hazir = BULUT_MODU or (db_yolu and _os.path.exists(
        _os.path.dirname(db_yolu) if _os.path.dirname(db_yolu) else "."))

    if not db_hazir:
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QFileDialog as QFD
        dlg = QDialog()
        dlg.setWindowTitle("Arsac Metal ERP — Veritabanı Kurulumu")
        dlg.setMinimumWidth(520)
        dlg.setStyleSheet("QDialog{background:#f4f6f9;} QLabel{color:#2c3e50;font-size:13px;}")
        lay = QVBoxLayout(dlg)
        lay.setSpacing(14)
        lay.setContentsMargins(24, 20, 24, 20)
        lbl_baslik = QLabel("Veritabanı Konumu Seçin")
        lbl_baslik.setStyleSheet("font-size:16px;font-weight:bold;color:#c0392b;")
        lay.addWidget(lbl_baslik)
        yol_lay = QHBoxLayout()
        txt_yol = QLineEdit()
        txt_yol.setPlaceholderText("Veritabanı dosya yolu...")
        txt_yol.setFixedHeight(36)
        if getattr(sys, 'frozen', False):
            _varsayilan = _os.path.join(_os.path.dirname(sys.executable), "arsac_metal.db")
        else:
            _varsayilan = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "arsac_metal.db")
        txt_yol.setText(_varsayilan)
        btn_sec = QPushButton("Gözat...")
        btn_sec.setFixedHeight(36)
        btn_sec.setStyleSheet("background:#2980b9;color:white;border-radius:7px;padding:5px 14px;font-weight:bold;border:none;")
        def _gozat():
            yol, _ = QFD.getSaveFileName(dlg, "Veritabanı Dosyası", txt_yol.text(), "SQLite DB (*.db)")
            if yol:
                txt_yol.setText(yol)
        btn_sec.clicked.connect(_gozat)
        yol_lay.addWidget(txt_yol)
        yol_lay.addWidget(btn_sec)
        lay.addLayout(yol_lay)
        btn_lay = QHBoxLayout()
        btn_lay.addStretch()
        btn_tamam = QPushButton("Başlat")
        btn_tamam.setFixedHeight(40)
        btn_tamam.setStyleSheet("background:#c0392b;color:white;border-radius:8px;padding:8px 24px;font-weight:bold;font-size:14px;border:none;")
        btn_tamam.clicked.connect(dlg.accept)
        btn_lay.addWidget(btn_tamam)
        lay.addLayout(btn_lay)
        dlg.exec_()
        secilen_yol = txt_yol.text().strip()
        if secilen_yol:
            db_yolu_kaydet(secilen_yol)

    try:
        from updater import guncelleme_kontrol
        _guncelleme_timer = QTimer()
        _guncelleme_timer.setSingleShot(True)
        _guncelleme_timer.timeout.connect(lambda: guncelleme_kontrol(parent=None, sessiz=True))
        _guncelleme_timer.start(1800000)
    except Exception as _ge:
        print("[Güncelleme] Modül yüklenemedi:", _ge)

    try:
        _conn, _cursor = baglanti_kur()
        if not BULUT_MODU:
            varsayilan_admin_olustur(_cursor, _conn)
    except Exception as _db_hata:
        if BULUT_MODU:
            print(f"[DB] Lokal SQLite hatası (bulut modunda yok sayıldı): {_db_hata}")
            from database_bulut import BulutConn, BulutCursor
            _conn, _cursor = BulutConn(), BulutCursor()
        else:
            QMessageBox.critical(None, "Veritabanı Hatası",
                                 "Veritabanı açılamadı:\n{}\n\nYedekler klasöründen geri yükleme yapın.".format(_db_hata))
            sys.exit(1)

    giris = GirisEkrani(_cursor, _conn)
    if giris.exec_() != QDialog.Accepted or not giris.sonuc:
        sys.exit(0)

    rol, kullanici_adi, ad_soyad = giris.sonuc
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
                ozet = "Günlük rapor hazırlandı!\n\n"
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
