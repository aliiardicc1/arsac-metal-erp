"""
Arsac Metal ERP — Bildirim Sistemi
Sağ alt köşede kayar bildirim popup'ları.
"""
try:
    from ayarlar import ayar_al
except Exception:
    ayar_al = lambda b,k,v=None: v
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QColor
from datetime import datetime


# Bildirim tipleri ve renkleri
TIPLER = {
    "kritik":  {"renk": "#e74c3c", "ikon": "🚨"},
    "uyari":   {"renk": "#e67e22", "ikon": "⚠️"},
    "bilgi":   {"renk": "#2980b9", "ikon": "ℹ️"},
    "basari":  {"renk": "#27ae60", "ikon": "✅"},
    "odeme":   {"renk": "#8e44ad", "ikon": "💳"},
}

# Aktif bildirimler listesi
_aktif_bildirimler = []


class BildirimWidget(QWidget):
    """Tek bir bildirim kutusu."""
    def __init__(self, baslik, mesaj, tip="bilgi", sure=5000, parent=None):
        super().__init__(parent)
        self.sure = sure
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.init_ui(baslik, mesaj, tip)

    def init_ui(self, baslik, mesaj, tip):
        tip_bilgi = TIPLER.get(tip, TIPLER["bilgi"])
        renk = tip_bilgi["renk"]
        ikon = tip_bilgi["ikon"]

        self.setFixedWidth(320)

        # Ana container
        container = QWidget(self)
        container.setObjectName("container")
        container.setStyleSheet(f"""
            QWidget#container {{
                background: #2c3e50;
                border-radius: 10px;
                border-left: 4px solid {renk};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(container)

        ic_lay = QHBoxLayout(container)
        ic_lay.setContentsMargins(12, 10, 12, 10)
        ic_lay.setSpacing(10)

        # İkon
        ikon_lbl = QLabel(ikon)
        ikon_lbl.setStyleSheet("font-size: 22px; background: transparent;")
        ikon_lbl.setFixedWidth(30)
        ic_lay.addWidget(ikon_lbl)

        # Metin
        metin_lay = QVBoxLayout()
        metin_lay.setSpacing(2)

        baslik_lbl = QLabel(baslik)
        baslik_lbl.setStyleSheet(f"""
            color: {renk}; font-size: 12px; font-weight: bold;
            background: transparent;
        """)
        baslik_lbl.setWordWrap(True)

        mesaj_lbl = QLabel(mesaj)
        mesaj_lbl.setStyleSheet("color: #ecf0f1; font-size: 11px; background: transparent;")
        mesaj_lbl.setWordWrap(True)

        metin_lay.addWidget(baslik_lbl)
        metin_lay.addWidget(mesaj_lbl)
        ic_lay.addLayout(metin_lay)

        # Kapat butonu
        kapat_btn = QPushButton("✕")
        kapat_btn.setFixedSize(20, 20)
        kapat_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: rgba(255,255,255,0.4);
                border: none; font-size: 12px; padding: 0;
            }
            QPushButton:hover { color: white; }
        """)
        kapat_btn.clicked.connect(self.kapat)
        ic_lay.addWidget(kapat_btn, alignment=Qt.AlignTop)

        self.adjustSize()

        # Otomatik kapanma zamanlayıcısı
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.kapat)
        self.timer.start(self.sure)

        # İlerleme çubuğu (alt kısım)
        self.progress = QWidget(container)
        self.progress.setFixedHeight(3)
        self.progress.setStyleSheet(f"background: {renk}; border-radius: 0px;")
        self.progress.setGeometry(4, container.height() - 3,
                                   container.width() - 4, 3)

        # Progress animasyonu
        self.prog_timer = QTimer()
        self.prog_timer.timeout.connect(self._progress_guncelle)
        self.prog_timer.start(50)
        self._baslangic = datetime.now().timestamp() * 1000

    def _progress_guncelle(self):
        try:
            gecen = datetime.now().timestamp() * 1000 - self._baslangic
            oran = max(0, 1 - gecen / self.sure)
            container = self.findChild(QWidget, "container")
            if container:
                w = int((container.width() - 4) * oran)
                self.progress.setFixedWidth(max(0, w))
        except:
            pass

    def kapat(self):
        self.timer.stop()
        self.prog_timer.stop()
        if self in _aktif_bildirimler:
            _aktif_bildirimler.remove(self)
        _bildirim_yeniden_diz()
        self.hide()
        self.deleteLater()

    def goster(self, x, y):
        self.move(x, y)
        self.show()
        self.raise_()


def _bildirim_yeniden_diz():
    """Aktif bildirimleri alt alta hizala."""
    try:
        ekran = QApplication.primaryScreen().geometry()
        bosluk = 10
        alt = ekran.height() - 60

        for b in reversed(_aktif_bildirimler):
            if b and not b.isHidden():
                x = ekran.width() - b.width() - 20
                b.move(x, alt - b.height())
                alt -= b.height() + bosluk
    except:
        pass


def bildirim_goster(baslik, mesaj, tip="bilgi", sure=5000):
    """
    Herhangi bir yerden çağrılır.
    tip: kritik / uyari / bilgi / basari / odeme
    sure: milisaniye (varsayılan 5 saniye)
    """
    try:
        ekran = QApplication.primaryScreen().geometry()

        b = BildirimWidget(baslik, mesaj, tip, sure)
        _aktif_bildirimler.append(b)

        bosluk = 10
        alt = ekran.height() - 60
        for onceki in _aktif_bildirimler[:-1]:
            if onceki and not onceki.isHidden():
                alt -= onceki.height() + bosluk

        x = ekran.width() - b.width() - 20
        b.goster(x, alt - b.height())
    except Exception as e:
        print(f"Bildirim hatası: {e}")


def acilis_bildirimleri_goster(cursor):
    """
    Program açılışında veritabanını kontrol edip
    önemli bildirimleri sırayla gösterir.
    """
    try:
        gecikme = 500  # ms

        # 1. Vadesi geçmiş ödemeler
        try:
            cursor.execute("""
                SELECT COUNT(*), SUM(toplam_tutar)
                FROM satinalma_kayitlari
                WHERE (odendi IS NULL OR odendi=0)
            """)
            row = cursor.fetchone()
            bekleyen_sayi  = int(row[0] or 0)
            bekleyen_tutar = float(row[1] or 0)

            # Gerçek vade kontrolü
            cursor.execute("""
                SELECT firma, vade_tarihi, toplam_tutar
                FROM satinalma_kayitlari
                WHERE (odendi IS NULL OR odendi=0)
            """)
            gecmis = 0
            bugun  = 0
            for firma, vade, tutar in cursor.fetchall():
                try:
                    if "Gün" in str(vade or ""):
                        continue
                    gun = (datetime.strptime(vade, '%d.%m.%Y') - datetime.now()).days
                    if gun < 0:
                        gecmis += 1
                    elif gun == 0:
                        bugun += 1
                except:
                    pass

            if gecmis > 0:
                QTimer = _get_qtimer()
                QTimer.singleShot(gecikme, lambda: bildirim_goster(
                    "Vadesi Geçmiş Ödeme!",
                    f"{gecmis} ödeme vadesi geçmiş durumda!",
                    "kritik", 7000
                ))
                gecikme += 800

            if bugun > 0:
                QTimer = _get_qtimer()
                QTimer.singleShot(gecikme, lambda: bildirim_goster(
                    "Bugün Ödenecek!",
                    f"{bugun} ödeme bugün vadeli.",
                    "odeme", 6000
                ))
                gecikme += 800
        except:
            pass

        # 2. Kritik stok
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM (
                    SELECT malzeme, SUM(kg) as topkg
                    FROM stok GROUP BY malzeme
                    HAVING topkg < 500
                )
            """)
            kritik = cursor.fetchone()[0]
            if kritik > 0:
                QTimer = _get_qtimer()
                QTimer.singleShot(gecikme, lambda k=kritik: bildirim_goster(
                    "Kritik Stok Uyarısı!",
                    f"{k} malzeme kritik seviyenin altında.",
                    "kritik", 6000
                ))
                gecikme += 800
        except:
            pass

        # 3. Bekleyen talepler
        try:
            cursor.execute("SELECT COUNT(*) FROM talepler WHERE durum=0")
            talep = cursor.fetchone()[0]
            if talep > 0:
                QTimer = _get_qtimer()
                QTimer.singleShot(gecikme, lambda t=talep: bildirim_goster(
                    "Bekleyen Hammadde Talebi",
                    f"{t} adet talep satın alma bekliyor.",
                    "uyari", 5000
                ))
                gecikme += 800
        except:
            pass

        # 4. Yolda saclar
        try:
            cursor.execute("SELECT COUNT(*) FROM stok WHERE durum=0")
            yolda = cursor.fetchone()[0]
            if yolda > 0:
                QTimer = _get_qtimer()
                QTimer.singleShot(gecikme, lambda y=yolda: bildirim_goster(
                    "Yolda Bekleyen Sac",
                    f"{y} sac depo girişi bekliyor.",
                    "bilgi", 5000
                ))
        except:
            pass

    except Exception as e:
        print(f"Açılış bildirimleri hatası: {e}")


def _get_qtimer():
    from PyQt5.QtCore import QTimer
    return QTimer