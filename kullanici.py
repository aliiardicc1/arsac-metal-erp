"""
Arsac Metal ERP — Kullanıcı Yönetim Sistemi
Şifreli giriş, kullanıcı ekleme/silme/rol değiştirme.
"""
import hashlib
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
try:
    from log import log_yaz
except:
    def log_yaz(c,n,i,d=""): pass


def sifre_hashle(sifre):
    return hashlib.sha256(sifre.encode('utf-8')).hexdigest()


def kullanici_dogrula(cursor, kullanici_adi, sifre):
    """
    Kullanıcı adı + şifre doğrular.
    Döner: (rol, ad_soyad) veya None
    """
    try:
        h = sifre_hashle(sifre)
        cursor.execute(
            "SELECT rol, ad_soyad, aktif FROM kullanicilar WHERE kullanici_adi=? AND sifre_hash=?",
            (kullanici_adi.strip(), h)
        )
        row = cursor.fetchone()
        if row and row[2] == 1:
            return row[0], row[1]
    except Exception as e:
        print(f"Doğrulama hatası: {e}")
    return None


def varsayilan_admin_olustur(cursor, conn):
    """Eski admin rolleri yonetici yapar, yoksa yeni hesap oluşturur."""
    try:
        # Eski 'admin' rolunu 'yonetici' ye cevir (migration)
        cursor.execute("UPDATE kullanicilar SET rol='yonetici' WHERE rol='admin'")
        conn.commit()
        # Hic yonetici yoksa varsayilan olustur
        cursor.execute("SELECT COUNT(*) FROM kullanicilar WHERE rol='yonetici'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO kullanicilar (kullanici_adi, sifre_hash, rol, ad_soyad, aktif)
                VALUES (?, ?, 'yonetici', 'Sistem Yoneticisi', 1)
            """, ("aliiardicc", sifre_hashle("arsac2024")))
            conn.commit()
    except Exception as e:
        print(f"Varsayilan yonetici hatasi: {e}")


# ─────────────────────────────────────────────
#  GİRİŞ EKRANI
# ─────────────────────────────────────────────
class GirisEkrani(QDialog):
    def __init__(self, cursor, conn):
        super().__init__()
        self.cursor = cursor
        self.conn   = conn
        self.sonuc  = None  # (rol, kullanici_adi, ad_soyad)
        self.setWindowTitle("ARSAC METAL ERP — Giriş")
        self.setFixedSize(420, 520)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        self.setStyleSheet("""
            QDialog { background: #f4f6f9; font-family: 'Segoe UI'; }
            QLabel  { font-family: 'Segoe UI'; }
            QLineEdit {
                border: 2px solid #dcdde1;
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 14px;
                color: #2c3e50;
                background: white;
            }
            QLineEdit:focus { border: 2px solid #c0392b; }
            QPushButton#GirisBtn {
                background: #c0392b;
                color: white;
                border-radius: 10px;
                padding: 14px;
                font-weight: bold;
                font-size: 15px;
            }
            QPushButton#GirisBtn:hover { background: #a93226; }
        """)
        self.init_ui()

    def init_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 30, 40, 30)
        lay.setSpacing(0)

        # Logo / başlık
        lbl_logo = QLabel("ARSAC METAL")
        lbl_logo.setAlignment(Qt.AlignCenter)
        lbl_logo.setStyleSheet("font-size:28px;font-weight:900;color:#c0392b;letter-spacing:2px;")
        lay.addWidget(lbl_logo)

        lbl_alt = QLabel("ERP Yönetim Sistemi")
        lbl_alt.setAlignment(Qt.AlignCenter)
        lbl_alt.setStyleSheet("font-size:13px;color:#7f8c8d;margin-bottom:30px;")
        lay.addWidget(lbl_alt)
        lay.addSpacing(30)

        # Hata bandı
        self.lbl_hata = QLabel("")
        self.lbl_hata.setAlignment(Qt.AlignCenter)
        self.lbl_hata.setFixedHeight(36)
        self.lbl_hata.setStyleSheet("background:#e74c3c;color:white;border-radius:8px;font-size:13px;font-weight:bold;")
        self.lbl_hata.hide()
        lay.addWidget(self.lbl_hata)
        lay.addSpacing(10)

        # Kullanıcı adı
        lbl_k = QLabel("Kullanıcı Adı")
        lbl_k.setStyleSheet("font-size:12px;font-weight:bold;color:#7f8c8d;margin-bottom:4px;")
        lay.addWidget(lbl_k)
        self.txt_kullanici = QLineEdit()
        self.txt_kullanici.setPlaceholderText("Kullanıcı adınızı girin")
        self.txt_kullanici.setFixedHeight(46)
        lay.addWidget(self.txt_kullanici)
        lay.addSpacing(16)

        # Şifre
        lbl_s = QLabel("Şifre")
        lbl_s.setStyleSheet("font-size:12px;font-weight:bold;color:#7f8c8d;margin-bottom:4px;")
        lay.addWidget(lbl_s)
        self.txt_sifre = QLineEdit()
        self.txt_sifre.setPlaceholderText("Şifrenizi girin")
        self.txt_sifre.setEchoMode(QLineEdit.Password)
        self.txt_sifre.setFixedHeight(46)
        self.txt_sifre.returnPressed.connect(self.giris_yap)
        lay.addWidget(self.txt_sifre)
        lay.addSpacing(24)

        # Giriş butonu
        self.btn_giris = QPushButton("GİRİŞ YAP")
        self.btn_giris.setObjectName("GirisBtn")
        self.btn_giris.setFixedHeight(50)
        self.btn_giris.clicked.connect(self.giris_yap)
        lay.addWidget(self.btn_giris)
        lay.addStretch()

        # Alt bilgi
        lbl_bilgi = QLabel("v1.0 © 2024 Arsac Metal")
        lbl_bilgi.setAlignment(Qt.AlignCenter)
        lbl_bilgi.setStyleSheet("font-size:11px;color:#bdc3c7;")
        lay.addWidget(lbl_bilgi)

        # Enter ile giriş
        self.txt_kullanici.returnPressed.connect(lambda: self.txt_sifre.setFocus())

    def giris_yap(self):
        kullanici = self.txt_kullanici.text().strip()
        sifre     = self.txt_sifre.text()

        if not kullanici or not sifre:
            self._hata("Kullanıcı adı ve şifre boş bırakılamaz!")
            return

        sonuc = kullanici_dogrula(self.cursor, kullanici, sifre)
        if sonuc:
            rol, ad_soyad = sonuc
            self.sonuc = (rol, kullanici, ad_soyad)
            log_yaz(self.cursor, self.conn, "GIRIS", f"{kullanici} ({rol}) giris yapti")
            self.accept()
        else:
            self._hata("Kullanıcı adı veya şifre hatalı!")
            self.txt_sifre.clear()
            self.txt_sifre.setFocus()

    def _hata(self, mesaj):
        self.lbl_hata.setText(f"⚠️  {mesaj}")
        self.lbl_hata.show()


# ─────────────────────────────────────────────
#  YENİ KULLANICI EKLE
# ─────────────────────────────────────────────
class KullaniciEkleDialog(QDialog):
    def __init__(self, cursor, conn, parent=None):
        super().__init__(parent)
        self.cursor = cursor
        self.conn   = conn
        self.kullanici_adi = ""
        self.rol = "personel"
        self.setWindowTitle("Yeni Kullanici Ekle")
        self.setFixedSize(380, 300)
        self.setStyleSheet("""
            QDialog { background:#f4f6f9; }
            QLabel { color:#2c3e50; font-size:12px; font-weight:bold; }
            QLineEdit, QComboBox {
                border:1.5px solid #dcdde1; border-radius:7px;
                padding:7px 10px; font-size:13px; background:white; color:#2c3e50;
            }
        """)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20); lay.setSpacing(12)

        lay.addWidget(QLabel("Kullanici Adi:"))
        self.txt_kadi = QLineEdit(); self.txt_kadi.setFixedHeight(38)
        lay.addWidget(self.txt_kadi)

        lay.addWidget(QLabel("Ad Soyad:"))
        self.txt_ad = QLineEdit(); self.txt_ad.setFixedHeight(38)
        lay.addWidget(self.txt_ad)

        lay.addWidget(QLabel("Sifre:"))
        self.txt_sifre = QLineEdit()
        self.txt_sifre.setEchoMode(QLineEdit.Password)
        self.txt_sifre.setFixedHeight(38)
        lay.addWidget(self.txt_sifre)

        lay.addWidget(QLabel("Rol:"))
        self.cmb_rol = QComboBox(); self.cmb_rol.setFixedHeight(38)
        self.cmb_rol.addItems(["personel", "satis", "uretim", "sevkiyat",
                                "muhasebe", "yonetici"])
        lay.addWidget(self.cmb_rol)

        btn_lay = QHBoxLayout(); btn_lay.addStretch()
        btn_iptal = QPushButton("Iptal")
        btn_iptal.setStyleSheet("background:#dcdde1;color:#2c3e50;border-radius:7px;"
                                 "padding:8px 20px;font-weight:bold;border:none;")
        btn_iptal.clicked.connect(self.reject)
        btn_kaydet = QPushButton("Kaydet")
        btn_kaydet.setStyleSheet("background:#c0392b;color:white;border-radius:7px;"
                                  "padding:8px 20px;font-weight:bold;border:none;")
        btn_kaydet.clicked.connect(self._kaydet)
        btn_lay.addWidget(btn_iptal); btn_lay.addWidget(btn_kaydet)
        lay.addLayout(btn_lay)

    def _kaydet(self):
        kadi  = self.txt_kadi.text().strip()
        ad    = self.txt_ad.text().strip()
        sifre = self.txt_sifre.text().strip()
        rol   = self.cmb_rol.currentText()

        if not kadi:
            QMessageBox.warning(self, "Hata", "Kullanici adi bos olamaz!"); return
        if not sifre:
            QMessageBox.warning(self, "Hata", "Sifre bos olamaz!"); return

        import hashlib
        h = hashlib.sha256(sifre.encode()).hexdigest()
        tarih = __import__("datetime").datetime.now().strftime("%d.%m.%Y %H:%M")
        try:
            self.cursor.execute("""
                INSERT INTO kullanicilar
                    (kullanici_adi, sifre_hash, rol, ad_soyad, aktif, olusturma_tarihi)
                VALUES (?, ?, ?, ?, 1, ?)
            """, (kadi, h, rol, ad, tarih))
            self.conn.commit()
            self.kullanici_adi = kadi
            self.rol = rol
            self.accept()
        except Exception as e:
            if "UNIQUE" in str(e):
                QMessageBox.warning(self, "Hata", "Bu kullanici adi zaten mevcut!")
            else:
                QMessageBox.critical(self, "Hata", str(e))


# ─────────────────────────────────────────────
#  KULLANICI YÖNETİMİ (Admin paneli)
# ─────────────────────────────────────────────
class KullaniciYonetimiDialog(QDialog):
    MODULLER = [
        ("ozet",       "Ozet / Dashboard"),
        ("stok",       "Stok"),
        ("talepler",   "Hammadde Talepleri"),
        ("siparisler", "Siparisler"),
        ("uretim",     "Uretim"),
        ("sevkiyat",   "Sevkiyat"),
        ("muhasebe",   "Muhasebe"),
        ("satinalma",  "Satinalma"),
        ("cariler",    "Cariler"),
        ("analiz",     "Analiz"),
        ("piyasa",     "Piyasa"),
    ]

    def __init__(self, cursor, conn, parent=None):
        super().__init__(parent)
        self.cursor = cursor
        self.conn   = conn
        self.secili_kullanici = None
        self.setWindowTitle("Kullanici Yonetimi")
        self.setMinimumSize(1000, 600)
        self.setStyleSheet("""
            QDialog { background:#f4f6f9; font-family:'Segoe UI'; }
            QTableWidget { background:white; border-radius:8px; border:1px solid #dcdde1; font-size:13px; }
            QHeaderView::section { background:#2c3e50; color:white; padding:8px; font-weight:bold; border:none; }
            QLabel { font-size:13px; font-weight:bold; color:#2c3e50; }
            QLineEdit, QComboBox { border:1.5px solid #dcdde1; border-radius:8px; padding:8px 12px; font-size:13px; background:white; }
            QLineEdit:focus { border:1.5px solid #c0392b; }
            QGroupBox { background:white; border-radius:8px; border:1px solid #dcdde1;
                        margin-top:8px; padding:12px; font-size:13px; }
            QGroupBox::title { color:#c0392b; font-weight:bold; padding:0 6px; }
            QCheckBox { font-size:13px; }
        """)
        self.init_ui()
        self.yenile()

    def init_ui(self):
        main = QHBoxLayout(self)
        main.setContentsMargins(15, 15, 15, 15)
        main.setSpacing(14)

        # ── SOL: Kullanici listesi ──
        sol = QWidget()
        sol_lay = QVBoxLayout(sol)
        sol_lay.setContentsMargins(0,0,0,0)
        sol_lay.setSpacing(8)

        lbl = QLabel("Kullanicilar")
        lbl.setStyleSheet("font-size:15px;font-weight:bold;color:#2c3e50;")
        sol_lay.addWidget(lbl)

        self.tablo = QTableWidget(0, 4)
        self.tablo.setHorizontalHeaderLabels(["ID", "Kullanici Adi", "Ad Soyad", "Rol"])
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tablo.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tablo.setAlternatingRowColors(True)
        self.tablo.verticalHeader().setVisible(False)
        self.tablo.clicked.connect(self._kullanici_sec)
        sol_lay.addWidget(self.tablo)

        btn_lay = QHBoxLayout()
        for etiket, stil, slot in [
            ("Yeni Kullanici", "background:#27ae60;color:white;border-radius:8px;padding:8px 12px;font-weight:bold;font-size:12px;", self._kullanici_ekle),
            ("Sifre Degistir", "background:#2980b9;color:white;border-radius:8px;padding:8px 12px;font-weight:bold;font-size:12px;", self._sifre_degistir),
            ("Rol Degistir",   "background:#e67e22;color:white;border-radius:8px;padding:8px 12px;font-weight:bold;font-size:12px;", self._rol_degistir),
            ("Aktif/Pasif",    "background:#8e44ad;color:white;border-radius:8px;padding:8px 12px;font-weight:bold;font-size:12px;", self._durum_degistir),
            ("Sil",            "background:#e74c3c;color:white;border-radius:8px;padding:8px 12px;font-weight:bold;font-size:12px;", self._kullanici_sil),
        ]:
            b = QPushButton(etiket); b.setStyleSheet(stil); b.clicked.connect(slot)
            btn_lay.addWidget(b)
        sol_lay.addLayout(btn_lay)
        main.addWidget(sol, 2)

        # ── SAĞ: İzin paneli ──
        sag = QWidget()
        sag_lay = QVBoxLayout(sag)
        sag_lay.setContentsMargins(0,0,0,0)
        sag_lay.setSpacing(8)

        izin_baslik = QHBoxLayout()
        self.lbl_izin_baslik = QLabel("Izin Duzenle — once kullanici secin")
        self.lbl_izin_baslik.setStyleSheet("font-size:15px;font-weight:bold;color:#2c3e50;")
        izin_baslik.addWidget(self.lbl_izin_baslik)
        izin_baslik.addStretch()

        btn_rol_sifirla = QPushButton("Role Gore Sifirla")
        btn_rol_sifirla.setStyleSheet("background:#95a5a6;color:white;border-radius:8px;padding:6px 12px;font-weight:bold;font-size:12px;border:none;")
        btn_rol_sifirla.clicked.connect(self._rol_sifirla)
        izin_baslik.addWidget(btn_rol_sifirla)

        btn_kaydet = QPushButton("Izinleri Kaydet")
        btn_kaydet.setStyleSheet("background:#c0392b;color:white;border-radius:8px;padding:6px 16px;font-weight:bold;font-size:13px;border:none;")
        btn_kaydet.clicked.connect(self._izin_kaydet)
        izin_baslik.addWidget(btn_kaydet)
        sag_lay.addLayout(izin_baslik)

        # Açıklama
        aciklama = QLabel(
            "Goruntule: sayfayi gorebilir   |   "
            "Duzenle: veri girebilir/degistirebilir"
        )
        aciklama.setStyleSheet("font-size:11px;color:#7f8c8d;font-weight:normal;background:transparent;")
        sag_lay.addWidget(aciklama)

        # İzin tablosu
        izin_grp = QGroupBox("Modul Izinleri")
        izin_grp_lay = QVBoxLayout(izin_grp)

        self.izin_tablo = QTableWidget(len(self.MODULLER), 3)
        self.izin_tablo.setHorizontalHeaderLabels(["Modul", "Goruntule", "Duzenle"])
        self.izin_tablo.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.izin_tablo.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.izin_tablo.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.izin_tablo.setColumnWidth(1, 100)
        self.izin_tablo.setColumnWidth(2, 100)
        self.izin_tablo.verticalHeader().setVisible(False)
        self.izin_tablo.setEditTriggers(QTableWidget.NoEditTriggers)
        self.izin_tablo.setAlternatingRowColors(True)
        self.izin_tablo.setShowGrid(False)
        self.izin_tablo.setEnabled(False)

        for i, (modul_key, modul_adi) in enumerate(self.MODULLER):
            lbl_item = QTableWidgetItem("  " + modul_adi)
            lbl_item.setData(Qt.UserRole, modul_key)
            self.izin_tablo.setItem(i, 0, lbl_item)
            self.izin_tablo.setRowHeight(i, 36)

            for col, tip in [(1, "goruntule"), (2, "duzenle")]:
                chk_widget = QWidget()
                chk_lay = QHBoxLayout(chk_widget)
                chk_lay.setContentsMargins(0,0,0,0)
                chk_lay.setAlignment(Qt.AlignCenter)
                chk = QCheckBox()
                chk.setObjectName("{}_{}".format(modul_key, tip))
                chk_lay.addWidget(chk)
                self.izin_tablo.setCellWidget(i, col, chk_widget)

        izin_grp_lay.addWidget(self.izin_tablo)
        sag_lay.addWidget(izin_grp)

        btn_kapat = QPushButton("Kapat")
        btn_kapat.setStyleSheet("background:#dcdde1;color:#2c3e50;border-radius:8px;padding:10px 24px;font-weight:bold;")
        btn_kapat.clicked.connect(self.accept)
        h = QHBoxLayout(); h.addStretch(); h.addWidget(btn_kapat)
        sag_lay.addLayout(h)

        main.addWidget(sag, 3)

    def yenile(self):
        try:
            self.cursor.execute("SELECT id, kullanici_adi, ad_soyad, rol, aktif FROM kullanicilar ORDER BY id")
            self.tablo.setRowCount(0)
            for i, row in enumerate(self.cursor.fetchall()):
                self.tablo.insertRow(i)
                for j, val in enumerate(row[:4]):
                    item = QTableWidgetItem(str(val or ""))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.tablo.setItem(i, j, item)
                aktif = row[4]
                durum_item = QTableWidgetItem("Aktif" if aktif else "Pasif")
                durum_item.setTextAlignment(Qt.AlignCenter)
                renk_map = {
                    "yonetici": "#c0392b", "satis": "#27ae60",
                    "uretim": "#8e44ad", "sevkiyat": "#e67e22",
                    "muhasebe": "#2980b9", "personel": "#7f8c8d"
                }
                rol_item = self.tablo.item(i, 3)
                if rol_item:
                    renk = renk_map.get(row[3], "#2c3e50")
                    rol_item.setForeground(QColor(renk))
                if not aktif:
                    for c in range(4):
                        item2 = self.tablo.item(i, c)
                        if item2: item2.setForeground(QColor("#bdc3c7"))
        except Exception as e:
            print("Kullanici yenile hatasi:", e)

    def _kullanici_sec(self, index):
        row = index.row()
        item = self.tablo.item(row, 1)
        if not item: return
        self.secili_kullanici = item.text()
        self.lbl_izin_baslik.setText("Izin Duzenle: {}".format(self.secili_kullanici))
        self.izin_tablo.setEnabled(True)
        self._izin_yukle(self.secili_kullanici)

    def _izin_yukle(self, kullanici_adi):
        try:
            self.cursor.execute(
                "SELECT modul, goruntule, duzenle FROM kullanici_izinler WHERE kullanici_adi=?",
                (kullanici_adi,))
            izinler = {m: (bool(g), bool(d)) for m, g, d in self.cursor.fetchall()}

            for i in range(self.izin_tablo.rowCount()):
                modul_key = self.izin_tablo.item(i, 0).data(Qt.UserRole)
                g, d = izinler.get(modul_key, (False, False))
                for col, deger in [(1, g), (2, d)]:
                    w = self.izin_tablo.cellWidget(i, col)
                    if w:
                        chk = w.findChild(QCheckBox)
                        if chk:
                            chk.blockSignals(True)
                            chk.setChecked(deger)
                            chk.blockSignals(False)
        except Exception as e:
            print("Izin yukle hatasi:", e)

    def _izin_kaydet(self):
        if not self.secili_kullanici:
            QMessageBox.warning(self, "Uyari", "Once bir kullanici secin.")
            return
        try:
            for i in range(self.izin_tablo.rowCount()):
                modul_key = self.izin_tablo.item(i, 0).data(Qt.UserRole)
                g_widget = self.izin_tablo.cellWidget(i, 1)
                d_widget = self.izin_tablo.cellWidget(i, 2)
                g = g_widget.findChild(QCheckBox).isChecked() if g_widget else False
                d = d_widget.findChild(QCheckBox).isChecked() if d_widget else False

                # Düzenle işaretliyse görüntüle de otomatik işaret
                if d: g = True

                self.cursor.execute("""
                    INSERT INTO kullanici_izinler (kullanici_adi, modul, goruntule, duzenle)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(kullanici_adi, modul) DO UPDATE SET goruntule=?, duzenle=?
                """, (self.secili_kullanici, modul_key, int(g), int(d), int(g), int(d)))

            self.conn.commit()
            # Checkboxları senkronize et (duzenle -> goruntule otomatik)
            self._izin_yukle(self.secili_kullanici)
            QMessageBox.information(self, "Kaydedildi",
                "{} icin izinler guncellendi.".format(self.secili_kullanici))
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _rol_sifirla(self):
        if not self.secili_kullanici:
            QMessageBox.warning(self, "Uyari", "Once bir kullanici secin.")
            return
        try:
            self.cursor.execute("SELECT rol FROM kullanicilar WHERE kullanici_adi=?",
                                (self.secili_kullanici,))
            row = self.cursor.fetchone()
            if not row: return
            rol = row[0]
            from database import ROL_VARSAYILAN_IZIN
            for modul, rol_izinleri in ROL_VARSAYILAN_IZIN.items():
                g, d = rol_izinleri.get(rol, (0, 0))
                self.cursor.execute("""
                    INSERT INTO kullanici_izinler (kullanici_adi, modul, goruntule, duzenle)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(kullanici_adi, modul) DO UPDATE SET goruntule=?, duzenle=?
                """, (self.secili_kullanici, modul, g, d, g, d))
            self.conn.commit()
            self._izin_yukle(self.secili_kullanici)
            QMessageBox.information(self, "Sifirlandi",
                "{} icin izinler '{}' rolune gore sifirlandi.".format(
                    self.secili_kullanici, rol))
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _kullanici_ekle(self):
        dlg = KullaniciEkleDialog(self.cursor, self.conn, self)
        if dlg.exec_() == QDialog.Accepted:
            # Yeni kullaniciya varsayilan izinleri yukle
            yeni_kadi = dlg.kullanici_adi
            yeni_rol  = dlg.rol
            from database import ROL_VARSAYILAN_IZIN
            for modul, rol_izinleri in ROL_VARSAYILAN_IZIN.items():
                g, d = rol_izinleri.get(yeni_rol, (0, 0))
                try:
                    self.cursor.execute("""
                        INSERT OR IGNORE INTO kullanici_izinler
                            (kullanici_adi, modul, goruntule, duzenle)
                        VALUES (?, ?, ?, ?)
                    """, (yeni_kadi, modul, g, d))
                except: pass
            self.conn.commit()
            self.yenile()

    def _sifre_degistir(self):
        row = self.tablo.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyari", "Bir kullanici secin."); return
        kadi = self.tablo.item(row, 1).text()
        yeni, ok = QInputDialog.getText(self, "Sifre Degistir",
            "{} icin yeni sifre:".format(kadi), QLineEdit.Password)
        if ok and yeni.strip():
            import hashlib
            h = hashlib.sha256(yeni.strip().encode()).hexdigest()
            self.cursor.execute("UPDATE kullanicilar SET sifre_hash=? WHERE kullanici_adi=?", (h, kadi))
            self.conn.commit()
            QMessageBox.information(self, "Tamam", "Sifre guncellendi.")

    def _rol_degistir(self):
        row = self.tablo.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyari", "Bir kullanici secin."); return
        kadi = self.tablo.item(row, 1).text()
        roller = ["personel","yonetici","satis","uretim","sevkiyat","muhasebe"]
        mevcut_rol = self.tablo.item(row, 3).text()
        rol, ok = QInputDialog.getItem(self, "Rol Degistir",
            "{} icin yeni rol:".format(kadi), roller,
            roller.index(mevcut_rol) if mevcut_rol in roller else 0, False)
        if ok:
            self.cursor.execute("UPDATE kullanicilar SET rol=? WHERE kullanici_adi=?", (rol, kadi))
            self.conn.commit()
            self.yenile()

    def _durum_degistir(self):
        row = self.tablo.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyari", "Bir kullanici secin."); return
        kadi = self.tablo.item(row, 1).text()
        self.cursor.execute("SELECT aktif FROM kullanicilar WHERE kullanici_adi=?", (kadi,))
        r = self.cursor.fetchone()
        if r:
            yeni = 0 if r[0] else 1
            self.cursor.execute("UPDATE kullanicilar SET aktif=? WHERE kullanici_adi=?", (yeni, kadi))
            self.conn.commit()
            self.yenile()

    def _kullanici_sil(self):
        row = self.tablo.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyari", "Bir kullanici secin."); return
        kadi = self.tablo.item(row, 1).text()
        uid  = self.tablo.item(row, 0).text()
        cevap = QMessageBox.question(self, "Sil",
            "{} silinsin mi?".format(kadi),
            QMessageBox.Yes | QMessageBox.No)
        if cevap == QMessageBox.Yes:
            self.cursor.execute("DELETE FROM kullanicilar WHERE id=?", (uid,))
            self.cursor.execute("DELETE FROM kullanici_izinler WHERE kullanici_adi=?", (kadi,))
            self.conn.commit()
            if self.secili_kullanici == kadi:
                self.secili_kullanici = None
                self.izin_tablo.setEnabled(False)
                self.lbl_izin_baslik.setText("Izin Duzenle — once kullanici secin")
            self.yenile()
