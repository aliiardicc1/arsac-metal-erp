"""
Arsac Metal ERP — Piyasa Takip Modülü
USD/TRY canlı kur + geçmiş grafik + hesap makinesi
"""
import json, urllib.request
from datetime import datetime, timedelta
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QColor, QFont

# ─────────────────────────────────────────────
#  Arka planda kur çeken thread
# ─────────────────────────────────────────────
class KurCekThread(QThread):
    veri_geldi  = pyqtSignal(dict)   # {"usd": 32.5, "zaman": "14:32"}
    hata_oldu   = pyqtSignal(str)

    def run(self):
        try:
            # Ücretsiz, kayıt gerektirmeyen API
            url = "https://api.exchangerate-api.com/v4/latest/USD"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read())
            try_kur = data["rates"]["TRY"]
            self.veri_geldi.emit({
                "usd": try_kur,
                "zaman": datetime.now().strftime("%H:%M"),
                "tarih": datetime.now().strftime("%d.%m.%Y")
            })
        except Exception as e:
            self.hata_oldu.emit(str(e))


# ─────────────────────────────────────────────
#  Ticker Bandı (nav bar altına eklenir)
# ─────────────────────────────────────────────
class TickerBand(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(38)
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #1a252f, stop:0.5 #2c3e50, stop:1 #1a252f);
                border-bottom: 2px solid #c0392b;
            }
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(24, 0, 24, 0)
        lay.setSpacing(6)

        # Canlı göstergesi
        dot = QLabel("●")
        dot.setStyleSheet("color:#2ecc71;font-size:10px;background:transparent;")
        lay.addWidget(dot)

        # USD/TRY etiketi
        self.lbl_usd = self._etiket("USD/TRY", "#f39c12", bold=True, size=13)
        self.lbl_usd_deger = self._etiket("---.----  ₺", "white", bold=True, size=15)
        self.lbl_usd_degisim = self._etiket("", "#7f8c8d", size=12)
        self.lbl_usd_zaman = self._etiket("", "#95a5a6", size=11)

        lay.addWidget(self.lbl_usd)
        lay.addSpacing(8)
        lay.addWidget(self.lbl_usd_deger)
        lay.addWidget(self.lbl_usd_degisim)
        lay.addStretch()
        lay.addWidget(self.lbl_usd_zaman)
        lay.addSpacing(10)

        # Güncelleme butonu
        self.btn_yenile = QPushButton("🔄 Güncelle")
        self.btn_yenile.setFixedHeight(26)
        self.btn_yenile.setStyleSheet("""
            QPushButton { background:#c0392b; color:white; border-radius:5px;
                          font-size:11px; font-weight:bold; border:none; padding:2px 10px; }
            QPushButton:hover { background:#a93226; }
        """)
        lay.addWidget(self.btn_yenile)

        # Son değer (karşılaştırma için)
        self._son_deger = None

        # Otomatik yenileme — 5 dakikada bir
        self.timer = QTimer()
        self.timer.timeout.connect(self.guncelle)
        self.timer.start(5 * 60 * 1000)
        self.btn_yenile.clicked.connect(self.guncelle)

        # İlk yükleme
        QTimer.singleShot(1500, self.guncelle)

    def _etiket(self, metin, renk, bold=False, size=12):
        l = QLabel(metin)
        w = "bold" if bold else "normal"
        l.setStyleSheet(f"color:{renk};font-size:{size}px;font-weight:{w};background:transparent;")
        return l

    def guncelle(self):
        self.lbl_usd_zaman.setText("yükleniyor...")
        self.thread = KurCekThread()
        self.thread.veri_geldi.connect(self._veri_al)
        self.thread.hata_oldu.connect(self._hata)
        self.thread.start()

    def _veri_al(self, veri):
        kur = veri["usd"]
        zaman = veri["zaman"]

        # Artış/azalış oku
        if self._son_deger:
            if kur > self._son_deger:
                ok = " ▲"; renk = "#e74c3c"
            elif kur < self._son_deger:
                ok = " ▼"; renk = "#2ecc71"
            else:
                ok = ""; renk = "white"
        else:
            ok = ""; renk = "white"

        self._son_deger = kur
        self.lbl_usd_deger.setText(f"{kur:.4f}  ₺")
        self.lbl_usd_deger.setStyleSheet(f"color:{renk};font-size:15px;font-weight:bold;background:transparent;font-family:'Segoe UI',Arial;")
        if ok:
            self.lbl_usd_degisim.setText(ok)
            self.lbl_usd_degisim.setStyleSheet(f"color:{renk};font-size:12px;font-weight:bold;background:transparent;")
        self.lbl_usd_zaman.setText(f"güncellendi: {zaman}")

    def _hata(self, hata):
        self.lbl_usd_zaman.setText("  bağlantı yok")
        self.lbl_usd_zaman.setStyleSheet("color:#e74c3c;font-size:11px;background:transparent;")


# ─────────────────────────────────────────────
#  Piyasa Sayfası (ayrı sekme)
# ─────────────────────────────────────────────
class PiyasaSayfasi(QWidget):
    def __init__(self, cursor, conn):
        super().__init__()
        self.cursor = cursor
        self.conn   = conn
        self.gecmis = []   # [(tarih, kur), ...]
        self.init_ui()
        QTimer.singleShot(500, self.guncelle)

        # 5 dk'da bir otomatik güncelle
        self.oto_timer = QTimer()
        self.oto_timer.timeout.connect(self.guncelle)
        self.oto_timer.start(5 * 60 * 1000)

    def init_ui(self):
        self.setStyleSheet("""
            QWidget { background:#ebedef; font-family:'Segoe UI',Arial; }
            QFrame#Panel { background:white; border-radius:16px; border:1px solid #eaecee; }
            QLabel { background:transparent; }
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 16, 24, 16)
        lay.setSpacing(16)

        # Başlık
        ust = QHBoxLayout()
        lbl_bas = QLabel("📊 PİYASA TAKİBİ")
        lbl_bas.setStyleSheet("font-size:18px;font-weight:bold;color:#2c3e50;")
        self.btn_yenile = QPushButton("🔄 Güncelle")
        self.btn_yenile.setStyleSheet("background:#2980b9;color:white;border-radius:8px;padding:8px 18px;font-weight:bold;font-size:13px;")
        self.btn_yenile.clicked.connect(self.guncelle)
        ust.addWidget(lbl_bas); ust.addStretch(); ust.addWidget(self.btn_yenile)
        lay.addLayout(ust)

        # Ana kur kartı
        self.kart = self._buyuk_kart()
        lay.addWidget(self.kart)

        # Alt satır: hesap makinesi + geçmiş
        alt = QHBoxLayout(); alt.setSpacing(14)
        alt.addWidget(self._hesap_makinesi(), 1)
        alt.addWidget(self._gecmis_panel(), 2)
        lay.addLayout(alt)

    def _panel(self):
        f = QFrame(); f.setObjectName("Panel")
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect
        ef = QGraphicsDropShadowEffect()
        ef.setBlurRadius(20); ef.setOffset(0,4); ef.setColor(QColor(0,0,0,20))
        f.setGraphicsEffect(ef)
        return f

    def _buyuk_kart(self):
        f = self._panel()
        f.setFixedHeight(160)
        f.setStyleSheet("""
            QFrame#Panel {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #1a252f, stop:1 #2c3e50);
                border-radius:16px; border:none;
            }
        """)
        lay = QHBoxLayout(f); lay.setContentsMargins(30,20,30,20)

        # Sol: kur
        sol = QVBoxLayout()
        lbl_isim = QLabel("💵  USD / TRY")
        lbl_isim.setStyleSheet("color:rgba(255,255,255,0.7);font-size:14px;font-weight:bold;")
        self.lbl_kur = QLabel("---.----")
        self.lbl_kur.setStyleSheet("color:white;font-size:48px;font-weight:900;letter-spacing:2px;")
        self.lbl_degisim = QLabel("")
        self.lbl_degisim.setStyleSheet("font-size:14px;font-weight:bold;")
        sol.addWidget(lbl_isim); sol.addWidget(self.lbl_kur); sol.addWidget(self.lbl_degisim)
        lay.addLayout(sol, 2)

        # Sağ: bilgiler
        sag = QVBoxLayout(); sag.setSpacing(6)
        self.lbl_zaman = self._bilgi_lbl("Son güncelleme: --:--")
        self.lbl_tarih = self._bilgi_lbl("Tarih: --.--.----")
        self.lbl_durum = self._bilgi_lbl("Durum: Bekleniyor...")
        sag.addStretch()
        sag.addWidget(self.lbl_zaman)
        sag.addWidget(self.lbl_tarih)
        sag.addWidget(self.lbl_durum)
        sag.addStretch()
        lay.addLayout(sag, 1)
        return f

    def _bilgi_lbl(self, metin):
        l = QLabel(metin)
        l.setStyleSheet("color:rgba(255,255,255,0.6);font-size:12px;background:transparent;")
        return l

    def _hesap_makinesi(self):
        f = self._panel()
        lay = QVBoxLayout(f); lay.setContentsMargins(16,16,16,16); lay.setSpacing(10)
        lbl = QLabel("🧮 Kur Hesaplayıcı")
        lbl.setStyleSheet("font-size:13px;font-weight:bold;color:#2c3e50;")
        lay.addWidget(lbl)

        # USD → TRY
        self.txt_usd = QLineEdit()
        self.txt_usd.setPlaceholderText("USD miktarı girin...")
        self.txt_usd.setFixedHeight(40)
        self.txt_usd.setStyleSheet("border:1.5px solid #dcdde1;border-radius:8px;padding:8px 12px;font-size:13px;")
        self.lbl_try_sonuc = QLabel("= --- ₺")
        self.lbl_try_sonuc.setStyleSheet("font-size:20px;font-weight:bold;color:#c0392b;text-align:center;")
        self.lbl_try_sonuc.setAlignment(Qt.AlignCenter)
        self.txt_usd.textChanged.connect(self._hesapla_usd_try)
        lay.addWidget(QLabel("USD → TRY:"))
        lay.addWidget(self.txt_usd)
        lay.addWidget(self.lbl_try_sonuc)

        lay.addWidget(self._cizgi())

        # TRY → USD
        self.txt_try = QLineEdit()
        self.txt_try.setPlaceholderText("TRY miktarı girin...")
        self.txt_try.setFixedHeight(40)
        self.txt_try.setStyleSheet("border:1.5px solid #dcdde1;border-radius:8px;padding:8px 12px;font-size:13px;")
        self.lbl_usd_sonuc = QLabel("= --- $")
        self.lbl_usd_sonuc.setStyleSheet("font-size:20px;font-weight:bold;color:#2980b9;")
        self.lbl_usd_sonuc.setAlignment(Qt.AlignCenter)
        self.txt_try.textChanged.connect(self._hesapla_try_usd)
        lay.addWidget(QLabel("TRY → USD:"))
        lay.addWidget(self.txt_try)
        lay.addWidget(self.lbl_usd_sonuc)
        lay.addStretch()
        return f

    def _cizgi(self):
        l = QFrame(); l.setFrameShape(QFrame.HLine)
        l.setStyleSheet("border:none;border-top:1px solid #eaecee;margin:4px 0;")
        return l

    def _gecmis_panel(self):
        f = self._panel()
        lay = QVBoxLayout(f); lay.setContentsMargins(16,16,16,16); lay.setSpacing(8)
        lbl = QLabel("📈 Kur Geçmişi (Son 10 Güncelleme)")
        lbl.setStyleSheet("font-size:13px;font-weight:bold;color:#2c3e50;")
        lay.addWidget(lbl)

        self.tablo_gecmis = QTableWidget(0, 3)
        self.tablo_gecmis.setHorizontalHeaderLabels(["Tarih", "Saat", "USD/TRY"])
        self.tablo_gecmis.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo_gecmis.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tablo_gecmis.verticalHeader().setVisible(False)
        self.tablo_gecmis.setAlternatingRowColors(True)
        self.tablo_gecmis.setShowGrid(False)
        self.tablo_gecmis.setStyleSheet("""
            QTableWidget { border:none; font-size:13px; background:white; }
            QTableWidget::item { padding:7px; }
            QHeaderView::section { background:#f4f6f8;color:#2c3e50;padding:8px;
                                   font-weight:bold;border:none;border-bottom:2px solid #dfe6e9; }
        """)
        lay.addWidget(self.tablo_gecmis)
        return f

    def _hesapla_usd_try(self, metin):
        try:
            usd = float(metin.replace(",","."))
            kur = float(self.lbl_kur.text().replace(",","."))
            self.lbl_try_sonuc.setText(f"= {usd * kur:,.2f} ₺")
        except:
            self.lbl_try_sonuc.setText("= --- ₺")

    def _hesapla_try_usd(self, metin):
        try:
            try_ = float(metin.replace(",","."))
            kur  = float(self.lbl_kur.text().replace(",","."))
            self.lbl_usd_sonuc.setText(f"= {try_ / kur:,.2f} $")
        except:
            self.lbl_usd_sonuc.setText("= --- $")

    def guncelle(self):
        self.lbl_durum.setText("Durum: Güncelleniyor...")
        self.btn_yenile.setEnabled(False)
        self.thread = KurCekThread()
        self.thread.veri_geldi.connect(self._veri_al)
        self.thread.hata_oldu.connect(self._hata)
        self.thread.start()

    def _veri_al(self, veri):
        kur   = veri["usd"]
        zaman = veri["zaman"]
        tarih = veri["tarih"]

        # Önceki kurla karşılaştır
        if self.gecmis:
            onceki = self.gecmis[-1][1]
            if kur > onceki:
                degisim = f"▲ +{kur-onceki:.4f}"
                drenk = "#e74c3c"
            elif kur < onceki:
                degisim = f"▼ -{onceki-kur:.4f}"
                drenk = "#27ae60"
            else:
                degisim = "— değişmedi"
                drenk = "#7f8c8d"
            self.lbl_degisim.setText(degisim)
            self.lbl_degisim.setStyleSheet(f"font-size:14px;font-weight:bold;color:{drenk};background:transparent;")

        self.lbl_kur.setText(f"{kur:.4f}")
        self.lbl_zaman.setText(f"Son güncelleme: {zaman}")
        self.lbl_tarih.setText(f"Tarih: {tarih}")
        self.lbl_durum.setText("Durum: ✅ Canlı")
        self.lbl_durum.setStyleSheet("color:#2ecc71;font-size:12px;background:transparent;")
        self.btn_yenile.setEnabled(True)

        # Geçmişe ekle (son 10)
        self.gecmis.append((f"{tarih} {zaman}", kur))
        self.gecmis = self.gecmis[-10:]
        self._gecmis_guncelle()

        # Hesaplayıcıları tetikle
        self._hesapla_usd_try(self.txt_usd.text())
        self._hesapla_try_usd(self.txt_try.text())

    def _hata(self, hata):
        self.lbl_durum.setText("Durum: ❌ Bağlantı yok")
        self.lbl_durum.setStyleSheet("color:#e74c3c;font-size:12px;background:transparent;")
        self.btn_yenile.setEnabled(True)

    def _gecmis_guncelle(self):
        self.tablo_gecmis.setRowCount(0)
        for i, (zaman, kur) in enumerate(reversed(self.gecmis)):
            self.tablo_gecmis.insertRow(i)
            parcalar = zaman.split(" ")
            tarih_str = parcalar[0] if len(parcalar) > 0 else "-"
            saat_str  = parcalar[1] if len(parcalar) > 1 else "-"
            self.tablo_gecmis.setItem(i, 0, QTableWidgetItem(tarih_str))
            s = QTableWidgetItem(saat_str); s.setTextAlignment(Qt.AlignCenter)
            self.tablo_gecmis.setItem(i, 1, s)
            k = QTableWidgetItem(f"{kur:.4f} ₺"); k.setTextAlignment(Qt.AlignCenter)
            k.setForeground(QColor("#c0392b"))
            self.tablo_gecmis.setItem(i, 2, k)