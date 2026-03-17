from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from datetime import datetime
try:
    from log import log_yaz, kullanici_al
except:
    def log_yaz(c,n,i,d=""): pass
    def kullanici_al(): return "sistem"


class HammaddeSayfasi(QWidget):
    def __init__(self, cursor, conn, callback, user_role):
        super().__init__()
        self.cursor, self.conn, self.callback, self.user_role = cursor, conn, callback, user_role
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QLabel { font-size: 14px; font-weight: bold; color: #2c3e50; }
            QLineEdit { padding: 10px; border: 2px solid #bdc3c7; border-radius: 5px; background: white; color: black; }
            QLineEdit:focus { border: 2px solid #c0392b; }
            QPushButton { background-color: #c0392b; color: white; font-weight: bold; padding: 12px; border-radius: 5px; }
            QPushButton:hover { background-color: #a93226; }
            QTableWidget { background: white; border-radius: 8px; border: 1px solid #dcdde1; font-size: 13px; }
            QHeaderView::section { background-color: #2c3e50; color: white; padding: 10px; font-weight: bold; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        # Başlık + yardım butonu
        ust = QHBoxLayout()
        ust.addWidget(QLabel("🏗️ YENİ HAMMADDE TALEBİ"))
        ust.addStretch()
        btn_yardim = QPushButton("❓")
        btn_yardim.setFixedSize(32, 32)
        btn_yardim.setStyleSheet("background:#2980b9;color:white;border-radius:16px;font-weight:bold;font-size:14px;padding:0;")
        btn_yardim.setToolTip("Yardım")
        btn_yardim.clicked.connect(self._yardim)
        ust.addWidget(btn_yardim)
        layout.addLayout(ust)

        # Bilgi bandı
        bilgi = QLabel("💡  Üretimde ihtiyaç duyulan hammadde taleplerini buradan girin. Satın alma ekibi taleplerinizi görecek ve sipariş verecektir.")
        bilgi.setWordWrap(True)
        bilgi.setStyleSheet("background:#eaf4fb;border:1px solid #3498db;border-radius:6px;padding:8px 12px;font-size:12px;color:#2980b9;font-weight:normal;")
        layout.addWidget(bilgi)

        # Form
        form_frame = QFrame()
        form_frame.setStyleSheet("background: white; border-radius: 10px; border: 1px solid #dcdde1; padding: 10px;")
        grid = QGridLayout(form_frame)
        grid.setSpacing(10)

        grid.addWidget(QLabel("MALZEME / KALİTE: *"), 0, 0)
        self.txt_kalite = QLineEdit()
        self.txt_kalite.setPlaceholderText("Örn: St37, S235, DD11...")
        self.txt_kalite.textChanged.connect(lambda: self._alan_kontrol(self.txt_kalite))
        grid.addWidget(self.txt_kalite, 0, 1, 1, 3)

        grid.addWidget(QLabel("EN (mm): *"), 1, 0)
        self.txt_en = QLineEdit()
        self.txt_en.setPlaceholderText("Örn: 1500")
        self.txt_en.textChanged.connect(self.kg_hesapla)
        self.txt_en.textChanged.connect(lambda: self._alan_kontrol(self.txt_en, sayisal=True))
        grid.addWidget(self.txt_en, 1, 1)

        grid.addWidget(QLabel("BOY (mm): *"), 1, 2)
        self.txt_boy = QLineEdit()
        self.txt_boy.setPlaceholderText("Örn: 6000")
        self.txt_boy.textChanged.connect(self.kg_hesapla)
        self.txt_boy.textChanged.connect(lambda: self._alan_kontrol(self.txt_boy, sayisal=True))
        grid.addWidget(self.txt_boy, 1, 3)

        grid.addWidget(QLabel("KALINLIK (mm): *"), 2, 0)
        self.txt_kal = QLineEdit()
        self.txt_kal.setPlaceholderText("Örn: 3")
        self.txt_kal.textChanged.connect(self.kg_hesapla)
        self.txt_kal.textChanged.connect(lambda: self._alan_kontrol(self.txt_kal, sayisal=True))
        grid.addWidget(self.txt_kal, 2, 1)

        grid.addWidget(QLabel("ADET:"), 2, 2)
        self.txt_adet = QLineEdit("1")
        self.txt_adet.setPlaceholderText("Kaç adet?")
        self.txt_adet.textChanged.connect(self.kg_hesapla)
        grid.addWidget(self.txt_adet, 2, 3)

        grid.addWidget(QLabel("TOPLAM AĞIRLIK (KG):"), 3, 0)
        self.txt_kg = QLineEdit()
        self.txt_kg.setPlaceholderText("Otomatik hesaplanır")
        self.txt_kg.setReadOnly(True)
        self.txt_kg.setStyleSheet("background:#eaf4fb;border:2px solid #3498db;color:#2980b9;font-weight:bold;font-size:15px;padding:10px;border-radius:5px;")
        grid.addWidget(self.txt_kg, 3, 1, 1, 3)

        lbl_f = QLabel("📐 Formül: En × Boy × Kalınlık × 7.85 / 1.000.000")
        lbl_f.setStyleSheet("font-size:11px;color:#7f8c8d;font-weight:normal;")
        grid.addWidget(lbl_f, 4, 0, 1, 4)

        layout.addWidget(form_frame)

        # Talep sil butonu (sadece admin)
        btn_row = QHBoxLayout()
        self.btn_kaydet = QPushButton("📥 TALEBİ KAYDET")
        self.btn_kaydet.clicked.connect(self.kaydet)
        btn_row.addWidget(self.btn_kaydet)

        if self.user_role == "yonetici":
            self.btn_sil = QPushButton("🗑️ SEÇİLİ TALEBİ SİL")
            self.btn_sil.setStyleSheet("background:#e74c3c;color:white;font-weight:bold;padding:12px;border-radius:5px;")
            self.btn_sil.clicked.connect(self.talep_sil)
            btn_row.addWidget(self.btn_sil)
        layout.addLayout(btn_row)

        layout.addWidget(QLabel("📋 Bekleyen Talepler:"))
        self.tablo = QTableWidget(0, 7)
        self.tablo.setHorizontalHeaderLabels(["ID","Kalite","En (mm)","Boy (mm)","Kalınlık (mm)","KG","Tarih"])
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tablo.setAlternatingRowColors(True)
        self.tablo.verticalHeader().setVisible(False)
        layout.addWidget(self.tablo)
        self.yenile()

    def _alan_kontrol(self, widget, sayisal=False):
        """Boş veya hatalı alanlara kırmızı border."""
        metin = widget.text().strip()
        hata = False
        if not metin:
            hata = True
        elif sayisal:
            try:
                v = float(metin.replace(',','.'))
                if v <= 0: hata = True
            except:
                hata = True
        if hata:
            widget.setStyleSheet("padding:10px;border:2px solid #e74c3c;border-radius:5px;background:#fde8e8;color:black;")
        else:
            widget.setStyleSheet("padding:10px;border:2px solid #27ae60;border-radius:5px;background:white;color:black;")

    def _yardim(self):
        QMessageBox.information(self, "❓ Hammadde Talebi Nasıl Girilir?",
            "1. Malzeme / Kalite alanına çelik tipini yazın (örn: St37)\n"
            "2. En, Boy ve Kalınlık değerlerini mm cinsinden girin\n"
            "3. KG otomatik hesaplanacaktır\n"
            "4. 'Talebi Kaydet' butonuna tıklayın\n\n"
            "📌 Talep kaydedildikten sonra Satın Alma ekibi\n"
            "   bu talebi görerek sipariş verecektir.\n\n"
            "⚠️ Yıldız (*) ile işaretli alanlar zorunludur.")

    def kg_hesapla(self):
        try:
            en   = float(self.txt_en.text().replace(',','.') or 0)
            boy  = float(self.txt_boy.text().replace(',','.') or 0)
            kal  = float(self.txt_kal.text().replace(',','.') or 0)
            adet = float(self.txt_adet.text().replace(',','.') or 1)
            if en > 0 and boy > 0 and kal > 0:
                kg = (en * boy * kal * 7.85) / 1_000_000 * adet
                self.txt_kg.setText(f"{kg:.2f}")
            else:
                self.txt_kg.clear()
        except ValueError:
            self.txt_kg.clear()

    def kaydet(self):
        try:
            kalite = self.txt_kalite.text().strip()
            en     = self.txt_en.text().strip()
            boy    = self.txt_boy.text().strip()
            kal    = self.txt_kal.text().strip()
            kg     = self.txt_kg.text().strip()

            # Zorunlu alan kontrolleri
            hatalar = []
            if not kalite:
                hatalar.append("• Malzeme / Kalite boş bırakılamaz")
            if not en or float(en.replace(',','.') or 0) <= 0:
                hatalar.append("• En değeri geçersiz")
            if not boy or float(boy.replace(',','.') or 0) <= 0:
                hatalar.append("• Boy değeri geçersiz")
            if not kal or float(kal.replace(',','.') or 0) <= 0:
                hatalar.append("• Kalınlık değeri geçersiz")
            if not kg or float(kg) <= 0:
                hatalar.append("• KG hesaplanamadı, ölçüleri kontrol edin")

            if hatalar:
                QMessageBox.warning(self, "⚠️ Eksik / Hatalı Bilgi",
                    "Lütfen aşağıdaki hataları düzeltin:\n\n" + "\n".join(hatalar))
                return

            # Onay ekranı
            onay = QMessageBox.question(self, "✅ Talebi Onayla",
                f"Aşağıdaki talep kaydedilecek:\n\n"
                f"  Malzeme : {kalite}\n"
                f"  Ölçü    : {en} × {boy} × {kal} mm\n"
                f"  Ağırlık : {float(kg):,.2f} KG\n\n"
                "Onaylıyor musunuz?",
                QMessageBox.Yes | QMessageBox.No)
            if onay != QMessageBox.Yes:
                return

            tarih = datetime.now().strftime('%d.%m.%Y')
            self.cursor.execute(
                "INSERT INTO talepler (kalite, en, boy, kalinlik, kg, durum, tarih) VALUES (?,?,?,?,?,0,?)",
                (kalite, en, boy, kal, kg, tarih)
            )
            self.conn.commit()
            log_yaz(self.cursor, self.conn, "TALEP_GIRIS",
                    f"{kalite} | {en}x{boy}x{kal}mm | {float(kg):,.2f} KG")

            self.txt_kalite.clear(); self.txt_en.clear()
            self.txt_boy.clear();   self.txt_kal.clear()
            self.txt_adet.setText("1"); self.txt_kg.clear()
            for w in [self.txt_kalite, self.txt_en, self.txt_boy, self.txt_kal]:
                w.setStyleSheet("padding:10px;border:2px solid #bdc3c7;border-radius:5px;background:white;color:black;")

            if self.callback: self.callback()
            self.yenile()
            QMessageBox.information(self, "✅ Başarılı", f"Talep kaydedildi.\n{kalite} — {float(kg):,.2f} KG")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt Hatası: {e}")

    def talep_sil(self):
        row = self.tablo.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen silmek istediğiniz talebi seçin."); return
        talep_id = self.tablo.item(row, 0).text()
        kalite   = self.tablo.item(row, 1).text()
        onay = QMessageBox.question(self, "🗑️ Talebi Sil",
            f"'{kalite}' talebi silinecek.\nBu işlem geri alınamaz!",
            QMessageBox.Yes | QMessageBox.No)
        if onay == QMessageBox.Yes:
            self.cursor.execute("DELETE FROM talepler WHERE id=?", (talep_id,))
            self.conn.commit()
            log_yaz(self.cursor, self.conn, "TALEP_SILME", f"ID:{talep_id} | {kalite}")
            self.yenile()
            if self.callback: self.callback()

    def yenile(self):
        try:
            self.tablo.setRowCount(0)
            self.cursor.execute("SELECT id,kalite,en,boy,kalinlik,kg,tarih FROM talepler ORDER BY id DESC")
            for i, row in enumerate(self.cursor.fetchall()):
                self.tablo.insertRow(i)
                for j, val in enumerate(row):
                    item = QTableWidgetItem(str(val) if val is not None else "")
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                    self.tablo.setItem(i, j, item)
        except Exception as e:
            print(f"Tablo yenileme hatası: {e}")