"""
Arsac Metal ERP — Uretim Modulu
Ayri is emirleri ve parca bazli takip
"""
from styles import BTN_BLUE, BTN_GRAY, BTN_GREEN, BTN_ORANGE, BTN_PRIMARY, BTN_PURPLE, DIALOG_QSS, DURUM_RENK, GROUPBOX_QSS, INPUT, INPUT_QSS, LIST_QSS, SAYFA_QSS, TABLO_QSS, make_badge, make_buton, tab_qss, tablo_sag_tik_menu_ekle
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont
from datetime import datetime

try:
    from log import log_yaz
except:
    def log_yaz(c, n, i, d=""): pass

DURUMLAR   = ["Beklemede", "Uretimde", "Tamamlandi", "Iptal"]
INPUT  = "border:1.5px solid #dcdde1;border-radius:7px;padding:5px 10px;font-size:13px;background:white;color:#2c3e50;"
STL_PRI    = "background:#8e44ad;color:white;border-radius:8px;padding:7px 18px;font-weight:bold;font-size:13px;border:none;"
STL_BLUE   = "background:#2980b9;color:white;border-radius:8px;padding:7px 16px;font-weight:bold;font-size:13px;border:none;"
STL_GREEN  = "background:#27ae60;color:white;border-radius:8px;padding:7px 16px;font-weight:bold;font-size:13px;border:none;"
STL_RED    = "background:#e74c3c;color:white;border-radius:8px;padding:7px 16px;font-weight:bold;font-size:13px;border:none;"
STL_GRAY   = "background:#dcdde1;color:#2c3e50;border-radius:8px;padding:7px 16px;font-weight:bold;font-size:13px;"




def _tablo(headers, stretch_col=None):
    t = QTableWidget(0, len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.setEditTriggers(QTableWidget.NoEditTriggers)
    t.setAlternatingRowColors(True)
    t.setShowGrid(False)
    t.verticalHeader().setVisible(False)
    t.verticalHeader().setDefaultSectionSize(44)
    t.setSelectionBehavior(QTableWidget.SelectRows)
    t.setWordWrap(False)
    t.setStyleSheet("""
        QTableWidget{background:white;border-radius:10px;border:1px solid #dcdde1;color:#2c3e50;}
        QTableWidget::item{color:#2c3e50;padding:8px 10px;}
        QTableWidget::item:selected{background:#8e44ad;color:white;}
        QHeaderView::section{background:#2c3e50;color:white;padding:9px 10px;font-weight:bold;border:none;min-height:36px;}
        QTableWidget::item:alternate{background:#f8f9fa;}
    """)
    if stretch_col is not None:
        t.horizontalHeader().setSectionResizeMode(stretch_col, QHeaderView.Stretch)
        for c in range(len(headers)):
            if c != stretch_col:
                t.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeToContents)
    return t


def _item(text, align=Qt.AlignCenter, fg="#2c3e50", uid=None):
    it = QTableWidgetItem(str(text))
    it.setTextAlignment(align)
    it.setForeground(QColor(fg))
    if uid is not None:
        it.setData(Qt.UserRole, uid)
    return it


# ─── Yeni / Duzenle Is Emri Dialog ────────────────────────────
class IsEmriDialog(QDialog):
    def __init__(self, cursor, conn, is_id=None, parent=None):
        super().__init__(parent)
        self.cursor = cursor; self.conn = conn; self.is_id = is_id
        self.setWindowTitle("Is Emri" if is_id else "Yeni Is Emri")
        self.setMinimumSize(680, 560)
        self.setStyleSheet(DIALOG_QSS)
        self._build()
        if is_id:
            self._yukle()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(20, 16, 20, 16); lay.setSpacing(10)
        lay.addWidget(self._baslik_lbl())

        # Bilgi kutusu
        gb = QGroupBox("Is Emri Bilgileri")
        fg = QGridLayout(gb); fg.setSpacing(8)

        def le(ph, h=36):
            w = QLineEdit(); w.setPlaceholderText(ph); w.setFixedHeight(h)
            w.setStyleSheet(INPUT); return w

        self.txt_musteri = le("Musteri adi *")
        self.txt_aciklama = le("Aciklama / proje notu")

        self.cmb_siparis = QComboBox(); self.cmb_siparis.setFixedHeight(36)
        self.cmb_siparis.setStyleSheet(INPUT)
        self.cmb_siparis.addItem("-- Siparis baglamadan devam --", None)
        try:
            self.cursor.execute(
                "SELECT id, sip_no, musteri FROM siparisler WHERE durum NOT IN ('Sevk Edildi','Iptal') ORDER BY id DESC")
            for sid, sno, mus in self.cursor.fetchall():
                self.cmb_siparis.addItem("{} — {}".format(sno, mus or "-"), sid)
        except: pass
        self.cmb_siparis.currentIndexChanged.connect(self._siparis_sec)

        self.dt_termin = QDateEdit(); self.dt_termin.setCalendarPopup(True)
        self.dt_termin.setDisplayFormat("dd.MM.yyyy"); self.dt_termin.setFixedHeight(36)
        self.dt_termin.setStyleSheet(INPUT)
        from PyQt5.QtCore import QDate
        self.dt_termin.setDate(QDate.currentDate().addDays(7))

        self.cmb_durum = QComboBox(); self.cmb_durum.addItems(DURUMLAR)
        self.cmb_durum.setFixedHeight(36); self.cmb_durum.setStyleSheet(INPUT)

        self.txt_operatr = le("Operatör / makine")

        for row, (lbl_txt, wgt) in enumerate([
            ("Musteri *:",   self.txt_musteri),
            ("Siparis Bagla:", self.cmb_siparis),
            ("Termin:",      self.dt_termin),
            ("Durum:",       self.cmb_durum),
            ("Operatör:",    self.txt_operatr),
            ("Aciklama:",    self.txt_aciklama),
        ]):
            fg.addWidget(QLabel(lbl_txt), row, 0)
            fg.addWidget(wgt, row, 1)
        lay.addWidget(gb)

        # Parca listesi
        pb = QGroupBox("Parcalar / Kalemler")
        pv = QVBoxLayout(pb)

        # Sutun basliklarI
        hdr = QWidget(); hdr.setStyleSheet("background:#f0f0f0;border-radius:5px;")
        hl = QHBoxLayout(hdr); hl.setContentsMargins(4, 3, 4, 3); hl.setSpacing(6)
        for txt, w in [("Parca Adi", None), ("Adet", 70), ("Kg/Adet", 85), ("Malzeme", 90), ("", 28)]:
            l = QLabel(txt)
            l.setStyleSheet("font-size:11px;font-weight:bold;color:#7f8c8d;")
            l.setAlignment(Qt.AlignCenter if w else Qt.AlignLeft | Qt.AlignVCenter)
            if w: l.setFixedWidth(w)
            else: l.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            hl.addWidget(l)
        pv.addWidget(hdr)

        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True); self.scroll.setFixedHeight(160)
        self.scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        self.parca_w = QWidget(); self.parca_lay = QVBoxLayout(self.parca_w)
        self.parca_lay.setContentsMargins(0, 0, 0, 0); self.parca_lay.setSpacing(3)
        self.parca_lay.addStretch()
        self.scroll.setWidget(self.parca_w)
        pv.addWidget(self.scroll)

        btn_p = QPushButton("+ Parca Ekle"); btn_p.setFixedHeight(32)
        btn_p.setStyleSheet(STL_GREEN); btn_p.clicked.connect(lambda: self._parca_satir())
        pv.addWidget(btn_p)
        lay.addWidget(pb)

        # Kaydet / Iptal
        bh = QHBoxLayout(); bh.addStretch()
        bi = QPushButton("Iptal"); bi.setStyleSheet(STL_GRAY); bi.clicked.connect(self.reject)
        bk = QPushButton("Kaydet"); bk.setStyleSheet(STL_PRI); bk.clicked.connect(self._kaydet)
        bh.addWidget(bi); bh.addWidget(bk); lay.addLayout(bh)

        self._parca_satir()

    def _baslik_lbl(self):
        l = QLabel("Yeni Is Emri" if not self.is_id else "Is Emri Duzenle")
        l.setStyleSheet("font-size:16px;font-weight:bold;color:#8e44ad;"); return l

    def _siparis_sec(self, idx):
        sid = self.cmb_siparis.currentData()
        if not sid: return
        try:
            self.cursor.execute("SELECT musteri FROM siparisler WHERE id=?", (sid,))
            r = self.cursor.fetchone()
            if r and r[0]: self.txt_musteri.setText(r[0])
            self.cursor.execute(
                "SELECT urun_adi, adet, kalinlik FROM siparis_kalemleri WHERE siparis_id=?", (sid,))
            rows = self.cursor.fetchall()
            while self.parca_lay.count() > 1:
                it = self.parca_lay.itemAt(0)
                if it and it.widget():
                    it.widget().deleteLater(); self.parca_lay.removeItem(it)
                else: break
            for urun, adet, kal in rows:
                self._parca_satir(urun or "", int(adet or 1), 0.0, str(kal or ""))
        except Exception as e:
            print("Siparis sec hatasi:", e)

    def _parca_satir(self, ad="", adet=1, kg=0.0, malzeme=""):
        w = QWidget(); w.setFixedHeight(38)
        l = QHBoxLayout(w); l.setContentsMargins(2, 2, 2, 2); l.setSpacing(6)

        txt = QLineEdit(); txt.setPlaceholderText("Parca adi"); txt.setText(ad)
        txt.setFixedHeight(32); txt.setStyleSheet(INPUT)
        txt.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        spn_a = QSpinBox(); spn_a.setRange(1, 99999); spn_a.setValue(int(adet))
        spn_a.setFixedSize(70, 32); spn_a.setStyleSheet(INPUT)

        spn_k = QDoubleSpinBox(); spn_k.setRange(0, 99999); spn_k.setValue(float(kg))
        spn_k.setDecimals(2); spn_k.setFixedSize(85, 32); spn_k.setStyleSheet(INPUT)

        txt_m = QLineEdit(); txt_m.setPlaceholderText("ST37"); txt_m.setText(malzeme)
        txt_m.setFixedSize(90, 32); txt_m.setStyleSheet(INPUT)

        btn_s = QPushButton("x"); btn_s.setFixedSize(28, 28)
        btn_s.setStyleSheet("background:#e74c3c;color:white;border-radius:5px;font-weight:bold;border:none;")
        btn_s.clicked.connect(lambda: (w.deleteLater(),))

        for wgt in [txt, spn_a, spn_k, txt_m, btn_s]: l.addWidget(wgt)
        self.parca_lay.insertWidget(self.parca_lay.count() - 1, w)

    def _parca_satirlari(self):
        parcalar = []
        for i in range(self.parca_lay.count() - 1):
            w = self.parca_lay.itemAt(i).widget()
            if not w: continue
            txts = w.findChildren(QLineEdit)
            spins_i = w.findChildren(QSpinBox)
            spins_d = w.findChildren(QDoubleSpinBox)
            if not txts: continue
            ad = txts[0].text().strip()
            if not ad: continue
            adet = spins_i[0].value() if spins_i else 1
            kg = spins_d[0].value() if spins_d else 0.0
            malzeme = txts[1].text().strip() if len(txts) > 1 else ""
            parcalar.append((ad, adet, kg, malzeme))
        return parcalar

    def _is_no_uret(self):
        yil = datetime.now().strftime("%Y")
        ay  = datetime.now().strftime("%m")
        self.cursor.execute("SELECT COUNT(*) FROM isler WHERE is_no LIKE ?", ("IE-{}{}-%" .format(yil, ay),))
        n = self.cursor.fetchone()[0]
        return "IE-{}{}-{:03d}".format(yil, ay, n + 1)

    def _kaydet(self):
        musteri = self.txt_musteri.text().strip()
        if not musteri:
            QMessageBox.warning(self, "Eksik", "Musteri adi zorunlu!"); return
        parcalar = self._parca_satirlari()
        if not parcalar:
            QMessageBox.warning(self, "Eksik", "En az bir parca girin!"); return
        try:
            tarih  = datetime.now().strftime("%d.%m.%Y")
            termin = self.dt_termin.date().toString("dd.MM.yyyy")
            durum  = self.cmb_durum.currentText()
            oper   = self.txt_operatr.text().strip()
            acikl  = self.txt_aciklama.text().strip()
            toplam_kg = sum(a * k for _, a, k, _ in parcalar)
            sid    = self.cmb_siparis.currentData()

            if self.is_id:
                self.cursor.execute(
                    "UPDATE isler SET musteri=?,termin=?,durum=?,toplam_kg=?,ilerleme=? WHERE id=?",
                    (musteri, termin, durum, toplam_kg, 0, self.is_id))
                self.cursor.execute("DELETE FROM parcalar WHERE is_no=(SELECT is_no FROM isler WHERE id=?)", (self.is_id,))
                self.cursor.execute("SELECT is_no FROM isler WHERE id=?", (self.is_id,))
                is_no = self.cursor.fetchone()[0]
            else:
                is_no = self._is_no_uret()
                self.cursor.execute(
                    "INSERT INTO isler (is_no,musteri,tarih,durum,termin,toplam_kg,ilerleme) VALUES (?,?,?,?,?,?,0)",
                    (is_no, musteri, tarih, durum, termin, toplam_kg))

            for ad, adet, kg, malzeme in parcalar:
                self.cursor.execute(
                    "INSERT INTO parcalar (is_no,parca_adi,adet,birim_kg,durum,biten_adet) VALUES (?,?,?,?,'Beklemede',0)",
                    (is_no, ad, adet, kg))

            # Siparis ile bagla
            if sid and not self.is_id:
                try:
                    self.cursor.execute("UPDATE siparisler SET durum='Uretimde' WHERE id=?", (sid,))
                except: pass

            self.conn.commit()
            log_yaz(self.cursor, self.conn, "IS_EMRI", "{} — {}".format(is_no, musteri))
            QMessageBox.information(self, "Tamam", "{} numarali is emri kaydedildi.".format(is_no))
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _yukle(self):
        try:
            self.cursor.execute(
                "SELECT is_no,musteri,termin,durum FROM isler WHERE id=?", (self.is_id,))
            r = self.cursor.fetchone()
            if not r: return
            is_no, mus, ter, dur = r
            self.txt_musteri.setText(mus or "")
            self.cmb_durum.setCurrentText(dur or "Beklemede")
            from PyQt5.QtCore import QDate
            if ter:
                try:
                    parts = ter.split(".")
                    self.dt_termin.setDate(QDate(int(parts[2]), int(parts[1]), int(parts[0])))
                except: pass
            self.cursor.execute("SELECT parca_adi,adet,birim_kg FROM parcalar WHERE is_no=?", (is_no,))
            while self.parca_lay.count() > 1:
                it = self.parca_lay.itemAt(0)
                if it and it.widget():
                    it.widget().deleteLater(); self.parca_lay.removeItem(it)
                else: break
            for ad, adet, kg in self.cursor.fetchall():
                self._parca_satir(ad or "", int(adet or 1), float(kg or 0))
        except Exception as e:
            print("Is emri yukle hatasi:", e)


# ─── Parca Durum Dialog ────────────────────────────────────────
class ParcaDurumDialog(QDialog):
    def __init__(self, cursor, conn, is_no, parent=None):
        super().__init__(parent)
        self.cursor = cursor; self.conn = conn; self.is_no = is_no
        self.setWindowTitle("Parca Takibi — " + str(is_no))
        self.setMinimumSize(640, 420)
        self.setStyleSheet(DIALOG_QSS)
        self._build()
        self._yukle()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(16, 14, 16, 14); lay.setSpacing(10)
        lbl = QLabel("Is No: <b>" + str(self.is_no) + "</b>")
        lbl.setStyleSheet("font-size:14px;color:#8e44ad;")
        lay.addWidget(lbl)

        self.tablo = _tablo(["Parca Adi", "Toplam", "Tamamlanan", "Kalan", "Durum", "Islem"], stretch_col=0)
        lay.addWidget(self.tablo)

        # Toplu islemler
        bh = QHBoxLayout(); bh.setSpacing(8)
        bh.addWidget(QLabel("Secilileri:"))
        for txt, stl, d in [
            ("Uretimde",   STL_BLUE,  "Uretimde"),
            ("Tamamlandi", STL_GREEN, "Tamamlandi"),
        ]:
            b = QPushButton(txt); b.setFixedHeight(32); b.setStyleSheet(stl)
            b.clicked.connect(lambda _, dd=d: self._toplu(dd))
            bh.addWidget(b)
        bh.addStretch()
        btn_k = QPushButton("Kapat"); btn_k.setFixedHeight(32); btn_k.setStyleSheet(STL_GRAY)
        btn_k.clicked.connect(self.accept); bh.addWidget(btn_k)
        lay.addLayout(bh)

    def _yukle(self):
        try:
            self.cursor.execute(
                "SELECT id,parca_adi,adet,biten_adet,durum FROM parcalar WHERE is_no=?",
                (self.is_no,))
            rows = self.cursor.fetchall()
            self.tablo.setRowCount(0)
            for i, (pid, ad, adet, biten, durum) in enumerate(rows):
                self.tablo.insertRow(i); self.tablo.setRowHeight(i, 44)
                durum = durum or "Beklemede"
                af = int(adet or 1); bf = int(biten or 0); kalan = max(0, af - bf)

                self.tablo.setItem(i, 0, _item(ad or "-", Qt.AlignLeft | Qt.AlignVCenter, uid=pid))
                self.tablo.setItem(i, 1, _item(str(af), uid=pid))

                # Tamamlanan adet — düzenlenebilir spinbox
                spn = QSpinBox(); spn.setRange(0, af); spn.setValue(bf)
                spn.setFixedHeight(30)
                spn.setStyleSheet(
                    "border:1.5px solid #dcdde1;border-radius:5px;"
                    "padding:2px 6px;background:white;color:#2c3e50;font-size:12px;")
                spn.valueChanged.connect(
                    lambda val, p=pid, a=af: self._tam_adet_degisti(p, val, a))
                self.tablo.setCellWidget(i, 2, spn)

                self.tablo.setItem(i, 3, _item(str(kalan), uid=pid))
                self.tablo.setCellWidget(i, 4, make_badge(durum))

                # Hızlı butonlar
                bw = QWidget(); bl = QHBoxLayout(bw)
                bl.setContentsMargins(2, 2, 2, 2); bl.setSpacing(4)
                for txt, rk, nd in [("Uretimde", "#2980b9", "Uretimde"),
                                     ("Bitti",    "#27ae60", "Tamamlandi")]:
                    b = QPushButton(txt); b.setFixedHeight(26)
                    b.setStyleSheet(
                        "background:{};color:white;border-radius:4px;"
                        "font-size:11px;border:none;padding:0 6px;".format(rk))
                    b.clicked.connect(lambda _, p=pid, d=nd: self._guncelle(p, d))
                    bl.addWidget(b)
                self.tablo.setCellWidget(i, 5, bw)
        except Exception as e:
            print("Parca yukle hatasi:", e)

    def _tam_adet_degisti(self, pid, yeni_adet, toplam_adet):
        """Tamamlanan adet spinbox değişince DB güncelle, tamamsa sevkiyata düşür."""
        try:
            if yeni_adet == toplam_adet:
                # Tümü tamamlandı
                self.cursor.execute(
                    "UPDATE parcalar SET biten_adet=?, durum='Tamamlandi' WHERE id=?",
                    (yeni_adet, pid))
                self.conn.commit()
                self._is_ilerleme_guncelle()
                self._sevkiyata_dus(pid)
            else:
                durum = "Uretimde" if yeni_adet > 0 else "Beklemede"
                self.cursor.execute(
                    "UPDATE parcalar SET biten_adet=?, durum=? WHERE id=?",
                    (yeni_adet, durum, pid))
                self.conn.commit()
                self._is_ilerleme_guncelle()
            # Kalan sütununu güncelle
            for r in range(self.tablo.rowCount()):
                it = self.tablo.item(r, 0)
                if it and it.data(Qt.UserRole) == pid:
                    spn = self.tablo.cellWidget(r, 2)
                    tam = spn.value() if spn else yeni_adet
                    kalan = max(0, toplam_adet - tam)
                    self.tablo.item(r, 3).setText(str(kalan))
                    break
        except Exception as e:
            print("Tam adet degisti hatasi:", e)

    def _guncelle(self, pid, durum):
        try:
            if durum == "Tamamlandi":
                self.cursor.execute(
                    "UPDATE parcalar SET durum=?,biten_adet=adet WHERE id=?", (durum, pid))
            else:
                self.cursor.execute("UPDATE parcalar SET durum=? WHERE id=?", (durum, pid))
            self.conn.commit()
            self._yukle()
            self._is_ilerleme_guncelle()
            # Tamamlandıysa sevkiyata düşür
            if durum == "Tamamlandi":
                self._sevkiyata_dus(pid)
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _sevkiyata_dus(self, pid):
        """Tamamlanan parçayı sevkiyat bekleme listesine ekle."""
        try:
            # Parça bilgilerini al
            self.cursor.execute(
                "SELECT parca_adi, adet, is_no FROM parcalar WHERE id=?", (pid,))
            r = self.cursor.fetchone()
            if not r:
                print("Sevkiyata dus: parca bulunamadi pid=", pid); return
            parca_adi, adet, is_no = r

            # Zaten bekliyor mu?
            self.cursor.execute(
                "SELECT id FROM parca_sevk_bekliyor "
                "WHERE kalem_id=? AND durum='Bekliyor'", (pid,))
            if self.cursor.fetchone():
                return  # Zaten var

            # is_no = "IE-ARSC-2026-0001" → sip_no = "ARSC-2026-0001"
            sip_no_tahmin = is_no[3:] if (is_no or "").startswith("IE-") else (is_no or "")

            # Önce direkt sip_no ile dene
            self.cursor.execute(
                "SELECT id, sip_no, musteri FROM siparisler WHERE sip_no=?",
                (sip_no_tahmin,))
            sr = self.cursor.fetchone()

            # Bulunamazsa LIKE ile dene
            if not sr and sip_no_tahmin:
                self.cursor.execute(
                    "SELECT id, sip_no, musteri FROM siparisler "
                    "WHERE sip_no LIKE ? ORDER BY id DESC LIMIT 1",
                    ("%{}%".format(sip_no_tahmin),))
                sr = self.cursor.fetchone()

            # Hâlâ bulunamazsa musteri üzerinden dene
            if not sr:
                self.cursor.execute(
                    "SELECT s.id, s.sip_no, s.musteri FROM siparisler s "
                    "JOIN isler i ON i.musteri=s.musteri "
                    "WHERE i.is_no=? ORDER BY s.id DESC LIMIT 1", (is_no,))
                sr = self.cursor.fetchone()

            sip_id  = sr[0] if sr else None
            sip_no  = sr[1] if sr else sip_no_tahmin
            musteri = sr[2] if sr else "-"

            tarih = datetime.now().strftime("%d.%m.%Y")
            self.cursor.execute("""
                INSERT INTO parca_sevk_bekliyor
                    (siparis_id, sip_no, musteri, kalem_id, parca_adi,
                     tamamlanan_adet, bekleyen_adet, tarih, durum)
                VALUES (?,?,?,?,?,?,?,?,'Bekliyor')
            """, (sip_id, sip_no, musteri, pid, parca_adi,
                  float(adet or 1), float(adet or 1), tarih))
            self.conn.commit()
            print("Sevkiyata dustu: {} | sip_no={} | sip_id={}".format(
                parca_adi, sip_no, sip_id))
        except Exception as e:
            print("Sevkiyata dus HATA:", e)
            import traceback; traceback.print_exc()

    def _toplu(self, durum):
        secili = list(set(it.row() for it in self.tablo.selectedItems()))
        if not secili:
            QMessageBox.warning(self, "Uyari", "Satirlari secin."); return
        try:
            for r in secili:
                it = self.tablo.item(r, 0)
                if not it: continue
                pid = it.data(Qt.UserRole)
                if not pid: continue
                if durum == "Tamamlandi":
                    self.cursor.execute(
                        "UPDATE parcalar SET durum=?,biten_adet=adet WHERE id=?", (durum, pid))
                else:
                    self.cursor.execute("UPDATE parcalar SET durum=? WHERE id=?", (durum, pid))
            self.conn.commit(); self._yukle(); self._is_ilerleme_guncelle()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _is_ilerleme_guncelle(self):
        try:
            self.cursor.execute(
                "SELECT COUNT(*), SUM(CASE WHEN durum='Tamamlandi' THEN 1 ELSE 0 END) FROM parcalar WHERE is_no=?",
                (self.is_no,))
            toplam, tam = self.cursor.fetchone()
            if toplam:
                oran = int((tam or 0) / toplam * 100)
                self.cursor.execute("UPDATE isler SET ilerleme=? WHERE is_no=?", (oran, self.is_no))
                if oran == 100:
                    self.cursor.execute(
                        "UPDATE isler SET durum='Tamamlandi' WHERE is_no=?", (self.is_no,))
            self.conn.commit()
        except: pass


# ─── Ana Uretim Sayfasi ────────────────────────────────────────
class UretimSayfasi(QWidget):
    def __init__(self, cursor, conn, user_role="yonetici", kullanici_adi=""):
        super().__init__()
        self.cursor = cursor; self.conn = conn
        self.user_role = user_role; self.kullanici_adi = kullanici_adi
        self.readonly = (user_role == "readonly")
        self.setStyleSheet("QWidget{background:#f4f6f9;font-family:'Segoe UI';}")
        self._build()
        self.yenile()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(20, 16, 20, 16); lay.setSpacing(12)

        # Baslik + butonlar
        hdr = QHBoxLayout()
        lbl = QLabel("ÜRETİM TAKİBİ")
        lbl.setStyleSheet("font-size:18px;font-weight:900;color:#2c3e50;")
        hdr.addWidget(lbl); hdr.addStretch()
        if not self.readonly:
            btn_y = QPushButton("+ Yeni Is Emri"); btn_y.setFixedHeight(38); btn_y.setStyleSheet(STL_PRI)
            btn_y.clicked.connect(self._yeni_is); hdr.addWidget(btn_y)
        btn_r = QPushButton("Yenile"); btn_r.setFixedHeight(38); btn_r.setStyleSheet(STL_GRAY)
        btn_r.clicked.connect(self.yenile); hdr.addWidget(btn_r)
        lay.addLayout(hdr)

        # Ozet kartlar
        klay = QHBoxLayout(); klay.setSpacing(10)
        self.k_bekl = self._kart("BEKLEMEDE",   "0", "#f39c12")
        self.k_urt  = self._kart("URETIMDE",    "0", "#2980b9")
        self.k_tam  = self._kart("TAMAMLANDI",  "0", "#27ae60")
        self.k_top  = self._kart("TOPLAM EMIR", "0", "#8e44ad")
        for k in [self.k_bekl, self.k_urt, self.k_tam, self.k_top]: klay.addWidget(k)
        lay.addLayout(klay)

        # Filtre
        flay = QHBoxLayout(); flay.setSpacing(8)
        self.txt_ara = QLineEdit(); self.txt_ara.setPlaceholderText("Is no veya musteri ara...")
        self.txt_ara.setFixedHeight(36); self.txt_ara.setStyleSheet(INPUT)
        self.txt_ara.textChanged.connect(self._filtrele)
        self.cmb_fil = QComboBox(); self.cmb_fil.addItems(["Tumu"] + DURUMLAR)
        self.cmb_fil.setFixedSize(140, 36); self.cmb_fil.setStyleSheet(INPUT)
        self.cmb_fil.currentTextChanged.connect(self._filtrele)
        flay.addWidget(self.txt_ara); flay.addWidget(self.cmb_fil)
        lay.addLayout(flay)

        # Is emirleri tablosu
        self.tablo = _tablo(
            ["Is No", "Musteri", "Tarih", "Termin", "Kg", "Ilerleme", "Durum", "Islem"],
            stretch_col=1)
        self.tablo.setColumnWidth(5, 120)
        self.tablo.setColumnWidth(6, 130)  # Durum sütunu
        self.tablo.setColumnWidth(7, 200)  # Islem sütunu
        self.tablo.verticalHeader().setDefaultSectionSize(44)
        lay.addWidget(self.tablo)

    def _kart(self, baslik, deger, renk):
        f = QFrame(); f.setFixedHeight(68)
        f.setStyleSheet(
            "QFrame{{background:white;border-radius:10px;border:1px solid #dcdde1;"
            "border-left:5px solid {r}; }}".format(r=renk))
        v = QVBoxLayout(f); v.setContentsMargins(12, 6, 12, 6); v.setSpacing(2)
        lb = QLabel(baslik)
        lb.setStyleSheet("color:#7f8c8d;font-size:10px;font-weight:bold;background:transparent;")
        ld = QLabel(deger)
        ld.setStyleSheet("color:{};font-size:18px;font-weight:900;background:transparent;".format(renk))
        ld.setObjectName("val")
        v.addWidget(lb); v.addWidget(ld); return f

    def _set_kart(self, k, v):
        k.findChild(QLabel, "val").setText(str(v))

    def yenile(self):
        try:
            self.cursor.execute("SELECT durum, COUNT(*) FROM isler GROUP BY durum")
            sc = dict(self.cursor.fetchall())
            self._set_kart(self.k_top,  sum(sc.values()))
            self._set_kart(self.k_bekl, sc.get("Beklemede", 0))
            self._set_kart(self.k_urt,  sc.get("Uretimde", 0))
            self._set_kart(self.k_tam,  sc.get("Tamamlandi", 0))

            self.cursor.execute(
                "SELECT id,is_no,musteri,tarih,termin,toplam_kg,ilerleme,durum FROM isler ORDER BY id DESC")
            rows = self.cursor.fetchall()
            self.tablo.setRowCount(0)

            for i, (iid, is_no, mus, tarih, ter, kg, iler, durum) in enumerate(rows):
                self.tablo.insertRow(i); self.tablo.setRowHeight(i, 44)
                durum = durum or "Beklemede"

                for col, val, uid in [
                    (0, is_no or "-",                      iid),
                    (1, mus or "-",                        iid),
                    (2, tarih or "-",                      iid),
                    (3, ter or "-",                        iid),
                    (4, "{:.1f} kg".format(float(kg or 0)), iid),
                ]:
                    it = _item(val, Qt.AlignCenter if col != 1 else Qt.AlignLeft | Qt.AlignVCenter, uid=uid)
                    self.tablo.setItem(i, col, it)

                # Ilerleme bar
                pb = QProgressBar(); pb.setValue(int(iler or 0)); pb.setFixedHeight(22)
                pb.setTextVisible(True)
                pb.setStyleSheet("""
                    QProgressBar{background:#ecf0f1;border-radius:5px;border:1px solid #dcdde1;font-size:11px;color:#2c3e50;}
                    QProgressBar::chunk{background:#27ae60;border-radius:4px;}
                """)
                self.tablo.setCellWidget(i, 5, pb)
                self.tablo.setCellWidget(i, 6, make_badge(durum))

                # Islem butonlari
                bw = QWidget(); bl = QHBoxLayout(bw); bl.setContentsMargins(2, 2, 2, 2); bl.setSpacing(4)
                for txt, stl, fn in [
                    ("Parcalar", STL_BLUE,  lambda _, n=is_no: self._parcalara_bak(n)),
                    ("Duzenle",  STL_GRAY,  lambda _, iid_=iid: self._duzenle(iid_)),
                ]:
                    b = QPushButton(txt); b.setFixedHeight(32)
                    b.setMinimumWidth(80)
                    b.setStyleSheet(stl + "padding:4px 12px;font-size:12px;")
                    b.clicked.connect(fn); bl.addWidget(b)
                self.tablo.setCellWidget(i, 7, bw)

            self._filtrele()
        except Exception as e:
            print("Uretim yenile hatasi:", e)

    def _filtrele(self):
        txt  = self.txt_ara.text().lower()
        fil  = self.cmb_fil.currentText()
        for r in range(self.tablo.rowCount()):
            sno = (self.tablo.item(r, 0).text() if self.tablo.item(r, 0) else "").lower()
            mus = (self.tablo.item(r, 1).text() if self.tablo.item(r, 1) else "").lower()
            dw  = self.tablo.cellWidget(r, 6)
            dur = ""
            if dw:
                lbs = dw.findChildren(QLabel)
                if lbs: dur = lbs[0].text()
            esle = (not txt or txt in sno or txt in mus) and (fil == "Tumu" or fil == dur)
            self.tablo.setRowHidden(r, not esle)

    def _yeni_is(self):
        dlg = IsEmriDialog(self.cursor, self.conn, parent=self)
        if dlg.exec_() == QDialog.Accepted: self.yenile()

    def _duzenle(self, iid):
        dlg = IsEmriDialog(self.cursor, self.conn, is_id=iid, parent=self)
        if dlg.exec_() == QDialog.Accepted: self.yenile()

    def _parcalara_bak(self, is_no):
        dlg = ParcaDurumDialog(self.cursor, self.conn, is_no, parent=self)
        dlg.exec_(); self.yenile()
