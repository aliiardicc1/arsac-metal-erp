"""
Arsac Metal ERP — Analiz Modulu
Ozet kartlar + musteri/uretim tablolari. Sifir grafik kutuphanesi.
"""
from styles import BTN_BLUE, BTN_GRAY, BTN_GREEN, BTN_ORANGE, BTN_PRIMARY, BTN_PURPLE, DIALOG_QSS, DURUM_RENK, GROUPBOX_QSS, INPUT, INPUT_QSS, LIST_QSS, SAYFA_QSS, TABLO_QSS, make_badge, make_buton, tab_qss
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor

INPUT = "border:1.5px solid #dcdde1;border-radius:7px;padding:5px 10px;font-size:13px;background:white;color:#2c3e50;"


def _tablo(headers, stretch_col=0):
    t = QTableWidget(0, len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.setEditTriggers(QTableWidget.NoEditTriggers)
    t.setAlternatingRowColors(True); t.setShowGrid(False)
    t.verticalHeader().setVisible(False)
    t.setSelectionBehavior(QTableWidget.SelectRows)
    t.setStyleSheet("""
        QTableWidget{background:white;border-radius:10px;border:1px solid #dcdde1;color:#2c3e50;}
        QTableWidget::item{color:#2c3e50;padding:6px;}
        QTableWidget::item:selected{background:#c0392b;color:white;}
        QHeaderView::section{background:#2c3e50;color:white;padding:8px;font-weight:bold;border:none;}
        QTableWidget::item:alternate{background:#f8f9fa;}
    """)
    t.horizontalHeader().setSectionResizeMode(stretch_col, QHeaderView.Stretch)
    for c in range(len(headers)):
        if c != stretch_col:
            t.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeToContents)
    return t


def _item(text, align=Qt.AlignCenter, fg="#2c3e50", bold=False):
    it = QTableWidgetItem(str(text))
    it.setTextAlignment(align)
    it.setForeground(QColor(fg))
    if bold:
        f = it.font(); f.setBold(True); it.setFont(f)
    return it


class AnalizSayfasi(QWidget):
    def __init__(self, cursor):
        super().__init__()
        self.cursor = cursor
        self.setStyleSheet("QWidget{background:#f4f6f9;font-family:'Segoe UI';}")
        self._build()
        QTimer.singleShot(200, self.yenile)

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(20, 16, 20, 16); lay.setSpacing(12)

        # Baslik
        hdr = QHBoxLayout()
        lbl = QLabel("ANALİZ VE RAPORLAMA")
        lbl.setStyleSheet("font-size:18px;font-weight:900;color:#2c3e50;")
        hdr.addWidget(lbl); hdr.addStretch()
        self.cmb_donem = QComboBox()
        self.cmb_donem.addItems(["Bu Ay", "Son 3 Ay", "Son 6 Ay", "Bu Yil", "Tumu"])
        self.cmb_donem.setFixedHeight(36); self.cmb_donem.setStyleSheet(INPUT)
        self.cmb_donem.setFixedWidth(130)
        self.cmb_donem.currentTextChanged.connect(self.yenile)
        hdr.addWidget(self.cmb_donem)
        btn = QPushButton("Yenile"); btn.setFixedHeight(36)
        btn.setStyleSheet("background:#2c3e50;color:white;border-radius:8px;padding:4px 18px;font-weight:bold;border:none;")
        btn.clicked.connect(self.yenile); hdr.addWidget(btn)
        lay.addLayout(hdr)

        # Ozet kartlar — 2 satir
        k1 = QHBoxLayout(); k1.setSpacing(10)
        self.k_sip_top    = self._kart("TOPLAM SIPARIS",    "0", "#c0392b")
        self.k_sip_alindi = self._kart("ALINDI",            "0", "#f39c12")
        self.k_sip_urt    = self._kart("URETIMDE",          "0", "#2980b9")
        self.k_sip_sevk   = self._kart("SEVK EDILDI",       "0", "#27ae60")
        self.k_ciro       = self._kart("TOPLAM CIRO (TL)",  "—", "#8e44ad")
        for k in [self.k_sip_top, self.k_sip_alindi, self.k_sip_urt, self.k_sip_sevk, self.k_ciro]:
            k1.addWidget(k)
        lay.addLayout(k1)

        k2 = QHBoxLayout(); k2.setSpacing(10)
        self.k_is_top  = self._kart("TOPLAM IS EMRI",   "0", "#2c3e50")
        self.k_is_urt  = self._kart("URETIMDE",         "0", "#2980b9")
        self.k_is_tam  = self._kart("TAMAMLANDI",       "0", "#27ae60")
        self.k_parca   = self._kart("TOPLAM PARCA",     "0", "#16a085")
        self.k_alis    = self._kart("TOPLAM ALIS (TL)", "—", "#e67e22")
        for k in [self.k_is_top, self.k_is_urt, self.k_is_tam, self.k_parca, self.k_alis]:
            k2.addWidget(k)
        lay.addLayout(k2)

        # Sekmeli tablolar
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane{border:1px solid #dcdde1;border-radius:8px;background:white;}
            QTabBar::tab{background:#ecf0f1;color:#2c3e50;padding:8px 14px;
                         border-radius:6px 6px 0 0;font-weight:bold;font-size:12px;
                         min-width:80px;}
            QTabBar::tab:selected{background:#c0392b;color:white;}
            QTabBar::tab:hover:!selected{background:#d5d8dc;}
            QTabBar{alignment:left;}
        """)

        # Sekme 1: En cok siparis veren musteriler
        t1 = QWidget(); t1l = QVBoxLayout(t1); t1l.setContentsMargins(10, 10, 10, 10)
        self.tbl_musteri = _tablo(["Musteri", "Siparis Sayisi", "Toplam Tutar (TL)", "Son Siparis"], stretch_col=0)
        t1l.addWidget(self.tbl_musteri)
        self.tabs.addTab(t1, "En Cok Siparis Verenler")

        # Sekme 2: Aylik siparis ozeti
        t2 = QWidget(); t2l = QVBoxLayout(t2); t2l.setContentsMargins(10, 10, 10, 10)
        self.tbl_aylik = _tablo(["Ay", "Siparis Sayisi", "Toplam Tutar (TL)", "Tamamlanan"], stretch_col=0)
        t2l.addWidget(self.tbl_aylik)
        self.tabs.addTab(t2, "Aylik Siparis Ozeti")

        # Sekme 3: Is emri ozeti
        t3 = QWidget(); t3l = QVBoxLayout(t3); t3l.setContentsMargins(10, 10, 10, 10)
        self.tbl_isemri = _tablo(["Musteri", "Is Emri Sayisi", "Tamamlanan", "Toplam Kg"], stretch_col=0)
        t3l.addWidget(self.tbl_isemri)
        self.tabs.addTab(t3, "Is Emri Ozeti")

        # Sekme 4: Durum dagilimi
        t4 = QWidget(); t4l = QHBoxLayout(t4); t4l.setContentsMargins(10, 10, 10, 10); t4l.setSpacing(10)
        self.tbl_sip_durum = _tablo(["Siparis Durumu", "Adet", "Oran (%)"], stretch_col=0)
        self.tbl_is_durum  = _tablo(["Is Emri Durumu", "Adet", "Oran (%)"], stretch_col=0)
        t4l.addWidget(self._cerceve(self.tbl_sip_durum, "Siparis Durumlari"))
        t4l.addWidget(self._cerceve(self.tbl_is_durum,  "Is Emri Durumlari"))
        self.tabs.addTab(t4, "Durum Dagilimi")

        lay.addWidget(self.tabs)

    def _kart(self, baslik, deger, renk):
        f = QFrame()
        f.setMinimumHeight(80)
        f.setMaximumHeight(100)
        f.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        f.setStyleSheet(
            "QFrame{{background:white;border-radius:10px;border:1px solid #dcdde1;"
            "border-left:5px solid {r};}}".format(r=renk))
        v = QVBoxLayout(f); v.setContentsMargins(12, 8, 12, 8); v.setSpacing(4)
        lb = QLabel(baslik)
        lb.setStyleSheet("color:#7f8c8d;font-size:11px;font-weight:bold;background:transparent;")
        lb.setWordWrap(True)
        ld = QLabel(deger)
        ld.setStyleSheet("color:{};font-size:20px;font-weight:900;background:transparent;".format(renk))
        ld.setObjectName("val")
        v.addWidget(lb); v.addWidget(ld); return f

    def _set(self, k, v):
        k.findChild(QLabel, "val").setText(str(v))

    def _cerceve(self, widget, baslik=""):
        gb = QGroupBox(baslik)
        gb.setStyleSheet(
            "QGroupBox{{background:white;border-radius:10px;border:1px solid #dcdde1;"
            "margin-top:8px;padding:8px;}}"
            "QGroupBox::title{{color:#c0392b;font-weight:bold;padding:0 6px;}}")
        v = QVBoxLayout(gb); v.addWidget(widget); return gb

    def _donem_filtresi(self):
        """WHERE tarih filtresi icin gun offseti dondur. None = filtre yok."""
        from datetime import datetime, timedelta
        d = self.cmb_donem.currentText()
        if d == "Tumu": return None, None
        bugun = datetime.now()
        if d == "Bu Ay":
            bas = bugun.replace(day=1)
        elif d == "Son 3 Ay":
            bas = bugun - timedelta(days=90)
        elif d == "Son 6 Ay":
            bas = bugun - timedelta(days=180)
        else:  # Bu Yil
            bas = bugun.replace(month=1, day=1)
        return bas.strftime("%d.%m.%Y"), bugun.strftime("%d.%m.%Y")

    def _tarih_filtreli_sorgula(self, sql, bas, bit, params=()):
    try:
        if bas:
            # GROUP BY / ORDER BY / LIMIT oncesine tarih filtresi ekle
            import re
            m = re.search(r'\b(GROUP\s+BY|ORDER\s+BY|LIMIT)\b', sql, re.IGNORECASE)
            if m:
                pos = m.start()
                sql = sql[:pos] + " AND tarih >= ? AND tarih <= ? " + sql[pos:]
            else:
                sql += " AND tarih >= ? AND tarih <= ?"
            params = tuple(params) + (bas, bit)
            self.cursor.execute(sql, params)
            return self.cursor.fetchall()
        except Exception as e:
            # tarih kolonu yoksa filtresiz dene
            try:
                self.cursor.execute(sql.split(" AND tarih")[0], ())
                return self.cursor.fetchall()
            except:
                return []

    def yenile(self):
        try:
            bas, bit = self._donem_filtresi()

            # ── Siparis kartlari ──────────────────────────────────────
            sql = "SELECT durum, COUNT(*), COALESCE(SUM(genel_toplam),0) FROM siparisler WHERE 1=1"
            rows = self._tarih_filtreli_sorgula(sql, bas, bit)
            sc = {r[0]: (r[1], r[2]) for r in rows}
            toplam_sip = sum(v[0] for v in sc.values())
            ciro = sum(v[1] for v in sc.values())
            self._set(self.k_sip_top,    toplam_sip)
            self._set(self.k_sip_alindi, sc.get("Alindi",      (0,))[0])
            self._set(self.k_sip_urt,    sc.get("Uretimde",    (0,))[0])
            self._set(self.k_sip_sevk,   sc.get("Sevk Edildi", (0,))[0])
            self._set(self.k_ciro,       "{:,.0f}".format(ciro))

            # ── Is emri kartlari ─────────────────────────────────────
            if bas:
                self.cursor.execute(
                    "SELECT durum, COUNT(*) FROM isler WHERE tarih >= ? AND tarih <= ? GROUP BY durum",
                    (bas, bit))
            else:
                self.cursor.execute("SELECT durum, COUNT(*) FROM isler GROUP BY durum")
            ic = dict(self.cursor.fetchall())
            toplam_is = sum(ic.values())
            self._set(self.k_is_top,  toplam_is)
            self._set(self.k_is_urt,  ic.get("Uretimde", 0))
            self._set(self.k_is_tam,  ic.get("Tamamlandi", 0))

            self.cursor.execute("SELECT COUNT(*) FROM parcalar")
            self._set(self.k_parca, self.cursor.fetchone()[0] or 0)

            self.cursor.execute("SELECT COALESCE(SUM(toplam_tutar),0) FROM satinalma_kayitlari")
            self._set(self.k_alis, "{:,.0f}".format(float(self.cursor.fetchone()[0] or 0)))

            self._tbl_musteri(bas, bit)
            self._tbl_aylik(bas, bit)
            self._tbl_isemri(bas, bit)
            self._tbl_durum(sc, ic)

        except Exception as e:
            print("Analiz yenile hatasi:", e)

    def _tbl_musteri(self, bas, bit):
        sql = ("SELECT musteri, COUNT(*) as sayi, COALESCE(SUM(genel_toplam),0), MAX(tarih)"
               " FROM siparisler WHERE 1=1")
        rows = self._tarih_filtreli_sorgula(sql + " GROUP BY musteri ORDER BY sayi DESC LIMIT 20", bas, bit)
        SIRALI_RENKLER = ["#c0392b","#2980b9","#27ae60","#f39c12","#8e44ad"]
        self.tbl_musteri.setRowCount(0)
        for i, (mus, sayi, toplam, son) in enumerate(rows):
            self.tbl_musteri.insertRow(i); self.tbl_musteri.setRowHeight(i, 36)
            renk = SIRALI_RENKLER[i] if i < 5 else "#2c3e50"
            self.tbl_musteri.setItem(i, 0, _item(mus or "-", Qt.AlignLeft | Qt.AlignVCenter, fg=renk, bold=(i < 3)))
            self.tbl_musteri.setItem(i, 1, _item(str(sayi), fg=renk, bold=(i < 3)))
            self.tbl_musteri.setItem(i, 2, _item("{:,.2f}".format(float(toplam or 0))))
            self.tbl_musteri.setItem(i, 3, _item(son or "-"))

    def _tbl_aylik(self, bas, bit):
        from datetime import datetime, timedelta
        # Son 12 ay
        self.cursor.execute(
            "SELECT tarih, genel_toplam, durum FROM siparisler ORDER BY tarih DESC")
        kayitlar = self.cursor.fetchall()
        ay_dict = {}
        from datetime import datetime
        bugun = datetime.now()
        for i in range(11, -1, -1):
            ay = (bugun.month - i - 1) % 12 + 1
            yil = bugun.year - ((bugun.month - i - 1) // 12)
            k = "{:02d}.{}".format(ay, yil)
            ay_dict[k] = {"sayi": 0, "toplam": 0.0, "tamamlanan": 0}

        for tarih, toplam, durum in kayitlar:
            try:
                parts = (tarih or "").split(".")
                if len(parts) == 3:
                    k = "{}.{}".format(parts[1], parts[2])
                    if k in ay_dict:
                        ay_dict[k]["sayi"] += 1
                        ay_dict[k]["toplam"] += float(toplam or 0)
                        if durum in ("Hazir", "Sevk Edildi"):
                            ay_dict[k]["tamamlanan"] += 1
            except: pass

        self.tbl_aylik.setRowCount(0)
        for i, (ay, veri) in enumerate(reversed(list(ay_dict.items()))):
            self.tbl_aylik.insertRow(i); self.tbl_aylik.setRowHeight(i, 36)
            self.tbl_aylik.setItem(i, 0, _item(ay, Qt.AlignLeft | Qt.AlignVCenter))
            self.tbl_aylik.setItem(i, 1, _item(str(veri["sayi"])))
            self.tbl_aylik.setItem(i, 2, _item("{:,.2f}".format(veri["toplam"])))
            self.tbl_aylik.setItem(i, 3, _item(str(veri["tamamlanan"])))

    def _tbl_isemri(self, bas, bit):
        sql = ("SELECT musteri, COUNT(*) as sayi, "
               "SUM(CASE WHEN durum='Tamamlandi' THEN 1 ELSE 0 END), "
               "COALESCE(SUM(toplam_kg),0) FROM isler WHERE 1=1")
        rows = self._tarih_filtreli_sorgula(sql + " GROUP BY musteri ORDER BY sayi DESC LIMIT 20", bas, bit)
        self.tbl_isemri.setRowCount(0)
        for i, (mus, sayi, tam, kg) in enumerate(rows):
            self.tbl_isemri.insertRow(i); self.tbl_isemri.setRowHeight(i, 36)
            self.tbl_isemri.setItem(i, 0, _item(mus or "-", Qt.AlignLeft | Qt.AlignVCenter))
            self.tbl_isemri.setItem(i, 1, _item(str(sayi)))
            self.tbl_isemri.setItem(i, 2, _item(str(tam or 0)))
            self.tbl_isemri.setItem(i, 3, _item("{:,.1f}".format(float(kg or 0))))

    def _tbl_durum(self, sc, ic):
        # Siparis durum tablosu
        toplam_s = sum(v[0] for v in sc.values()) or 1
        self.tbl_sip_durum.setRowCount(0)
        DURUM_RENK = {
            "Alindi": "#f39c12", "Uretimde": "#2980b9",
            "Hazir": "#8e44ad", "Sevk Edildi": "#27ae60", "Iptal": "#e74c3c"
        }
        for i, (durum, (adet, _)) in enumerate(sorted(sc.items(), key=lambda x: -x[1][0])):
            self.tbl_sip_durum.insertRow(i); self.tbl_sip_durum.setRowHeight(i, 36)
            renk = DURUM_RENK.get(durum, "#7f8c8d")
            self.tbl_sip_durum.setItem(i, 0, _item(durum, Qt.AlignLeft | Qt.AlignVCenter, fg=renk, bold=True))
            self.tbl_sip_durum.setItem(i, 1, _item(str(adet), fg=renk))
            self.tbl_sip_durum.setItem(i, 2, _item("{:.1f}%".format(adet / toplam_s * 100)))

        # Is emri durum tablosu
        toplam_i = sum(ic.values()) or 1
        self.tbl_is_durum.setRowCount(0)
        for i, (durum, adet) in enumerate(sorted(ic.items(), key=lambda x: -x[1])):
            self.tbl_is_durum.insertRow(i); self.tbl_is_durum.setRowHeight(i, 36)
            renk = DURUM_RENK.get(durum, "#7f8c8d")
            self.tbl_is_durum.setItem(i, 0, _item(durum, Qt.AlignLeft | Qt.AlignVCenter, fg=renk, bold=True))
            self.tbl_is_durum.setItem(i, 1, _item(str(adet), fg=renk))
            self.tbl_is_durum.setItem(i, 2, _item("{:.1f}%".format(adet / toplam_i * 100)))
