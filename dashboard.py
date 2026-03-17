from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush, QLinearGradient
from datetime import datetime
from takvim import TakvimWidget

try:
    from ayarlar import ayar_al
except:
    ayar_al = lambda b, k, v=None: v


class ShadowFrame(QFrame):
    """Gölgeli, yuvarlatılmış kart."""
    def __init__(self, bg="#ffffff", accent="#c0392b", radius=16):
        super().__init__()
        self._bg     = bg
        self._accent = accent
        self._radius = radius
        self.setStyleSheet("background: transparent;")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect().adjusted(4, 4, -4, -4)
        # gölge
        for i in range(6, 0, -1):
            shadow_color = QColor(0, 0, 0, 8)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(shadow_color))
            p.drawRoundedRect(r.adjusted(-i//2, -i//2, i, i), self._radius+2, self._radius+2)
        # kart arka planı
        p.setBrush(QBrush(QColor(self._bg)))
        p.setPen(QPen(QColor("#e8ecef"), 1))
        p.drawRoundedRect(r, self._radius, self._radius)
        # alt accent çizgisi
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(self._accent)))
        bar = r.adjusted(0, r.height()-6, 0, 0)
        p.drawRoundedRect(bar, 4, 4)
        p.end()


class DashboardSayfasi(QWidget):
    def __init__(self, cursor, callback, conn=None):
        super().__init__()
        self.cursor   = cursor
        self.callback = callback
        self.conn     = conn
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QWidget { font-family: 'Segoe UI', Arial; }
            QTableWidget {
                background: white; border-radius: 12px;
                border: none; font-size: 13px;
                gridline-color: #f0f3f5;
            }
            QHeaderView::section {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #34495e, stop:1 #2c3e50);
                color: white; padding: 10px;
                font-weight: bold; border: none; font-size: 12px;
            }
            QTableWidget::item { padding: 6px; }
            QTableWidget::item:selected { background: #fde8e8; color: #c0392b; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(16)

        # ── Uyarı bandı ──
        self.uyari_band = QLabel("")
        self.uyari_band.setAlignment(Qt.AlignCenter)
        self.uyari_band.setFixedHeight(38)
        self.uyari_band.setStyleSheet("border-radius:10px;font-weight:bold;font-size:13px;")
        self.uyari_band.hide()
        layout.addWidget(self.uyari_band)

        # ── Üst kartlar — Sipariş/Üretim/Sevkiyat/Muhasebe istatistikleri ──
        kart_lay = QHBoxLayout(); kart_lay.setSpacing(14)
        self.kart_sip_acik  = self._stat_kart("🛒 AÇIK SİPARİŞ",    "0",      "#c0392b", "#fff5f5")
        self.kart_uretimde  = self._stat_kart("🏭 ÜRETİMDE",        "0",      "#8e44ad", "#f8f0ff")
        self.kart_hazir     = self._stat_kart("✅ SEVKİYATA HAZIR",  "0",      "#27ae60", "#f0fff4")
        self.kart_fatura    = self._stat_kart("💼 FATURALANACAK",    "0",      "#2980b9", "#f0f8ff")
        for k in [self.kart_sip_acik, self.kart_uretimde, self.kart_hazir, self.kart_fatura]:
            kart_lay.addWidget(k)
        layout.addLayout(kart_lay)

        # ── 2. satır kartlar — Stok ──
        kart2_lay = QHBoxLayout(); kart2_lay.setSpacing(14)
        self.kart_toplam = self._stat_kart("📦 TOPLAM STOK",    "0 KG",   "#e67e22", "#fff8f0")
        self.kart_depoda = self._stat_kart("🏭 DEPODA AKTİF",  "0",      "#2c3e50", "#f4f6f9")
        self.kart_yolda  = self._stat_kart("🚚 YOLDA BEKLEYEN","0",      "#16a085", "#f0fffe")
        self.kart_cesit  = self._stat_kart("🔢 FARKLI KALİTE", "0",      "#8e44ad", "#f8f0ff")
        for k in [self.kart_toplam, self.kart_depoda, self.kart_yolda, self.kart_cesit]:
            kart2_lay.addWidget(k)
        layout.addLayout(kart2_lay)

        # ── Alt bölüm ──
        alt_lay = QHBoxLayout(); alt_lay.setSpacing(14)

        # Sol — Son siparişler
        sol_frame = self._panel_frame()
        sol_v = QVBoxLayout(sol_frame); sol_v.setContentsMargins(14,12,14,12); sol_v.setSpacing(8)
        sol_v.addWidget(self._baslik("🛒 Son Siparişler"))
        self.tablo_son_sip = self._tablo(["Sipariş No","Müşteri","Tutar","Durum"])
        sol_v.addWidget(self.tablo_son_sip)
        alt_lay.addWidget(sol_frame, 3)

        # Orta — stok durumu + vadeler
        orta_frame = self._panel_frame()
        orta_v = QVBoxLayout(orta_frame); orta_v.setContentsMargins(14,12,14,12); orta_v.setSpacing(8)
        orta_v.addWidget(self._baslik("📦 Kritik Stok & Vadeler"))
        self.tablo_stok = self._tablo(["Kalite","KG","Durum"])
        self.tablo_stok.setMaximumHeight(180)
        orta_v.addWidget(self.tablo_stok)
        orta_v.addWidget(self._baslik("💳 Yaklaşan Vadeler"))
        self.tablo_vade = self._tablo(["Firma","Tutar","Vade"])
        orta_v.addWidget(self.tablo_vade)
        alt_lay.addWidget(orta_frame, 2)

        # Sağ — takvim
        sag_frame = self._panel_frame()
        sag_v = QVBoxLayout(sag_frame); sag_v.setContentsMargins(10,10,10,10); sag_v.setSpacing(6)
        sag_v.addWidget(self._baslik("📅 Takvim & Notlar"))
        self.takvim_widget = TakvimWidget(self.cursor, self.conn)
        sag_v.addWidget(self.takvim_widget)
        alt_lay.addWidget(sag_frame, 3)

        layout.addLayout(alt_lay)

    # ── Yardımcı widget oluşturucular ──

    def _panel_frame(self):
        f = QFrame()
        f.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 16px;
                border: 1px solid #eaecee;
            }
        """)
        effect = QGraphicsDropShadowEffect()
        effect.setBlurRadius(20)
        effect.setOffset(0, 4)
        effect.setColor(QColor(0, 0, 0, 25))
        f.setGraphicsEffect(effect)
        return f

    def _stat_kart(self, baslik, deger, accent, bg):
        kart = QFrame()
        kart.setFixedHeight(105)
        kart.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border-radius: 16px;
                border-left: 5px solid {accent};
                border-top: 1px solid #eaecee;
                border-right: 1px solid #eaecee;
                border-bottom: 1px solid #eaecee;
            }}
        """)
        effect = QGraphicsDropShadowEffect()
        effect.setBlurRadius(18)
        effect.setOffset(0, 3)
        effect.setColor(QColor(0, 0, 0, 20))
        kart.setGraphicsEffect(effect)

        lay = QVBoxLayout(kart); lay.setContentsMargins(16,10,16,10); lay.setSpacing(4)
        lb = QLabel(baslik)
        lb.setStyleSheet(f"color:{accent};font-size:11px;font-weight:bold;background:transparent;letter-spacing:1px;")
        lv = QLabel(deger)
        lv.setObjectName("CardValue")
        lv.setStyleSheet("color:#2c3e50;font-size:26px;font-weight:900;background:transparent;")
        lv.setAlignment(Qt.AlignLeft)
        lay.addWidget(lb); lay.addStretch(); lay.addWidget(lv)
        return kart

    def _baslik(self, metin):
        l = QLabel(metin)
        l.setStyleSheet("font-size:13px;font-weight:bold;color:#2c3e50;background:transparent;padding-bottom:2px;border-bottom:2px solid #f0f3f5;")
        return l

    def _tablo(self, basliklar):
        t = QTableWidget(0, len(basliklar))
        t.setHorizontalHeaderLabels(basliklar)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        t.setEditTriggers(QTableWidget.NoEditTriggers)
        t.verticalHeader().setVisible(False)
        t.setAlternatingRowColors(True)
        t.setShowGrid(False)
        t.setStyleSheet("""
            QTableWidget { background:white; border:none; border-radius:8px; font-size:13px; }
            QTableWidget::item { padding:7px; border-bottom:1px solid #f4f6f8; }
            QTableWidget::item:alternate { background:#fafbfc; }
            QHeaderView::section {
                background: #f4f6f8; color:#2c3e50; padding:9px;
                font-weight:bold; border:none; font-size:12px;
                border-bottom: 2px solid #dfe6e9;
            }
        """)
        return t

    def _set_card(self, kart, deger):
        kart.findChild(QLabel, "CardValue").setText(str(deger))

    def yenile(self):
        try:
            kritik_esik = ayar_al("stok", "kritik_esik", 500)
            uyari_esik  = ayar_al("stok", "uyari_esik",  2000)

            # ── Sipariş/Üretim/Sevkiyat/Muhasebe istatistikleri ──
            def _say(q, *p):
                self.cursor.execute(q, p); return self.cursor.fetchone()[0] or 0

            acik  = _say("SELECT COUNT(*) FROM siparisler WHERE durum NOT IN ('Faturalandı','İptal')")
            urt   = _say("SELECT COUNT(*) FROM siparisler WHERE durum='Üretimde'")
            hazir = _say("SELECT COUNT(*) FROM siparisler WHERE durum='Hazır'")
            fat   = _say("SELECT COUNT(*) FROM siparisler WHERE durum='Sevk Edildi'")

            self._set_card(self.kart_sip_acik, str(acik))
            self._set_card(self.kart_uretimde, str(urt))
            self._set_card(self.kart_hazir,    str(hazir))
            self._set_card(self.kart_fatura,   str(fat))

            # ── Stok istatistikleri ──
            toplam_kg = float(_say("SELECT COALESCE(SUM(kg),0) FROM stok"))
            depoda    = _say("SELECT COUNT(*) FROM stok WHERE durum=1")
            yolda     = _say("SELECT COUNT(*) FROM stok WHERE durum=0")
            cesit     = _say("SELECT COUNT(DISTINCT malzeme) FROM stok")

            self._set_card(self.kart_toplam, "{:,.0f} KG".format(toplam_kg))
            self._set_card(self.kart_depoda, str(depoda))
            self._set_card(self.kart_yolda,  str(yolda))
            self._set_card(self.kart_cesit,  str(cesit))

            # ── Son Siparişler tablosu ──
            self.cursor.execute("""
                SELECT sip_no, musteri, genel_toplam, durum
                FROM siparisler ORDER BY id DESC LIMIT 12
            """)
            self.tablo_son_sip.setRowCount(0)
            durum_renk = {
                "Alindi":       "#fef9e7", "Alındı":      "#fef9e7",
                "Uretimde":     "#eaf4fb", "Üretimde":    "#eaf4fb",
                "Hazir":        "#f5eef8", "Hazır":       "#f5eef8",
                "Sevk Edildi":  "#eafaf1",
                "Faturalandi":  "#f0f3f4", "Faturalandı": "#f0f3f4",
                "Iptal":        "#fde8e8", "İptal":       "#fde8e8",
            }
            for i, (sno, mus, top, dur) in enumerate(self.cursor.fetchall()):
                self.tablo_son_sip.insertRow(i)
                self.tablo_son_sip.setItem(i, 0, QTableWidgetItem("  " + (sno or "-")))
                self.tablo_son_sip.setItem(i, 1, QTableWidgetItem("  " + (mus or "-")))
                ti = QTableWidgetItem("{:,.0f} TL".format(float(top or 0)))
                ti.setTextAlignment(Qt.AlignCenter)
                self.tablo_son_sip.setItem(i, 2, ti)
                di = QTableWidgetItem(dur or "-"); di.setTextAlignment(Qt.AlignCenter)
                self.tablo_son_sip.setItem(i, 3, di)
                renk = QColor(durum_renk.get(dur, "#ffffff"))
                for c in range(4): self.tablo_son_sip.item(i, c).setBackground(renk)

            # ── Stok tablosu (kritikler) ──
            self.cursor.execute("""
                SELECT malzeme, kalinlik, SUM(kg)
                FROM stok GROUP BY malzeme, kalinlik ORDER BY SUM(kg) ASC LIMIT 8
            """)
            self.tablo_stok.setRowCount(0)
            kritik_sayisi = 0
            for i, (malzeme, kal, kg) in enumerate(self.cursor.fetchall()):
                kg = float(kg or 0)
                self.tablo_stok.insertRow(i)
                self.tablo_stok.setItem(i, 0, QTableWidgetItem("  {} {} mm".format(malzeme or '-', kal or '-')))
                ki = QTableWidgetItem("{:,.0f} KG".format(kg)); ki.setTextAlignment(Qt.AlignCenter)
                self.tablo_stok.setItem(i, 1, ki)
                if kg <= kritik_esik:
                    durum, renk, kritik_sayisi = "Kritik", QColor("#fde8e8"), kritik_sayisi+1
                elif kg <= uyari_esik:
                    durum, renk = "Uyari", QColor("#fef9e7")
                else:
                    durum, renk = "Yeterli", QColor("#eafaf1")
                di = QTableWidgetItem(durum); di.setTextAlignment(Qt.AlignCenter)
                for c in [0,1]: self.tablo_stok.item(i,c).setBackground(renk)
                di.setBackground(renk)
                self.tablo_stok.setItem(i, 2, di)

            # ── Uyarı bandı ──
            uyari_metinleri = []
            if kritik_sayisi > 0:
                uyari_metinleri.append("{} stok kritik".format(kritik_sayisi))
            if hazir > 0:
                uyari_metinleri.append("{} siparis sevkiyat bekliyor".format(hazir))
            if fat > 0:
                uyari_metinleri.append("{} siparis faturalama bekliyor".format(fat))

            if uyari_metinleri:
                self.uyari_band.setText("Dikkat:  " + "  |  ".join(uyari_metinleri))
                self.uyari_band.setStyleSheet("background:#e74c3c;color:white;font-weight:bold;font-size:13px;border-radius:10px;padding:4px;")
                self.uyari_band.show()
            else:
                self.uyari_band.setText("Tum sistemler normal")
                self.uyari_band.setStyleSheet("background:#27ae60;color:white;font-weight:bold;font-size:13px;border-radius:10px;padding:4px;")
                self.uyari_band.show()

            # ── Vadeler tablosu ──
            self.cursor.execute("""
                SELECT firma, toplam_tutar, vade_tarihi
                FROM satinalma_kayitlari
                WHERE odendi=0 OR odendi IS NULL
                ORDER BY tarih DESC LIMIT 8
            """)
            self.tablo_vade.setRowCount(0)
            for i, (firma, tutar, vade) in enumerate(self.cursor.fetchall()):
                self.tablo_vade.insertRow(i)
                self.tablo_vade.setItem(i, 0, QTableWidgetItem("  " + (firma or '-')))
                ti = QTableWidgetItem("{:,.0f} TL".format(float(tutar or 0)))
                ti.setTextAlignment(Qt.AlignCenter)
                self.tablo_vade.setItem(i, 1, ti)
                vi = QTableWidgetItem(str(vade or "-")); vi.setTextAlignment(Qt.AlignCenter)
                try:
                    gun = (datetime.strptime(vade, '%d.%m.%Y') - datetime.now()).days
                    if gun < 0:    vi.setBackground(QColor("#fde8e8"))
                    elif gun <= 3: vi.setBackground(QColor("#fef9e7"))
                except: pass
                self.tablo_vade.setItem(i, 2, vi)

        except Exception as e:
            print("Dashboard yenile hatasi: {}".format(e))

    def kritik_uyari_goster(self):
        try:
            if not ayar_al("bildirim", "acilis_popup", True): return
            kritik_esik = ayar_al("stok", "kritik_esik", 500)
            self.cursor.execute("""
                SELECT malzeme, SUM(kg) as topkg FROM stok
                GROUP BY malzeme HAVING topkg < ?
            """, (kritik_esik,))
            kritikler = self.cursor.fetchall()
            if kritikler:
                mesaj = f"⚠️ {len(kritikler)} malzeme kritik seviyenin altında!\n\n"
                for malzeme, kg in kritikler[:5]:
                    mesaj += f"• {malzeme}: {float(kg or 0):,.0f} KG\n"
                if len(kritikler) > 5:
                    mesaj += f"... ve {len(kritikler)-5} malzeme daha"
                QMessageBox.warning(None, "🚨 Kritik Stok Uyarısı", mesaj)
        except Exception as e:
            print(f"Kritik uyarı hatası: {e}")