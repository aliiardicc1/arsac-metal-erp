"""
Arsac Metal ERP — Merkezi Stil Dosyası
Tüm sayfalarda tutarlı görünüm sağlar.
"""

# ── Uygulama geneli QSS — main.py'de app.setStyleSheet(APP_QSS) ile kullan ──
APP_QSS = """
/* ── Nav butonları — global QPushButton kuralını override eder ── */
QPushButton#NavButton {
    background: white;
    color: #2c3e50;
    border: 1px solid #dcdde1;
    border-radius: 4px;
    font-weight: bold;
    font-size: 12px;
    padding: 4px 10px;
    min-width: 0px;
    min-height: 0px;
}
QPushButton#NavButton:hover {
    background: #f0f2f5;
}
QPushButton#NavButton:checked {
    background: #c0392b;
    color: white;
    border: none;
}

/* ── Genel ── */
QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    color: #2c3e50;
}

/* ── Input alanları ── */
QLineEdit, QTextEdit, QPlainTextEdit {
    color: #2c3e50;
    background: white;
    border: 1.5px solid #dcdde1;
    border-radius: 7px;
    padding: 5px 10px;
    min-height: 28px;
    selection-background-color: #2980b9;
    selection-color: white;
}
QLineEdit:focus, QTextEdit:focus {
    border: 1.5px solid #2980b9;
}
QLineEdit:read-only {
    background: #f4f6f9;
    color: #7f8c8d;
}
QLineEdit:disabled, QTextEdit:disabled {
    background: #f4f6f9;
    color: #95a5a6;
}

/* ── SpinBox ── */
QSpinBox, QDoubleSpinBox {
    color: #2c3e50;
    background: white;
    border: 1.5px solid #dcdde1;
    border-radius: 7px;
    padding: 4px 8px;
    min-height: 28px;
}
QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1.5px solid #2980b9;
}

/* ── ComboBox ── */
QComboBox {
    color: #2c3e50;
    background: white;
    border: 1.5px solid #dcdde1;
    border-radius: 7px;
    padding: 5px 10px;
    min-height: 28px;
}
QComboBox:focus {
    border: 1.5px solid #2980b9;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    color: #2c3e50;
    background: white;
    selection-background-color: #2980b9;
    selection-color: white;
    border: 1px solid #dcdde1;
    padding: 4px;
}

/* ── DateEdit ── */
QDateEdit {
    color: #2c3e50;
    background: white;
    border: 1.5px solid #dcdde1;
    border-radius: 7px;
    padding: 5px 10px;
    min-height: 28px;
}
QDateEdit:focus {
    border: 1.5px solid #2980b9;
}

/* ── Butonlar ── */
QPushButton {
    font-size: 13px;
    font-weight: bold;
    border-radius: 8px;
    padding: 6px 16px;
    min-height: 32px;
    min-width: 70px;
    border: none;
}
QPushButton:disabled {
    background: #dcdde1;
    color: #95a5a6;
}

/* ── Tablo ── */
QTableWidget, QTableView {
    color: #2c3e50;
    background: white;
    gridline-color: #f0f2f5;
    border: 1px solid #dcdde1;
    border-radius: 8px;
    font-size: 13px;
    selection-background-color: #2980b9;
    selection-color: white;
    alternate-background-color: #f8f9fa;
}
QTableWidget::item, QTableView::item {
    color: #2c3e50;
    padding: 4px 8px;
    min-height: 32px;
    border-bottom: 1px solid #f0f2f5;
}
QTableWidget::item:selected, QTableView::item:selected {
    background: #2980b9;
    color: white;
}
QTableWidget::item:selected:!active, QTableView::item:selected:!active {
    background: #5dade2;
    color: white;
}
QTableWidget::item:hover, QTableView::item:hover {
    background: #eaf4fb;
    color: #2c3e50;
}
QHeaderView {
    background: #2c3e50;
}
QHeaderView::section {
    background: #2c3e50;
    color: white;
    padding: 8px 8px;
    font-weight: bold;
    font-size: 12px;
    border: none;
    border-right: 1px solid #3d5166;
    min-height: 36px;
}
QHeaderView::section:last {
    border-right: none;
}
QHeaderView::section:hover {
    background: #34495e;
}
QTableWidget QLineEdit {
    color: #2c3e50;
    background: white;
    border: 1.5px solid #2980b9;
    border-radius: 4px;
    padding: 2px 6px;
}
QTableCornerButton::section {
    background: #2c3e50;
    border: none;
}

/* ── Label (badge dahil) ── */
QLabel {
    color: #2c3e50;
    background: transparent;
}

/* ── ListWidget ── */
QListWidget {
    color: #2c3e50;
    background: white;
    border: 1px solid #dcdde1;
    border-radius: 8px;
    outline: none;
}
QListWidget::item {
    color: #2c3e50;
    padding: 8px 12px;
    border-bottom: 1px solid #f0f2f5;
}
QListWidget::item:selected {
    background: #2980b9;
    color: white;
}

/* ── GroupBox ── */
QGroupBox {
    background: white;
    border: 1px solid #dcdde1;
    border-radius: 10px;
    margin-top: 10px;
    padding: 12px 8px 8px 8px;
    font-size: 13px;
    font-weight: bold;
    color: #2c3e50;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #c0392b;
    font-weight: bold;
}

/* ── TabWidget ── */
QTabWidget::pane {
    border: 1px solid #dcdde1;
    border-radius: 8px;
    background: white;
}
QTabBar::tab {
    background: #ecf0f1;
    color: #2c3e50;
    padding: 8px 14px;
    border-radius: 6px 6px 0 0;
    font-weight: bold;
    font-size: 12px;
    min-width: 0px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #c0392b;
    color: white;
}
QTabBar::tab:hover:!selected {
    background: #d5d8dc;
}

/* ── ScrollBar ── */
QScrollBar:vertical {
    border: none;
    background: #f0f0f0;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #bdc3c7;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #95a5a6;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical { height: 0; }

/* ── Dialog ve MessageBox ── */
QDialog {
    background: #f4f6f9;
}
QMessageBox QLabel {
    color: #2c3e50;
    font-size: 13px;
}
QInputDialog QLineEdit {
    color: #2c3e50;
    background: white;
}
"""

RENKLER = {
    "primary":    "#c0392b",
    "blue":       "#2980b9",
    "green":      "#27ae60",
    "orange":     "#e67e22",
    "purple":     "#8e44ad",
    "dark":       "#2c3e50",
    "gray":       "#7f8c8d",
    "light_gray": "#dcdde1",
    "bg":         "#f4f6f9",
    "white":      "#ffffff",
    "text":       "#2c3e50",
    "text_light": "#7f8c8d",
}

# ── Input / Form elemanları ──────────────────────────────────
INPUT = (
    "border: 1.5px solid #dcdde1;"
    "border-radius: 7px;"
    "padding: 6px 10px;"
    "font-size: 13px;"
    "background: white;"
    "color: #2c3e50;"        # ← yazı rengi — her zaman koyu
    "selection-background-color: #2980b9;"
    "selection-color: white;"
)

INPUT_FOCUS = (
    "border: 1.5px solid #2980b9;"
    "border-radius: 7px;"
    "padding: 6px 10px;"
    "font-size: 13px;"
    "background: white;"
    "color: #2c3e50;"
    "selection-background-color: #2980b9;"
    "selection-color: white;"
)

# QSS bloğu — widget setStyleSheet ile kullan
INPUT_QSS = """
    QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit {
        border: 1.5px solid #dcdde1;
        border-radius: 7px;
        padding: 6px 10px;
        font-size: 13px;
        background: white;
        color: #2c3e50;
        selection-background-color: #2980b9;
        selection-color: white;
    }
    QLineEdit:focus, QTextEdit:focus, QSpinBox:focus,
    QDoubleSpinBox:focus, QDateEdit:focus {
        border: 1.5px solid #2980b9;
    }
    QLineEdit:disabled, QTextEdit:disabled {
        background: #f4f6f9;
        color: #95a5a6;
    }
    QLineEdit[readOnly="true"] {
        background: #f4f6f9;
        color: #7f8c8d;
    }
    QComboBox {
        border: 1.5px solid #dcdde1;
        border-radius: 7px;
        padding: 5px 10px;
        font-size: 13px;
        background: white;
        color: #2c3e50;
        min-height: 28px;
    }
    QComboBox:focus {
        border: 1.5px solid #2980b9;
    }
    QComboBox::drop-down {
        border: none;
        width: 24px;
    }
    QComboBox QAbstractItemView {
        background: white;
        color: #2c3e50;
        selection-background-color: #2980b9;
        selection-color: white;
        border: 1px solid #dcdde1;
        border-radius: 4px;
        padding: 4px;
    }
"""

# ── Tablo ────────────────────────────────────────────────────
TABLO_QSS = """
    QTableWidget {
        background: white;
        border-radius: 10px;
        border: 1px solid #dcdde1;
        color: #2c3e50;
        gridline-color: transparent;
        font-size: 13px;
    }
    QTableWidget::item {
        color: #2c3e50;
        padding: 6px 8px;
        border-bottom: 1px solid #f0f2f5;
    }
    QTableWidget::item:selected {
        background: #2980b9;
        color: white;
    }
    QTableWidget::item:alternate {
        background: #f8f9fa;
    }
    QHeaderView::section {
        background: #2c3e50;
        color: white;
        padding: 8px 10px;
        font-weight: bold;
        font-size: 12px;
        border: none;
        border-right: 1px solid #3d5166;
    }
    QHeaderView::section:last {
        border-right: none;
    }
    QTableCornerButton::section {
        background: #2c3e50;
        border: none;
    }
"""

# ── Butonlar ─────────────────────────────────────────────────
def btn_stl(renk, text_renk="white", min_w=80):
    return (
        "QPushButton {{"
        "  background: " + renk + ";"
        "  color: " + text_renk + ";"
        "  border-radius: 8px;"
        "  padding: 7px 16px;"
        "  font-weight: bold;"
        "  font-size: 13px;"
        "  border: none;"
        "  min-width: " + str(min_w) + "px;"
        "}}"
        "QPushButton:hover {{"
        "  background: " + _karistir(renk, 15) + ";"
        "}}"
        "QPushButton:pressed {{"
        "  background: " + _karistir(renk, 30) + ";"
        "}}"
        "QPushButton:disabled {{"
        "  background: #dcdde1;"
        "  color: #95a5a6;"
        "}}"
    )

def _karistir(hex_renk, miktar):
    """Rengi biraz koyulaştır."""
    try:
        h = hex_renk.lstrip("#")
        r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        r = max(0, r - miktar)
        g = max(0, g - miktar)
        b = max(0, b - miktar)
        return "#{:02x}{:02x}{:02x}".format(r, g, b)
    except:
        return hex_renk

# Hazır buton stilleri
BTN_PRIMARY = btn_stl("#c0392b")
BTN_BLUE    = btn_stl("#2980b9")
BTN_GREEN   = btn_stl("#27ae60")
BTN_ORANGE  = btn_stl("#e67e22")
BTN_PURPLE  = btn_stl("#8e44ad")
BTN_GRAY    = btn_stl("#dcdde1", "#2c3e50")
BTN_DARK    = btn_stl("#2c3e50")

# ── Sekmeler ─────────────────────────────────────────────────
def tab_qss(secili_renk="#c0392b"):
    return """
        QTabWidget::pane {{
            border: 1px solid #dcdde1;
            border-radius: 10px;
            background: white;
        }}
        QTabBar::tab {{
            background: #ecf0f1;
            color: #2c3e50;
            padding: 8px 14px;
            border-radius: 6px 6px 0 0;
            font-weight: bold;
            font-size: 12px;
            margin-right: 2px;
            min-width: 0px;
        }}
        QTabBar::tab:selected {{
            background: {r};
            color: white;
        }}
        QTabBar::tab:hover:!selected {{
            background: #d5d8dc;
        }}
    """.format(r=secili_renk)

# ── GroupBox ──────────────────────────────────────────────────
GROUPBOX_QSS = """
    QGroupBox {
        background: white;
        border-radius: 10px;
        border: 1px solid #dcdde1;
        margin-top: 10px;
        padding: 14px 10px 10px 10px;
        font-size: 13px;
        color: #2c3e50;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 8px;
        color: #c0392b;
        font-weight: bold;
        font-size: 13px;
    }
"""

# ── Ana sayfa arka planı ─────────────────────────────────────
SAYFA_QSS = """
    QWidget {
        background: #f4f6f9;
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 13px;
        color: #2c3e50;
    }
    QLabel {
        color: #2c3e50;
        background: transparent;
    }
    QScrollBar:vertical {
        border: none;
        background: #f0f0f0;
        width: 8px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical {
        background: #bdc3c7;
        border-radius: 4px;
        min-height: 30px;
    }
    QScrollBar::handle:vertical:hover {
        background: #95a5a6;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
"""

# ── Dialog ───────────────────────────────────────────────────
DIALOG_QSS = SAYFA_QSS + INPUT_QSS + GROUPBOX_QSS

# ── Kart widget'ı ────────────────────────────────────────────
KART_QSS = """
    QFrame {{
        background: white;
        border-radius: 10px;
        border: 1px solid #dcdde1;
        border-left: 5px solid {renk};
    }}
"""

# ── Liste widget ─────────────────────────────────────────────
LIST_QSS = """
    QListWidget {
        background: white;
        border-radius: 10px;
        border: 1px solid #dcdde1;
        color: #2c3e50;
        font-size: 13px;
        outline: none;
    }
    QListWidget::item {
        padding: 10px 12px;
        border-bottom: 1px solid #f0f2f5;
        color: #2c3e50;
    }
    QListWidget::item:selected {
        background: #2980b9;
        color: white;
        border-radius: 4px;
    }
    QListWidget::item:hover {
        background: #eaf4fb;
    }
"""


# ── Durum renkleri — tüm modüller aynı renk setini kullanır ──
DURUM_RENK = {
    "Alindi":       ("#f39c12", "#fef9e7"),
    "Uretimde":     ("#2980b9", "#eaf4fb"),
    "Hazir":        ("#8e44ad", "#f5eef8"),
    "Sevk Edildi":  ("#27ae60", "#eafaf1"),
    "Tamamlandi":   ("#27ae60", "#eafaf1"),
    "Beklemede":    ("#f39c12", "#fef9e7"),
    "Iptal":        ("#e74c3c", "#fde8e8"),
    "Faturalandı":  ("#2c3e50", "#eaecee"),
    "Bekliyor":     ("#f39c12", "#fef9e7"),
    "Yolda":        ("#e67e22", "#fef5ec"),
    "Teslim Edildi":("#27ae60", "#eafaf1"),
}


def make_badge(durum, min_w=None):
    """
    Durum badge'i oluştur — tüm modüller bu fonksiyonu kullanır.
    min_w belirtilmezse metin uzunluğuna göre otomatik ayarlanır.
    """
    from PyQt5.QtWidgets import QLabel
    from PyQt5.QtCore import Qt
    fc, bg = DURUM_RENK.get(durum, ("#7f8c8d", "#f4f6f9"))
    lbl = QLabel("  {}  ".format(durum))
    lbl.setAlignment(Qt.AlignCenter)
    # Otomatik genişlik: karakter sayısı * 9, en az 90px
    auto_w = max(90, len(durum) * 9 + 24)
    lbl.setMinimumWidth(min_w if min_w else auto_w)
    lbl.setFixedHeight(26)
    lbl.setStyleSheet(
        "color:{fc};background:{bg};font-weight:bold;font-size:12px;"
        "border-radius:6px;border:1px solid {fc};padding:0 6px;".format(fc=fc, bg=bg))
    return lbl


def _darken(hex_renk, miktar=20):
    """Rengi biraz koyulaştır — hover efekti için."""
    try:
        h = hex_renk.lstrip("#")
        r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        return "#{:02x}{:02x}{:02x}".format(
            max(0,r-miktar), max(0,g-miktar), max(0,b-miktar))
    except:
        return hex_renk


def make_buton(txt, renk, text_renk="white", h=34, min_w=None):
    """
    Standart buton oluştur — yazı her zaman sığar.
    """
    from PyQt5.QtWidgets import QPushButton
    auto_w = max(70, len(txt) * 9 + 24) if min_w is None else min_w
    btn = QPushButton(txt)
    btn.setFixedHeight(h)
    btn.setMinimumWidth(auto_w)
    btn.setStyleSheet(
        "QPushButton{{background:{r};color:{t};border-radius:8px;"
        "padding:5px 14px;font-weight:bold;font-size:13px;border:none;}}"
        "QPushButton:hover{{background:{d};}}"
        "QPushButton:disabled{{background:#dcdde1;color:#95a5a6;}}".format(
            r=renk, t=text_renk, d=_darken(renk)))
    return btn


def tablo_sutun_ayarla(tablo, stretch_col=0, min_genislikler=None):
    """
    Tablo sütun genişliklerini akıllıca ayarla.
    stretch_col: genişleyecek sütun (varsayılan 0)
    min_genislikler: {sutun_no: min_px} dict — belirtilmezse otomatik
    """
    from PyQt5.QtWidgets import QHeaderView
    h = tablo.horizontalHeader()
    for c in range(tablo.columnCount()):
        if c == stretch_col:
            h.setSectionResizeMode(c, QHeaderView.Stretch)
        else:
            h.setSectionResizeMode(c, QHeaderView.ResizeToContents)
            if min_genislikler and c in min_genislikler:
                tablo.setColumnWidth(c, max(
                    min_genislikler[c],
                    tablo.columnWidth(c)))


def tablo_hazirla(tablo, stretch_col=0, min_genislikler=None,
                  coklu_secim=True, satir_yuksekligi=34):
    """
    Tablo için tüm standart ayarları tek seferde uygular.
    Tüm modüllerde tutarlı görünüm sağlar.

    Kullanım:
        from styles import tablo_hazirla
        tablo_hazirla(self.tablo, stretch_col=2)
    """
    from PyQt5.QtWidgets import QHeaderView, QAbstractItemView
    from PyQt5.QtCore import Qt

    # Genel tablo ayarları
    tablo.setAlternatingRowColors(True)
    tablo.setShowGrid(True)
    tablo.setWordWrap(False)
    tablo.verticalHeader().setVisible(False)
    tablo.setSelectionBehavior(QAbstractItemView.SelectRows)
    tablo.verticalHeader().setDefaultSectionSize(satir_yuksekligi)

    # Çoklu / tekli seçim
    if coklu_secim:
        tablo.setSelectionMode(QAbstractItemView.ExtendedSelection)
    else:
        tablo.setSelectionMode(QAbstractItemView.SingleSelection)

    # Sütun genişlikleri
    h = tablo.horizontalHeader()
    h.setStretchLastSection(False)
    h.setHighlightSections(False)
    for c in range(tablo.columnCount()):
        if c == stretch_col:
            h.setSectionResizeMode(c, QHeaderView.Stretch)
        else:
            h.setSectionResizeMode(c, QHeaderView.ResizeToContents)
            if min_genislikler and c in min_genislikler:
                tablo.setColumnWidth(c, max(
                    min_genislikler[c],
                    tablo.columnWidth(c)))


# ── Sağ tık menüsü — tüm tablolara eklenebilir ───────────────
def tablo_sag_tik_menu_ekle(tablo):
    """
    QTableWidget'a sağ tık menüsü ekler.
    Kopyala, Yapıştır, Sil, Tümünü Seç destekler.
    """
    from PyQt5.QtWidgets import QMenu, QAction, QApplication
    from PyQt5.QtCore import Qt

    tablo.setContextMenuPolicy(Qt.CustomContextMenu)

    def _menu_goster(pos):
        menu = QMenu(tablo)
        menu.setStyleSheet("""
            QMenu {
                background: white;
                border: 1px solid #dcdde1;
                border-radius: 6px;
                padding: 4px;
                font-size: 13px;
                color: #2c3e50;
            }
            QMenu::item {
                padding: 7px 28px 7px 14px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: #2980b9;
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background: #dcdde1;
                margin: 4px 8px;
            }
        """)

        akt_item = tablo.itemAt(pos)

        act_kopyala = QAction("📋  Kopyala", tablo)
        act_kopyala.setShortcut("Ctrl+C")
        act_yapistir = QAction("📌  Yapıştır", tablo)
        act_yapistir.setShortcut("Ctrl+V")
        act_sil = QAction("🗑  Seçili hücreleri temizle", tablo)
        act_sil.setShortcut("Delete")
        act_tumunu_sec = QAction("☑  Tümünü Seç", tablo)
        act_tumunu_sec.setShortcut("Ctrl+A")

        # Kopyala
        def _kopyala():
            secili = tablo.selectedItems()
            if not secili: return
            satirlar = {}
            for it in secili:
                satirlar.setdefault(it.row(), {})[it.column()] = it.text()
            satirlar_s = sorted(satirlar.items())
            satirlar_list = []
            for r, cols in satirlar_s:
                satirlar_list.append("\t".join(
                    cols.get(c, "") for c in sorted(cols)))
            QApplication.clipboard().setText("\n".join(satirlar_list))

        # Yapıştır
        def _yapistir():
            clip = QApplication.clipboard().text()
            if not clip: return
            cur = tablo.currentIndex()
            if not cur.isValid(): return
            bas_r, bas_c = cur.row(), cur.column()
            for ri, satir in enumerate(clip.split("\n")):
                for ci, deger in enumerate(satir.split("\t")):
                    r, c = bas_r + ri, bas_c + ci
                    if r < tablo.rowCount() and c < tablo.columnCount():
                        it = tablo.item(r, c)
                        if it and (it.flags() & Qt.ItemIsEditable):
                            it.setText(deger)

        # Sil
        def _sil():
            for it in tablo.selectedItems():
                if it and (it.flags() & Qt.ItemIsEditable):
                    it.setText("")

        act_kopyala.triggered.connect(_kopyala)
        act_yapistir.triggered.connect(_yapistir)
        act_sil.triggered.connect(_sil)
        act_tumunu_sec.triggered.connect(tablo.selectAll)

        menu.addAction(act_kopyala)
        menu.addAction(act_yapistir)
        menu.addSeparator()
        menu.addAction(act_sil)
        menu.addSeparator()
        menu.addAction(act_tumunu_sec)

        menu.exec_(tablo.viewport().mapToGlobal(pos))

    tablo.customContextMenuRequested.connect(_menu_goster)
