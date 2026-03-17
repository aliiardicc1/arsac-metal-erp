"""
Arsac Metal ERP — Sevkiyat Modülü
Hazır siparişleri araç + şoför bilgisiyle sevke çıkarır.
"""
from styles import BTN_BLUE, BTN_GRAY, BTN_GREEN, BTN_ORANGE, BTN_PRIMARY, BTN_PURPLE, DIALOG_QSS, DURUM_RENK, GROUPBOX_QSS, INPUT, INPUT_QSS, LIST_QSS, SAYFA_QSS, TABLO_QSS, make_badge, make_buton, tab_qss, tablo_sag_tik_menu_ekle
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
from datetime import datetime
try:
    from log import log_yaz
except:
    def log_yaz(c,n,i,d=""): pass
def excel_kaydet(*a, **kw):
    try:
        from excel_export import excel_kaydet as _ek
        _ek(*a, **kw)
    except ImportError:
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.warning(None, "Hata", "excel_export.py bulunamadi. Arsac_App klasorune kopyalayin.")
    except Exception as _e:
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(None, "Excel Hatasi", str(_e))


class ParcaSevkDialog(QDialog):
    """Parça bazlı sevkiyat — araç ve şoför bilgisi giriş dialog'u."""
    def __init__(self, parca_adi, musteri, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Parça Sevk Et")
        self.setFixedSize(420, 300)
        self.setStyleSheet(DIALOG_QSS)
        self.plaka = ""; self.sofor = ""; self.telefon = ""
        self._build(parca_adi, musteri)

    def _build(self, parca_adi, musteri):
        lay = QVBoxLayout(self); lay.setContentsMargins(20,16,20,16); lay.setSpacing(10)

        t = QLabel("Parça Sevk Et"); t.setStyleSheet(
            "font-size:15px;font-weight:bold;color:#8e44ad;")
        lay.addWidget(t)

        info = QLabel("Parca: {}  |  Musteri: {}".format(parca_adi, musteri))
        info.setStyleSheet(
            "background:#f5eef8;border:1px solid #c39bd3;border-radius:6px;"
            "padding:8px;color:#6c3483;font-size:12px;")
        lay.addWidget(info)

        fg = QGridLayout(); fg.setSpacing(8)
        self.txt_plaka = QLineEdit(); self.txt_plaka.setPlaceholderText("Ornek: 16 ABC 123")
        self.txt_plaka.setFixedHeight(36)
        self.txt_sofor = QLineEdit(); self.txt_sofor.setPlaceholderText("Sofor adi soyadı")
        self.txt_sofor.setFixedHeight(36)
        self.txt_tel   = QLineEdit(); self.txt_tel.setPlaceholderText("Telefon (opsiyonel)")
        self.txt_tel.setFixedHeight(36)

        for row, (lbl, w) in enumerate([
            ("Plaka *:", self.txt_plaka),
            ("Sofor *:", self.txt_sofor),
            ("Telefon:", self.txt_tel),
        ]):
            fg.addWidget(QLabel(lbl), row, 0)
            fg.addWidget(w, row, 1)
        lay.addLayout(fg)

        bh = QHBoxLayout(); bh.addStretch()
        bi = QPushButton("Iptal")
        bi.setStyleSheet("background:#dcdde1;color:#2c3e50;border-radius:7px;padding:7px 16px;font-weight:bold;")
        bi.clicked.connect(self.reject)
        bk = QPushButton("Sevk Et")
        bk.setFixedHeight(38)
        bk.setStyleSheet("background:#8e44ad;color:white;border-radius:7px;padding:7px 20px;font-weight:bold;font-size:13px;border:none;")
        bk.clicked.connect(self._kaydet)
        bh.addWidget(bi); bh.addWidget(bk); lay.addLayout(bh)

    def _kaydet(self):
        plaka = self.txt_plaka.text().strip()
        sofor = self.txt_sofor.text().strip()
        if not plaka or not sofor:
            QMessageBox.warning(self, "Eksik", "Plaka ve sofor zorunlu!"); return
        self.plaka = plaka; self.sofor = sofor
        self.telefon = self.txt_tel.text().strip()
        self.accept()


class YeniSevkDialog(QDialog):
    def __init__(self, cursor, conn, parent=None):
        super().__init__(parent)
        self.cursor = cursor
        self.conn   = conn
        self.setWindowTitle("Yeni Sevkiyat Olustur")
        self.setMinimumSize(640, 560)
        self.setStyleSheet(DIALOG_QSS)
        self.init_ui()

    def init_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20,16,20,16); lay.setSpacing(12)

        # Araç bilgileri
        arac_box = QGroupBox("🚛 Araç & Şoför Bilgileri")
        ag = QGridLayout(arac_box); ag.setSpacing(8)

        def _le(ph):
            w = QLineEdit(); w.setPlaceholderText(ph); w.setFixedHeight(40); return w

        self.txt_plaka   = _le("34 ABC 123")
        self.txt_sofor   = _le("Şoför adı soyadı")
        self.txt_telefon = _le("Şoför telefonu")
        self.txt_notlar  = _le("Notlar (opsiyonel)")

        ag.addWidget(QLabel("Plaka:"),    0,0); ag.addWidget(self.txt_plaka,   0,1)
        ag.addWidget(QLabel("Şoför:"),    0,2); ag.addWidget(self.txt_sofor,   0,3)
        ag.addWidget(QLabel("Telefon:"),  1,0); ag.addWidget(self.txt_telefon, 1,1)
        ag.addWidget(QLabel("Notlar:"),   1,2); ag.addWidget(self.txt_notlar,  1,3)
        lay.addWidget(arac_box)

        # Hazır siparişler
        sip_box = QGroupBox("📦 Sevk Edilecek Siparişler (Hazır olanlar)")
        sv = QVBoxLayout(sip_box)

        self.tablo = QTableWidget(0,5)
        self.tablo.setHorizontalHeaderLabels(["✓","SİPARİŞ NO","MÜŞTERİ","TERMİN","TOPLAM"])
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.tablo.setColumnWidth(0, 40)
        self.tablo.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tablo.verticalHeader().setVisible(False)
        self.tablo.setShowGrid(False)
        self.tablo.setAlternatingRowColors(True)
        self.tablo.setStyleSheet("QTableWidget{background:white;border:none;font-size:13px;} QHeaderView::section{background:#f4f6f8;color:#2c3e50;padding:8px;font-weight:bold;border:none;border-bottom:2px solid #dfe6e9;}")
        sv.addWidget(self.tablo)

        lbl_bilgi = QLabel("💡 Sevk etmek istediğiniz siparişleri işaretleyin")
        lbl_bilgi.setStyleSheet("color:#7f8c8d;font-size:11px;font-weight:normal;margin-top:4px;")
        sv.addWidget(lbl_bilgi)
        lay.addWidget(sip_box)

        # Butonlar
        bl = QHBoxLayout()
        btn_iptal = QPushButton("İptal"); btn_iptal.setStyleSheet("background:#dcdde1;color:#2c3e50;border-radius:8px;padding:10px 24px;font-weight:bold;")
        btn_iptal.clicked.connect(self.reject)
        btn_kaydet = QPushButton("Sevkiyat Olustur")
        btn_kaydet.setStyleSheet("background:#e67e22;color:white;border-radius:8px;padding:10px 24px;font-weight:bold;font-size:14px;")
        btn_kaydet.clicked.connect(self._kaydet)
        bl.addWidget(btn_iptal); bl.addStretch(); bl.addWidget(btn_kaydet)
        lay.addLayout(bl)

        self._hazir_siparisleri_yukle()

    def _hazir_siparisleri_yukle(self):
        try:
            self.cursor.execute("""
                SELECT id, sip_no, musteri, termin, genel_toplam
                FROM siparisler WHERE durum='Hazır' ORDER BY id DESC
            """)
            self.tablo.setRowCount(0)
            for i, (sid, sno, mus, ter, top) in enumerate(self.cursor.fetchall()):
                self.tablo.insertRow(i)
                chk = QCheckBox(); chk.setStyleSheet("margin-left:10px;")
                self.tablo.setCellWidget(i, 0, chk)
                for j, v in enumerate([sno, mus or "-", ter or "-", f"{float(top or 0):,.2f} ₺"]):
                    item = QTableWidgetItem(v); item.setTextAlignment(Qt.AlignCenter)
                    item.setData(Qt.UserRole, sid)
                    self.tablo.setItem(i, j+1, item)
        except Exception as e:
            print(f"Hazır sipariş yükleme hatası: {e}")

    def _kaydet(self):
        plaka = self.txt_plaka.text().strip()
        sofor = self.txt_sofor.text().strip()
        if not plaka or not sofor:
            QMessageBox.warning(self,"Hata","Plaka ve şoför bilgisi zorunludur!"); return

        # Seçili siparişleri bul
        secili = []
        for r in range(self.tablo.rowCount()):
            chk = self.tablo.cellWidget(r, 0)
            if chk and chk.isChecked():
                item = self.tablo.item(r, 1)
                if item: secili.append(item.data(Qt.UserRole))

        if not secili:
            QMessageBox.warning(self,"Hata","En az bir sipariş seçmelisiniz!"); return

        try:
            tarih = datetime.now().strftime("%d.%m.%Y %H:%M")
            sip_listesi = ", ".join(str(s) for s in secili)

            self.cursor.execute("""
                INSERT INTO sevkiyatlar (plaka, sofor, telefon, tarih, siparis_listesi, notlar, durum)
                VALUES (?,?,?,?,?,?,'Yolda')
            """, (plaka, sofor, self.txt_telefon.text().strip(), tarih,
                  sip_listesi, self.txt_notlar.text().strip()))
            sev_id = self.cursor.lastrowid

            for sid in secili:
                self.cursor.execute("INSERT INTO sevkiyat_siparisler (sevkiyat_id, siparis_id) VALUES (?,?)", (sev_id, sid))
                self.cursor.execute("UPDATE siparisler SET durum='Sevk Edildi', arac=?, sofor=? WHERE id=?",
                                    (plaka, sofor, sid))

            self.conn.commit()
            log_yaz(self.cursor, self.conn, "SEVKIYAT_OLUSTURULDU",
                    f"{plaka} | {sofor} | {len(secili)} sipariş")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self,"Hata",str(e))


class SevkiyatSayfasi(QWidget):
    def __init__(self, cursor, conn, user_role):
        super().__init__()
        self.cursor    = cursor
        self.conn      = conn
        self.user_role = user_role
        self.init_ui()
        self.yenile()

    def init_ui(self):
        self.setStyleSheet(SAYFA_QSS + INPUT_QSS + TABLO_QSS)
        lay = QVBoxLayout(self); lay.setContentsMargins(24,16,24,16); lay.setSpacing(14)

        # Üst
        ust = QHBoxLayout()
        lbl = QLabel("SEVKIYAT")
        lbl.setStyleSheet("font-size:18px;font-weight:bold;color:#2c3e50;")
        ust.addWidget(lbl); ust.addStretch()

        self.k_parca  = self._kart("BEKLEYEN PARCA", "0", "#8e44ad")
        self.k_hazir  = self._kart("SEVKE HAZIR",    "0", "#e67e22")
        self.k_yolda  = self._kart("YOLDA",          "0", "#f39c12")
        self.k_teslim = self._kart("TESLIM",         "0", "#27ae60")
        for k in [self.k_parca, self.k_hazir, self.k_yolda, self.k_teslim]:
            ust.addWidget(k)
        ust.addSpacing(10)

        if self.user_role != "readonly":
            btn_yeni = QPushButton("Yeni Sevkiyat")
            btn_yeni.setFixedHeight(38)
            btn_yeni.setStyleSheet("background:#e67e22;color:white;border-radius:8px;font-weight:bold;font-size:13px;padding:4px 16px;border:none;")
            btn_yeni.clicked.connect(self._yeni_sevk)
            ust.addWidget(btn_yeni)

        btn_excel_sev = QPushButton("Excel")
        btn_excel_sev.setFixedHeight(38)
        btn_excel_sev.setStyleSheet("background:#27ae60;color:white;border-radius:8px;font-weight:bold;font-size:12px;padding:4px 14px;border:none;")
        btn_excel_sev.clicked.connect(self._excel_export)
        ust.addWidget(btn_excel_sev)

        btn_yenile = QPushButton("Yenile")
        btn_yenile.setFixedHeight(38)
        btn_yenile.setStyleSheet("background:#dcdde1;color:#2c3e50;border-radius:8px;font-weight:bold;font-size:12px;padding:4px 14px;border:none;")
        btn_yenile.clicked.connect(self.yenile)
        ust.addWidget(btn_yenile)
        lay.addLayout(ust)

        # Sekmeler
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane{border:1px solid #dcdde1;border-radius:10px;background:white;
            color: #2c3e50;}
            QTabBar::tab{background:#ecf0f1;color:#2c3e50;padding:8px 20px;
                         border-radius:6px 6px 0 0;font-weight:bold;}
            QTabBar::tab:selected{background:#e67e22;color:white;}
        """)

        # Sekme 1: Bekleyen Parçalar (üretimden gelen)
        t1 = QWidget(); t1l = QVBoxLayout(t1); t1l.setContentsMargins(10,10,10,10); t1l.setSpacing(6)

        # Üst araç çubuğu
        t1h = QHBoxLayout()
        lbl_info = QLabel("Uretimi tamamlanan ve sevkiyat bekleyen parcalar")
        lbl_info.setStyleSheet("color:#7f8c8d;font-size:12px;")
        t1h.addWidget(lbl_info); t1h.addStretch()

        btn_tumunu_sec = QPushButton("Tumunu Sec")
        btn_tumunu_sec.setFixedHeight(30)
        btn_tumunu_sec.setStyleSheet("background:#ecf0f1;color:#2c3e50;border-radius:6px;padding:5px 12px;font-size:12px;font-weight:bold;border:1px solid #dcdde1;")
        btn_tumunu_sec.clicked.connect(self._tumunu_sec)

        self.btn_secili_sevk = QPushButton("Secilileri Sevk Et")
        self.btn_secili_sevk.setFixedHeight(30)
        self.btn_secili_sevk.setStyleSheet("background:#8e44ad;color:white;border-radius:6px;padding:5px 14px;font-size:12px;font-weight:bold;border:none;")
        self.btn_secili_sevk.clicked.connect(self._secilileri_sevk_et)
        self.btn_secili_sevk.setEnabled(False)

        t1h.addWidget(btn_tumunu_sec)
        t1h.addWidget(self.btn_secili_sevk)
        t1l.addLayout(t1h)

        self.tablo_parca = QTableWidget(0, 6)
        tablo_sag_tik_menu_ekle(self.tablo_parca)
        self.tablo_parca.setHorizontalHeaderLabels(
            ["", "Siparis No", "Musteri", "Parca Adi", "Adet", "Tarih"])
        self.tablo_parca.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.tablo_parca.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.tablo_parca.setColumnWidth(0, 36)
        for c in [1,2,4,5]:
            self.tablo_parca.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeToContents)
        self.tablo_parca.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tablo_parca.verticalHeader().setVisible(False)
        self.tablo_parca.setShowGrid(False)
        self.tablo_parca.setAlternatingRowColors(True)
        self.tablo_parca.verticalHeader().setDefaultSectionSize(40)
        self.tablo_parca.setStyleSheet("""
            QTableWidget{background:white;color:#2c3e50;}
            QTableWidget::item{color:#2c3e50;padding:5px;}
            QHeaderView::section{background:#2c3e50;color:white;padding:8px;font-weight:bold;border:none;}
            QTableWidget::item:alternate{background:#f8f9fa;}
        """)
        t1l.addWidget(self.tablo_parca)
        self.tabs.addTab(t1, "Bekleyen Parcalar")

        # Sekme 2: Hazır Siparişler (eski davranış)
        t2 = QWidget(); t2l = QVBoxLayout(t2); t2l.setContentsMargins(10,10,10,10)
        self.tablo_hazir = QTableWidget(0,5)
        tablo_sag_tik_menu_ekle(self.tablo_hazir)
        self.tablo_hazir.setHorizontalHeaderLabels(["SIPARIS NO","MUSTERI","TERMIN","TOPLAM","ISLEM"])
        self.tablo_hazir.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo_hazir.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tablo_hazir.verticalHeader().setVisible(False)
        self.tablo_hazir.setShowGrid(False)
        self.tablo_hazir.setAlternatingRowColors(True)
        self.tablo_hazir.verticalHeader().setDefaultSectionSize(40)
        t2l.addWidget(self.tablo_hazir)
        self.tabs.addTab(t2, "Hazir Siparisler")

        # Sekme 3: Sevkiyat Geçmişi
        t3 = QWidget(); t3l = QVBoxLayout(t3); t3l.setContentsMargins(10,10,10,10)
        self.tablo_sev = QTableWidget(0,6)
        tablo_sag_tik_menu_ekle(self.tablo_sev)
        self.tablo_sev.setHorizontalHeaderLabels(["TARIH","PLAKA","SOFOR","TELEFON","SIPARISLER","DURUM"])
        self.tablo_sev.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo_sev.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tablo_sev.verticalHeader().setVisible(False)
        self.tablo_sev.setShowGrid(False)
        self.tablo_sev.setAlternatingRowColors(True)
        self.tablo_sev.verticalHeader().setDefaultSectionSize(40)
        self.tablo_sev.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tablo_sev.customContextMenuRequested.connect(self._sag_tik)
        t3l.addWidget(self.tablo_sev)
        self.tabs.addTab(t3, "Sevkiyat Gecmisi")

        lay.addWidget(self.tabs)

        # Sekme değişince yenile
        self.tabs.currentChanged.connect(lambda: self.yenile())

        # 30 saniyede bir otomatik yenile
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.yenile)
        self._timer.start(30000)

    def hideEvent(self, event):
        self._timer.stop()
        super().hideEvent(event)

    def showEvent(self, event):
        self._timer.start(30000)
        super().showEvent(event)

    def _kart(self, b, v, r):
        f = QFrame(); f.setFixedSize(120,54)
        f.setStyleSheet(f"QFrame{{background:{r};border-radius:10px;border:none;}}")
        l = QVBoxLayout(f); l.setContentsMargins(8,4,8,4); l.setSpacing(0)
        lb = QLabel(b); lb.setStyleSheet("color:rgba(255,255,255,0.75);font-size:9px;font-weight:bold;background:transparent;letter-spacing:1px;")
        lv = QLabel(v); lv.setObjectName("Val"); lv.setStyleSheet("color:white;font-size:18px;font-weight:900;background:transparent;")
        l.addWidget(lb); l.addWidget(lv); return f

    def _set_kart(self, k, v):
        k.findChild(QLabel,"Val").setText(str(v))

    def _excel_export(self):
        if not excel_kaydet:
            return
        sutunlar = ["Plaka","Sofor","Tarih","Siparis Listesi","Durum"]
        satirlar = []
        try:
            self.cursor.execute("SELECT plaka, sofor, tarih, siparis_listesi, durum FROM sevkiyatlar ORDER BY id DESC")
            for row in self.cursor.fetchall():
                satirlar.append(list(row))
        except Exception as e:
            print("Sevkiyat excel hatasi:", e)
        excel_kaydet(self, "Sevkiyatlar", sutunlar, satirlar)

    def yenile(self):
        try:
            # Kartlar
            self.cursor.execute(
                "SELECT COUNT(*) FROM parca_sevk_bekliyor WHERE durum='Bekliyor'")
            self._set_kart(self.k_parca, self.cursor.fetchone()[0])
            self.cursor.execute(
                "SELECT COUNT(*) FROM siparisler WHERE durum='Hazir'")
            self._set_kart(self.k_hazir, self.cursor.fetchone()[0])
            self.cursor.execute(
                "SELECT COUNT(*) FROM sevkiyatlar WHERE durum='Yolda'")
            self._set_kart(self.k_yolda, self.cursor.fetchone()[0])
            self.cursor.execute(
                "SELECT COUNT(*) FROM sevkiyatlar WHERE durum='Teslim Edildi'")
            self._set_kart(self.k_teslim, self.cursor.fetchone()[0])

            # Sekme 1: Bekleyen Parçalar
            self.cursor.execute("""
                SELECT id, sip_no, musteri, parca_adi, bekleyen_adet, tarih
                FROM parca_sevk_bekliyor WHERE durum='Bekliyor'
                ORDER BY sip_no, id
            """)
            self.tablo_parca.setRowCount(0)
            for i, (psb_id, sno, mus, pad, adet, tarih) in enumerate(
                    self.cursor.fetchall()):
                self.tablo_parca.insertRow(i)
                self.tablo_parca.setRowHeight(i, 40)

                # Checkbox
                chk = QCheckBox(); chk.setStyleSheet("margin-left:10px;")
                chk.stateChanged.connect(self._secim_degisti)
                self.tablo_parca.setCellWidget(i, 0, chk)

                for j, v in enumerate([sno or "-", mus or "-", pad or "-",
                                        "{:g}".format(float(adet or 0)), tarih or "-"]):
                    it = QTableWidgetItem(v)
                    it.setTextAlignment(Qt.AlignCenter)
                    it.setData(Qt.UserRole, psb_id)
                    self.tablo_parca.setItem(i, j+1, it)

            self.btn_secili_sevk.setEnabled(False)

            # Sekme 2: Hazır Siparişler
            self.cursor.execute("""
                SELECT id, sip_no, musteri, termin, genel_toplam
                FROM siparisler WHERE durum='Hazir' ORDER BY id DESC
            """)
            self.tablo_hazir.setRowCount(0)
            for i, (sid, sno, mus, ter, top) in enumerate(self.cursor.fetchall()):
                self.tablo_hazir.insertRow(i)
                for j, v in enumerate([sno, mus or "-", ter or "-",
                                        "{:,.2f}".format(float(top or 0))]):
                    it = QTableWidgetItem(v); it.setTextAlignment(Qt.AlignCenter)
                    it.setData(Qt.UserRole, sid)
                    self.tablo_hazir.setItem(i, j, it)
                btn = QPushButton("Sevke Al"); btn.setFixedHeight(32); btn.setMinimumWidth(90)
                btn.setStyleSheet(
                    "background:#e67e22;color:white;font-weight:bold;"
                    "font-size:12px;border-radius:6px;border:none;padding:4px 12px;")
                btn.clicked.connect(lambda _, s=sid: self._tek_sevk(s))
                bw = QWidget(); bl = QHBoxLayout(bw)
                bl.setContentsMargins(4,4,4,4); bl.addWidget(btn)
                self.tablo_hazir.setCellWidget(i, 4, bw)

            # Sekme 3: Sevkiyat Geçmişi
            self.cursor.execute("""
                SELECT id, tarih, plaka, sofor, telefon, siparis_listesi, durum
                FROM sevkiyatlar ORDER BY id DESC
            """)
            self.tablo_sev.setRowCount(0)
            for i, (sev_id, tarih, plaka, sofor, tel, sip_l, durum) in enumerate(
                    self.cursor.fetchall()):
                self.cursor.execute(
                    "SELECT COUNT(*) FROM sevkiyat_siparisler WHERE sevkiyat_id=?",
                    (sev_id,))
                sip_sayi = self.cursor.fetchone()[0]
                self.tablo_sev.insertRow(i)
                renk = {"Yolda":"#e67e22","Teslim Edildi":"#27ae60"}.get(durum,"#7f8c8d")
                for j, v in enumerate([tarih or "-", plaka or "-", sofor or "-",
                                        tel or "-", "{} siparis".format(sip_sayi), durum or "-"]):
                    it = QTableWidgetItem(v); it.setTextAlignment(Qt.AlignCenter)
                    it.setData(Qt.UserRole, sev_id)
                    if j == 5: it.setForeground(QColor(renk))
                    self.tablo_sev.setItem(i, j, it)

        except Exception as e:
            print("Sevkiyat yenile hatasi:", e)

    def _secim_degisti(self):
        """Herhangi bir checkbox değişince Sevk Et butonunu aktif/pasif yap."""
        secili_var = any(
            self.tablo_parca.cellWidget(r, 0) and
            self.tablo_parca.cellWidget(r, 0).isChecked()
            for r in range(self.tablo_parca.rowCount())
        )
        self.btn_secili_sevk.setEnabled(secili_var)

    def _tumunu_sec(self):
        """Tüm satırları seç / seçimi kaldır."""
        tumu_secili = all(
            self.tablo_parca.cellWidget(r, 0) and
            self.tablo_parca.cellWidget(r, 0).isChecked()
            for r in range(self.tablo_parca.rowCount())
            if self.tablo_parca.cellWidget(r, 0)
        )
        for r in range(self.tablo_parca.rowCount()):
            chk = self.tablo_parca.cellWidget(r, 0)
            if chk: chk.setChecked(not tumu_secili)

    def _secilileri_sevk_et(self):
        """Seçili parçaları tek dialog ile toplu sevk et."""
        secili_ids = []
        secili_adlar = []
        for r in range(self.tablo_parca.rowCount()):
            chk = self.tablo_parca.cellWidget(r, 0)
            if chk and chk.isChecked():
                it = self.tablo_parca.item(r, 1)  # sip_no sütunu
                if it:
                    secili_ids.append(it.data(Qt.UserRole))
                    pad = self.tablo_parca.item(r, 3)
                    secili_adlar.append(pad.text() if pad else "-")

        if not secili_ids:
            QMessageBox.warning(self, "Uyari", "En az bir parca secin."); return

        # Müşteri bilgisini al (ilk seçiliden)
        musteri_it = self.tablo_parca.item(
            [r for r in range(self.tablo_parca.rowCount())
             if self.tablo_parca.cellWidget(r,0) and
             self.tablo_parca.cellWidget(r,0).isChecked()][0], 2)
        musteri = musteri_it.text() if musteri_it else "-"

        ozet = "{} parca".format(len(secili_ids))
        dlg = ParcaSevkDialog(ozet, musteri, self)
        if dlg.exec_() != QDialog.Accepted:
            return

        try:
            tarih = datetime.now().strftime("%d.%m.%Y %H:%M")
            parca_listesi = ", ".join(secili_adlar)
            self.cursor.execute("""
                INSERT INTO sevkiyatlar
                    (plaka, sofor, telefon, tarih, siparis_listesi, notlar, durum)
                VALUES (?,?,?,?,?,?,'Yolda')
            """, (dlg.plaka, dlg.sofor, dlg.telefon, tarih,
                  parca_listesi, ""))

            for psb_id in secili_ids:
                self.cursor.execute(
                    "UPDATE parca_sevk_bekliyor SET durum='Sevk Edildi' WHERE id=?",
                    (psb_id,))

            self.conn.commit()

            # Sipariş senkronizasyonu — bekleyen parça kalmadıysa siparişi kapat
            self._siparis_durum_guncelle(secili_ids)

            log_yaz(self.cursor, self.conn, "TOPLU_PARCA_SEVK",
                    "{} parca | {} | {}".format(len(secili_ids), dlg.plaka, dlg.sofor))
            QMessageBox.information(
                self, "Sevk Edildi",
                "{} parca sevk edildi.\n\nArac: {}\nSofor: {}".format(
                    len(secili_ids), dlg.plaka, dlg.sofor))
            self.yenile()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _siparis_durum_guncelle(self, sevk_edilen_psb_ids):
        """Sevk edilen parçaların sipariş ID'lerini bul,
        siparişi 'Sevk Edildi' yap."""
        try:
            if not sevk_edilen_psb_ids: return
            ph = ",".join("?" * len(sevk_edilen_psb_ids))

            # UPDATE öncesi siparis_id'leri al (id listesi ile)
            self.cursor.execute(
                "SELECT DISTINCT siparis_id FROM parca_sevk_bekliyor "
                "WHERE id IN ({}) AND siparis_id IS NOT NULL".format(ph),
                sevk_edilen_psb_ids)
            sip_idler = [r[0] for r in self.cursor.fetchall()]

            print("Senkronizasyon - siparis idleri:", sip_idler)

            for sip_id in sip_idler:
                self.cursor.execute(
                    "UPDATE siparisler SET durum='Sevk Edildi' "
                    "WHERE id=? AND durum NOT IN ('Iptal', 'Faturalandı')",
                    (sip_id,))
                print("Siparis {} -> Sevk Edildi guncellendi".format(sip_id))

            self.conn.commit()
        except Exception as e:
            print("Siparis durum guncelleme hatasi:", e)
            import traceback; traceback.print_exc()

    def _yeni_sevk(self):
        dlg = YeniSevkDialog(self.cursor, self.conn, self)
        if dlg.exec_() == QDialog.Accepted:
            self.yenile()

    def _tek_sevk(self, sid):
        plaka, ok = QInputDialog.getText(self,"Sevke Al","Araç plakası:")
        if not ok or not plaka: return
        sofor, ok2 = QInputDialog.getText(self,"Sevke Al","Şoför adı:")
        if not ok2: return
        try:
            tarih = datetime.now().strftime("%d.%m.%Y %H:%M")
            self.cursor.execute("""
                INSERT INTO sevkiyatlar (plaka, sofor, tarih, siparis_listesi, durum)
                VALUES (?,?,?,?,'Yolda')
            """, (plaka, sofor, tarih, str(sid)))
            sev_id = self.cursor.lastrowid
            self.cursor.execute("INSERT INTO sevkiyat_siparisler (sevkiyat_id, siparis_id) VALUES (?,?)", (sev_id, sid))
            self.cursor.execute("UPDATE siparisler SET durum='Sevk Edildi', arac=?, sofor=? WHERE id=?", (plaka, sofor, sid))
            self.conn.commit()
            log_yaz(self.cursor, self.conn, "SEVKIYAT_OLUSTURULDU", f"{plaka} | {sofor} | Sipariş ID:{sid}")
            self.yenile()
        except Exception as e:
            QMessageBox.critical(self,"Hata",str(e))

    def _sag_tik(self, pos):
        row = self.tablo_sev.currentRow()
        if row < 0: return
        item = self.tablo_sev.item(row, 0)
        sev_id = item.data(Qt.UserRole) if item else None
        if not sev_id: return
        menu = QMenu(self)
        menu.setStyleSheet("QMenu{background:white;border:1px solid #dcdde1;border-radius:8px;padding:6px;font-size:13px;} QMenu::item{padding:8px 18px;border-radius:4px;} QMenu::item:selected{background:#fde8e8;color:#c0392b;}")
        act_teslim = menu.addAction("✅ Teslim Edildi Olarak İşaretle")
        secim = menu.exec_(self.tablo_sev.mapToGlobal(pos))
        if secim == act_teslim:
            self.cursor.execute("UPDATE sevkiyatlar SET durum='Teslim Edildi' WHERE id=?", (sev_id,))
            self.conn.commit()
            log_yaz(self.cursor, self.conn, "SEVKIYAT_TESLIM", f"Sevkiyat ID:{sev_id}")
            self.yenile()
