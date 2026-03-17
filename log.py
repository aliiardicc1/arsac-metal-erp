"""
Arsac Metal ERP — Merkezi Log Sistemi
Her önemli işlemi kullanıcı adıyla kaydeder.
"""
from datetime import datetime

# Aktif kullanıcıyı global tut
_aktif_kullanici = "sistem"

def kullanici_ayarla(ad):
    global _aktif_kullanici
    _aktif_kullanici = ad

def kullanici_al():
    return _aktif_kullanici

def log_yaz(cursor, conn, islem, detay=""):
    """Kullanici_log tablosuna kayıt yazar."""
    try:
        cursor.execute(
            "INSERT INTO kullanici_log (kullanici, islem, detay, tarih) VALUES (?,?,?,?)",
            (_aktif_kullanici, islem, detay, datetime.now().strftime('%d.%m.%Y %H:%M:%S'))
        )
        conn.commit()
    except Exception as e:
        print(f"Log yazma hatası: {e}")


# ─────────────────────────────────────────────
#  LOG GEÇMİŞİ EKRANI
# ─────────────────────────────────────────────
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

class LogGecmisiDialog(QDialog):
    def __init__(self, cursor, parent=None):
        super().__init__(parent)
        self.cursor = cursor
        self.setWindowTitle("📋 İşlem Geçmişi")
        self.setMinimumSize(800, 500)
        self.setStyleSheet("""
            QDialog { background: #f4f6f9; }
            QTableWidget { background: white; border-radius: 8px; border: 1px solid #dcdde1; font-size: 13px; }
            QHeaderView::section { background: #2c3e50; color: white; padding: 8px; font-weight: bold; border: none; }
            QLabel { font-size: 13px; font-weight: bold; color: #2c3e50; }
            QComboBox, QLineEdit { border: 1.5px solid #dcdde1; border-radius: 6px; padding: 6px 12px; font-size: 13px; background: white; }
        """)
        self.init_ui()

    def init_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(15, 15, 15, 15)
        lay.setSpacing(10)

        # Filtre satırı
        filtre = QHBoxLayout()
        filtre.addWidget(QLabel("Kullanıcı:"))
        self.cmb_kullanici = QComboBox()
        self.cmb_kullanici.addItem("Tümü")
        try:
            self.cursor.execute("SELECT DISTINCT kullanici FROM kullanici_log ORDER BY kullanici")
            for row in self.cursor.fetchall():
                self.cmb_kullanici.addItem(row[0])
        except: pass
        self.cmb_kullanici.currentTextChanged.connect(self.yenile)
        filtre.addWidget(self.cmb_kullanici)

        filtre.addWidget(QLabel("Ara:"))
        self.txt_ara = QLineEdit()
        self.txt_ara.setPlaceholderText("İşlem veya detayda ara...")
        self.txt_ara.setFixedWidth(200)
        self.txt_ara.textChanged.connect(self.yenile)
        filtre.addWidget(self.txt_ara)
        filtre.addStretch()

        lbl_toplam = QLabel()
        lbl_toplam.setObjectName("lbl_toplam")
        lbl_toplam.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        filtre.addWidget(lbl_toplam)
        lay.addLayout(filtre)

        self.tablo = QTableWidget(0, 4)
        self.tablo.setHorizontalHeaderLabels(["Tarih / Saat", "Kullanıcı", "İşlem", "Detay"])
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tablo.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tablo.verticalHeader().setVisible(False)
        self.tablo.setAlternatingRowColors(True)
        lay.addWidget(self.tablo)

        btn_kapat = QPushButton("Kapat")
        btn_kapat.setStyleSheet("background: #dcdde1; color: #2c3e50; border-radius: 6px; padding: 10px 24px; font-weight: bold;")
        btn_kapat.clicked.connect(self.accept)
        h = QHBoxLayout()
        h.addStretch()
        h.addWidget(btn_kapat)
        lay.addLayout(h)

        self.yenile()

    def yenile(self):
        try:
            kullanici = self.cmb_kullanici.currentText()
            ara = self.txt_ara.text().strip()

            sorgu = "SELECT tarih, kullanici, islem, detay FROM kullanici_log WHERE 1=1"
            params = []
            if kullanici != "Tümü":
                sorgu += " AND kullanici=?"
                params.append(kullanici)
            if ara:
                sorgu += " AND (islem LIKE ? OR detay LIKE ?)"
                params += [f"%{ara}%", f"%{ara}%"]
            sorgu += " ORDER BY id DESC LIMIT 500"

            self.cursor.execute(sorgu, params)
            rows = self.cursor.fetchall()
            self.tablo.setRowCount(0)

            renk_map = {
                "TALEP": "#eaf4fb", "STOK": "#eafaf1", "SIPARIS": "#fef9e7",
                "TEKLIF": "#f5eef8", "ODEME": "#eafaf1", "SILME": "#fde8e8",
            }

            for i, row in enumerate(rows):
                self.tablo.insertRow(i)
                for j, val in enumerate(row):
                    item = QTableWidgetItem(str(val or ""))
                    item.setTextAlignment(Qt.AlignCenter if j < 3 else Qt.AlignLeft | Qt.AlignVCenter)
                    # İşlem tipine göre renk
                    for anahtar, renk in renk_map.items():
                        if anahtar in str(row[2]).upper():
                            from PyQt5.QtGui import QColor
                            item.setBackground(QColor(renk))
                            break
                    self.tablo.setItem(i, j, item)

            # Toplam güncelle
            lbl = self.findChild(QLabel, "lbl_toplam")
            if lbl:
                lbl.setText(f"{len(rows)} kayıt")
        except Exception as e:
            print(f"Log geçmişi hatası: {e}")