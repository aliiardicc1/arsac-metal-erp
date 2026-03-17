"""
Arsac Metal ERP — Not & Takvim Modülü
Aylık takvim görünümü + hatırlatıcı + renkli öncelik
"""
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QDate, QTimer
from PyQt5.QtGui import QColor, QFont
from datetime import datetime, date
try:
    from log import log_yaz
except:
    def log_yaz(c,n,i,d=""): pass

ONCELIK_RENK = {
    "Düşük":   ("#2980b9", "#eaf4fb"),
    "Normal":  ("#27ae60", "#eafaf1"),
    "Yüksek":  ("#e67e22", "#fef9e7"),
    "Acil":    ("#e74c3c", "#fde8e8"),
}

# ─────────────────────────────────────────────
#  Not Ekleme / Düzenleme Dialog
# ─────────────────────────────────────────────
class NotDialog(QDialog):
    def __init__(self, cursor, conn, tarih=None, not_id=None, parent=None):
        super().__init__(parent)
        self.cursor = cursor
        self.conn   = conn
        self.not_id = not_id
        self.setWindowTitle("📝 Not Ekle" if not not_id else "📝 Notu Düzenle")
        self.setFixedSize(440, 420)
        self.setStyleSheet("""
            QDialog { background:#f4f6f9; font-family:'Segoe UI'; }
            QLineEdit, QTextEdit, QComboBox, QDateEdit {
                border:1.5px solid #dcdde1; border-radius:8px;
                padding:8px 12px; font-size:13px; background:white;
            }
            QLineEdit:focus, QTextEdit:focus { border:1.5px solid #c0392b; }
            QLabel { font-size:12px; font-weight:bold; color:#7f8c8d; }
        """)
        self.init_ui(tarih)
        if not_id:
            self._yukle(not_id)

    def init_ui(self, tarih):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20,20,20,20)
        lay.setSpacing(8)

        def _row(lbl, widget):
            l = QLabel(lbl); lay.addWidget(l); lay.addWidget(widget)

        # Başlık
        self.txt_baslik = QLineEdit()
        self.txt_baslik.setPlaceholderText("Not başlığı...")
        self.txt_baslik.setFixedHeight(40)
        _row("Başlık:", self.txt_baslik)

        # Tarih
        self.dt_tarih = QDateEdit()
        self.dt_tarih.setCalendarPopup(True)
        self.dt_tarih.setFixedHeight(40)
        self.dt_tarih.setDisplayFormat("dd.MM.yyyy")
        if tarih:
            self.dt_tarih.setDate(QDate(tarih.year, tarih.month, tarih.day))
        else:
            self.dt_tarih.setDate(QDate.currentDate())
        _row("Tarih:", self.dt_tarih)

        # Öncelik
        self.cmb_oncelik = QComboBox()
        self.cmb_oncelik.addItems(["Düşük", "Normal", "Yüksek", "Acil"])
        self.cmb_oncelik.setCurrentText("Normal")
        self.cmb_oncelik.setFixedHeight(40)
        _row("Öncelik:", self.cmb_oncelik)

        # Hatırlatıcı
        hat_lay = QHBoxLayout()
        self.chk_hatirlatici = QCheckBox("Hatırlatıcı ekle")
        self.chk_hatirlatici.setStyleSheet("font-size:13px;color:#2c3e50;font-weight:bold;")
        self.dt_hatirlatici = QDateEdit()
        self.dt_hatirlatici.setCalendarPopup(True)
        self.dt_hatirlatici.setFixedHeight(40)
        self.dt_hatirlatici.setDisplayFormat("dd.MM.yyyy")
        self.dt_hatirlatici.setDate(QDate.currentDate())
        self.dt_hatirlatici.setEnabled(False)
        self.chk_hatirlatici.toggled.connect(self.dt_hatirlatici.setEnabled)
        hat_lay.addWidget(self.chk_hatirlatici)
        hat_lay.addWidget(self.dt_hatirlatici)
        lay.addLayout(hat_lay)

        # Not metni
        self.txt_not = QTextEdit()
        self.txt_not.setPlaceholderText("Not içeriği...")
        self.txt_not.setFixedHeight(90)
        _row("Not:", self.txt_not)

        lay.addSpacing(6)

        # Butonlar
        btn_lay = QHBoxLayout()
        btn_iptal = QPushButton("İptal")
        btn_iptal.setStyleSheet("background:#dcdde1;color:#2c3e50;border-radius:8px;padding:10px 20px;font-weight:bold;font-size:13px;")
        btn_iptal.clicked.connect(self.reject)

        btn_kaydet = QPushButton("💾 Kaydet")
        btn_kaydet.setStyleSheet("background:#c0392b;color:white;border-radius:8px;padding:10px 20px;font-weight:bold;font-size:13px;")
        btn_kaydet.clicked.connect(self._kaydet)

        btn_lay.addWidget(btn_iptal)
        btn_lay.addStretch()
        btn_lay.addWidget(btn_kaydet)
        lay.addLayout(btn_lay)

    def _yukle(self, not_id):
        self.cursor.execute(
            "SELECT baslik, tarih, oncelik, not_metni, hatirlatici FROM notlar WHERE id=?", (not_id,))
        row = self.cursor.fetchone()
        if not row: return
        baslik, tarih, oncelik, metin, hat = row
        self.txt_baslik.setText(baslik or "")
        try:
            d = datetime.strptime(tarih, "%Y-%m-%d")
            self.dt_tarih.setDate(QDate(d.year, d.month, d.day))
        except: pass
        self.cmb_oncelik.setCurrentText(oncelik or "Normal")
        self.txt_not.setPlainText(metin or "")
        if hat:
            try:
                dh = datetime.strptime(hat, "%Y-%m-%d")
                self.dt_hatirlatici.setDate(QDate(dh.year, dh.month, dh.day))
                self.chk_hatirlatici.setChecked(True)
            except: pass

    def _kaydet(self):
        baslik = self.txt_baslik.text().strip()
        if not baslik:
            QMessageBox.warning(self, "Hata", "Başlık boş olamaz!")
            return

        tarih    = self.dt_tarih.date().toString("yyyy-MM-dd")
        oncelik  = self.cmb_oncelik.currentText()
        metin    = self.txt_not.toPlainText().strip()
        hat      = self.dt_hatirlatici.date().toString("yyyy-MM-dd") if self.chk_hatirlatici.isChecked() else None

        if self.not_id:
            self.cursor.execute("""
                UPDATE notlar SET baslik=?, tarih=?, oncelik=?, not_metni=?, hatirlatici=?
                WHERE id=?
            """, (baslik, tarih, oncelik, metin, hat, self.not_id))
            log_yaz(self.cursor, self.conn, "NOT_GUNCELLEME", f"{baslik} | {tarih}")
        else:
            self.cursor.execute("""
                INSERT INTO notlar (baslik, tarih, oncelik, not_metni, hatirlatici, olusturma)
                VALUES (?,?,?,?,?,?)
            """, (baslik, tarih, oncelik, metin, hat, datetime.now().strftime("%Y-%m-%d")))
            log_yaz(self.cursor, self.conn, "NOT_EKLENDI", f"{baslik} | {tarih} | {oncelik}")

        self.conn.commit()
        self.accept()


# ─────────────────────────────────────────────
#  Takvim Widget (Dashboard'a gömülür)
# ─────────────────────────────────────────────
class TakvimWidget(QWidget):
    def __init__(self, cursor, conn):
        super().__init__()
        self.cursor  = cursor
        self.conn    = conn
        self.bugun   = date.today()
        self.aktif_yil  = self.bugun.year
        self.aktif_ay   = self.bugun.month
        self.notlar_map = {}   # "YYYY-MM-DD" -> [notlar]
        self.setStyleSheet("""
            QWidget { background:white; font-family:'Segoe UI',Arial; }
            QPushButton#GunBtn {
                border:1px solid #ecf0f1; border-radius:6px;
                font-size:13px; font-weight:bold; background:white; color:#2c3e50;
                font-family:'Segoe UI',Arial;
            }
            QPushButton#GunBtn:hover { background:#fde8e8; border-color:#c0392b; }
            QPushButton#BosBtn {
                border:none; background:transparent;
            }
        """)
        self.init_ui()

    def init_ui(self):
        self.ana_lay = QVBoxLayout(self)
        self.ana_lay.setContentsMargins(8,8,8,8)
        self.ana_lay.setSpacing(6)

        # Başlık: ay/yıl + ileri geri
        self.nav_lay = QHBoxLayout()
        btn_geri = QPushButton("‹")
        btn_geri.setFixedSize(28,28)
        btn_geri.setStyleSheet("background:#ecf0f1;border-radius:14px;font-size:16px;font-weight:bold;color:#2c3e50;border:none;")
        btn_geri.clicked.connect(self._onceki_ay)

        btn_ileri = QPushButton("›")
        btn_ileri.setFixedSize(28,28)
        btn_ileri.setStyleSheet("background:#ecf0f1;border-radius:14px;font-size:16px;font-weight:bold;color:#2c3e50;border:none;")
        btn_ileri.clicked.connect(self._sonraki_ay)

        self.lbl_ay = QLabel()
        self.lbl_ay.setAlignment(Qt.AlignCenter)
        self.lbl_ay.setStyleSheet("font-size:14px;font-weight:bold;color:#2c3e50;")

        btn_bugun = QPushButton("Bugün")
        btn_bugun.setFixedHeight(26)
        btn_bugun.setStyleSheet("background:#c0392b;color:white;border-radius:5px;font-size:11px;font-weight:bold;padding:2px 10px;border:none;")
        btn_bugun.clicked.connect(self._bugun_git)

        self.nav_lay.addWidget(btn_geri)
        self.nav_lay.addWidget(self.lbl_ay)
        self.nav_lay.addWidget(btn_ileri)
        self.nav_lay.addStretch()
        self.nav_lay.addWidget(btn_bugun)
        self.ana_lay.addLayout(self.nav_lay)

        # Gün isimleri
        gun_lay = QHBoxLayout()
        gun_lay.setSpacing(2)
        for g in ["Pzt","Sal","Çar","Per","Cum","Cmt","Paz"]:
            l = QLabel(g)
            l.setAlignment(Qt.AlignCenter)
            l.setFixedHeight(22)
            l.setStyleSheet(f"font-size:11px;font-weight:bold;color:{'#c0392b' if g=='Paz' else '#7f8c8d'};")
            gun_lay.addWidget(l)
        self.ana_lay.addLayout(gun_lay)

        # Gün butonları grid
        self.grid_widget = QWidget()
        self.grid_lay = QGridLayout(self.grid_widget)
        self.grid_lay.setSpacing(2)
        self.grid_lay.setContentsMargins(0,0,0,0)
        self.ana_lay.addWidget(self.grid_widget)

        # Alt: yaklaşan notlar listesi
        self.ana_lay.addWidget(self._ayrac("📌 Yaklaşan Notlar"))
        self.liste = QListWidget()
        self.liste.setMaximumHeight(130)
        self.liste.setStyleSheet("""
            QListWidget { border:1px solid #ecf0f1; border-radius:6px; font-size:12px; background:white; }
            QListWidget::item { padding:5px 8px; border-bottom:1px solid #f4f6f9; }
            QListWidget::item:selected { background:#fde8e8; color:#c0392b; }
        """)
        self.liste.itemDoubleClicked.connect(self._liste_duzenle)
        self.ana_lay.addWidget(self.liste)

        # Not ekle butonu
        btn_not = QPushButton("➕  Yeni Not Ekle")
        btn_not.setFixedHeight(34)
        btn_not.setStyleSheet("background:#27ae60;color:white;border-radius:8px;font-weight:bold;font-size:13px;border:none;")
        btn_not.clicked.connect(lambda: self._not_ekle())
        self.ana_lay.addWidget(btn_not)

        self.takvim_yenile()

    def _ayrac(self, metin):
        l = QLabel(metin)
        l.setStyleSheet("font-size:12px;font-weight:bold;color:#2c3e50;padding-top:4px;")
        return l

    def _onceki_ay(self):
        if self.aktif_ay == 1: self.aktif_ay=12; self.aktif_yil-=1
        else: self.aktif_ay -= 1
        self.takvim_yenile()

    def _sonraki_ay(self):
        if self.aktif_ay == 12: self.aktif_ay=1; self.aktif_yil+=1
        else: self.aktif_ay += 1
        self.takvim_yenile()

    def _bugun_git(self):
        self.aktif_yil = self.bugun.year
        self.aktif_ay  = self.bugun.month
        self.takvim_yenile()

    def takvim_yenile(self):
        # Notları DB'den çek
        self.notlar_map = {}
        try:
            ay_str = f"{self.aktif_yil}-{self.aktif_ay:02d}"
            self.cursor.execute(
                "SELECT id, baslik, tarih, oncelik FROM notlar WHERE tarih LIKE ?",
                (f"{ay_str}%",))
            for not_id, baslik, tarih, oncelik in self.cursor.fetchall():
                self.notlar_map.setdefault(tarih, []).append((not_id, baslik, oncelik))
        except: pass

        # Ay başlığı
        ay_adlari = ["","Ocak","Şubat","Mart","Nisan","Mayıs","Haziran",
                     "Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"]
        self.lbl_ay.setText(f"{ay_adlari[self.aktif_ay]} {self.aktif_yil}")

        # Grid temizle
        for i in reversed(range(self.grid_lay.count())):
            w = self.grid_lay.itemAt(i).widget()
            if w: w.deleteLater()

        # Takvim hesapla
        from calendar import monthrange, weekday
        ilk_gun_haftaici = weekday(self.aktif_yil, self.aktif_ay, 1)  # 0=Pzt
        toplam_gun = monthrange(self.aktif_yil, self.aktif_ay)[1]

        col = ilk_gun_haftaici
        row = 0
        for g in range(1, toplam_gun + 1):
            tarih_str = f"{self.aktif_yil}-{self.aktif_ay:02d}-{g:02d}"
            gunun_notlari = self.notlar_map.get(tarih_str, [])
            bugun_mu = (g == self.bugun.day and
                        self.aktif_ay == self.bugun.month and
                        self.aktif_yil == self.bugun.year)

            btn = QPushButton(str(g))
            btn.setObjectName("GunBtn")
            btn.setFixedSize(40, 36)

            if bugun_mu:
                btn.setStyleSheet("""
                    QPushButton { background:#c0392b;color:white;border-radius:6px;
                                  font-size:13px;font-weight:bold;border:none;
                                  font-family:'Segoe UI',Arial; }
                    QPushButton:hover { background:#a93226; }
                """)
            elif gunun_notlari:
                # VADE notu varsa özel renk
                vade_var = any("VADE:" in (b or "") for _, b, _ in gunun_notlari)
                if vade_var:
                    # Kaç gün kaldı?
                    try:
                        from datetime import date as _d
                        gun_kalan = (_d(self.aktif_yil, self.aktif_ay, g) - self.bugun).days
                        if gun_kalan < 0:
                            bg, brd = "#fde8e8", "#e74c3c"   # geçmiş vade — kırmızı
                        elif gun_kalan <= 3:
                            bg, brd = "#fef9e7", "#e67e22"   # 3 gün içinde — turuncu
                        else:
                            bg, brd = "#eaf4fb", "#2980b9"   # normal vade — mavi
                    except:
                        bg, brd = "#eaf4fb", "#2980b9"
                else:
                    oncelik = gunun_notlari[0][2]
                    bg  = ONCELIK_RENK.get(oncelik, ("#2c3e50","#f4f6f9"))[1]
                    brd = ONCELIK_RENK.get(oncelik, ("#2c3e50","#f4f6f9"))[0]
                btn.setStyleSheet(
                    "QPushButton {{ background:{bg};color:#2c3e50;border-radius:6px;"
                    "font-size:13px;font-weight:bold;border:2px solid {brd};"
                    "font-family:'Segoe UI',Arial; }}"
                    "QPushButton:hover {{ background:{brd};color:white; }}".format(
                        bg=bg, brd=brd))
                # Küçük nokta göstergesi için tooltip
                btn.setToolTip("\n".join(b for _, b, _ in gunun_notlari))
            elif col == 6:  # Pazar
                btn.setStyleSheet("""
                    QPushButton { background:white;color:#e74c3c;border:1px solid #ecf0f1;
                                  border-radius:6px;font-size:13px;font-weight:bold;
                                  font-family:'Segoe UI',Arial; }
                    QPushButton:hover { background:#fde8e8; }
                """)

            d = date(self.aktif_yil, self.aktif_ay, g)
            btn.clicked.connect(lambda _, dd=d, ts=tarih_str, nn=gunun_notlari: self._gun_tikla(dd, ts, nn))
            self.grid_lay.addWidget(btn, row, col)

            col += 1
            if col == 7: col = 0; row += 1

        # Yaklaşan notlar listesi
        self._yaklasan_yenile()

    def _gun_tikla(self, d, tarih_str, notlar):
        if notlar:
            # Gün menüsü: mevcut notlar + yeni ekle
            menu = QMenu(self)
            menu.setStyleSheet("""
                QMenu { background:white; border:1px solid #dcdde1; border-radius:8px;
                        padding:6px; font-size:13px; font-family:'Segoe UI'; }
                QMenu::item { padding:8px 18px; border-radius:4px; }
                QMenu::item:selected { background:#fde8e8; color:#c0392b; }
                QMenu::separator { height:1px; background:#dcdde1; margin:4px 8px; }
            """)
            for not_id, baslik, oncelik in notlar:
                renk = ONCELIK_RENK.get(oncelik, ("#2c3e50",""))[0]
                act = menu.addAction(f"● {baslik}  [{oncelik}]")
                act.setData(not_id)
            menu.addSeparator()
            menu.addAction("➕  Yeni Not Ekle")
            secim = menu.exec_(QCursor.pos())
            if secim:
                if secim.data():
                    self._not_duzenle(secim.data())
                else:
                    self._not_ekle(d)
        else:
            self._not_ekle(d)

    def _not_ekle(self, tarih=None):
        if tarih is None:
            tarih = date(self.aktif_yil, self.aktif_ay, 1)
        dlg = NotDialog(self.cursor, self.conn, tarih=tarih, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self.takvim_yenile()

    def _not_duzenle(self, not_id):
        dlg = NotDialog(self.cursor, self.conn, not_id=not_id, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self.takvim_yenile()

    def _liste_duzenle(self, item):
        not_id = item.data(Qt.UserRole)
        if not_id:
            self._not_duzenle(not_id)

    def _yaklasan_yenile(self):
        self.liste.clear()
        try:
            bugun_str = self.bugun.strftime("%Y-%m-%d")
            # Geçmiş vadeler + gelecek 30 günlük notlar
            self.cursor.execute("""
                SELECT id, baslik, tarih, oncelik FROM notlar
                WHERE tarih >= date(?, '-7 days')
                ORDER BY
                    CASE WHEN baslik LIKE 'VADE:%' THEN 0 ELSE 1 END,
                    tarih ASC
                LIMIT 12
            """, (bugun_str,))
            rows = self.cursor.fetchall()
            if not rows:
                item = QListWidgetItem("  Yaklaşan not yok")
                item.setForeground(QColor("#bdc3c7"))
                self.liste.addItem(item)
                return
            for not_id, baslik, tarih, oncelik in rows:
                try:
                    d = datetime.strptime(tarih, "%Y-%m-%d")
                    gun_fark = (d.date() - self.bugun).days
                    if gun_fark < 0:   gun_txt = "{} gün geçti!".format(abs(gun_fark))
                    elif gun_fark == 0: gun_txt = "BUGÜN"
                    elif gun_fark == 1: gun_txt = "Yarın"
                    else:               gun_txt = "{} gün sonra".format(gun_fark)
                except:
                    gun_txt = tarih

                vade_notu = baslik.startswith("VADE:")
                if vade_notu:
                    if gun_fark < 0:
                        ikon, renk = "💸", "#e74c3c"   # geçmiş
                    elif gun_fark == 0:
                        ikon, renk = "🔴", "#e74c3c"   # bugün
                    elif gun_fark <= 3:
                        ikon, renk = "🟠", "#e67e22"   # yakın
                    else:
                        ikon, renk = "💰", "#2980b9"   # normal
                    metin = "  {} {}  —  {}".format(ikon, baslik, gun_txt)
                else:
                    renk = ONCELIK_RENK.get(oncelik, ("#2c3e50",""))[0]
                    metin = "  ● {}  —  {}".format(baslik, gun_txt)

                item = QListWidgetItem(metin)
                item.setForeground(QColor(renk))
                item.setData(Qt.UserRole, not_id)
                self.liste.addItem(item)
        except Exception as e:
            print("Yaklaşan notlar hatasi: {}".format(e))

    def hatirlatici_kontrol(self):
        try:
            bugun_str = self.bugun.strftime("%Y-%m-%d")

            # Vadesi gecmis veya yaklasan vade notlari (7 gun onceden itibaren)
            self.cursor.execute(
                "SELECT baslik, tarih, not_metni FROM notlar "
                "WHERE hatirlatici <= ? AND baslik LIKE 'VADE:%' "
                "ORDER BY tarih ASC",
                (bugun_str,))
            vadeler = self.cursor.fetchall()

            # Normal hatirlaticilar (sadece bugun)
            self.cursor.execute(
                "SELECT baslik, oncelik FROM notlar "
                "WHERE hatirlatici=? AND baslik NOT LIKE 'VADE:%'",
                (bugun_str,))
            notlar = self.cursor.fetchall()

            if vadeler:
                from datetime import datetime as _dt2
                satirlar = []
                for baslik, tarih, metin in vadeler:
                    try:
                        gun = (_dt2.strptime(tarih, "%Y-%m-%d").date() - self.bugun).days
                        if gun < 0:
                            satirlar.append("  GECIKTI {} gun: {}".format(abs(gun), baslik))
                        elif gun == 0:
                            satirlar.append("  BUGUN DOLUYOR: {}".format(baslik))
                        elif gun <= 7:
                            satirlar.append("  {} gun kaldi: {}".format(gun, baslik))
                    except:
                        satirlar.append("  " + baslik)
                if satirlar:
                    mesaj = "VADE UYARISI\n\n" + "\n".join(satirlar)
                    QMessageBox.warning(None, "Vade Uyarisi", mesaj)

            if notlar:
                satirlar = ["  {} [{}]".format(b, o) for b, o in notlar]
                mesaj = "Bugun {} hatirlaticiniz var:\n\n".format(len(notlar))
                mesaj += "\n".join(satirlar)
                QMessageBox.information(None, "Hatirlatici", mesaj)

        except Exception as e:
            print("Hatirlatici hatasi: {}".format(e))