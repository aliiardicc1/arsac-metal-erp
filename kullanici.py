"""
Arsac Metal ERP â€” KullanÄ±cÄ± YÃ¶netim Sistemi
Bulut modu: API Ã¼zerinden giriÅŸ doÄŸrulama.
Lokal modu: SQLite Ã¼zerinden giriÅŸ doÄŸrulama.
"""
import hashlib
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

try:
    from log import log_yaz
except:
    def log_yaz(c, n, i, d=""): pass

# Bulut modu kontrolÃ¼
import json, os, sys
def _bulut_modu():
    try:
        yol = os.path.join(
            os.path.dirname(sys.executable) if getattr(sys, 'frozen', False)
            else os.path.dirname(os.path.abspath(__file__)), "ayarlar.json")
        with open(yol, "r", encoding="utf-8") as f:
            return json.load(f).get("bulut_modu", False)
    except:
        return False

BULUT_MODU = _bulut_modu()


def sifre_hashle(sifre):
    return hashlib.sha256(sifre.encode('utf-8')).hexdigest()


def kullanici_dogrula(cursor, kullanici_adi, sifre):
    """
    Bulut modunda API'ye istek atar.
    Lokal modunda SQLite sorgular.
    DÃ¶ner: (rol, ad_soyad) veya None
    """
    if BULUT_MODU:
        try:
            from database_bulut import giris_yap
            sonuc = giris_yap(kullanici_adi.strip(), sifre)
            if sonuc and sonuc.get("token"):
                return sonuc.get("rol", "personel"), sonuc.get("ad_soyad", "")
        except Exception as e:
            print(f"[Bulut] GiriÅŸ hatasÄ±: {e}")
        return None
    else:
        try:
            h = sifre_hashle(sifre)
            cursor.execute(
                "SELECT rol, ad_soyad, aktif FROM kullanicilar WHERE kullanici_adi=? AND sifre_hash=?",
                (kullanici_adi.strip(), h))
            row = cursor.fetchone()
            if row and row[2] == 1:
                return row[0], row[1]
        except Exception as e:
            print(f"DoÄŸrulama hatasÄ±: {e}")
        return None


def varsayilan_admin_olustur(cursor, conn):
    if BULUT_MODU:
        return  # API tarafÄ±nda zaten oluÅŸturuldu
    try:
        cursor.execute("UPDATE kullanicilar SET rol='yonetici' WHERE rol='admin'")
        conn.commit()
        cursor.execute("SELECT COUNT(*) FROM kullanicilar WHERE rol='yonetici'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO kullanicilar (kullanici_adi, sifre_hash, rol, ad_soyad, aktif)
                VALUES (?, ?, 'yonetici', 'Sistem Yoneticisi', 1)
            """, ("aliiardicc", sifre_hashle("arsac2024")))
            conn.commit()
    except Exception as e:
        print(f"Varsayilan yonetici hatasi: {e}")


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
#  GÄ°RÄ°Å EKRANI
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class GirisEkrani(QDialog):
    def __init__(self, cursor, conn):
        super().__init__()
        self.cursor = cursor
        self.conn   = conn
        self.sonuc  = None
        self._sifre = ""  # main.py'de token almak iÃ§in
        self.setWindowTitle("ARSAC METAL ERP â€” GiriÅŸ")
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

        lbl_logo = QLabel("ARSAC METAL")
        lbl_logo.setAlignment(Qt.AlignCenter)
        lbl_logo.setStyleSheet("font-size:28px;font-weight:900;color:#c0392b;letter-spacing:2px;")
        lay.addWidget(lbl_logo)

        lbl_alt = QLabel("ERP YÃ¶netim Sistemi")
        lbl_alt.setAlignment(Qt.AlignCenter)
        lbl_alt.setStyleSheet("font-size:13px;color:#7f8c8d;margin-bottom:30px;")
        lay.addWidget(lbl_alt)
        lay.addSpacing(30)

        self.lbl_hata = QLabel("")
        self.lbl_hata.setAlignment(Qt.AlignCenter)
        self.lbl_hata.setFixedHeight(36)
        self.lbl_hata.setStyleSheet("background:#e74c3c;color:white;border-radius:8px;font-size:13px;font-weight:bold;")
        self.lbl_hata.hide()
        lay.addWidget(self.lbl_hata)
        lay.addSpacing(10)

        lbl_k = QLabel("KullanÄ±cÄ± AdÄ±")
        lbl_k.setStyleSheet("font-size:12px;font-weight:bold;color:#7f8c8d;margin-bottom:4px;")
        lay.addWidget(lbl_k)
        self.txt_kullanici = QLineEdit()
        self.txt_kullanici.setPlaceholderText("KullanÄ±cÄ± adÄ±nÄ±zÄ± girin")
        self.txt_kullanici.setFixedHeight(46)
        lay.addWidget(self.txt_kullanici)
        lay.addSpacing(16)

        lbl_s = QLabel("Åifre")
        lbl_s.setStyleSheet("font-size:12px;font-weight:bold;color:#7f8c8d;margin-bottom:4px;")
        lay.addWidget(lbl_s)
        self.txt_sifre = QLineEdit()
        self.txt_sifre.setPlaceholderText("Åifrenizi girin")
        self.txt_sifre.setEchoMode(QLineEdit.Password)
        self.txt_sifre.setFixedHeight(46)
        self.txt_sifre.returnPressed.connect(self.giris_yap)
        lay.addWidget(self.txt_sifre)
        lay.addSpacing(24)

        self.btn_giris = QPushButton("GÄ°RÄ°Å YAP")
        self.btn_giris.setObjectName("GirisBtn")
        self.btn_giris.setFixedHeight(50)
        self.btn_giris.clicked.connect(self.giris_yap)
        lay.addWidget(self.btn_giris)
        lay.addStretch()

        mod_etiket = "â˜ Bulut Modu" if BULUT_MODU else "ğŸ’¾ Lokal Mod"
        lbl_bilgi = QLabel(f"v1.0 Â© 2024 Arsac Metal  â€¢  {mod_etiket}")
        lbl_bilgi.setAlignment(Qt.AlignCenter)
        lbl_bilgi.setStyleSheet("font-size:11px;color:#bdc3c7;")
        lay.addWidget(lbl_bilgi)

        self.txt_kullanici.returnPressed.connect(lambda: self.txt_sifre.setFocus())

    def giris_yap(self):
        kullanici = self.txt_kullanici.text().strip()
        sifre     = self.txt_sifre.text()

        if not kullanici or not sifre:
            self._hata("KullanÄ±cÄ± adÄ± ve ÅŸifre boÅŸ bÄ±rakÄ±lamaz!")
            return

        self.btn_giris.setEnabled(False)
        self.btn_giris.setText("GiriÅŸ yapÄ±lÄ±yor...")

        sonuc = kullanici_dogrula(self.cursor, kullanici, sifre)
        if sonuc:
            rol, ad_soyad = sonuc
            self.sonuc  = (rol, kullanici, ad_soyad)
            self._sifre = sifre
            try:
                log_yaz(self.cursor, self.conn, "GIRIS", f"{kullanici} ({rol}) giris yapti")
            except:
                pass
            self.accept()
        else:
            self._hata("KullanÄ±cÄ± adÄ± veya ÅŸifre hatalÄ±!")
            self.txt_sifre.clear()
            self.txt_sifre.setFocus()
            self.btn_giris.setEnabled(True)
            self.btn_giris.setText("GÄ°RÄ°Å YAP")

    def _hata(self, mesaj):
        self.lbl_hata.setText(f"âš ï¸  {mesaj}")
        self.lbl_hata.show()


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
#  YENÄ° KULLANICI EKLE
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
                padding:8px; font-size:13px; background:white; color:#2c3e50;
            }
        """)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(10)

        lay.addWidget(QLabel("Kullanici Adi"))
        self.txt_kadi = QLineEdit()
        self.txt_kadi.setFixedHeight(36)
        lay.addWidget(self.txt_kadi)

        lay.addWidget(QLabel("Ad Soyad"))
        self.txt_ad = QLineEdit()
        self.txt_ad.setFixedHeight(36)
        lay.addWidget(self.txt_ad)

        lay.addWidget(QLabel("Sifre"))
        self.txt_sifre = QLineEdit()
        self.txt_sifre.setEchoMode(QLineEdit.Password)
        self.txt_sifre.setFixedHeight(36)
        lay.addWidget(self.txt_sifre)

        lay.addWidget(QLabel("Rol"))
        self.cmb_rol = QComboBox()
        self.cmb_rol.addItems(["personel","yonetici","satis","uretim","sevkiyat","muhasebe"])
        self.cmb_rol.setFixedHeight(36)
        lay.addWidget(self.cmb_rol)

        btn_lay = QHBoxLayout()
        btn_lay.addStretch()
        btn_ekle = QPushButton("Ekle")
        btn_ekle.setFixedHeight(36)
        btn_ekle.setStyleSheet("background:#c0392b;color:white;border-radius:7px;padding:6px 20px;font-weight:bold;border:none;")
        btn_ekle.clicked.connect(self._ekle)
        btn_lay.addWidget(btn_ekle)
        lay.addLayout(btn_lay)

    def _ekle(self):
        kadi  = self.txt_kadi.text().strip()
        ad    = self.txt_ad.text().strip()
        sifre = self.txt_sifre.text().strip()
        rol   = self.cmb_rol.currentText()

        if not kadi or not sifre:
            QMessageBox.warning(self, "Eksik", "Kullanici adi ve sifre zorunludur.")
            return

        if BULUT_MODU:
            try:
                import urllib.request as urlreq
                import json as _json
                from database_bulut import _post, API_URL
                _post("/kullanici_ekle", {
                    "kullanici_adi": kadi, "ad_soyad": ad,
                    "sifre": sifre, "rol": rol
                })
                self.kullanici_adi = kadi
                self.rol = rol
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
        else:
            try:
                from datetime import datetime
                h = sifre_hashle(sifre)
                now = datetime.now().strftime("%d.%m.%Y %H:%M")
                self.cursor.execute("""
                    INSERT INTO kullanicilar (kullanici_adi, sifre_hash, rol, ad_soyad, aktif, olusturma_tarihi)
                    VALUES (?, ?, ?, ?, 1, ?)
                """, (kadi, h, rol, ad, now))
                self.conn.commit()
                self.kullanici_adi = kadi
                self.rol = rol
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
#  KULLANICI YÃ–NETÄ°MÄ° DÄ°ALOGU
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class KullaniciYonetimiDialog(QDialog):
    def __init__(self, cursor, conn, parent=None):
        super().__init__(parent)
        self.cursor = cursor
        self.conn   = conn
        self.secili_kullanici = None
        self.setWindowTitle("Kullanici Yonetimi")
        self.setMinimumSize(900, 600)
        self.setStyleSheet("""
            QDialog { background:#f4f6f9; }
            QLabel { color:#2c3e50; font-size:12px; }
            QTableWidget { background:white; border:1px solid #dcdde1; gridline-color:#f0f0f0; }
            QHeaderView::section { background:#2c3e50; color:white; padding:6px; font-weight:bold; font-size:12px; }
        """)
        self._build()
        self.yenile()

    def _build(self):
        main = QHBoxLayout(self)
        main.setContentsMargins(16, 16, 16, 16)
        main.setSpacing(12)

        # Sol â€” kullanici listesi
        sol = QVBoxLayout()
        baslik = QLabel("Kullanicilar")
        baslik.setStyleSheet("font-size:15px;font-weight:bold;color:#2c3e50;")
        sol.addWidget(baslik)

        self.tablo = QTableWidget()
        self.tablo.setColumnCount(5)
        self.tablo.setHorizontalHeaderLabels(["ID","Kullanici","Ad Soyad","Rol","Durum"])
        self.tablo.horizontalHeader().setStretchLastSection(True)
        self.tablo.setSelectionBehavior(QTableWidget.SelectRows)
        self.tablo.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tablo.clicked.connect(self._kullanici_sec)
        sol.addWidget(self.tablo)

        btn_lay = QHBoxLayout()
        for etiket, slot in [("+ Ekle", self._kullanici_ekle),
                              ("Sifre", self._sifre_degistir),
                              ("Rol",   self._rol_degistir),
                              ("Durum", self._durum_degistir),
                              ("Sil",   self._kullanici_sil)]:
            btn = QPushButton(etiket)
            btn.setFixedHeight(32)
            btn.setStyleSheet("background:#2c3e50;color:white;border-radius:6px;padding:4px 12px;font-size:12px;border:none;")
            btn.clicked.connect(slot)
            btn_lay.addWidget(btn)
        sol.addLayout(btn_lay)
        main.addLayout(sol, 2)

        # SaÄŸ â€” izin yÃ¶netimi
        sag = QVBoxLayout()
        self.lbl_izin_baslik = QLabel("Izin Duzenle â€” once kullanici secin")
        self.lbl_izin_baslik.setStyleSheet("font-size:14px;font-weight:bold;color:#2c3e50;")
        sag.addWidget(self.lbl_izin_baslik)

        MODULLER = [
            ("ozet","Ozet"),("stok","Stok"),("talepler","Talepler"),
            ("siparisler","Siparisler"),("uretim","Uretim"),("sevkiyat","Sevkiyat"),
            ("muhasebe","Muhasebe"),("satinalma","Satinalma"),("cariler","Cariler"),
            ("analiz","Analiz"),("piyasa","Piyasa"),
        ]

        self.izin_tablo = QTableWidget(len(MODULLER), 3)
        self.izin_tablo.setHorizontalHeaderLabels(["Modul","Goruntule","Duzenle"])
        self.izin_tablo.horizontalHeader().setStretchLastSection(True)
        self.izin_tablo.setEnabled(False)

        for i, (key, ad) in enumerate(MODULLER):
            item = QTableWidgetItem(ad)
            item.setData(Qt.UserRole, key)
            item.setFlags(Qt.ItemIsEnabled)
            self.izin_tablo.setItem(i, 0, item)
            for col in [1, 2]:
                w = QWidget()
                h = QHBoxLayout(w)
                h.setAlignment(Qt.AlignCenter)
                h.setContentsMargins(0,0,0,0)
                chk = QCheckBox()
                h.addWidget(chk)
                self.izin_tablo.setCellWidget(i, col, w)

        sag.addWidget(self.izin_tablo)

        btn_izin_lay = QHBoxLayout()
        btn_kaydet = QPushButton("Izinleri Kaydet")
        btn_kaydet.setFixedHeight(34)
        btn_kaydet.setStyleSheet("background:#27ae60;color:white;border-radius:6px;padding:4px 16px;font-weight:bold;border:none;")
        btn_kaydet.clicked.connect(self._izin_kaydet)
        btn_sifirla = QPushButton("Role Gore Sifirla")
        btn_sifirla.setFixedHeight(34)
        btn_sifirla.setStyleSheet("background:#e67e22;color:white;border-radius:6px;padding:4px 16px;font-weight:bold;border:none;")
        btn_sifirla.clicked.connect(self._rol_sifirla)
        btn_izin_lay.addWidget(btn_kaydet)
        btn_izin_lay.addWidget(btn_sifirla)
        btn_izin_lay.addStretch()
        sag.addLayout(btn_izin_lay)
        main.addLayout(sag, 3)

    def yenile(self):
        try:
            if BULUT_MODU:
                from database_bulut import API_URL, _token
                import urllib.request, json
                req = urllib.request.Request(
                    API_URL + "/kullanicilar",
                    headers={"Authorization": "Bearer " + (_token or "")}
                )
                with urllib.request.urlopen(req, timeout=10) as r:
                    sonuc = json.loads(r.read().decode())
                if isinstance(sonuc, dict):
                    rows = sonuc.get("kullanicilar", [])
                elif isinstance(sonuc, list):
                    rows = sonuc
                else:
                    rows = []
            else:
                self.cursor.execute("SELECT id, kullanici_adi, ad_soyad, rol, aktif FROM kullanicilar ORDER BY id")
                rows = self.cursor.fetchall()

            self.tablo.setRowCount(0)
            for i, row in enumerate(rows):
                if isinstance(row, dict):
                    vals = [row.get("id",""), row.get("kullanici_adi",""),
                            row.get("ad_soyad",""), row.get("rol",""), row.get("aktif",1)]
                else:
                    vals = list(row)
                self.tablo.insertRow(i)
                for j, val in enumerate(vals[:4]):
                    item = QTableWidgetItem(str(val or ""))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.tablo.setItem(i, j, item)
                aktif = vals[4]
                durum_item = QTableWidgetItem("Aktif" if aktif else "Pasif")
                durum_item.setTextAlignment(Qt.AlignCenter)
                self.tablo.setItem(i, 4, durum_item)
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
            if BULUT_MODU:
                from database_bulut import API_URL, _token
                import urllib.request, json
                req = urllib.request.Request(
                    API_URL + "/izinler/{}".format(kullanici_adi),
                    headers={"Authorization": "Bearer " + (_token or "")}
                )
                with urllib.request.urlopen(req, timeout=10) as r:
                    izinler_raw = json.loads(r.read().decode())
                if isinstance(izinler_raw, dict):
                    izinler = {m: (bool(v[0]) if isinstance(v,(list,tuple)) else bool(v), 
                                   bool(v[1]) if isinstance(v,(list,tuple)) else False) 
                               for m, v in izinler_raw.items()}
                else:
                    izinler = {}
            else:
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
            izinler = {}
            for i in range(self.izin_tablo.rowCount()):
                modul_key = self.izin_tablo.item(i, 0).data(Qt.UserRole)
                g_widget = self.izin_tablo.cellWidget(i, 1)
                d_widget = self.izin_tablo.cellWidget(i, 2)
                g = g_widget.findChild(QCheckBox).isChecked() if g_widget else False
                d = d_widget.findChild(QCheckBox).isChecked() if d_widget else False
                if d: g = True
                izinler[modul_key] = (int(g), int(d))

            if BULUT_MODU:
                from database_bulut import API_URL, _token
                import urllib.request, json
                body = json.dumps(izinler).encode("utf-8")
                req = urllib.request.Request(
                    API_URL + "/izinler/{}".format(self.secili_kullanici),
                    data=body,
                    headers={"Content-Type": "application/json",
                             "Authorization": "Bearer " + (_token or "")},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=10) as r:
                    r.read()
            else:
                for modul, (g, d) in izinler.items():
                    self.cursor.execute("""
                        INSERT INTO kullanici_izinler (kullanici_adi, modul, goruntule, duzenle)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(kullanici_adi, modul) DO UPDATE SET goruntule=?, duzenle=?
                    """, (self.secili_kullanici, modul, g, d, g, d))
                self.conn.commit()

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
            if BULUT_MODU:
                from database_bulut import _get, _post, ROL_VARSAYILAN_IZIN
                kullanicilar = _get("/kullanicilar")
                rol = next((k["rol"] for k in kullanicilar if k["kullanici_adi"] == self.secili_kullanici), "personel")
            else:
                self.cursor.execute("SELECT rol FROM kullanicilar WHERE kullanici_adi=?", (self.secili_kullanici,))
                row = self.cursor.fetchone()
                if not row: return
                rol = row[0]
                from database import ROL_VARSAYILAN_IZIN

            izinler = {}
            for modul, rol_izinleri in ROL_VARSAYILAN_IZIN.items():
                g, d = rol_izinleri.get(rol, (0, 0))
                izinler[modul] = (g, d)

            if BULUT_MODU:
                from database_bulut import API_URL, _token
                import urllib.request, json
                body = json.dumps(izinler).encode("utf-8")
                req = urllib.request.Request(
                    API_URL + "/izinler/{}".format(self.secili_kullanici),
                    data=body,
                    headers={"Content-Type": "application/json",
                             "Authorization": "Bearer " + (_token or "")},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=10) as r:
                    r.read()
            else:
                for modul, (g, d) in izinler.items():
                    self.cursor.execute("""
                        INSERT INTO kullanici_izinler (kullanici_adi, modul, goruntule, duzenle)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(kullanici_adi, modul) DO UPDATE SET goruntule=?, duzenle=?
                    """, (self.secili_kullanici, modul, g, d, g, d))
                self.conn.commit()

            self._izin_yukle(self.secili_kullanici)
            QMessageBox.information(self, "Sifirlandi",
                "{} icin izinler '{}' rolune gore sifirlandi.".format(self.secili_kullanici, rol))
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _kullanici_ekle(self):
        dlg = KullaniciEkleDialog(self.cursor, self.conn, self)
        if dlg.exec_() == QDialog.Accepted:
            if not BULUT_MODU:
                yeni_kadi = dlg.kullanici_adi
                yeni_rol  = dlg.rol
                from database import ROL_VARSAYILAN_IZIN
                for modul, rol_izinleri in ROL_VARSAYILAN_IZIN.items():
                    g, d = rol_izinleri.get(yeni_rol, (0, 0))
                    try:
                        self.cursor.execute("""
                            INSERT OR IGNORE INTO kullanici_izinler (kullanici_adi, modul, goruntule, duzenle)
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
            if BULUT_MODU:
                try:
                    from database_bulut import _post
                    _post("/sifre_degistir", {"kullanici_adi": kadi, "sifre": yeni.strip()})
                    QMessageBox.information(self, "Tamam", "Sifre guncellendi.")
                except Exception as e:
                    QMessageBox.critical(self, "Hata", str(e))
            else:
                h = sifre_hashle(yeni.strip())
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
            if BULUT_MODU:
                try:
                    from database_bulut import _post
                    _post("/rol_degistir", {"kullanici_adi": kadi, "rol": rol})
                except Exception as e:
                    QMessageBox.critical(self, "Hata", str(e)); return
            else:
                self.cursor.execute("UPDATE kullanicilar SET rol=? WHERE kullanici_adi=?", (rol, kadi))
                self.conn.commit()
            self.yenile()

    def _durum_degistir(self):
        row = self.tablo.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyari", "Bir kullanici secin."); return
        kadi = self.tablo.item(row, 1).text()
        if BULUT_MODU:
            try:
                from database_bulut import _post
                _post("/durum_degistir", {"kullanici_adi": kadi})
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e)); return
        else:
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
            "{} silinsin mi?".format(kadi), QMessageBox.Yes | QMessageBox.No)
        if cevap == QMessageBox.Yes:
            if BULUT_MODU:
                try:
                    from database_bulut import _post
                    _post("/kullanici_sil", {"kullanici_adi": kadi})
                except Exception as e:
                    QMessageBox.critical(self, "Hata", str(e)); return
            else:
                self.cursor.execute("DELETE FROM kullanicilar WHERE id=?", (uid,))
                self.cursor.execute("DELETE FROM kullanici_izinler WHERE kullanici_adi=?", (kadi,))
                self.conn.commit()
            if self.secili_kullanici == kadi:
                self.secili_kullanici = None
                self.izin_tablo.setEnabled(False)
                self.lbl_izin_baslik.setText("Izin Duzenle â€” once kullanici secin")
            self.yenile()

