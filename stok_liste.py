import os, sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
try:
    from log import log_yaz
except:
    def log_yaz(c,n,i,d=""): pass
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from stok_fis import stok_fisi_olustur
    STOK_FIS_AKTIF = True
except ImportError:
    STOK_FIS_AKTIF = False
try:
    import qrcode
    QR_AKTIF = True
except:
    QR_AKTIF = False


class StokListeSayfasi(QWidget):
    def __init__(self, cursor, conn, user_role):
        super().__init__()
        self.cursor, self.conn, self.user_role = cursor, conn, user_role
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #ebedef; font-family: 'Segoe UI', Arial; }
            QLabel { font-size: 16px; font-weight: bold; color: #2c3e50; }
            QTableWidget { background-color: white; border: 1px solid #dcdde1; border-radius: 8px; font-size: 13px; }
            QHeaderView::section { background-color: #2c3e50; color: white; padding: 10px; font-weight: bold; font-size: 13px; border: none; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        # Başlık + yardım
        ust = QHBoxLayout()
        ust.addWidget(QLabel("📦 MEVCUT STOK VE DİJİTAL QR YÖNETİMİ"))
        ust.addStretch()
        btn_yardim = QPushButton("❓")
        btn_yardim.setFixedSize(32,32)
        btn_yardim.setStyleSheet("background:#2980b9;color:white;border-radius:16px;font-weight:bold;font-size:14px;padding:0;")
        btn_yardim.clicked.connect(self._yardim)
        ust.addWidget(btn_yardim)
        layout.addLayout(ust)

        # Filtre + arama
        filtre_lay = QHBoxLayout()
        self.txt_filtre = QLineEdit()
        self.txt_filtre.setPlaceholderText("🔍 Stok koduna veya malzemeye göre filtrele...")
        self.txt_filtre.setFixedHeight(36)
        self.txt_filtre.setStyleSheet("border:1.5px solid #dcdde1;border-radius:18px;padding:6px 14px;font-size:13px;background:white;")
        self.txt_filtre.textChanged.connect(self.filtrele)
        filtre_lay.addWidget(self.txt_filtre)

        self.cmb_durum = QComboBox()
        self.cmb_durum.addItems(["Tümü", "Yolda", "Depoda"])
        self.cmb_durum.setFixedHeight(36)
        self.cmb_durum.setStyleSheet("border:1.5px solid #dcdde1;border-radius:6px;padding:4px 10px;font-size:13px;background:white;")
        self.cmb_durum.currentTextChanged.connect(self.filtrele)
        filtre_lay.addWidget(self.cmb_durum)
        layout.addLayout(filtre_lay)

        # Butonlar
        btn_lay = QHBoxLayout()
        self.btn_fis = QPushButton("🖨️ FİŞ YAZDIR")
        self.btn_fis.setFixedHeight(40)
        self.btn_fis.setStyleSheet("background:#8e44ad;color:white;border-radius:6px;padding:8px 16px;font-weight:bold;font-size:13px;")
        self.btn_fis.clicked.connect(self.fis_yazdir)
        btn_lay.addWidget(self.btn_fis)

        self.btn_belgeler = QPushButton("📂 FİŞLERİ AÇ")
        self.btn_belgeler.setFixedHeight(40)
        self.btn_belgeler.setStyleSheet("background:#2980b9;color:white;border-radius:6px;padding:8px 16px;font-weight:bold;font-size:13px;")
        self.btn_belgeler.clicked.connect(self.belgeleri_ac)
        btn_lay.addWidget(self.btn_belgeler)

        if self.user_role == "yonetici":
            self.btn_sil = QPushButton("🗑️ SEÇİLİ STOĞU SİL")
            self.btn_sil.setFixedHeight(40)
            self.btn_sil.setStyleSheet("background:#e74c3c;color:white;border-radius:6px;padding:8px 16px;font-weight:bold;font-size:13px;")
            self.btn_sil.clicked.connect(self.stok_sil)
            btn_lay.addWidget(self.btn_sil)

        btn_lay.addStretch()
        self.lbl_say = QLabel("0 kayıt")
        self.lbl_say.setStyleSheet("font-size:13px;color:#7f8c8d;font-weight:normal;")
        btn_lay.addWidget(self.lbl_say)

        self.btn_yenile = QPushButton("🔄 YENİLE")
        self.btn_yenile.setFixedHeight(40)
        self.btn_yenile.setStyleSheet("background:#2c3e50;color:white;border-radius:6px;padding:8px 16px;font-weight:bold;font-size:13px;")
        self.btn_yenile.clicked.connect(self.yenile)
        btn_lay.addWidget(self.btn_yenile)
        layout.addLayout(btn_lay)

        self.tablo = QTableWidget(0, 8)
        self.tablo.setHorizontalHeaderLabels(["ID","Stok Kodu","Malzeme","En (mm)","Boy (mm)","Kal (mm)","KG","Durum"])
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tablo.setAlternatingRowColors(True)
        self.tablo.verticalHeader().setVisible(False)
        self.tablo.verticalHeader().setDefaultSectionSize(40)
        self.tablo.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tablo.customContextMenuRequested.connect(self.sag_tik_menu)
        layout.addWidget(self.tablo)
        self.yenile()

    def _yardim(self):
        QMessageBox.information(self, "❓ Stok Listesi Nasıl Kullanılır?",
            "📦 STOK DURUMU:\n"
            "  🚚 Yolda   — Sipariş verildi, depo girişi bekleniyor\n"
            "  ✅ Depoda  — Malzeme fiziksel olarak depoda\n\n"
            "🖱️ DEPO GİRİŞİ:\n"
            "  'Giriş Yap' butonuna tıklayarak yolda olan\n"
            "  malzemeyi depoya kabul edin.\n\n"
            "🖱️ SAĞ TIK:\n"
            "  Herhangi bir satıra sağ tıklayarak\n"
            "  QR kod oluşturabilirsiniz.\n\n"
            "🖨️ FİŞ:\n"
            "  CTRL ile birden fazla seçip fiş yazdırabilirsiniz.")

    def belgeleri_ac(self):
        klasor = "Satin Alma Belgeleri"
        if not os.path.exists(klasor): os.makedirs(klasor)
        try: os.startfile(klasor)
        except: QMessageBox.information(self,"Bilgi",os.path.abspath(klasor))

    def fis_yazdir(self):
        if not STOK_FIS_AKTIF:
            QMessageBox.warning(self,"Hata","stok_fis.py bulunamadı!"); return
        secili = self.tablo.selectedItems()
        if not secili:
            QMessageBox.warning(self,"Uyarı","Fiş yazdırmak için satır seçin.\n(CTRL ile birden fazla seçebilirsiniz)"); return
        satirlar = list(set(i.row() for i in secili))
        bilgiler = []
        for r in satirlar:
            stok_id = self.tablo.item(r,0).text()
            self.cursor.execute("SELECT stok_kodu,malzeme,en,boy,kalinlik,kg,son_firma,son_tarih FROM stok WHERE id=?",(stok_id,))
            row = self.cursor.fetchone()
            if row:
                bilgiler.append({'stok_kodu':row[0],'malzeme':row[1],'en':row[2],'boy':row[3],'kalinlik':row[4],'kg':row[5],'son_firma':row[6],'son_tarih':row[7]})
        if not bilgiler: return
        try:
            pdf_yolu = stok_fisi_olustur(bilgiler)
            log_yaz(self.cursor, self.conn, "STOK_FIS", f"{len(bilgiler)} adet fis")
            QMessageBox.information(self,"✅ Fiş Oluşturuldu",f"{len(bilgiler)} adet fiş oluşturuldu!\n📄 {pdf_yolu}")
            try: os.startfile(pdf_yolu)
            except: pass
        except Exception as e:
            QMessageBox.critical(self,"Hata",str(e))

    def stok_sil(self):
        row = self.tablo.currentRow()
        if row < 0:
            QMessageBox.warning(self,"Uyarı","Silmek istediğiniz stoğu seçin."); return
        stok_id  = self.tablo.item(row,0).text()
        stok_kod = self.tablo.item(row,1).text()
        malzeme  = self.tablo.item(row,2).text()
        durum_w  = self.tablo.cellWidget(row,7)

        onay = QMessageBox.question(self, "🗑️ Stok Sil",
            f"Stok kodu: {stok_kod}\nMalzeme: {malzeme}\n\nBu kayıt kalıcı olarak silinecek!\nEmin misiniz?",
            QMessageBox.Yes | QMessageBox.No)
        if onay == QMessageBox.Yes:
            self.cursor.execute("DELETE FROM stok WHERE id=?", (stok_id,))
            self.conn.commit()
            log_yaz(self.cursor, self.conn, "STOK_SILME", f"{stok_kod} | {malzeme}")
            self.yenile()

    def sag_tik_menu(self, pos):
        menu = QMenu()
        qr_ak = menu.addAction("📱 QR KOD OLUŞTUR")
        fis_ak = menu.addAction("🖨️ FİŞ YAZDIR")
        action = menu.exec_(self.tablo.mapToGlobal(pos))
        if action == qr_ak: self.qr_olustur()
        elif action == fis_ak: self.fis_yazdir()

    def qr_olustur(self):
        if not QR_AKTIF:
            QMessageBox.warning(self,"Hata","qrcode kütüphanesi kurulu değil.\npip install qrcode pillow"); return
        row = self.tablo.currentRow()
        if row < 0: return
        s_kod = self.tablo.item(row,1).text()
        s_mat = self.tablo.item(row,2).text()
        s_en  = self.tablo.item(row,3).text()
        s_boy = self.tablo.item(row,4).text()
        s_kal = self.tablo.item(row,5).text()
        s_kg  = self.tablo.item(row,6).text()
        import qrcode as qr
        web_link = f"https://aliiardicc1.github.io/arsac/stok.html?id={s_kod}&mat={s_mat}&dim={s_en}x{s_boy}x{s_kal}&kg={s_kg}"
        q = qr.QRCode(box_size=10, border=2)
        q.add_data(web_link); q.make(fit=True)
        img = q.make_image(fill_color="black", back_color="white")
        if not os.path.exists("qrcodes"): os.makedirs("qrcodes")
        path = f"qrcodes/{s_kod}.png"
        img.save(path)
        msg = QMessageBox(self)
        msg.setWindowTitle("QR Hazır")
        msg.setText(f"<b>{s_kod}</b> için QR Kod oluşturuldu.")
        msg.setIconPixmap(QPixmap(path).scaled(250,250,Qt.KeepAspectRatio))
        msg.exec_()

    def filtrele(self):
        metin  = self.txt_filtre.text().strip().lower()
        durum_f = self.cmb_durum.currentText()
        for i in range(self.tablo.rowCount()):
            kod = (self.tablo.item(i,1).text() if self.tablo.item(i,1) else "").lower()
            mal = (self.tablo.item(i,2).text() if self.tablo.item(i,2) else "").lower()
            # durum widget'ından metin al
            d_w = self.tablo.cellWidget(i,7)
            d_txt = ""
            if d_w:
                lbl = d_w.findChild(QLabel)
                btn = d_w.findChild(QPushButton)
                if lbl: d_txt = lbl.text()
                elif btn: d_txt = btn.text()

            metin_ok  = not metin or metin in kod or metin in mal
            durum_ok  = (durum_f == "Tümü" or
                        (durum_f == "Yolda"  and "Giriş" in d_txt) or
                        (durum_f == "Depoda" and "Depoda" in d_txt))
            self.tablo.setRowHidden(i, not (metin_ok and durum_ok))

    def yenile(self):
        self.tablo.setRowCount(0)
        self.cursor.execute("SELECT id,stok_kodu,malzeme,en,boy,kalinlik,kg,durum FROM stok ORDER BY id DESC")
        rows = self.cursor.fetchall()
        for i, row in enumerate(rows):
            self.tablo.insertRow(i)
            for j in range(7):
                item = QTableWidgetItem(str(row[j]) if row[j] is not None else "")
                item.setTextAlignment(Qt.AlignCenter)
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.tablo.setItem(i, j, item)
            durum = row[7]
            if durum == 0:
                btn = QPushButton("🚚 Giriş Yap")
                btn.setFixedHeight(30)
                btn.setStyleSheet("background:#e67e22;color:white;font-weight:bold;font-size:12px;border-radius:4px;padding:2px 8px;")
                btn.clicked.connect(lambda ch, s_id=row[0]: self.stok_onayla(s_id))
                c = QWidget(); cl = QHBoxLayout(c); cl.setContentsMargins(4,4,4,4); cl.addWidget(btn)
                self.tablo.setCellWidget(i, 7, c)
            else:
                lbl = QLabel("✅ Depoda")
                lbl.setStyleSheet("color:#27ae60;font-weight:bold;font-size:12px;")
                lbl.setAlignment(Qt.AlignCenter)
                self.tablo.setCellWidget(i, 7, lbl)
        self.lbl_say.setText(f"{len(rows)} kayıt")

    def stok_onayla(self, stok_id):
        self.cursor.execute("SELECT stok_kodu, malzeme, kg FROM stok WHERE id=?", (stok_id,))
        row = self.cursor.fetchone()
        if not row: return
        stok_kodu, malzeme, kg = row

        onay = QMessageBox.question(self, "🚚 Depo Girişi Onayı",
            f"Aşağıdaki malzeme depoya kabul edilecek:\n\n"
            f"  Stok Kodu : {stok_kodu}\n"
            f"  Malzeme   : {malzeme}\n"
            f"  Ağırlık   : {float(kg or 0):,.2f} KG\n\n"
            "Malzeme fiziksel olarak depoya ulaştı mı?",
            QMessageBox.Yes | QMessageBox.No)
        if onay == QMessageBox.Yes:
            self.cursor.execute("UPDATE stok SET durum=1 WHERE id=?", (stok_id,))
            self.conn.commit()
            log_yaz(self.cursor, self.conn, "STOK_DEPO_GIRIS",
                    f"{stok_kodu} | {malzeme} | {float(kg or 0):,.2f} KG")
            self.yenile()
            QMessageBox.information(self, "✅ Kabul Edildi",
                f"{stok_kodu} depoya kabul edildi.")