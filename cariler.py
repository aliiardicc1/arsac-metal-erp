"""
Arsac Metal ERP — Cariler Modulu  (cariler.py)
4 sekme: Musteriler | Tedarikciler | Borc/Alacak Takibi | Odeme Gecmisi
"""

from styles import (DIALOG_QSS, INPUT, SAYFA_QSS,
                    make_buton, tablo_sag_tik_menu_ekle,
                    BTN_PRIMARY, BTN_BLUE, BTN_GREEN, BTN_GRAY, BTN_ORANGE)

TABLO_QSS = """
    QTableWidget {
        background: white; border-radius: 10px;
        border: 1px solid #dcdde1; color: #2c3e50;
        gridline-color: #f0f2f5; font-size: 13px;
        selection-background-color: #2980b9;
        selection-color: white;
        alternate-background-color: #f8f9fa;
    }
    QTableWidget::item {
        color: #2c3e50; padding: 5px 8px;
        border-bottom: 1px solid #f0f2f5;
    }
    QTableWidget::item:selected {
        background: #2980b9; color: white;
    }
    QTableWidget::item:selected:!active {
        background: #5dade2; color: white;
    }
    QTableWidget::item:hover {
        background: #eaf4fb; color: #2c3e50;
    }
    QHeaderView::section {
        background: #2c3e50; color: white;
        padding: 8px; font-weight: bold;
        font-size: 12px; border: none;
        border-right: 1px solid #3d5166;
        min-height: 36px;
    }
    QHeaderView::section:last { border-right: none; }
    QTableCornerButton::section { background: #2c3e50; border: none; }
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QDoubleSpinBox,
    QComboBox, QDialog, QDialogButtonBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QListWidget, QListWidgetItem, QGroupBox, QFrame,
    QSplitter, QStackedWidget, QScrollArea, QMessageBox, QTabWidget,
    QAbstractItemView, QSizePolicy, QCheckBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QIcon
from datetime import datetime

try:
    from log import log_yaz
except Exception:
    def log_yaz(c, n, i, d=""): pass

# ═══════════════════════════════════════════════════════════════
#  RENK / STİL SABİTLERİ
# ═══════════════════════════════════════════════════════════════
C = {
    "kirmizi":  "#c0392b",
    "mavi":     "#2980b9",
    "yesil":    "#27ae60",
    "turuncu":  "#e67e22",
    "mor":      "#8e44ad",
    "koyu":     "#2c3e50",
    "gri":      "#7f8c8d",
    "acik_gri": "#dcdde1",
    "bg":       "#f4f6f9",
    "white":    "#ffffff",
}

INP = ("border:1.5px solid #dcdde1;border-radius:7px;padding:6px 10px;"
       "font-size:13px;background:white;color:#2c3e50;")

TAB_QSS = """
    QTabWidget::pane{{border:1px solid #dcdde1;border-radius:8px;background:white;}}
    QTabBar::tab{{background:#ecf0f1;color:#2c3e50;padding:7px 16px;
                  border-radius:6px 6px 0 0;font-weight:bold;font-size:12px;
                  min-width:0px;margin-right:2px;}}
    QTabBar::tab:selected{{background:{sel};color:white;}}
    QTabBar::tab:hover:!selected{{background:#d5d8dc;}}
"""

LISTE_QSS = """
    QListWidget{{background:white;border-radius:10px;border:1px solid #dcdde1;
                color:#2c3e50;font-size:13px;outline:none;}}
    QListWidget::item{{padding:10px 12px;border-bottom:1px solid #f0f0f0;color:#2c3e50;}}
    QListWidget::item:selected{{background:{sel};color:white;border-radius:6px;}}
    QListWidget::item:hover{{background:{hov};}}
"""

# ═══════════════════════════════════════════════════════════════
#  YARDIMCI FONKSİYONLAR
# ═══════════════════════════════════════════════════════════════
def _item(txt, align=Qt.AlignCenter, fg="#2c3e50", bg=None, bold=False):
    it = QTableWidgetItem(str(txt if txt is not None else ""))
    it.setTextAlignment(align)
    it.setForeground(QColor(fg))
    if bg: it.setBackground(QColor(bg))
    if bold:
        f = it.font(); f.setBold(True); it.setFont(f)
    it.setFlags(it.flags() & ~Qt.ItemIsEditable)
    return it

def _tablo(headers, stretch_col=0):
    t = QTableWidget(0, len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.setEditTriggers(QTableWidget.NoEditTriggers)
    t.setAlternatingRowColors(True)
    t.setShowGrid(False)
    t.verticalHeader().setVisible(False)
    t.verticalHeader().setDefaultSectionSize(38)
    t.setSelectionBehavior(QTableWidget.SelectRows)
    t.setSelectionMode(QTableWidget.SingleSelection)
    t.setStyleSheet(TABLO_QSS)
    t.horizontalHeader().setSectionResizeMode(stretch_col, QHeaderView.Stretch)
    for c in range(len(headers)):
        if c != stretch_col:
            t.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeToContents)
    tablo_sag_tik_menu_ekle(t)
    return t

def _kart(baslik, deger, renk):
    f = QFrame()
    f.setMinimumHeight(72)
    f.setMaximumHeight(90)
    f.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    f.setStyleSheet(
        "QFrame{{background:white;border-radius:8px;"
        "border:1px solid #e0e0e0;border-left:4px solid {r};}}".format(r=renk))
    v = QVBoxLayout(f); v.setContentsMargins(12, 8, 12, 8); v.setSpacing(4)
    lb = QLabel(baslik)
    lb.setStyleSheet("color:#7f8c8d;font-size:11px;font-weight:bold;"
                     "letter-spacing:0.5px;background:transparent;")
    lb.setWordWrap(True)
    ld = QLabel(str(deger))
    ld.setStyleSheet("color:{r};font-size:15px;font-weight:900;"
                     "background:transparent;".format(r=renk))
    ld.setWordWrap(True)
    v.addWidget(lb); v.addWidget(ld)
    return f

def _ayrac():
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet("background:#e8e8e8;border:none;max-height:1px;")
    return line

def _baslik(txt, renk="#2c3e50", boyut=14):
    l = QLabel(txt)
    l.setStyleSheet("font-size:{b}px;font-weight:bold;color:{r};".format(b=boyut, r=renk))
    return l

def _le(ph, h=36):
    w = QLineEdit(); w.setPlaceholderText(ph)
    w.setFixedHeight(h); w.setStyleSheet(INP); return w

def _para_fmt(val):
    try:
        v = float(val or 0)
        # Binlik ayracı nokta, ondalık virgül (TR formatı)
        s = "{:,.2f}".format(v)          # 1,234.56
        s = s.replace(",", "X").replace(".", ",").replace("X", ".")  # 1.234,56
        return s + " TL"
    except: return "0,00 TL"

def _tarih_kontrol(tarih_str):
    """Tarihin gecikmeli mi, yakın mı yoksa normal mi olduğunu döner."""
    if not tarih_str or tarih_str == "-": return "#2c3e50", ""
    try:
        vd = datetime.strptime(tarih_str, "%d.%m.%Y")
        kalan = (vd - datetime.now()).days
        if kalan < 0:    return "#e74c3c", " ⚠ Gecikmiş ({} gün)".format(abs(kalan))
        elif kalan <= 7: return "#f39c12", " ⚠ {} gün kaldı".format(kalan)
        else:            return "#27ae60", " ({} gün kaldı)".format(kalan)
    except: return "#2c3e50", ""


# ═══════════════════════════════════════════════════════════════
#  FİRMA EKLE / DÜZENLE DİALOG  (Müşteri & Tedarikçi ortak)
# ═══════════════════════════════════════════════════════════════
class FirmaDialog(QDialog):
    def __init__(self, cursor, conn, tip="musteri", firma_adi=None, parent=None):
        super().__init__(parent)
        self.cursor = cursor; self.conn = conn
        self.tip = tip; self.firma_adi = firma_adi
        tip_ad = "Müşteri" if tip == "musteri" else "Tedarikçi"
        self.setWindowTitle(tip_ad + (" Düzenle" if firma_adi else " Ekle"))
        self.setMinimumWidth(500)
        self.setStyleSheet(DIALOG_QSS)
        self._build()
        if firma_adi: self._yukle()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20); lay.setSpacing(14)

        # Başlık
        hdr = QHBoxLayout()
        tip_ad = "Müşteri" if self.tip == "musteri" else "Tedarikçi"
        renk = C["mavi"] if self.tip == "musteri" else C["kirmizi"]
        bas = QLabel(("Yeni " + tip_ad) if not self.firma_adi else tip_ad + " Düzenle")
        bas.setStyleSheet("font-size:17px;font-weight:bold;color:{};".format(renk))
        hdr.addWidget(bas); hdr.addStretch()
        lay.addLayout(hdr)
        lay.addWidget(_ayrac())

        # Form
        gb = QGroupBox("Firma Bilgileri")
        gb.setStyleSheet("""
            QGroupBox{{background:white;border-radius:8px;border:1px solid #e0e0e0;
                       margin-top:6px;padding:14px;}}
            QGroupBox::title{{color:#2c3e50;font-weight:bold;
                              subcontrol-origin:margin;left:12px;padding:0 6px;}}
        """)
        grid = QGridLayout(gb); grid.setSpacing(10)

        self.txt_ad      = _le("Firma adı *")
        self.txt_yetkili = _le("Yetkili kişi")
        self.txt_tel     = _le("Telefon")
        self.txt_email   = _le("E-posta")
        self.txt_vergi   = _le("Vergi no / TC kimlik")
        self.txt_iban    = _le("IBAN")
        self.cmb_sehir   = QComboBox()
        self.cmb_sehir.setFixedHeight(36)
        self.cmb_sehir.setStyleSheet(INP)
        self.cmb_sehir.setEditable(True)
        for il in ["", "Adana","Ankara","Antalya","Bursa","Eskişehir","Gaziantep",
                   "İstanbul","İzmir","Kayseri","Kocaeli","Konya","Mersin","Sakarya"]:
            self.cmb_sehir.addItem(il)
        self.txt_adres   = QTextEdit()
        self.txt_adres.setPlaceholderText("Adres")
        self.txt_adres.setFixedHeight(64); self.txt_adres.setStyleSheet(INP)
        self.txt_notlar  = QTextEdit()
        self.txt_notlar.setPlaceholderText("Notlar / Açıklamalar")
        self.txt_notlar.setFixedHeight(64); self.txt_notlar.setStyleSheet(INP)
        self.spn_limit   = QDoubleSpinBox()
        self.spn_limit.setRange(0, 99_999_999); self.spn_limit.setDecimals(2)
        self.spn_limit.setSuffix(" TL"); self.spn_limit.setFixedHeight(36)
        self.spn_limit.setStyleSheet(INP)
        self.cmb_odeme   = QComboBox()
        self.cmb_odeme.setFixedHeight(36); self.cmb_odeme.setStyleSheet(INP)
        for o in ["Nakit", "Havale/EFT", "Çek", "Vadeli", "Kredi Kartı"]:
            self.cmb_odeme.addItem(o)

        satirlar = [
            ("Firma Adı *:",     self.txt_ad),
            ("Yetkili:",         self.txt_yetkili),
            ("Telefon:",         self.txt_tel),
            ("E-posta:",         self.txt_email),
            ("Vergi No:",        self.txt_vergi),
            ("IBAN:",            self.txt_iban),
            ("Şehir:",           self.cmb_sehir),
            ("Adres:",           self.txt_adres),
            ("Kredi Limiti:",    self.spn_limit),
            ("Ödeme Şekli:",     self.cmb_odeme),
            ("Notlar:",          self.txt_notlar),
        ]
        for row, (lbl_txt, wgt) in enumerate(satirlar):
            lbl = QLabel(lbl_txt)
            lbl.setStyleSheet("color:#7f8c8d;font-size:12px;font-weight:bold;")
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(lbl, row, 0)
            grid.addWidget(wgt, row, 1)
        lay.addWidget(gb)

        # Butonlar
        bh = QHBoxLayout(); bh.addStretch()
        bi = QPushButton("İptal"); bi.setFixedHeight(38)
        bi.setStyleSheet(BTN_GRAY); bi.clicked.connect(self.reject)
        bk = QPushButton("💾  Kaydet"); bk.setFixedHeight(38)
        bk.setStyleSheet(BTN_GREEN); bk.clicked.connect(self._kaydet)
        bh.addWidget(bi); bh.addWidget(bk)
        lay.addLayout(bh)

    def _yukle(self):
        try:
            self.cursor.execute(
                "SELECT firma_adi,iban,vergi_no,telefon,email,adres,notlar,"
                "kredi_limit FROM tedarikciler WHERE firma_adi=?", (self.firma_adi,))
            r = self.cursor.fetchone()
            if not r: return
            ad, iban, vn, tel, email, adres, notlar, limit = r
            self.txt_ad.setText(ad or "")
            self.txt_ad.setReadOnly(True)
            self.txt_iban.setText(iban or "")
            self.txt_vergi.setText(vn or "")
            self.txt_tel.setText(tel or "")
            self.txt_email.setText(email or "")
            self.txt_adres.setPlainText(adres or "")
            self.txt_notlar.setPlainText(notlar or "")
            self.spn_limit.setValue(float(limit or 0))
        except Exception as e:
            print("FirmaDialog._yukle:", e)

    def _kaydet(self):
        ad = self.txt_ad.text().strip()
        if not ad:
            QMessageBox.warning(self, "Eksik Alan", "Firma adı zorunludur!"); return
        try:
            if self.firma_adi:
                self.cursor.execute("""
                    UPDATE tedarikciler SET iban=?,vergi_no=?,telefon=?,email=?,
                    adres=?,notlar=?,kredi_limit=? WHERE firma_adi=?
                """, (self.txt_iban.text().strip(), self.txt_vergi.text().strip(),
                      self.txt_tel.text().strip(), self.txt_email.text().strip(),
                      self.txt_adres.toPlainText().strip(),
                      self.txt_notlar.toPlainText().strip(),
                      self.spn_limit.value(), self.firma_adi))
            else:
                self.cursor.execute("""
                    INSERT INTO tedarikciler
                        (firma_adi,iban,vergi_no,telefon,email,adres,notlar,kredi_limit)
                    VALUES (?,?,?,?,?,?,?,?)
                """, (ad, self.txt_iban.text().strip(), self.txt_vergi.text().strip(),
                      self.txt_tel.text().strip(), self.txt_email.text().strip(),
                      self.txt_adres.toPlainText().strip(),
                      self.txt_notlar.toPlainText().strip(),
                      self.spn_limit.value()))
            self.conn.commit()
            log_yaz(self.cursor, self.conn, "CARI_KAYDET", ad)
            self.accept()
        except Exception as e:
            if "UNIQUE" in str(e):
                QMessageBox.warning(self, "Kayıt Var", "Bu firma adı zaten kayıtlı.")
            else:
                QMessageBox.critical(self, "Hata", str(e))


# ═══════════════════════════════════════════════════════════════
#  SOL PANEL — firma listesi + arama + butonlar
# ═══════════════════════════════════════════════════════════════
class _SolPanel(QWidget):
    firma_secildi = pyqtSignal(str)

    def __init__(self, baslik, sel_renk, hov_renk, butonlar):
        """
        butonlar: [(etiket, stil, callback), ...]
        """
        super().__init__()
        self.setFixedWidth(268)
        self._build(baslik, sel_renk, hov_renk, butonlar)

    def _build(self, baslik, sel_renk, hov_renk, butonlar):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(6)

        # Başlık
        bas = QLabel(baslik)
        bas.setStyleSheet(
            "font-size:11px;font-weight:bold;color:#7f8c8d;"
            "letter-spacing:1px;padding:2px 0 4px 2px;")
        lay.addWidget(bas)

        # Arama
        self.txt_ara = QLineEdit()
        self.txt_ara.setPlaceholderText("Firma ara...")
        self.txt_ara.setFixedHeight(36)
        self.txt_ara.setStyleSheet(INP)
        self.txt_ara.textChanged.connect(self._filtrele)
        lay.addWidget(self.txt_ara)

        # Liste
        self.liste = QListWidget()
        self.liste.setStyleSheet(LISTE_QSS.format(sel=sel_renk, hov=hov_renk))
        self.liste.currentTextChanged.connect(self.firma_secildi.emit)
        lay.addWidget(self.liste)

        # Butonlar
        if butonlar:
            btn_lay = QHBoxLayout(); btn_lay.setSpacing(6)
            for etiket, stil, fn in butonlar:
                b = QPushButton(etiket); b.setFixedHeight(36)
                # Ekle butonu yeşil, Sil butonu kırmızı, diğerleri mavi
                if "Ekle" in etiket or "+" in etiket:
                    b.setStyleSheet(
                        "QPushButton{background:#27ae60;color:white;border-radius:8px;"
                        "padding:5px 14px;font-weight:bold;font-size:13px;border:none;}"
                        "QPushButton:hover{background:#1e8449;}")
                elif "Sil" in etiket:
                    b.setStyleSheet(
                        "QPushButton{background:#e74c3c;color:white;border-radius:8px;"
                        "padding:5px 14px;font-weight:bold;font-size:13px;border:none;}"
                        "QPushButton:hover{background:#c0392b;}")
                else:
                    b.setStyleSheet(stil)
                b.clicked.connect(fn)
                btn_lay.addWidget(b)
            lay.addLayout(btn_lay)

    def _filtrele(self, txt):
        txt = txt.lower()
        for i in range(self.liste.count()):
            self.liste.item(i).setHidden(txt not in self.liste.item(i).text().lower())

    def doldur(self, firmalar, secili=None):
        self.liste.blockSignals(True)
        self.liste.clear()
        for f in firmalar:
            self.liste.addItem(f)
        self.liste.blockSignals(False)
        if secili:
            items = self.liste.findItems(secili, Qt.MatchExactly)
            if items: self.liste.setCurrentItem(items[0])

    def secili(self):
        cur = self.liste.currentItem()
        return cur.text() if cur else None


# ═══════════════════════════════════════════════════════════════
#  MÜŞTERİ PANELİ
# ═══════════════════════════════════════════════════════════════
class MusteriPaneli(QWidget):
    def __init__(self, cursor, conn):
        super().__init__()
        self.cursor = cursor; self.conn = conn
        self._secili = None
        self._build()
        self.yenile()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(12)

        self.sol = _SolPanel(
            baslik="MÜŞTERİ LİSTESİ",
            sel_renk=C["mavi"], hov_renk="#eaf4fb",
            butonlar=[
                ("+ Ekle",  BTN_BLUE,    self._ekle),
                ("Sil",     BTN_PRIMARY, self._sil),
            ]
        )
        self.sol.firma_secildi.connect(self._sec)
        lay.addWidget(self.sol)

        # Sağ taraf
        self.sag = QWidget()
        self.sag_lay = QVBoxLayout(self.sag)
        self.sag_lay.setContentsMargins(0, 0, 0, 0); self.sag_lay.setSpacing(10)
        self._bos()
        lay.addWidget(self.sag)

    def _bos(self):
        self._temizle()
        lbl = QLabel("← Listeden bir müşteri seçin")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color:#bdc3c7;font-size:14px;")
        self.sag_lay.addWidget(lbl)

    def _temizle(self):
        while self.sag_lay.count():
            it = self.sag_lay.takeAt(0)
            if it.widget(): it.widget().deleteLater()

    def _sec(self, ad):
        self._secili = ad or None
        if not ad: self._bos(); return
        self._detay(ad)

    def _detay(self, ad):
        self._temizle()

        # ── Başlık ──
        hdr = QHBoxLayout()
        lbl = QLabel(ad)
        lbl.setStyleSheet("font-size:17px;font-weight:bold;color:#2c3e50;")
        hdr.addWidget(lbl); hdr.addStretch()
        b_duz = make_buton("✏ Düzenle", C["mavi"])
        b_duz.setFixedHeight(32); b_duz.clicked.connect(self._duzenle)
        hdr.addWidget(b_duz)
        b_tah = make_buton("📥 Tahsilat Al", C["yesil"])
        b_tah.setFixedHeight(32)
        b_tah.clicked.connect(lambda: self._tahsilat_al(ad))
        hdr.addWidget(b_tah)
        b_mkb = make_buton("📋 Makbuzlar", C["gri"])
        b_mkb.setFixedHeight(32)
        b_mkb.clicked.connect(lambda: self._makbuz_gecmisi(ad))
        hdr.addWidget(b_mkb)
        self.sag_lay.addLayout(hdr)
        self.sag_lay.addWidget(_ayrac())

        # ── Özet Kartlar ──
        try:
            self.cursor.execute("""
                SELECT COUNT(*),
                       COALESCE(SUM(genel_toplam),0),
                       COALESCE(SUM(CASE WHEN tahsil_edildi=1 THEN genel_toplam ELSE 0 END),0),
                       MAX(tarih)
                FROM siparisler WHERE musteri=?
            """, (ad,))
            cnt, toplam, tahsil, son = self.cursor.fetchone()
            alacak = toplam - tahsil
        except: cnt=0; toplam=0; tahsil=0; alacak=0; son="-"

        klay = QHBoxLayout(); klay.setSpacing(8)
        for b, d, r, ac in [
            ("TOPLAM SİPARİŞ",   str(cnt),               C["koyu"],    "sipariş"),
            ("TOPLAM TUTAR",     _para_fmt(toplam),       C["mor"],     "faturalanan"),
            ("TAHSİL EDİLEN",    _para_fmt(tahsil),       C["yesil"],   "ödendi"),
            ("BEKLEYEN ALACAK",  _para_fmt(alacak),       C["kirmizi"], "ödenmedi"),
        ]:
            klay.addWidget(_kart(b, d, r))
        self.sag_lay.addLayout(klay)

        # ── Sekmeler ──
        tabs = QTabWidget()
        tabs.setStyleSheet(TAB_QSS.format(sel=C["mavi"]))

        # İletişim Bilgileri
        t_iletisim = self._iletisim_tab(ad)
        tabs.addTab(t_iletisim, "📋  İletişim")

        # Sipariş Geçmişi
        t_sip = self._siparis_tab(ad)
        tabs.addTab(t_sip, "📦  Sipariş Geçmişi")

        # Ödeme Durumu
        t_odeme = self._odeme_tab(ad)
        tabs.addTab(t_odeme, "💳  Ödeme Durumu")

        # Toplam Alacak detay
        t_alacak = self._alacak_tab(ad)
        tabs.addTab(t_alacak, "💰  Alacak Takibi")

        self.sag_lay.addWidget(tabs)

    def _iletisim_tab(self, ad):
        w = QWidget()
        lay = QVBoxLayout(w); lay.setContentsMargins(16, 14, 16, 14); lay.setSpacing(0)
        try:
            self.cursor.execute(
                "SELECT firma_adi,telefon,email,adres,notlar,kredi_limit "
                "FROM tedarikciler WHERE firma_adi=?", (ad,))
            r = self.cursor.fetchone()
        except: r = None

        if r:
            _, tel, email, adres, notlar, limit = r
        else:
            # Siparişlerden al
            try:
                self.cursor.execute(
                    "SELECT telefon FROM siparisler WHERE musteri=? "
                    "AND telefon IS NOT NULL LIMIT 1", (ad,))
                rr = self.cursor.fetchone()
                tel = rr[0] if rr else "-"
            except: tel = "-"
            email = adres = notlar = "-"; limit = 0

        form = QFormLayout(); form.setSpacing(12); form.setLabelAlignment(Qt.AlignRight)
        for lbl_txt, val in [
            ("Telefon:",      tel or "-"),
            ("E-posta:",      email or "-"),
            ("Adres:",        adres or "-"),
            ("Kredi Limiti:", _para_fmt(limit)),
            ("Notlar:",       notlar or "-"),
        ]:
            ll = QLabel(lbl_txt)
            ll.setStyleSheet("color:#7f8c8d;font-weight:bold;font-size:12px;")
            lv = QLabel(val); lv.setWordWrap(True)
            lv.setStyleSheet("color:#2c3e50;font-size:13px;")
            form.addRow(ll, lv)
        lay.addLayout(form)
        lay.addStretch()
        return w

    def _siparis_tab(self, ad):
        w = QWidget()
        lay = QVBoxLayout(w); lay.setContentsMargins(8, 8, 8, 8)
        tbl = _tablo(["Sipariş No", "Tarih", "Tutar (TL)", "Durum", "Termin", "Notlar"],
                     stretch_col=5)
        DUR = {"Alindi": "#f39c12", "Uretimde": "#2980b9", "Hazir": "#8e44ad",
               "Sevk Edildi": "#27ae60", "Iptal": "#e74c3c", "Faturalandı": "#95a5a6"}
        try:
            self.cursor.execute("""
                SELECT sip_no, tarih, genel_toplam, durum, termin, notlar
                FROM siparisler WHERE musteri=? ORDER BY id DESC
            """, (ad,))
            for i, row in enumerate(self.cursor.fetchall()):
                sno, tarih, top, durum, ter, not_ = row
                tbl.insertRow(i)
                tbl.setItem(i, 0, _item(sno or "-", bold=True))
                tbl.setItem(i, 1, _item(tarih or "-"))
                tbl.setItem(i, 2, _item("{:,.2f}".format(float(top or 0))))
                tbl.setItem(i, 3, _item(durum or "-", fg=DUR.get(durum, "#2c3e50")))
                tbl.setItem(i, 4, _item(ter or "-"))
                tbl.setItem(i, 5, _item(not_ or "", align=Qt.AlignLeft | Qt.AlignVCenter))
        except Exception as e:
            print("Musteri siparis tab:", e)
        lay.addWidget(tbl)
        return w

    def _odeme_tab(self, ad):
        w = QWidget()
        lay = QVBoxLayout(w); lay.setContentsMargins(8, 8, 8, 8)
        tbl = _tablo(["Sipariş No", "Tarih", "Tutar (TL)", "Tahsil", "Ödeme Şekli"],
                     stretch_col=0)
        try:
            self.cursor.execute("""
                SELECT sip_no, tarih, genel_toplam, tahsil_edildi, odeme_sekli
                FROM siparisler WHERE musteri=? ORDER BY id DESC
            """, (ad,))
            for i, (sno, tarih, top, tahsil, sekil) in enumerate(self.cursor.fetchall()):
                tbl.insertRow(i)
                tahsil_b = bool(tahsil)
                tbl.setItem(i, 0, _item(sno or "-", bold=True))
                tbl.setItem(i, 1, _item(tarih or "-"))
                tbl.setItem(i, 2, _item("{:,.2f}".format(float(top or 0))))
                tbl.setItem(i, 3, _item(
                    "✅ Tahsil Edildi" if tahsil_b else "⏳ Bekliyor",
                    fg="#27ae60" if tahsil_b else "#e74c3c"))
                tbl.setItem(i, 4, _item(sekil or "-"))
        except Exception as e:
            print("Musteri odeme tab:", e)
        lay.addWidget(tbl)
        return w

    def _alacak_tab(self, ad):
        w = QWidget()
        lay = QVBoxLayout(w); lay.setContentsMargins(8, 8, 8, 8)

        # Özet bilgi
        try:
            self.cursor.execute("""
                SELECT
                    COUNT(*),
                    COALESCE(SUM(genel_toplam),0),
                    COALESCE(SUM(CASE WHEN tahsil_edildi=0 THEN genel_toplam ELSE 0 END),0),
                    COALESCE(SUM(CASE WHEN tahsil_edildi=1 THEN genel_toplam ELSE 0 END),0)
                FROM siparisler WHERE musteri=?
            """, (ad,))
            cnt, toplam, bekleyen, tahsil = self.cursor.fetchone()
        except: cnt=0; toplam=0; bekleyen=0; tahsil=0

        ozet = QHBoxLayout(); ozet.setSpacing(8)
        for b, d, r in [
            ("BEKLEYEN ALACAK", _para_fmt(bekleyen), C["kirmizi"]),
            ("TAHSİL EDİLEN",   _para_fmt(tahsil),   C["yesil"]),
            ("TOPLAM",          _para_fmt(toplam),    C["koyu"]),
        ]:
            ozet.addWidget(_kart(b, d, r))
        lay.addLayout(ozet)
        lay.addSpacing(8)

        # Bekleyen alacaklar tablosu
        tbl = _tablo(["Sipariş No", "Tarih", "Tutar (TL)", "Geçen Gün"],
                     stretch_col=0)
        try:
            self.cursor.execute("""
                SELECT sip_no, tarih, genel_toplam
                FROM siparisler
                WHERE musteri=? AND (tahsil_edildi=0 OR tahsil_edildi IS NULL)
                ORDER BY id DESC
            """, (ad,))
            for i, (sno, tarih, top) in enumerate(self.cursor.fetchall()):
                tbl.insertRow(i)
                gec_gun = "-"
                try:
                    dt = datetime.strptime(tarih, "%d.%m.%Y")
                    gec_gun = str((datetime.now() - dt).days) + " gün"
                except: pass
                tbl.setItem(i, 0, _item(sno or "-", bold=True))
                tbl.setItem(i, 1, _item(tarih or "-"))
                tbl.setItem(i, 2, _item("{:,.2f}".format(float(top or 0)),
                                        fg=C["kirmizi"], bold=True))
                tbl.setItem(i, 3, _item(gec_gun, fg="#e67e22"))
        except Exception as e:
            print("Alacak tab:", e)
        lay.addWidget(tbl)
        return w

    def yenile(self):
        secili = self._secili
        try:
            self.cursor.execute(
                "SELECT DISTINCT musteri FROM siparisler "
                "WHERE musteri IS NOT NULL AND musteri!='' ORDER BY musteri")
            firmalar = [r[0] for r in self.cursor.fetchall()]
        except: firmalar = []
        self.sol.doldur(firmalar, secili)
        if secili and secili in firmalar:
            self._detay(secili)
        else:
            self._bos()

    def _ekle(self):
        dlg = FirmaDialog(self.cursor, self.conn, "musteri", parent=self)
        if dlg.exec_() == QDialog.Accepted: self.yenile()

    def _duzenle(self):
        if not self._secili: return
        dlg = FirmaDialog(self.cursor, self.conn, "musteri",
                          firma_adi=self._secili, parent=self)
        if dlg.exec_() == QDialog.Accepted: self.yenile()

    def _sil(self):
        ad = self.sol.secili()
        if not ad:
            QMessageBox.warning(self, "Uyarı", "Önce bir müşteri seçin."); return
        c = QMessageBox.question(
            self, "Emin misin?",
            "<b>{}</b> müşteri kartı silinecek.\n"
            "Sipariş kayıtları silinmez.".format(ad),
            QMessageBox.Yes | QMessageBox.No)
        if c == QMessageBox.Yes:
            try:
                self.cursor.execute("DELETE FROM tedarikciler WHERE firma_adi=?", (ad,))
                self.conn.commit()
                log_yaz(self.cursor, self.conn, "MUSTERI_SILINDI", ad)
                self._secili = None; self.yenile()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))

    def _tahsilat_al(self, ad):
        """Seçili müşteriden tahsilat al."""
        # Bekleyen alacak tutarını bul
        try:
            self.cursor.execute("""
                SELECT sip_no, genel_toplam
                FROM siparisler
                WHERE musteri=? AND (tahsil_edildi=0 OR tahsil_edildi IS NULL)
                ORDER BY id DESC LIMIT 1
            """, (ad,))
            r = self.cursor.fetchone()
            sip_no = r[0] if r else ""
            max_t  = float(r[1]) if r else 0.0
        except: sip_no = ""; max_t = 0.0

        dlg = TediyeDialog(
            cursor=self.cursor, conn=self.conn,
            tip="tahsilat", firma=ad,
            siparis_no=sip_no, max_tutar=max_t,
            parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self.yenile()

    def _makbuz_gecmisi(self, ad):
        dlg = MakbuzGecmisiDialog(self.cursor, self.conn, ad, parent=self)
        dlg.exec_()



# ═══════════════════════════════════════════════════════════════
#  TEDARİKÇİ PANELİ
# ═══════════════════════════════════════════════════════════════
class TedarikciPaneli(QWidget):
    def __init__(self, cursor, conn):
        super().__init__()
        self.cursor = cursor; self.conn = conn
        self._secili = None
        self._build()
        self.yenile()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(12)

        self.sol = _SolPanel(
            baslik="TEDARİKÇİ LİSTESİ",
            sel_renk=C["kirmizi"], hov_renk="#fdecea",
            butonlar=[
                ("+ Ekle", BTN_PRIMARY,  self._ekle),
                ("Sil",    BTN_GRAY,     self._sil),
            ]
        )
        self.sol.firma_secildi.connect(self._sec)
        lay.addWidget(self.sol)

        self.sag = QWidget()
        self.sag_lay = QVBoxLayout(self.sag)
        self.sag_lay.setContentsMargins(0, 0, 0, 0); self.sag_lay.setSpacing(10)
        self._bos()
        lay.addWidget(self.sag)

    def _bos(self):
        self._temizle()
        lbl = QLabel("← Listeden bir tedarikçi seçin")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color:#bdc3c7;font-size:14px;")
        self.sag_lay.addWidget(lbl)

    def _temizle(self):
        while self.sag_lay.count():
            it = self.sag_lay.takeAt(0)
            if it.widget(): it.widget().deleteLater()

    def _sec(self, ad):
        self._secili = ad or None
        if not ad: self._bos(); return
        self._detay(ad)

    def _detay(self, ad):
        self._temizle()

        # Başlık
        hdr = QHBoxLayout()
        lbl = QLabel(ad)
        lbl.setStyleSheet("font-size:17px;font-weight:bold;color:#2c3e50;")
        hdr.addWidget(lbl); hdr.addStretch()
        b_duz = make_buton("✏ Düzenle", C["kirmizi"])
        b_duz.setFixedHeight(32); b_duz.clicked.connect(self._duzenle)
        hdr.addWidget(b_duz)
        b_ted = make_buton("📤 Ödeme Yap", C["turuncu"])
        b_ted.setFixedHeight(32)
        b_ted.clicked.connect(lambda: self._tediye_yap(ad))
        hdr.addWidget(b_ted)
        b_mkb = make_buton("📋 Makbuzlar", C["gri"])
        b_mkb.setFixedHeight(32)
        b_mkb.clicked.connect(lambda: self._makbuz_gecmisi(ad))
        hdr.addWidget(b_mkb)
        self.sag_lay.addLayout(hdr)
        self.sag_lay.addWidget(_ayrac())

        # Özet kartlar
        try:
            self.cursor.execute("""
                SELECT COUNT(*),
                       COALESCE(SUM(toplam_tutar),0),
                       COALESCE(SUM(CASE WHEN odendi=1 THEN toplam_tutar ELSE 0 END),0)
                FROM satinalma_kayitlari WHERE firma=?
            """, (ad,))
            cnt, toplam, odenen = self.cursor.fetchone()
            bekleyen = toplam - odenen
        except: cnt=0; toplam=0; odenen=0; bekleyen=0

        klay = QHBoxLayout(); klay.setSpacing(8)
        for b, d, r, ac in [
            ("TOPLAM ALIM",     _para_fmt(toplam),   C["koyu"],    "harcama"),
            ("ÖDENEN",          _para_fmt(odenen),   C["yesil"],   "ödendi"),
            ("BEKLEYEN BORÇ",   _para_fmt(bekleyen), C["kirmizi"], "ödenmedi"),
            ("ALIM SAYISI",     str(cnt),            C["mavi"],    "kayıt"),
        ]:
            klay.addWidget(_kart(b, d, r))
        self.sag_lay.addLayout(klay)

        # Sekmeler
        tabs = QTabWidget()
        tabs.setStyleSheet(TAB_QSS.format(sel=C["kirmizi"]))

        tabs.addTab(self._iletisim_tab(ad),   "📋  İletişim")
        tabs.addTab(self._satin_alma_tab(ad), "🛒  Satın Alma Geçmişi")
        tabs.addTab(self._borc_tab(ad),       "💳  Borç/Ödeme")
        tabs.addTab(self._vade_tab(ad),       "📅  Vade Takibi")

        self.sag_lay.addWidget(tabs)

    def _iletisim_tab(self, ad):
        w = QWidget()
        lay = QVBoxLayout(w); lay.setContentsMargins(16, 14, 16, 14)
        try:
            self.cursor.execute(
                "SELECT iban,vergi_no,telefon,email,adres,notlar,kredi_limit "
                "FROM tedarikciler WHERE firma_adi=?", (ad,))
            r = self.cursor.fetchone()
        except: r = None
        if r:
            iban, vn, tel, email, adres, notlar, limit = r
        else:
            iban=vn=tel=email=adres=notlar="-"; limit=0

        form = QFormLayout(); form.setSpacing(12); form.setLabelAlignment(Qt.AlignRight)
        for lbl_txt, val in [
            ("Telefon:",      tel or "-"),
            ("E-posta:",      email or "-"),
            ("Vergi No:",     vn or "-"),
            ("IBAN:",         iban or "-"),
            ("Kredi Limiti:", _para_fmt(limit)),
            ("Adres:",        adres or "-"),
            ("Notlar:",       notlar or "-"),
        ]:
            ll = QLabel(lbl_txt)
            ll.setStyleSheet("color:#7f8c8d;font-weight:bold;font-size:12px;")
            lv = QLabel(val); lv.setWordWrap(True)
            lv.setStyleSheet("color:#2c3e50;font-size:13px;")
            form.addRow(ll, lv)
        lay.addLayout(form); lay.addStretch()
        return w

    def _satin_alma_tab(self, ad):
        w = QWidget()
        lay = QVBoxLayout(w); lay.setContentsMargins(8, 8, 8, 8)
        tbl = _tablo(["Tarih", "Malzeme/Açıklama", "Tutar (TL)", "Ödendi", "Ödeme Tipi"],
                     stretch_col=1)
        try:
            self.cursor.execute("""
                SELECT tarih, malzeme, toplam_tutar, odendi, odeme_tipi
                FROM satinalma_kayitlari WHERE firma=? ORDER BY tarih DESC
            """, (ad,))
            for i, (tarih, mal, tutar, odendi, tip_) in enumerate(self.cursor.fetchall()):
                tbl.insertRow(i)
                od_b = bool(odendi)
                tbl.setItem(i, 0, _item(tarih or "-"))
                tbl.setItem(i, 1, _item(mal or "-", align=Qt.AlignLeft | Qt.AlignVCenter))
                tbl.setItem(i, 2, _item("{:,.2f}".format(float(tutar or 0))))
                tbl.setItem(i, 3, _item("✅ Ödendi" if od_b else "⏳ Bekliyor",
                                        fg="#27ae60" if od_b else "#e74c3c"))
                tbl.setItem(i, 4, _item(tip_ or "-"))
        except Exception as e:
            print("Satin alma tab:", e)
        lay.addWidget(tbl)
        return w

    def _borc_tab(self, ad):
        w = QWidget()
        lay = QVBoxLayout(w); lay.setContentsMargins(8, 8, 8, 8)

        try:
            self.cursor.execute("""
                SELECT
                    COALESCE(SUM(CASE WHEN odendi=0 THEN toplam_tutar ELSE 0 END),0),
                    COALESCE(SUM(CASE WHEN odendi=1 THEN toplam_tutar ELSE 0 END),0),
                    COUNT(CASE WHEN odendi=0 THEN 1 END)
                FROM satinalma_kayitlari WHERE firma=?
            """, (ad,))
            bek, od, cnt_bek = self.cursor.fetchone()
        except: bek=0; od=0; cnt_bek=0

        ozet = QHBoxLayout(); ozet.setSpacing(8)
        ozet.addWidget(_kart("BEKLEYEN BORÇ",  _para_fmt(bek), C["kirmizi"]))
        ozet.addWidget(_kart("ÖDENEN TOPLAM",  _para_fmt(od),  C["yesil"]))
        ozet.addWidget(_kart("ÖDENMEMIŞ KALEM", str(cnt_bek), C["turuncu"]))
        lay.addLayout(ozet); lay.addSpacing(8)

        tbl = _tablo(["Tarih", "Açıklama", "Tutar (TL)", "Durum", "Vade"],
                     stretch_col=1)
        try:
            self.cursor.execute("""
                SELECT tarih, malzeme, toplam_tutar, odendi, vade_tarihi
                FROM satinalma_kayitlari
                WHERE firma=? AND odendi=0 ORDER BY vade_tarihi ASC
            """, (ad,))
            for i, (tarih, mal, tutar, od_, vade) in enumerate(self.cursor.fetchall()):
                tbl.insertRow(i)
                renk, _ = _tarih_kontrol(vade)
                tbl.setItem(i, 0, _item(tarih or "-"))
                tbl.setItem(i, 1, _item(mal or "-", align=Qt.AlignLeft | Qt.AlignVCenter))
                tbl.setItem(i, 2, _item("{:,.2f}".format(float(tutar or 0)),
                                        fg=C["kirmizi"], bold=True))
                tbl.setItem(i, 3, _item("⏳ Bekliyor", fg=C["kirmizi"]))
                tbl.setItem(i, 4, _item(vade or "-", fg=renk))
        except Exception as e:
            print("Borc tab:", e)
        lay.addWidget(tbl)
        return w

    def _vade_tab(self, ad):
        w = QWidget()
        lay = QVBoxLayout(w); lay.setContentsMargins(8, 8, 8, 8)

        # Uyarı bandı
        try:
            self.cursor.execute("""
                SELECT COUNT(*) FROM satinalma_kayitlari
                WHERE firma=? AND odendi=0
                AND vade_tarihi IS NOT NULL AND vade_tarihi != ''
            """, (ad,))
            gecmis_cnt = self.cursor.fetchone()[0]
        except: gecmis_cnt = 0

        if gecmis_cnt > 0:
            uyari = QLabel("⚠  {} adet vadesi geçmiş/yaklaşan kayıt var!".format(gecmis_cnt))
            uyari.setStyleSheet(
                "background:#fdecea;color:#c0392b;font-weight:bold;"
                "padding:8px 12px;border-radius:6px;font-size:13px;")
            lay.addWidget(uyari)
            lay.addSpacing(6)

        tbl = _tablo(["Vade Tarihi", "Açıklama", "Tutar (TL)", "Kalan Gün", "Durum"],
                     stretch_col=1)
        try:
            self.cursor.execute("""
                SELECT vade_tarihi, malzeme, toplam_tutar, odendi
                FROM satinalma_kayitlari
                WHERE firma=? AND vade_tarihi IS NOT NULL AND vade_tarihi!=''
                ORDER BY vade_tarihi ASC
            """, (ad,))
            for i, (vade, mal, tutar, od_) in enumerate(self.cursor.fetchall()):
                tbl.insertRow(i)
                od_b = bool(od_)
                renk, aciklama = _tarih_kontrol(vade)
                try:
                    kalan = (datetime.strptime(vade, "%d.%m.%Y") - datetime.now()).days
                    kalan_str = str(kalan) + " gün"
                except: kalan_str = "-"

                if od_b:
                    renk = "#27ae60"; durum = "✅ Ödendi"; kalan_str = "-"
                elif aciklama.startswith(" ⚠ Gecikmiş"):
                    durum = "🔴 Gecikmiş"
                elif aciklama.startswith(" ⚠"):
                    durum = "🟡 Yaklaşıyor"
                else:
                    durum = "🟢 Normal"

                tbl.setItem(i, 0, _item(vade or "-", fg=renk))
                tbl.setItem(i, 1, _item(mal or "-", align=Qt.AlignLeft | Qt.AlignVCenter))
                tbl.setItem(i, 2, _item("{:,.2f}".format(float(tutar or 0))))
                tbl.setItem(i, 3, _item(kalan_str, fg=renk))
                tbl.setItem(i, 4, _item(durum))
        except Exception as e:
            print("Vade tab:", e)
        lay.addWidget(tbl)
        return w

    def yenile(self):
        secili = self._secili
        try:
            self.cursor.execute("SELECT firma_adi FROM tedarikciler ORDER BY firma_adi")
            firmalar = [r[0] for r in self.cursor.fetchall()]
        except: firmalar = []
        self.sol.doldur(firmalar, secili)
        if secili and secili in firmalar:
            self._detay(secili)
        else:
            self._bos()

    def _ekle(self):
        dlg = FirmaDialog(self.cursor, self.conn, "tedarikci", parent=self)
        if dlg.exec_() == QDialog.Accepted: self.yenile()

    def _duzenle(self):
        if not self._secili: return
        dlg = FirmaDialog(self.cursor, self.conn, "tedarikci",
                          firma_adi=self._secili, parent=self)
        if dlg.exec_() == QDialog.Accepted: self.yenile()

    def _sil(self):
        ad = self.sol.secili()
        if not ad:
            QMessageBox.warning(self, "Uyarı", "Önce bir tedarikçi seçin."); return
        c = QMessageBox.question(
            self, "Emin misin?",
            "<b>{}</b> tedarikçisi silinecek.\n"
            "Satın alma kayıtları silinmez.".format(ad),
            QMessageBox.Yes | QMessageBox.No)
        if c == QMessageBox.Yes:
            try:
                self.cursor.execute("DELETE FROM tedarikciler WHERE firma_adi=?", (ad,))
                self.conn.commit()
                log_yaz(self.cursor, self.conn, "TEDARIKCI_SILINDI", ad)
                self._secili = None; self.yenile()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))

    def _tediye_yap(self, ad):
        """Seçili tedarikçiye ödeme yap."""
        try:
            self.cursor.execute("""
                SELECT id, malzeme, toplam_tutar
                FROM satinalma_kayitlari
                WHERE firma=? AND odendi=0
                ORDER BY id DESC LIMIT 1
            """, (ad,))
            r = self.cursor.fetchone()
            satinalma_id = r[0] if r else None
            aciklama     = r[1] if r else ""
            max_t        = float(r[2]) if r else 0.0
        except: satinalma_id=None; aciklama=""; max_t=0.0

        dlg = TediyeDialog(
            cursor=self.cursor, conn=self.conn,
            tip="tediye", firma=ad,
            siparis_no=aciklama, max_tutar=max_t,
            satinalma_id=satinalma_id,
            parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self.yenile()

    def _makbuz_gecmisi(self, ad):
        dlg = MakbuzGecmisiDialog(self.cursor, self.conn, ad, parent=self)
        dlg.exec_()



# ═══════════════════════════════════════════════════════════════
#  BORÇ / ALACAK TAKİBİ  (Genel özet)
# ═══════════════════════════════════════════════════════════════
class BorcAlacakPaneli(QWidget):
    def __init__(self, cursor, conn):
        super().__init__()
        self.cursor = cursor; self.conn = conn
        self._build()
        self.yenile()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(4, 4, 4, 4); lay.setSpacing(12)

        bas = _baslik("BORÇ / ALACAK TAKİBİ", C["koyu"], 15)
        lay.addWidget(bas)
        lay.addWidget(_ayrac())

        # Üst özet kartlar
        self.kart_lay = QHBoxLayout(); self.kart_lay.setSpacing(10)
        lay.addLayout(self.kart_lay)
        lay.addWidget(_ayrac())

        # İki tablo yan yana
        tablo_lay = QHBoxLayout(); tablo_lay.setSpacing(12)

        # Alacaklar (müşteriler)
        sol = QWidget()
        sl = QVBoxLayout(sol); sl.setContentsMargins(0, 0, 0, 0); sl.setSpacing(6)
        sl.addWidget(_baslik("📥  MÜŞTERİ ALACAKLARI", C["mavi"]))
        self.tbl_alacak = _tablo(
            ["Müşteri", "Toplam", "Tahsil", "Bekleyen"], stretch_col=0)
        sl.addWidget(self.tbl_alacak)
        tablo_lay.addWidget(sol)

        # Borçlar (tedarikçiler)
        sag = QWidget()
        sgl = QVBoxLayout(sag); sgl.setContentsMargins(0, 0, 0, 0); sgl.setSpacing(6)
        sgl.addWidget(_baslik("📤  TEDARİKÇİ BORÇLARI", C["kirmizi"]))
        self.tbl_borc = _tablo(
            ["Tedarikçi", "Toplam", "Ödenen", "Bekleyen"], stretch_col=0)
        sgl.addWidget(self.tbl_borc)
        tablo_lay.addWidget(sag)

        lay.addLayout(tablo_lay)

    def yenile(self):
        # Kartları temizle
        while self.kart_lay.count():
            it = self.kart_lay.takeAt(0)
            if it.widget(): it.widget().deleteLater()

        # Alacak özeti
        try:
            self.cursor.execute("""
                SELECT COALESCE(SUM(genel_toplam),0),
                       COALESCE(SUM(CASE WHEN tahsil_edildi=1 THEN genel_toplam ELSE 0 END),0)
                FROM siparisler WHERE musteri IS NOT NULL
            """)
            al_top, al_tah = self.cursor.fetchone()
            al_bek = al_top - al_tah
        except: al_top=0; al_tah=0; al_bek=0

        # Borç özeti
        try:
            self.cursor.execute("""
                SELECT COALESCE(SUM(toplam_tutar),0),
                       COALESCE(SUM(CASE WHEN odendi=1 THEN toplam_tutar ELSE 0 END),0)
                FROM satinalma_kayitlari
            """)
            bo_top, bo_od = self.cursor.fetchone()
            bo_bek = bo_top - bo_od
        except: bo_top=0; bo_od=0; bo_bek=0

        # Net pozisyon
        net = al_bek - bo_bek
        net_renk = C["yesil"] if net >= 0 else C["kirmizi"]
        net_str = ("+" if net >= 0 else "") + _para_fmt(net)

        for b, d, r in [
            ("TOPLAM ALACAK",    _para_fmt(al_bek),  C["mavi"]),
            ("TOPLAM BORÇ",      _para_fmt(bo_bek),  C["kirmizi"]),
            ("NET POZİSYON",     net_str,             net_renk),
            ("TAHSİL EDİLEN",    _para_fmt(al_tah),  C["yesil"]),
        ]:
            self.kart_lay.addWidget(_kart(b, d, r))

        # Alacak tablosu
        self.tbl_alacak.setRowCount(0)
        try:
            self.cursor.execute("""
                SELECT musteri,
                       COALESCE(SUM(genel_toplam),0),
                       COALESCE(SUM(CASE WHEN tahsil_edildi=1 THEN genel_toplam ELSE 0 END),0)
                FROM siparisler
                WHERE musteri IS NOT NULL AND musteri!=''
                GROUP BY musteri ORDER BY SUM(genel_toplam) DESC
            """)
            for i, (m, top, tah) in enumerate(self.cursor.fetchall()):
                bek = top - tah
                self.tbl_alacak.insertRow(i)
                self.tbl_alacak.setItem(i, 0, _item(m, align=Qt.AlignLeft | Qt.AlignVCenter))
                self.tbl_alacak.setItem(i, 1, _item("{:,.0f}".format(top)))
                self.tbl_alacak.setItem(i, 2, _item("{:,.0f}".format(tah), fg=C["yesil"]))
                self.tbl_alacak.setItem(i, 3, _item(
                    "{:,.0f}".format(bek),
                    fg=C["kirmizi"] if bek > 0 else C["yesil"],
                    bold=bek > 0))
        except Exception as e:
            print("Borc alacak tablo:", e)

        # Borç tablosu
        self.tbl_borc.setRowCount(0)
        try:
            self.cursor.execute("""
                SELECT firma,
                       COALESCE(SUM(toplam_tutar),0),
                       COALESCE(SUM(CASE WHEN odendi=1 THEN toplam_tutar ELSE 0 END),0)
                FROM satinalma_kayitlari
                GROUP BY firma ORDER BY SUM(toplam_tutar) DESC
            """)
            for i, (f, top, od) in enumerate(self.cursor.fetchall()):
                bek = top - od
                self.tbl_borc.insertRow(i)
                self.tbl_borc.setItem(i, 0, _item(f or "-", align=Qt.AlignLeft | Qt.AlignVCenter))
                self.tbl_borc.setItem(i, 1, _item("{:,.0f}".format(top)))
                self.tbl_borc.setItem(i, 2, _item("{:,.0f}".format(od), fg=C["yesil"]))
                self.tbl_borc.setItem(i, 3, _item(
                    "{:,.0f}".format(bek),
                    fg=C["kirmizi"] if bek > 0 else C["yesil"],
                    bold=bek > 0))
        except Exception as e:
            print("Borc tablo:", e)


# ═══════════════════════════════════════════════════════════════
#  ÖDEME GEÇMİŞİ  (Tüm tahsilatlar + ödemeler kronolojik)
# ═══════════════════════════════════════════════════════════════
class OdemeGecmisiPaneli(QWidget):
    def __init__(self, cursor, conn):
        super().__init__()
        self.cursor = cursor; self.conn = conn
        self._build()
        self.yenile()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(4, 4, 4, 4); lay.setSpacing(10)

        # Başlık + Filtreler
        filtre_lay = QHBoxLayout()
        filtre_lay.addWidget(_baslik("ÖDEME GEÇMİŞİ", C["koyu"], 15))
        filtre_lay.addStretch()

        self.cmb_tip = QComboBox()
        self.cmb_tip.setFixedHeight(34); self.cmb_tip.setFixedWidth(160)
        self.cmb_tip.setStyleSheet(INP)
        for t in ["Tümü", "Tahsilatlar (Müşteri)", "Ödemeler (Tedarikçi)"]:
            self.cmb_tip.addItem(t)
        self.cmb_tip.currentIndexChanged.connect(self.yenile)
        filtre_lay.addWidget(QLabel("Filtre:"))
        filtre_lay.addWidget(self.cmb_tip)

        self.txt_ara = QLineEdit()
        self.txt_ara.setPlaceholderText("Firma / açıklama ara...")
        self.txt_ara.setFixedHeight(34); self.txt_ara.setFixedWidth(200)
        self.txt_ara.setStyleSheet(INP)
        self.txt_ara.textChanged.connect(self._filtrele)
        filtre_lay.addWidget(self.txt_ara)
        lay.addLayout(filtre_lay)
        lay.addWidget(_ayrac())

        # Özet kartlar
        self.ozet_lay = QHBoxLayout(); self.ozet_lay.setSpacing(10)
        lay.addLayout(self.ozet_lay)
        lay.addSpacing(4)

        # Tablo
        self.tbl = _tablo(
            ["Tarih", "Tür", "Firma", "Açıklama", "Tutar (TL)", "Durum"],
            stretch_col=3)
        self.tbl.verticalHeader().setDefaultSectionSize(36)
        lay.addWidget(self.tbl)

    def yenile(self):
        # Özet kartları yenile
        while self.ozet_lay.count():
            it = self.ozet_lay.takeAt(0)
            if it.widget(): it.widget().deleteLater()

        try:
            self.cursor.execute("""
                SELECT COALESCE(SUM(genel_toplam),0),
                       COALESCE(SUM(CASE WHEN tahsil_edildi=1 THEN genel_toplam ELSE 0 END),0)
                FROM siparisler WHERE musteri IS NOT NULL
            """)
            al_top, al_tah = self.cursor.fetchone()
        except: al_top=0; al_tah=0

        try:
            self.cursor.execute("""
                SELECT COALESCE(SUM(toplam_tutar),0),
                       COALESCE(SUM(CASE WHEN odendi=1 THEN toplam_tutar ELSE 0 END),0)
                FROM satinalma_kayitlari
            """)
            bo_top, bo_od = self.cursor.fetchone()
        except: bo_top=0; bo_od=0

        for b, d, r in [
            ("TAHSİLAT TOPLAMI",  _para_fmt(al_tah), C["yesil"]),
            ("ÖDEME TOPLAMI",     _para_fmt(bo_od),  C["kirmizi"]),
            ("BEKLEYEN TAHSİLAT", _para_fmt(al_top - al_tah), C["mavi"]),
            ("BEKLEYEN ÖDEME",    _para_fmt(bo_top - bo_od),  C["turuncu"]),
        ]:
            self.ozet_lay.addWidget(_kart(b, d, r))

        # Tablo verisi
        self.tbl.setRowCount(0)
        tip = self.cmb_tip.currentIndex()  # 0=tümü, 1=tahsilat, 2=ödeme
        satirlar = []

        if tip in (0, 1):  # Müşteri tahsilatları
            try:
                self.cursor.execute("""
                    SELECT tarih, musteri, sip_no, genel_toplam, tahsil_edildi
                    FROM siparisler WHERE musteri IS NOT NULL ORDER BY tarih DESC
                """)
                for tarih, m, sno, top, tahsil in self.cursor.fetchall():
                    satirlar.append({
                        "tarih": tarih or "-",
                        "tur": "Tahsilat",
                        "firma": m or "-",
                        "aciklama": sno or "-",
                        "tutar": float(top or 0),
                        "durum": "Tahsil Edildi" if tahsil else "Bekliyor",
                        "durum_renk": C["yesil"] if tahsil else C["kirmizi"],
                        "tutar_renk": C["yesil"] if tahsil else C["koyu"],
                    })
            except Exception as e:
                print("Odeme gecmisi musteri:", e)

        if tip in (0, 2):  # Tedarikçi ödemeleri
            try:
                self.cursor.execute("""
                    SELECT tarih, firma, malzeme, toplam_tutar, odendi
                    FROM satinalma_kayitlari ORDER BY tarih DESC
                """)
                for tarih, f, mal, top, od in self.cursor.fetchall():
                    satirlar.append({
                        "tarih": tarih or "-",
                        "tur": "Ödeme",
                        "firma": f or "-",
                        "aciklama": mal or "-",
                        "tutar": float(top or 0),
                        "durum": "Ödendi" if od else "Bekliyor",
                        "durum_renk": C["yesil"] if od else C["kirmizi"],
                        "tutar_renk": C["kirmizi"],
                    })
            except Exception as e:
                print("Odeme gecmisi tedarikci:", e)

        # Tarihe göre sırala
        def _tarih_sort(s):
            try: return datetime.strptime(s["tarih"], "%d.%m.%Y")
            except: return datetime.min
        satirlar.sort(key=_tarih_sort, reverse=True)

        for i, s in enumerate(satirlar):
            self.tbl.insertRow(i)
            tur_renk = C["yesil"] if s["tur"] == "Tahsilat" else C["kirmizi"]
            self.tbl.setItem(i, 0, _item(s["tarih"]))
            self.tbl.setItem(i, 1, _item(s["tur"], fg=tur_renk, bold=True))
            self.tbl.setItem(i, 2, _item(s["firma"], align=Qt.AlignLeft | Qt.AlignVCenter))
            self.tbl.setItem(i, 3, _item(s["aciklama"], align=Qt.AlignLeft | Qt.AlignVCenter))
            self.tbl.setItem(i, 4, _item("{:,.2f}".format(s["tutar"]),
                                         fg=s["tutar_renk"], bold=True))
            self.tbl.setItem(i, 5, _item(s["durum"], fg=s["durum_renk"]))

        # Satır sayısı etiketi
        self.tbl.setToolTip("{} kayıt".format(len(satirlar)))

    def _filtrele(self, txt):
        txt = txt.lower()
        for i in range(self.tbl.rowCount()):
            firma = (self.tbl.item(i, 2) or QTableWidgetItem()).text().lower()
            aciklama = (self.tbl.item(i, 3) or QTableWidgetItem()).text().lower()
            self.tbl.setRowHidden(i, txt not in firma and txt not in aciklama)


# ═══════════════════════════════════════════════════════════════
#  ANA CARİLER SAYFASI
# ═══════════════════════════════════════════════════════════════
class TedarikciSayfasi(QWidget):
    """Ana giriş noktası — main.py'de bu sınıf import edilir."""

    def __init__(self, cursor, conn, user_role="yonetici"):
        super().__init__()
        self.cursor = cursor; self.conn = conn; self.user_role = user_role
        self.setStyleSheet(SAYFA_QSS)
        self._build()
        # Otomatik yenileme — 60 saniyede bir
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.yenile)
        self._timer.start(60_000)

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(20, 14, 20, 14); lay.setSpacing(12)

        # Başlık
        hdr = QHBoxLayout()
        bas = QLabel("CARİLER")
        bas.setStyleSheet("font-size:20px;font-weight:900;color:#2c3e50;"
                          "letter-spacing:1px;")
        hdr.addWidget(bas); hdr.addStretch()
        btn_r = make_buton("🔄 Yenile", C["gri"])
        btn_r.setFixedHeight(36); btn_r.clicked.connect(self.yenile)
        hdr.addWidget(btn_r)
        lay.addLayout(hdr)

        # Ana sekmeler
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane{{border:1px solid #dcdde1;border-radius:10px;
                              background:#f4f6f9;}}
            QTabBar::tab{{background:#ecf0f1;color:#2c3e50;padding:10px 22px;
                          border-radius:8px 8px 0 0;font-weight:bold;
                          font-size:12px;min-width:0px;margin-right:3px;}}
            QTabBar::tab:selected{{background:#2c3e50;color:white;}}
            QTabBar::tab:hover:!selected{{background:#d5d8dc;}}
        """)

        self.musteri_p    = MusteriPaneli(self.cursor, self.conn)
        self.tedarikci_p  = TedarikciPaneli(self.cursor, self.conn)
        self.borc_alacak  = BorcAlacakPaneli(self.cursor, self.conn)
        self.odeme_gecmis = OdemeGecmisiPaneli(self.cursor, self.conn)

        self.tabs.addTab(self.musteri_p,    "👤  Müşteriler")
        self.tabs.addTab(self.tedarikci_p,  "🏭  Tedarikçiler")
        self.tabs.addTab(self.borc_alacak,  "⚖  Borç/Alacak")
        self.tabs.addTab(self.odeme_gecmis, "💵  Ödeme Geçmişi")

        lay.addWidget(self.tabs)

    def yenile(self):
        self.musteri_p.yenile()
        self.tedarikci_p.yenile()
        self.borc_alacak.yenile()
        self.odeme_gecmis.yenile()


# ═══════════════════════════════════════════════════════════════
#  MAKBUZ NO ÜRETİCİ
# ═══════════════════════════════════════════════════════════════
def _otomatik_makbuz_no(cursor, tip):
    """TAH-2026-0001 veya TED-2026-0001 formatında sıradaki no."""
    prefix = "TAH" if tip == "tahsilat" else "TED"
    yil = datetime.now().year
    try:
        cursor.execute(
            "SELECT makbuz_no FROM tediye_makbuzlari "
            "WHERE makbuz_no LIKE ? ORDER BY id DESC LIMIT 1",
            ("{}-{}-%" .format(prefix, yil),))
        r = cursor.fetchone()
        if r:
            son = int(r[0].split("-")[-1])
            return "{}-{}-{:04d}".format(prefix, yil, son + 1)
    except: pass
    return "{}-{}-0001".format(prefix, yil)


# ═══════════════════════════════════════════════════════════════
#  PDF MAKBUZ ÜRETİCİ  (reportlab)
# ═══════════════════════════════════════════════════════════════
def makbuz_pdf_olustur(data: dict, pdf_yolu: str):
    """
    data anahtarları:
        makbuz_no, tip, firma, tarih, tutar, kalan_tutar,
        odeme_sekli, aciklama, siparis_no, olusturan
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.pdfgen import canvas as rl_canvas
        from reportlab.lib import colors
    except ImportError:
        return False

    W, H = A4
    c = rl_canvas.Canvas(pdf_yolu, pagesize=A4)

    tip_ad  = "TAHSİLAT MAKBUZU" if data.get("tip") == "tahsilat" else "TEDİYE MAKBUZU"
    ana_renk = colors.HexColor("#2980b9") if data.get("tip") == "tahsilat" \
               else colors.HexColor("#c0392b")

    # ── Arka plan üst bant ──
    c.setFillColor(ana_renk)
    c.rect(0, H - 90, W, 90, fill=True, stroke=False)

    # ── Firma adı (sol üst) ──
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(2*cm, H - 38, "ARSAC METAL")
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, H - 54, "Oksijen   Plazma   Lazer Kesim")

    # ── Makbuz tipi (sağ üst) ──
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(W - 2*cm, H - 38, tip_ad)
    c.setFont("Helvetica", 10)
    c.drawRightString(W - 2*cm, H - 54, data.get("makbuz_no", ""))

    # ── İnce çizgi ──
    c.setStrokeColor(ana_renk)
    c.setLineWidth(2)
    c.line(2*cm, H - 100, W - 2*cm, H - 100)

    # ── Bilgi kutusu ──
    def satir(y, etiket, deger, deger_renk=None):
        c.setFillColor(colors.HexColor("#7f8c8d"))
        c.setFont("Helvetica-Bold", 9)
        c.drawString(2*cm, y, etiket)
        c.setFillColor(deger_renk if deger_renk else colors.HexColor("#2c3e50"))
        c.setFont("Helvetica", 10)
        c.drawString(7*cm, y, str(deger))

    y = H - 130
    satir(y,       "Tarih:",        data.get("tarih", "-")); y -= 22
    satir(y,       "Firma:",        data.get("firma", "-")); y -= 22
    satir(y,       "Siparis No:",   data.get("siparis_no", "-")); y -= 22
    satir(y,       "Odeme Sekli:",  data.get("odeme_sekli", "-")); y -= 22
    satir(y,       "Aciklama:",     data.get("aciklama", "-")); y -= 30

    # ── Tutar kutusu ──
    c.setFillColor(colors.HexColor("#f8f9fa"))
    c.roundRect(2*cm, y - 50, W - 4*cm, 60, 8, fill=True, stroke=False)
    c.setStrokeColor(ana_renk); c.setLineWidth(1.5)
    c.roundRect(2*cm, y - 50, W - 4*cm, 60, 8, fill=False, stroke=True)

    c.setFillColor(colors.HexColor("#7f8c8d"))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(3*cm, y + 2, "TAHSIL EDILEN / ODENEN TUTAR")
    c.setFillColor(ana_renk)
    c.setFont("Helvetica-Bold", 22)
    tutar_str = "{:,.2f} TL".format(float(data.get("tutar", 0)))
    c.drawCentredString(W / 2, y - 30, tutar_str)

    y -= 70

    # Kalan borç varsa
    kalan = float(data.get("kalan_tutar", 0))
    if kalan > 0:
        c.setFillColor(colors.HexColor("#e74c3c"))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(2*cm, y, "Kalan Borc / Alacak: {:,.2f} TL".format(kalan))
        y -= 20

    y -= 20

    # ── İmza alanları ──
    c.setStrokeColor(colors.HexColor("#dcdde1")); c.setLineWidth(1)
    for x_start, etiket in [(2*cm, "Teslim Eden"), (W/2 + 1*cm, "Teslim Alan")]:
        c.line(x_start, y, x_start + 7*cm, y)
        c.setFillColor(colors.HexColor("#7f8c8d"))
        c.setFont("Helvetica", 9)
        c.drawString(x_start, y - 14, etiket)

    # ── Alt bilgi ──
    c.setFillColor(ana_renk)
    c.rect(0, 0, W, 28, fill=True, stroke=False)
    c.setFillColor(colors.white)
    c.setFont("Helvetica", 8)
    c.drawCentredString(W/2, 10,
        "Duzenleyen: {}   |   {}   |   Bu belge resmi makbuz yerine gecmez.".format(
            data.get("olusturan", ""), data.get("tarih", "")))

    c.save()
    return True


# ═══════════════════════════════════════════════════════════════
#  TEDİYE / TAHSİLAT DİALOGU
# ═══════════════════════════════════════════════════════════════
class TediyeDialog(QDialog):
    """
    tip = 'tahsilat'  →  Müşteriden para al  (alacak kapat)
    tip = 'tediye'    →  Tedarikçiye ödeme yap (borç kapat)
    """
    def __init__(self, cursor, conn, tip, firma=None, siparis_no=None,
                 max_tutar=0.0, satinalma_id=None, user="", parent=None):
        super().__init__(parent)
        self.cursor      = cursor
        self.conn        = conn
        self.tip         = tip
        self.firma_adi   = firma
        self.siparis_no  = siparis_no
        self.max_tutar   = float(max_tutar)
        self.satinalma_id = satinalma_id
        self.user        = user
        self._pdf_yolu   = None

        tip_ad = "Tahsilat Al" if tip == "tahsilat" else "Tediye / Ödeme Yap"
        self.setWindowTitle(tip_ad)
        self.setMinimumWidth(520)
        self.setStyleSheet(DIALOG_QSS)
        self._build()
        self._auto_doldur()

    # ── UI ──────────────────────────────────────────────────────
    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20); lay.setSpacing(14)

        # Başlık bandı
        is_tahsilat = self.tip == "tahsilat"
        renk = C["mavi"] if is_tahsilat else C["kirmizi"]
        ikon = "📥" if is_tahsilat else "📤"
        tip_ad = "Tahsilat Al" if is_tahsilat else "Tediye / Ödeme Yap"

        bant = QFrame()
        bant.setFixedHeight(56)
        bant.setStyleSheet("background:{};border-radius:10px;".format(renk))
        bant_lay = QHBoxLayout(bant); bant_lay.setContentsMargins(16, 0, 16, 0)
        bas = QLabel("{} {}".format(ikon, tip_ad))
        bas.setStyleSheet("color:white;font-size:16px;font-weight:bold;background:transparent;")
        bant_lay.addWidget(bas); bant_lay.addStretch()
        if self.firma_adi:
            lbl_f = QLabel(self.firma_adi)
            lbl_f.setStyleSheet("color:rgba(255,255,255,0.85);font-size:13px;"
                                "background:transparent;font-weight:bold;")
            bant_lay.addWidget(lbl_f)
        lay.addWidget(bant)

        # Form
        grid = QGridLayout(); grid.setSpacing(10); grid.setColumnStretch(1, 1)

        def lbl(t):
            l = QLabel(t)
            l.setStyleSheet("color:#7f8c8d;font-weight:bold;font-size:12px;")
            l.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            return l

        # Makbuz No (otomatik)
        self.txt_makbuz = _le("")
        self.txt_makbuz.setReadOnly(True)
        self.txt_makbuz.setStyleSheet(INP + "background:#f8f9fa;color:#7f8c8d;")
        grid.addWidget(lbl("Makbuz No:"),   0, 0); grid.addWidget(self.txt_makbuz, 0, 1)

        # Firma
        self.txt_firma = _le("Firma adı")
        grid.addWidget(lbl("Firma:"),        1, 0); grid.addWidget(self.txt_firma, 1, 1)

        # Tarih
        self.txt_tarih = _le(datetime.now().strftime("%d.%m.%Y"))
        self.txt_tarih.setText(datetime.now().strftime("%d.%m.%Y"))
        grid.addWidget(lbl("Tarih:"),        2, 0); grid.addWidget(self.txt_tarih, 2, 1)

        # Sipariş/Alım No
        self.txt_sip = _le("Sipariş no / Alım referansı")
        grid.addWidget(lbl("Referans No:"),  3, 0); grid.addWidget(self.txt_sip, 3, 1)

        # Toplam tutar (bilgi)
        self.lbl_toplam = QLabel("0,00 TL")
        self.lbl_toplam.setStyleSheet(
            "font-size:14px;font-weight:bold;color:{};".format(renk))
        grid.addWidget(lbl("Toplam Tutar:"), 4, 0); grid.addWidget(self.lbl_toplam, 4, 1)

        # Tahsil / Ödeme tutarı
        self.spn_tutar = QDoubleSpinBox()
        self.spn_tutar.setRange(0.01, 999_999_999)
        self.spn_tutar.setDecimals(2)
        self.spn_tutar.setSuffix(" TL")
        self.spn_tutar.setFixedHeight(40)
        self.spn_tutar.setStyleSheet(
            "font-size:16px;font-weight:bold;" + INP)
        self.spn_tutar.valueChanged.connect(self._kalan_guncelle)
        grid.addWidget(lbl("İşlem Tutarı *:"), 5, 0); grid.addWidget(self.spn_tutar, 5, 1)

        # Kalan göstergesi
        self.lbl_kalan = QLabel("Kalan: 0,00 TL")
        self.lbl_kalan.setStyleSheet("font-size:12px;color:#e74c3c;font-weight:bold;")
        grid.addWidget(lbl(""),              6, 0); grid.addWidget(self.lbl_kalan, 6, 1)

        # Ödeme şekli
        self.cmb_sekil = QComboBox()
        self.cmb_sekil.setFixedHeight(36)
        self.cmb_sekil.setStyleSheet(INP)
        for s in ["Nakit", "Havale / EFT", "Çek", "Kredi Kartı"]:
            self.cmb_sekil.addItem(s)
        grid.addWidget(lbl("Ödeme Şekli:"), 7, 0); grid.addWidget(self.cmb_sekil, 7, 1)

        # Açıklama
        self.txt_aciklama = QTextEdit()
        self.txt_aciklama.setPlaceholderText("Açıklama / not (isteğe bağlı)")
        self.txt_aciklama.setFixedHeight(60)
        self.txt_aciklama.setStyleSheet(INP)
        grid.addWidget(lbl("Açıklama:"),    8, 0); grid.addWidget(self.txt_aciklama, 8, 1)

        lay.addLayout(grid)
        lay.addWidget(_ayrac())

        # Makbuz seçenekleri
        makbuz_lay = QHBoxLayout()
        self.chk_pdf     = QCheckBox("PDF olarak kaydet")
        self.chk_yazici  = QCheckBox("Yazıcıya gönder")
        self.chk_pdf.setChecked(True)
        for chk in (self.chk_pdf, self.chk_yazici):
            chk.setStyleSheet("font-size:13px;color:#2c3e50;")
            makbuz_lay.addWidget(chk)
        makbuz_lay.addStretch()
        lay.addLayout(makbuz_lay)

        # Butonlar
        bh = QHBoxLayout(); bh.addStretch()
        bi = QPushButton("İptal"); bi.setFixedHeight(38)
        bi.setStyleSheet(BTN_GRAY); bi.clicked.connect(self.reject)
        islem_ad = "📥 Tahsilat Al" if is_tahsilat else "📤 Ödeme Yap"
        bk = QPushButton(islem_ad); bk.setFixedHeight(42)
        bk.setStyleSheet(
            "background:{};color:white;border-radius:8px;"
            "padding:6px 20px;font-weight:bold;font-size:14px;"
            "border:none;".format(renk))
        bk.clicked.connect(self._kaydet)
        bh.addWidget(bi); bh.addWidget(bk)
        lay.addLayout(bh)

    def _auto_doldur(self):
        """Dialog açılınca alanları otomatik doldur."""
        no = _otomatik_makbuz_no(self.cursor, self.tip)
        self.txt_makbuz.setText(no)
        if self.firma_adi:
            self.txt_firma.setText(self.firma_adi)
        if self.siparis_no:
            self.txt_sip.setText(self.siparis_no)
        if self.max_tutar > 0:
            self.lbl_toplam.setText("{:,.2f} TL".format(self.max_tutar))
            self.spn_tutar.setValue(self.max_tutar)
            self.lbl_kalan.setText("Kalan: 0,00 TL")

    def _kalan_guncelle(self, val):
        if self.max_tutar > 0:
            kalan = max(0.0, self.max_tutar - val)
            self.lbl_kalan.setText("Kalan: {:,.2f} TL".format(kalan))
            renk = "#e74c3c" if kalan > 0 else "#27ae60"
            self.lbl_kalan.setStyleSheet(
                "font-size:12px;color:{};font-weight:bold;".format(renk))

    # ── Kaydet ──────────────────────────────────────────────────
    def _kaydet(self):
        firma = self.txt_firma.text().strip()
        tutar = self.spn_tutar.value()
        if not firma:
            QMessageBox.warning(self, "Eksik", "Firma adı zorunlu!"); return
        if tutar <= 0:
            QMessageBox.warning(self, "Eksik", "Tutar sıfırdan büyük olmalı!"); return

        makbuz_no = self.txt_makbuz.text().strip()
        tarih     = self.txt_tarih.text().strip()
        sip_no    = self.txt_sip.text().strip()
        sekil     = self.cmb_sekil.currentText()
        aciklama  = self.txt_aciklama.toPlainText().strip()
        kalan     = max(0.0, self.max_tutar - tutar)

        try:
            # Makbuz kaydı
            self.cursor.execute("""
                INSERT INTO tediye_makbuzlari
                    (makbuz_no, tip, firma, tarih, tutar, kalan_tutar,
                     odeme_sekli, aciklama, siparis_no, satinalma_id, olusturan)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (makbuz_no, self.tip, firma, tarih, tutar, kalan,
                  sekil, aciklama, sip_no, self.satinalma_id, self.user))

            # Tahsilat → siparişi kapat (tam ödeme ise)
            if self.tip == "tahsilat" and sip_no:
                if kalan <= 0:
                    self.cursor.execute(
                        "UPDATE siparisler SET tahsil_edildi=1, odeme_sekli=? "
                        "WHERE sip_no=?", (sekil, sip_no))
                else:
                    # Kısmi — genel_toplam'dan tahsil tutarını düş
                    self.cursor.execute(
                        "UPDATE siparisler SET odeme_sekli=? WHERE sip_no=?",
                        (sekil, sip_no))

            # Tediye → satın alma kaydını kapat (tam ödeme ise)
            if self.tip == "tediye" and self.satinalma_id:
                if kalan <= 0:
                    self.cursor.execute(
                        "UPDATE satinalma_kayitlari SET odendi=1 WHERE id=?",
                        (self.satinalma_id,))

            self.conn.commit()
            log_yaz(self.cursor, self.conn, "MAKBUZ_OLUSTUR",
                    "{} | {} | {}".format(makbuz_no, firma, tutar))

        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e)); return

        # PDF
        pdf_tamam = False
        if self.chk_pdf.isChecked() or self.chk_yazici.isChecked():
            import os, tempfile
            pdf_klasor = os.path.join(os.path.expanduser("~"), "ArsacMakbuzlar")
            os.makedirs(pdf_klasor, exist_ok=True)
            self._pdf_yolu = os.path.join(pdf_klasor, makbuz_no + ".pdf")

            data = dict(
                makbuz_no=makbuz_no, tip=self.tip,
                firma=firma, tarih=tarih, tutar=tutar,
                kalan_tutar=kalan, odeme_sekli=sekil,
                aciklama=aciklama, siparis_no=sip_no,
                olusturan=self.user
            )
            pdf_tamam = makbuz_pdf_olustur(data, self._pdf_yolu)

            if pdf_tamam:
                # PDF yolunu DB'ye kaydet
                try:
                    self.cursor.execute(
                        "UPDATE tediye_makbuzlari SET pdf_yolu=? WHERE makbuz_no=?",
                        (self._pdf_yolu, makbuz_no))
                    self.conn.commit()
                except: pass

                if self.chk_pdf.isChecked():
                    try:
                        import subprocess, sys
                        if sys.platform == "win32":
                            os.startfile(self._pdf_yolu)
                        else:
                            subprocess.Popen(["xdg-open", self._pdf_yolu])
                    except: pass

                if self.chk_yazici.isChecked():
                    try:
                        import subprocess, sys
                        if sys.platform == "win32":
                            os.startfile(self._pdf_yolu, "print")
                        else:
                            subprocess.Popen(["lp", self._pdf_yolu])
                    except: pass

        # Başarı mesajı
        mesaj = "✅ {} başarıyla kaydedildi!\n\nMakbuz No: {}\nTutar: {:,.2f} TL".format(
            "Tahsilat" if self.tip == "tahsilat" else "Ödeme",
            makbuz_no, tutar)
        if pdf_tamam:
            mesaj += "\n\n📄 PDF: {}".format(self._pdf_yolu)
        QMessageBox.information(self, "Başarılı", mesaj)
        self.accept()


# ═══════════════════════════════════════════════════════════════
#  MAKBUZ GEÇMİŞİ DİALOGU  (firmaya ait tüm makbuzlar)
# ═══════════════════════════════════════════════════════════════
class MakbuzGecmisiDialog(QDialog):
    def __init__(self, cursor, conn, firma, parent=None):
        super().__init__(parent)
        self.cursor = cursor; self.conn = conn; self.firma = firma
        self.setWindowTitle("Makbuz Geçmişi — " + firma)
        self.setMinimumSize(700, 480)
        self.setStyleSheet(DIALOG_QSS)
        self._build()
        self._doldur()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(20, 16, 20, 16); lay.setSpacing(10)

        hdr = QHBoxLayout()
        hdr.addWidget(_baslik("📋  {}  — Makbuz Geçmişi".format(self.firma), C["koyu"], 14))
        hdr.addStretch()
        btn_kapat = QPushButton("Kapat"); btn_kapat.setFixedHeight(34)
        btn_kapat.setStyleSheet(BTN_GRAY); btn_kapat.clicked.connect(self.reject)
        hdr.addWidget(btn_kapat)
        lay.addLayout(hdr)

        self.tbl = _tablo(
            ["Makbuz No", "Tarih", "Tür", "Tutar (TL)", "Kalan (TL)",
             "Ödeme Şekli", "Referans No"], stretch_col=0)
        self.tbl.doubleClicked.connect(self._pdf_ac)
        lay.addWidget(self.tbl)

        self.lbl_toplam = QLabel("")
        self.lbl_toplam.setStyleSheet(
            "font-size:13px;font-weight:bold;color:#2c3e50;padding:4px;")
        lay.addWidget(self.lbl_toplam)

    def _doldur(self):
        self.tbl.setRowCount(0)
        try:
            self.cursor.execute("""
                SELECT makbuz_no, tarih, tip, tutar, kalan_tutar,
                       odeme_sekli, siparis_no, pdf_yolu
                FROM tediye_makbuzlari WHERE firma=? ORDER BY id DESC
            """, (self.firma,))
            rows = self.cursor.fetchall()
        except: rows = []

        toplam_tah = toplam_ted = 0.0
        for i, (mno, tarih, tip, tutar, kalan, sekil, sno, pdf) in enumerate(rows):
            self.tbl.insertRow(i)
            tur_ad   = "📥 Tahsilat" if tip == "tahsilat" else "📤 Tediye"
            tur_renk = C["yesil"] if tip == "tahsilat" else C["kirmizi"]
            kalan_r  = C["kirmizi"] if float(kalan or 0) > 0 else C["yesil"]

            self.tbl.setItem(i, 0, _item(mno or "-", bold=True))
            self.tbl.setItem(i, 1, _item(tarih or "-"))
            self.tbl.setItem(i, 2, _item(tur_ad, fg=tur_renk, bold=True))
            self.tbl.setItem(i, 3, _item("{:,.2f}".format(float(tutar or 0))))
            self.tbl.setItem(i, 4, _item(
                "{:,.2f}".format(float(kalan or 0)), fg=kalan_r))
            self.tbl.setItem(i, 5, _item(sekil or "-"))
            self.tbl.setItem(i, 6, _item(sno or "-"))

            # PDF yolunu UserRole'a sakla
            it = self.tbl.item(i, 0)
            if it: it.setData(Qt.UserRole, pdf)

            if tip == "tahsilat": toplam_tah += float(tutar or 0)
            else: toplam_ted += float(tutar or 0)

        self.lbl_toplam.setText(
            "  Toplam Tahsilat: {:,.2f} TL   |   Toplam Tediye: {:,.2f} TL".format(
                toplam_tah, toplam_ted))

    def _pdf_ac(self, idx):
        it = self.tbl.item(idx.row(), 0)
        if not it: return
        pdf = it.data(Qt.UserRole)
        if not pdf:
            QMessageBox.information(self, "PDF", "Bu makbuz için PDF bulunamadı."); return
        import os, subprocess, sys
        if not os.path.exists(pdf):
            QMessageBox.warning(self, "Bulunamadı", "PDF dosyası bulunamadı:\n" + pdf); return
        try:
            if sys.platform == "win32": os.startfile(pdf)
            else: subprocess.Popen(["xdg-open", pdf])
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
