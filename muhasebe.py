"""
Arsac Metal ERP — Muhasebe Modülü
Sevk edilmiş siparişleri faturalandırır, cariye işler.
"""
from styles import BTN_BLUE, BTN_GRAY, BTN_GREEN, BTN_ORANGE, BTN_PRIMARY, BTN_PURPLE, DIALOG_QSS, DURUM_RENK, GROUPBOX_QSS, INPUT, INPUT_QSS, LIST_QSS, SAYFA_QSS, TABLO_QSS, make_badge, make_buton, tab_qss, tablo_sag_tik_menu_ekle
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QDate
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
try:
    from finans import FinansSayfasi
except:
    FinansSayfasi = None


class FaturaDialog(QDialog):
    def __init__(self, cursor, conn, sip_id, parent=None):
        super().__init__(parent)
        self.cursor = cursor
        self.conn   = conn
        self.sip_id = sip_id
        self.setWindowTitle("🧾 Fatura Bilgileri")
        self.setFixedSize(600, 680)
        self.setStyleSheet(DIALOG_QSS)
        self.init_ui()
        self._siparis_bilgi_yukle()

    def _otomatik_fatura_no(self):
        """Veritabanındaki son fatura no'ya bakarak sıradaki no'yu üret."""
        try:
            yil = datetime.now().strftime("%Y")
            self.cursor.execute(
                "SELECT fatura_no FROM siparisler "
                "WHERE fatura_no LIKE ? AND fatura_no IS NOT NULL "
                "ORDER BY id DESC LIMIT 1",
                (f"FAT-{yil}-%",))
            row = self.cursor.fetchone()
            if row and row[0]:
                parca = row[0].rsplit("-", 1)[-1]
                try: sonraki = int(parca) + 1
                except: sonraki = 1
            else:
                sonraki = 1
            return f"FAT-{yil}-{sonraki:04d}"
        except:
            return f"FAT-{datetime.now().strftime('%Y')}-0001"

    def init_ui(self, cursor=None, conn=None, user_role=None):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20,16,20,16); lay.setSpacing(12)

        # Sipariş bilgileri (salt okunur)
        sip_box = QGroupBox("📋 Sipariş Bilgileri")
        sg = QGridLayout(sip_box)
        self.lbl_sip_no  = QLabel("-"); self.lbl_musteri = QLabel("-")
        self.lbl_tarih   = QLabel("-"); self.lbl_toplam  = QLabel("-")
        sg.addWidget(QLabel("Sipariş No:"),  0,0); sg.addWidget(self.lbl_sip_no,  0,1)
        sg.addWidget(QLabel("Müşteri:"),     0,2); sg.addWidget(self.lbl_musteri, 0,3)
        sg.addWidget(QLabel("Tarih:"),       1,0); sg.addWidget(self.lbl_tarih,   1,1)
        sg.addWidget(QLabel("Tutar:"),       1,2); sg.addWidget(self.lbl_toplam,  1,3)
        lay.addWidget(sip_box)

        # Parça bazlı fiyat tablosu
        parca_box = QGroupBox("📦 Parça Bazlı Fiyatlandırma")
        pv = QVBoxLayout(parca_box); pv.setContentsMargins(8,8,8,8)
        self.tablo_parca = QTableWidget(0, 6)
        tablo_sag_tik_menu_ekle(self.tablo_parca)
        self.tablo_parca.setHorizontalHeaderLabels(
            ["Parça Adı", "Adet", "Kg", "Fiyat Türü", "Birim Fiyat (₺)", "Tutar (₺)"])
        self.tablo_parca.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo_parca.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tablo_parca.verticalHeader().setVisible(False)
        self.tablo_parca.setFixedHeight(180)
        self.tablo_parca.setStyleSheet(
            "QTableWidget{border:1px solid #dcdde1;border-radius:6px;}"
            "QHeaderView::section{background:#f4f6f9;font-weight:bold;color:#2c3e50;"
            "padding:6px;border:none;}")
        pv.addWidget(self.tablo_parca)
        lay.addWidget(parca_box)

        # Fatura bilgileri
        fat_box = QGroupBox("🧾 Fatura Bilgileri")
        fg = QGridLayout(fat_box); fg.setSpacing(8)

        self.txt_fatura_no = QLineEdit()
        self.txt_fatura_no.setPlaceholderText("FAT-2026-0001")
        self.txt_fatura_no.setFixedHeight(40)
        self.dt_fatura = QDateEdit(); self.dt_fatura.setCalendarPopup(True)
        self.dt_fatura.setDisplayFormat("dd.MM.yyyy"); self.dt_fatura.setDate(QDate.currentDate()); self.dt_fatura.setFixedHeight(40)

        self.spn_kdv = QComboBox(); self.spn_kdv.addItems(["0","1","8","10","20"]); self.spn_kdv.setCurrentText("20"); self.spn_kdv.setFixedHeight(40)
        self.lbl_kdv_tutar  = QLabel("0,00 ₺")
        self.lbl_genel_toplam = QLabel("0,00 ₺")
        self.lbl_genel_toplam.setStyleSheet("font-size:15px;font-weight:bold;color:#c0392b;")

        self.cmb_odeme = QComboBox()
        self.cmb_odeme.addItems(["Nakit","Havale/EFT","Cek","Senet","Vadeli"])
        self.cmb_odeme.setFixedHeight(40)
        self.cmb_odeme.currentTextChanged.connect(self._odeme_degisti)

        self.dt_vade = QDateEdit(); self.dt_vade.setCalendarPopup(True)
        self.dt_vade.setDisplayFormat("dd.MM.yyyy")
        self.dt_vade.setDate(QDate.currentDate().addDays(30))
        self.dt_vade.setFixedHeight(40)
        self.dt_vade.setEnabled(False)

        self.lbl_vade_aciklama = QLabel("Vade tarihi yalnizca vadeli odemelerde aktif")
        self.lbl_vade_aciklama.setStyleSheet("color:#7f8c8d;font-size:11px;font-weight:normal;")

        fg.addWidget(QLabel("Fatura No:"),    0,0); fg.addWidget(self.txt_fatura_no,      0,1)
        fg.addWidget(QLabel("Fatura Tarihi:"),0,2); fg.addWidget(self.dt_fatura,           0,3)
        fg.addWidget(QLabel("KDV (%):"),      1,0); fg.addWidget(self.spn_kdv,             1,1)
        fg.addWidget(QLabel("KDV Tutari:"),   1,2); fg.addWidget(self.lbl_kdv_tutar,       1,3)
        fg.addWidget(QLabel("Odeme Sekli:"),  2,0); fg.addWidget(self.cmb_odeme,           2,1)
        fg.addWidget(QLabel("GENEL TOPLAM:"), 2,2); fg.addWidget(self.lbl_genel_toplam,    2,3)
        fg.addWidget(QLabel("Odeme Vadesi:"), 3,0); fg.addWidget(self.dt_vade,             3,1)
        fg.addWidget(self.lbl_vade_aciklama,  3,2,1,2)
        lay.addWidget(fat_box)

        self.spn_kdv.currentTextChanged.connect(self._kdv_guncelle)

        bl = QHBoxLayout()
        btn_iptal = QPushButton("İptal"); btn_iptal.setStyleSheet("background:#dcdde1;color:#2c3e50;border-radius:8px;padding:10px 24px;font-weight:bold;")
        btn_iptal.clicked.connect(self.reject)
        btn_faturalandir = QPushButton("🧾 Faturalandır")
        btn_faturalandir.setStyleSheet("background:#2c3e50;color:white;border-radius:8px;padding:10px 24px;font-weight:bold;font-size:14px;")
        btn_faturalandir.clicked.connect(self._faturalandir)
        bl.addWidget(btn_iptal); bl.addStretch(); bl.addWidget(btn_faturalandir)
        lay.addLayout(bl)

    def _siparis_bilgi_yukle(self):
        try:
            self.cursor.execute("""
                SELECT sip_no, musteri, tarih, genel_toplam
                FROM siparisler WHERE id=?
            """, (self.sip_id,))
            row = self.cursor.fetchone()
            if not row: return
            self.sip_no, self.musteri, tarih, toplam = row
            self.ara_toplam = float(toplam or 0)
            self.lbl_sip_no.setText(f"<b>{self.sip_no}</b>")
            self.lbl_musteri.setText(f"<b>{self.musteri}</b>")
            self.lbl_tarih.setText(tarih or "-")
            self.lbl_toplam.setText(f"<b>{self.ara_toplam:,.2f} ₺</b>")

            # Otomatik fatura no
            self.txt_fatura_no.setText(self._otomatik_fatura_no())

            # Parça bazlı fiyat tablosunu doldur
            self._parca_tablosu_doldur()
            self._kdv_guncelle()
        except Exception as e:
            print(f"Sipariş bilgi yükleme hatası: {e}")

    def _parca_tablosu_doldur(self):
        """Sipariş kalemlerini tabloya yükle, fiyat türü ve birim fiyat düzenlenebilir."""
        try:
            self.cursor.execute("""
                SELECT id, urun_adi, adet, kg, birim_fiyat, toplam_fiyat
                FROM siparis_kalemleri WHERE siparis_id=?
            """, (self.sip_id,))
            kalemler = self.cursor.fetchall()

            if not kalemler:
                is_no = "IE-" + self.sip_no
                self.cursor.execute("""
                    SELECT id, parca_adi, adet, birim_kg*adet, 0, 0
                    FROM parcalar WHERE is_no=?
                """, (is_no,))
                kalemler = self.cursor.fetchall()

            self.tablo_parca.setRowCount(0)
            self._kalem_idler = []
            toplam = 0.0

            for kid, ad, adet, kg, b_fiyat, t_fiyat in kalemler:
                r = self.tablo_parca.rowCount()
                self.tablo_parca.insertRow(r)
                self.tablo_parca.setRowHeight(r, 36)
                self._kalem_idler.append(kid)

                self.tablo_parca.setItem(r, 0, QTableWidgetItem(str(ad or "-")))
                adet_val = float(adet or 1)
                kg_val   = float(kg or 0)
                self.tablo_parca.setItem(r, 1, QTableWidgetItem(f"{adet_val:g}"))
                self.tablo_parca.setItem(r, 2, QTableWidgetItem(f"{kg_val:,.3f}"))

                # Fiyat türü — Adet / Kg
                cmb = QComboBox()
                cmb.addItems(["Adet", "Kg"])
                cmb.setFixedHeight(30)
                cmb.setStyleSheet("border:1px solid #dcdde1;border-radius:4px;padding:2px 6px;")
                cmb.currentTextChanged.connect(lambda v, row=r: self._fiyat_degisti(row))
                self.tablo_parca.setCellWidget(r, 3, cmb)

                # Birim fiyat
                spn = QDoubleSpinBox()
                spn.setRange(0, 9999999)
                spn.setDecimals(2)
                spn.setSuffix(" ₺")
                spn.setValue(float(b_fiyat or 0))
                spn.setFixedHeight(30)
                spn.valueChanged.connect(lambda v, row=r: self._fiyat_degisti(row))
                self.tablo_parca.setCellWidget(r, 4, spn)

                # Tutar
                tutar = float(b_fiyat or 0) * adet_val
                toplam += tutar
                tutar_it = QTableWidgetItem(f"{tutar:,.2f} ₺")
                tutar_it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tablo_parca.setItem(r, 5, tutar_it)

            if toplam > 0:
                self.ara_toplam = toplam
                self.lbl_toplam.setText(f"<b>{self.ara_toplam:,.2f} ₺</b>")
                self._kdv_guncelle()

        except Exception as e:
            print("Parça tablosu hatası:", e)

    def _fiyat_degisti(self, row):
        """Fiyat türü veya birim fiyat değişince tutar ve ara toplamı güncelle."""
        try:
            cmb  = self.tablo_parca.cellWidget(row, 3)
            spn  = self.tablo_parca.cellWidget(row, 4)
            adet_it = self.tablo_parca.item(row, 1)
            kg_it   = self.tablo_parca.item(row, 2)
            if not cmb or not spn: return

            tur   = cmb.currentText()   # "Adet" veya "Kg"
            fiyat = spn.value()

            if tur == "Kg":
                miktar = float(kg_it.text().replace(",", "") if kg_it else "0")
            else:
                miktar = float(adet_it.text() if adet_it else "1")

            tutar = fiyat * miktar
            tutar_it = self.tablo_parca.item(row, 5)
            if tutar_it:
                tutar_it.setText(f"{tutar:,.2f} ₺")

            # Tüm satırlardan ara toplamı yeniden hesapla
            toplam = 0.0
            for r in range(self.tablo_parca.rowCount()):
                c = self.tablo_parca.cellWidget(r, 3)
                s = self.tablo_parca.cellWidget(r, 4)
                a = self.tablo_parca.item(r, 1)
                k = self.tablo_parca.item(r, 2)
                if c and s and a:
                    m = float(k.text().replace(",","") if k else "0") if c.currentText()=="Kg" else float(a.text() or 1)
                    toplam += s.value() * m
            self.ara_toplam = toplam
            self.lbl_toplam.setText(f"<b>{toplam:,.2f} ₺</b>")
            self._kdv_guncelle()
        except Exception as e:
            print("Fiyat degisti hatasi:", e)

    def _odeme_degisti(self, text):
        vadeli = text in ("Vadeli", "Cek", "Senet")
        self.dt_vade.setEnabled(vadeli)
        if vadeli:
            self.lbl_vade_aciklama.setText("Vade tarihini secin — takvimde gozukecek")
            self.lbl_vade_aciklama.setStyleSheet("color:#c0392b;font-size:11px;font-weight:bold;")
        else:
            self.lbl_vade_aciklama.setText("Vade tarihi yalnizca vadeli odemelerde aktif")
            self.lbl_vade_aciklama.setStyleSheet("color:#7f8c8d;font-size:11px;font-weight:normal;")

    def _kdv_guncelle(self):
        try:
            oran = int(self.spn_kdv.currentText())
            kdv  = self.ara_toplam * oran / 100
            genel = self.ara_toplam + kdv
            self.lbl_kdv_tutar.setText(f"{kdv:,.2f} ₺")
            self.lbl_genel_toplam.setText(f"{genel:,.2f} ₺")
        except: pass

    def _faturalandir(self):
        fatura_no = self.txt_fatura_no.text().strip()
        if not fatura_no:
            QMessageBox.warning(self,"Hata","Fatura no boş olamaz!"); return
        try:
            oran  = int(self.spn_kdv.currentText())
            kdv   = self.ara_toplam * oran / 100
            genel = self.ara_toplam + kdv
            fatura_tarihi = self.dt_fatura.date().toString("dd.MM.yyyy")
            odeme = self.cmb_odeme.currentText()

            # Parça birim fiyatlarını kaydet
            for r in range(self.tablo_parca.rowCount()):
                cmb = self.tablo_parca.cellWidget(r, 3)
                spn = self.tablo_parca.cellWidget(r, 4)
                adet_it = self.tablo_parca.item(r, 1)
                kg_it   = self.tablo_parca.item(r, 2)
                if spn and r < len(self._kalem_idler):
                    tur = cmb.currentText() if cmb else "Adet"
                    if tur == "Kg":
                        miktar = float(kg_it.text().replace(",","") if kg_it else "0")
                    else:
                        miktar = float(adet_it.text() if adet_it else "1")
                    b_fiyat = spn.value()
                    tutar = b_fiyat * miktar
                    try:
                        self.cursor.execute(
                            "UPDATE siparis_kalemleri SET birim_fiyat=?, toplam_fiyat=? WHERE id=?",
                            (b_fiyat, tutar, self._kalem_idler[r]))
                    except:
                        pass

            # Vade bilgisi
            odeme_vadesi = ""
            if self.dt_vade.isEnabled():
                odeme_vadesi = self.dt_vade.date().toString("dd.MM.yyyy")

            self.cursor.execute("""
                UPDATE siparisler SET durum='Faturalandı',
                fatura_no=?, fatura_tarihi=?,
                kdv_toplam=?, genel_toplam=?,
                odeme_sekli=?, odeme_vadesi=?
                WHERE id=?
            """, (fatura_no, fatura_tarihi, kdv, genel,
                  odeme, odeme_vadesi, self.sip_id))

            # Vade takvime ekle — tarihi YYYY-MM-DD formatına çevir
            if odeme_vadesi:
                try:
                    from datetime import datetime as _dt
                    vade_db = _dt.strptime(odeme_vadesi, "%d.%m.%Y").strftime("%Y-%m-%d")
                    fat_db  = _dt.strptime(fatura_tarihi, "%d.%m.%Y").strftime("%Y-%m-%d")
                except:
                    vade_db = odeme_vadesi
                    fat_db  = fatura_tarihi

                not_baslik = "VADE: {} | {}".format(self.musteri, fatura_no)
                not_metni  = (
                    "Fatura No  : {}\n"
                    "Musteri    : {}\n"
                    "Tutar      : {:,.2f} TL\n"
                    "Odeme Sekli: {}\n"
                    "Vade Tarihi: {}"
                ).format(fatura_no, self.musteri, genel, odeme, odeme_vadesi)

                try:
                    # Ayni fatura için tekrar not eklemeyi önle
                    self.cursor.execute(
                        "DELETE FROM notlar WHERE baslik=?", (not_baslik,))
                    self.cursor.execute("""
                        INSERT INTO notlar
                            (baslik, tarih, oncelik, not_metni, hatirlatici, olusturma)
                        VALUES (?, ?, 'Yüksek', ?, ?, ?)
                    """, (not_baslik, vade_db, not_metni, vade_db, fat_db))
                except Exception as ne:
                    print("Takvim notu hatasi:", ne)

            # Cariye otomatik işle — her zaman yapılır
            self.cursor.execute(
                "SELECT id FROM tedarikciler WHERE firma_adi=?", (self.musteri,))
            mevcut = self.cursor.fetchone()
            if not mevcut:
                # Yeni cari oluştur
                self.cursor.execute("""
                    INSERT INTO tedarikciler (firma_adi, notlar)
                    VALUES (?, ?)
                """, (self.musteri, f"Otomatik eklendi. İlk fatura: {fatura_no}"))
                log_yaz(self.cursor, self.conn, "CARI_EKLENDI",
                        f"{self.musteri} muhasebe tarafindan otomatik eklendi")
            else:
                # Mevcut carinin notlarına fatura bilgisi ekle
                self.cursor.execute("""
                    UPDATE tedarikciler SET notlar = COALESCE(notlar,'') || ?
                    WHERE firma_adi=?
                """, (f" | Fatura:{fatura_no} ({fatura_tarihi})", self.musteri))

            self.conn.commit()
            log_yaz(self.cursor, self.conn, "SIPARIS_FATURALANDI",
                    f"{self.sip_no} | {fatura_no} | {genel:,.2f} TL | Cari: {self.musteri}")

            # Cariye otomatik isle: tahsil_edildi guncelle
            try:
                self.cursor.execute(
                    "UPDATE siparisler SET tahsil_edildi=1 WHERE id=?",
                    (self.sip_id,))
                self.conn.commit()
            except Exception as ce:
                print("Cari tahsil guncelleme hatasi:", ce)

            QMessageBox.information(self, "Basarili",
                f"Siparis faturalandi!\nFatura No: {fatura_no}\nToplam: {genel:,.2f} TL\n\nMusteri cari kaydina islendi.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self,"Hata",str(e))


class MuhasebeSayfasi(QWidget):
    def __init__(self, cursor, conn, user_role):
        super().__init__()
        self.cursor    = cursor
        self.conn      = conn
        self.user_role = user_role
        self.init_ui(cursor, conn, user_role)
        self.yenile()

    def init_ui(self, cursor=None, conn=None, user_role=None):
        self.setStyleSheet(SAYFA_QSS + INPUT_QSS + TABLO_QSS)
        lay = QVBoxLayout(self); lay.setContentsMargins(24,16,24,16); lay.setSpacing(14)

        # Üst
        ust = QHBoxLayout()
        lbl = QLabel("MUHASEBE")
        lbl.setStyleSheet("font-size:18px;font-weight:bold;color:#2c3e50;")
        ust.addWidget(lbl)

        self.k_bekleyen    = self._kart("FATURALANACAK","0","#e67e22")
        self.k_faturalandi = self._kart("FATURALANDI",  "0","#27ae60")
        self.k_tutar       = self._kart("TOPLAM TUTAR", "0 TL","#2c3e50")
        for k in [self.k_bekleyen, self.k_faturalandi, self.k_tutar]:
            ust.addWidget(k)

        ust.addStretch()
        btn_excel_muh = QPushButton("Excel")
        btn_excel_muh.setFixedHeight(36)
        btn_excel_muh.setStyleSheet("background:#27ae60;color:white;border-radius:8px;padding:4px 16px;font-weight:bold;font-size:12px;border:none;")
        btn_excel_muh.clicked.connect(self._excel_export)
        ust.addWidget(btn_excel_muh)
        lay.addLayout(ust)

        # Sekmeler
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { background:white; border-radius:10px; border:1px solid #dcdde1; }
            QTabBar::tab { background:#f4f6f9; color:#2c3e50; padding:8px 20px;
                           border-radius:6px; font-weight:bold; margin-right:4px; }
            QTabBar::tab:selected { background:#2c3e50; color:white; }
        """)

        # Bekleyen faturalar
        bek_w = QWidget(); bv = QVBoxLayout(bek_w); bv.setContentsMargins(8,8,8,8)
        self.tablo_bek = QTableWidget(0,6)
        tablo_sag_tik_menu_ekle(self.tablo_bek)
        self.tablo_bek.setHorizontalHeaderLabels(["SİPARİŞ NO","MÜŞTERİ","SEVK TARİHİ","TOPLAM","ARAÇ","İŞLEM"])
        self.tablo_bek.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo_bek.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tablo_bek.verticalHeader().setVisible(False)
        self.tablo_bek.setShowGrid(False)
        self.tablo_bek.setAlternatingRowColors(True)
        self.tablo_bek.verticalHeader().setDefaultSectionSize(44)
        bv.addWidget(self.tablo_bek)
        self.tabs.addTab(bek_w, "Bekleyen Sevkiyatlar")

        # Faturalandı
        fat_w = QWidget(); fv = QVBoxLayout(fat_w); fv.setContentsMargins(8,8,8,8)
        self.tablo_fat = QTableWidget(0,6)
        tablo_sag_tik_menu_ekle(self.tablo_fat)
        self.tablo_fat.setHorizontalHeaderLabels(["SİPARİŞ NO","MÜŞTERİ","FATURA NO","FATURA TARİHİ","TOPLAM","DURUM"])
        self.tablo_fat.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo_fat.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tablo_fat.verticalHeader().setVisible(False)
        self.tablo_fat.setShowGrid(False)
        self.tablo_fat.setAlternatingRowColors(True)
        self.tablo_fat.verticalHeader().setDefaultSectionSize(44)
        fv.addWidget(self.tablo_fat)
        self.tabs.addTab(fat_w, "Faturalananlar")

        # Finans / Vade takibi sekmesi
        if FinansSayfasi:
            self.finans_widget = FinansSayfasi(cursor, conn, user_role)
            self.tabs.addTab(self.finans_widget, "Finans & Vade")

        lay.addWidget(self.tabs)

    def _kart(self, b, v, r):
        f = QFrame(); f.setFixedSize(140,54)
        f.setStyleSheet(f"QFrame{{background:{r};border-radius:10px;border:none;}}")
        l = QVBoxLayout(f); l.setContentsMargins(8,4,8,4); l.setSpacing(0)
        lb = QLabel(b); lb.setStyleSheet("color:rgba(255,255,255,0.75);font-size:9px;font-weight:bold;background:transparent;letter-spacing:1px;")
        lv = QLabel(v); lv.setObjectName("Val"); lv.setStyleSheet("color:white;font-size:16px;font-weight:900;background:transparent;")
        l.addWidget(lb); l.addWidget(lv); return f

    def _set_kart(self, k, v):
        k.findChild(QLabel,"Val").setText(str(v))

    def _excel_export(self):
        if not excel_kaydet:
            return
        sutunlar = ["Siparis No","Musteri","Tarih","Toplam (TL)","Durum","Fatura No"]
        satirlar = []
        try:
            self.cursor.execute("""
                SELECT sip_no, musteri, tarih, genel_toplam, durum, COALESCE(fatura_no,'-')
                FROM siparisler WHERE durum NOT IN ('Alindi','Alindi')
                ORDER BY id DESC
            """)
            for row in self.cursor.fetchall():
                satirlar.append(list(row))
        except Exception as e:
            print("Muhasebe excel hatasi:", e)
        excel_kaydet(self, "Muhasebe", sutunlar, satirlar)

    def yenile(self):
        try:
            self.cursor.execute("SELECT COUNT(*) FROM siparisler WHERE durum='Sevk Edildi'")
            self._set_kart(self.k_bekleyen, self.cursor.fetchone()[0])
            self.cursor.execute("SELECT COUNT(*) FROM siparisler WHERE durum='Faturalandı'")
            self._set_kart(self.k_faturalandi, self.cursor.fetchone()[0])
            self.cursor.execute("SELECT COALESCE(SUM(genel_toplam),0) FROM siparisler WHERE durum='Faturalandı'")
            tutar = self.cursor.fetchone()[0]
            self._set_kart(self.k_tutar, f"{tutar:,.0f}₺")

            # Bekleyenler
            self.cursor.execute("""
                SELECT id, sip_no, musteri, tarih, genel_toplam, arac
                FROM siparisler WHERE durum='Sevk Edildi' ORDER BY id DESC
            """)
            self.tablo_bek.setRowCount(0)
            for i, (sid, sno, mus, tarih, top, arac) in enumerate(self.cursor.fetchall()):
                self.tablo_bek.insertRow(i)
                for j, v in enumerate([sno, mus or "-", tarih or "-",
                                        f"{float(top or 0):,.2f} ₺", arac or "-"]):
                    item = QTableWidgetItem(v); item.setTextAlignment(Qt.AlignCenter)
                    item.setData(Qt.UserRole, sid)
                    self.tablo_bek.setItem(i,j,item)
                btn = QPushButton("Faturalandir"); btn.setFixedHeight(32); btn.setMinimumWidth(110)
                btn.setStyleSheet("background:#2c3e50;color:white;font-weight:bold;font-size:12px;border-radius:6px;border:none;padding:4px 12px;")
                btn.clicked.connect(lambda _, sid=sid: self._faturalandir(sid))
                bw = QWidget(); bl = QHBoxLayout(bw); bl.setContentsMargins(4,4,4,4); bl.addWidget(btn)
                self.tablo_bek.setCellWidget(i,5,bw)

            # Faturalananlar
            self.cursor.execute("""
                SELECT sip_no, musteri, fatura_no, fatura_tarihi, genel_toplam, durum
                FROM siparisler WHERE durum='Faturalandı' ORDER BY id DESC
            """)
            self.tablo_fat.setRowCount(0)
            for i, (sno, mus, fno, ftar, top, durum) in enumerate(self.cursor.fetchall()):
                self.tablo_fat.insertRow(i)
                for j, v in enumerate([sno, mus or "-", fno or "-", ftar or "-",
                                        f"{float(top or 0):,.2f} ₺", durum]):
                    item = QTableWidgetItem(v); item.setTextAlignment(Qt.AlignCenter)
                    if j == 5: item.setForeground(QColor("#27ae60"))
                    self.tablo_fat.setItem(i,j,item)

        except Exception as e:
            print(f"Muhasebe yenile hatası: {e}")

    def _faturalandir(self, sid):
        dlg = FaturaDialog(self.cursor, self.conn, sid, self)
        if dlg.exec_() == QDialog.Accepted:
            self.yenile()
