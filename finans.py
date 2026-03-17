from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from datetime import datetime, timedelta
try:
    from log import log_yaz
except:
    def log_yaz(c,n,i,d=""): pass


def vade_gun_farki(vade_tarihi_str):
    try:
        if not vade_tarihi_str or vade_tarihi_str == "-": return None
        if "Gun" in str(vade_tarihi_str) or "Gün" in str(vade_tarihi_str): return None
        return (datetime.strptime(vade_tarihi_str.strip(), '%d.%m.%Y') - datetime.now()).days
    except: return None

def vade_goster(vade_tarihi_str):
    if not vade_tarihi_str or vade_tarihi_str == "-": return "-"
    if "Gun" in str(vade_tarihi_str) or "Gün" in str(vade_tarihi_str): return "Eski kayit"
    return vade_tarihi_str


class FinansSayfasi(QWidget):
    def __init__(self, cursor, conn, user_role):
        super().__init__()
        self.cursor, self.conn, self.user_role = cursor, conn, user_role
        self.filtre = "hepsi"
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #ebedef; font-family: 'Segoe UI', Arial; }
            QTableWidget { background: white; border-radius: 10px; border: 1px solid #dcdde1; font-size: 13px; }
            QHeaderView::section { background-color: #2c3e50; color: white; padding: 10px; font-weight: bold; border: none; }
            QLabel { font-size: 14px; font-weight: bold; color: #2c3e50; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        # Başlık + yardım
        ust = QHBoxLayout()
        ust.addWidget(QLabel("📈 FİNANSAL DURUM VE VADE TAKİBİ"))
        ust.addStretch()
        btn_yardim = QPushButton("❓")
        btn_yardim.setFixedSize(32,32)
        btn_yardim.setStyleSheet("background:#2980b9;color:white;border-radius:16px;font-weight:bold;font-size:14px;padding:0;")
        btn_yardim.clicked.connect(self._yardim)
        ust.addWidget(btn_yardim)
        layout.addLayout(ust)

        # Özet kartlar
        kartlar_lay = QHBoxLayout(); kartlar_lay.setSpacing(15)
        self.kart_toplam   = self._kart("TOPLAM ACIK BORC",        "0.00 TL", "#c0392b")
        self.kart_gecmis   = self._kart("VADESI GECMIS",           "0.00 TL", "#e74c3c")
        self.kart_yaklasan = self._kart("3 GUNDE ODENMESI GEREKEN","0.00 TL", "#e67e22")
        self.kart_odendi   = self._kart("TOPLAM ODENDI",           "0.00 TL", "#27ae60")
        for k in [self.kart_toplam, self.kart_gecmis, self.kart_yaklasan, self.kart_odendi]:
            kartlar_lay.addWidget(k)
        layout.addLayout(kartlar_lay)

        # Filtre satırı
        filtre_lay = QHBoxLayout()
        for renk, aciklama in [("#e74c3c","🔴 Vadesi Gecmis"),("#e67e22","🟡 3 Gune Kadar"),("#27ae60","🟢 Normal"),("#95a5a6","⚪ Odendi")]:
            lbl = QLabel(aciklama)
            lbl.setStyleSheet(f"color:{renk};font-size:12px;font-weight:bold;background:transparent;")
            filtre_lay.addWidget(lbl)
        filtre_lay.addStretch()
        self.btn_hepsi    = self._filtre_btn("Tumu",    "hepsi")
        self.btn_bekleyen = self._filtre_btn("Bekleyen","bekleyen")
        self.btn_odendi_f = self._filtre_btn("Odendi",  "odendi")
        for b in [self.btn_hepsi, self.btn_bekleyen, self.btn_odendi_f]:
            filtre_lay.addWidget(b)
        layout.addLayout(filtre_lay)

        # Tablo
        self.tablo = QTableWidget(0, 7)
        self.tablo.setHorizontalHeaderLabels(["ID","FIRMA ADI","SON ODEME TARIHI","TUTAR","ODEME TIPI","DURUM","ISLEM"])
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tablo.setAlternatingRowColors(True)
        self.tablo.verticalHeader().setVisible(False)
        self.tablo.verticalHeader().setDefaultSectionSize(46)
        self.tablo.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tablo.customContextMenuRequested.connect(self.sag_tik)
        layout.addWidget(self.tablo)
        self.yenile()

    def _kart(self, baslik, deger, renk):
        kart = QFrame(); kart.setFixedHeight(90)
        kart.setStyleSheet(f"QFrame {{ background:{renk};border-radius:12px; }}")
        lay = QVBoxLayout(kart); lay.setContentsMargins(15,8,15,8)
        lb = QLabel(baslik); lb.setStyleSheet("color:rgba(255,255,255,0.85);font-size:11px;font-weight:bold;background:transparent;"); lb.setAlignment(Qt.AlignCenter)
        lv = QLabel(deger);  lv.setStyleSheet("color:white;font-size:18px;font-weight:900;background:transparent;"); lv.setAlignment(Qt.AlignCenter); lv.setObjectName("deger")
        lay.addWidget(lb); lay.addWidget(lv)
        return kart

    def _filtre_btn(self, metin, kod):
        btn = QPushButton(metin); btn.setFixedSize(90,30); btn.setCheckable(True); btn.setChecked(kod=="hepsi")
        btn.setStyleSheet("QPushButton{background:white;color:#2c3e50;border:1px solid #bdc3c7;border-radius:5px;font-size:12px;font-weight:bold;} QPushButton:checked{background:#2c3e50;color:white;border:none;}")
        btn.clicked.connect(lambda _,k=kod: self.filtre_degistir(k))
        return btn

    def _yardim(self):
        QMessageBox.information(self, "❓ Finans Takibi Nasıl Kullanılır?",
            "💳 ÖDEME İŞARETLEME:\n"
            "  'Ödendi İşaretle' butonuna tıklayarak\n"
            "  yapılan ödemeleri kaydedin.\n\n"
            "🎨 RENK KODLARI:\n"
            "  🔴 Kırmızı — Vadesi geçmiş, acil ödeme gerekli\n"
            "  🟡 Sarı    — 3 gün içinde ödenmeli\n"
            "  🟢 Yeşil   — Normal, vadesine gün var\n"
            "  ⚪ Gri     — Ödendi\n\n"
            "🖱️ SAĞ TIK:\n"
            "  Kayıt silmek için sağ tık yapın (sadece admin)")

    def filtre_degistir(self, kod):
        self.filtre = kod
        self.btn_hepsi.setChecked(kod=="hepsi")
        self.btn_bekleyen.setChecked(kod=="bekleyen")
        self.btn_odendi_f.setChecked(kod=="odendi")
        self.yenile()

    def sag_tik(self, pos):
        if self.user_role != "yonetici": return
        menu = QMenu()
        sil = menu.addAction("🗑️ Kaydi Sil")
        if menu.exec_(self.tablo.mapToGlobal(pos)) == sil:
            row = self.tablo.currentRow()
            if row < 0: return
            id_val  = self.tablo.item(row,0).text()
            firma   = self.tablo.item(row,1).text() if self.tablo.item(row,1) else "-"
            tutar   = self.tablo.item(row,3).text() if self.tablo.item(row,3) else "-"
            onay = QMessageBox.question(self, "🗑️ Kayit Sil",
                f"Firma : {firma}\nTutar : {tutar}\n\nBu kayit kalici olarak silinecek!\nEmin misiniz?",
                QMessageBox.Yes | QMessageBox.No)
            if onay == QMessageBox.Yes:
                self.cursor.execute("DELETE FROM satinalma_kayitlari WHERE id=?", (id_val,))
                self.conn.commit()
                log_yaz(self.cursor, self.conn, "FINANS_SILME", f"ID:{id_val} | {firma} | {tutar}")
                self.yenile()

    def odeme_isle(self, kayit_id):
        # Kayit bilgilerini al
        self.cursor.execute("SELECT firma, toplam_tutar, vade_tarihi FROM satinalma_kayitlari WHERE id=?", (kayit_id,))
        row = self.cursor.fetchone()
        if not row: return
        firma, tutar, vade = row

        onay = QMessageBox.question(self, "💳 Ödeme Onayı",
            f"Aşağıdaki ödeme gerçekleşti olarak işaretlenecek:\n\n"
            f"  Firma : {firma}\n"
            f"  Tutar : {float(tutar or 0):,.2f} TL\n"
            f"  Vade  : {vade or '-'}\n\n"
            "Ödeme yapıldığını onaylıyor musunuz?",
            QMessageBox.Yes | QMessageBox.No)
        if onay == QMessageBox.Yes:
            bugun = datetime.now().strftime('%d.%m.%Y')
            self.cursor.execute(
                "UPDATE satinalma_kayitlari SET odendi=1, odeme_tarihi=? WHERE id=?",
                (bugun, kayit_id)
            )
            self.conn.commit()
            log_yaz(self.cursor, self.conn, "ODEME_YAPILDI",
                    f"{firma} | {float(tutar or 0):,.2f} TL | Vade:{vade}")
            self.yenile()

    def yenile(self):
        try:
            if self.filtre == "bekleyen":
                where = "WHERE (odendi IS NULL OR odendi=0)"
            elif self.filtre == "odendi":
                where = "WHERE odendi=1"
            else:
                where = ""

            self.cursor.execute(f"""
                SELECT id, firma, vade_tarihi, toplam_tutar, odeme_tipi, odendi, odeme_tarihi, tarih
                FROM satinalma_kayitlari {where}
                ORDER BY odendi ASC, id DESC
            """)
            kayitlar = self.cursor.fetchall()
            self.tablo.setRowCount(0)

            toplam_borc = gecmis_borc = yaklasan_borc = odendi_toplam = 0.0
            self.cursor.execute("SELECT toplam_tutar, odendi, vade_tarihi FROM satinalma_kayitlari")
            for t, o, v in self.cursor.fetchall():
                t = float(t or 0)
                if o == 1:
                    odendi_toplam += t
                else:
                    toplam_borc += t
                    gun = vade_gun_farki(v)
                    if gun is not None:
                        if gun < 0:  gecmis_borc   += t
                        elif gun<=3: yaklasan_borc += t

            self.kart_toplam.findChild(QLabel,"deger").setText(f"{toplam_borc:,.2f} TL")
            self.kart_gecmis.findChild(QLabel,"deger").setText(f"{gecmis_borc:,.2f} TL")
            self.kart_yaklasan.findChild(QLabel,"deger").setText(f"{yaklasan_borc:,.2f} TL")
            self.kart_odendi.findChild(QLabel,"deger").setText(f"{odendi_toplam:,.2f} TL")

            for r, row in enumerate(kayitlar):
                kayit_id, firma, vade, tutar, odeme_tipi, odendi, odeme_tarihi, tarih = row
                self.tablo.insertRow(r)

                if odendi == 1:
                    satir_renk = QColor("#f0f0f0")
                else:
                    gun = vade_gun_farki(vade)
                    if gun is not None and gun < 0:  satir_renk = QColor("#fde8e8")
                    elif gun is not None and gun<=3: satir_renk = QColor("#fef9e7")
                    else:                            satir_renk = QColor("#ffffff")

                for c, v in {0:str(kayit_id), 1:firma or "-", 3:f"{float(tutar or 0):,.2f} TL", 4:odeme_tipi or "-"}.items():
                    item = QTableWidgetItem(str(v))
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                    item.setBackground(satir_renk)
                    self.tablo.setItem(r, c, item)

                # Vade widget
                vade_w = QWidget()
                vade_w.setStyleSheet(f"background-color: {'#f0f0f0' if odendi==1 else satir_renk.name()};")
                vl = QVBoxLayout(vade_w); vl.setContentsMargins(5,3,5,3); vl.setSpacing(1)
                lt = QLabel(f"📅 {vade_goster(vade)}")
                lt.setStyleSheet("font-weight:bold;font-size:12px;color:#2c3e50;background:transparent;"); lt.setAlignment(Qt.AlignCenter)
                vl.addWidget(lt)
                if odendi != 1 and vade and vade != "-":
                    gun = vade_gun_farki(vade)
                    if gun is not None:
                        if gun < 0:  gtxt,gclr = f"{abs(gun)} gun gecti!","#e74c3c"
                        elif gun==0: gtxt,gclr = "Bugun!","#e74c3c"
                        elif gun<=3: gtxt,gclr = f"{gun} gun kaldi","#e67e22"
                        else:        gtxt,gclr = f"{gun} gun kaldi","#27ae60"
                        lg = QLabel(gtxt); lg.setStyleSheet(f"font-size:11px;color:{gclr};font-weight:bold;background:transparent;"); lg.setAlignment(Qt.AlignCenter)
                        vl.addWidget(lg)
                elif odendi==1 and odeme_tarihi:
                    lo = QLabel(f"Odendi: {odeme_tarihi}"); lo.setStyleSheet("font-size:11px;color:#27ae60;font-weight:bold;background:transparent;"); lo.setAlignment(Qt.AlignCenter)
                    vl.addWidget(lo)
                self.tablo.setCellWidget(r, 2, vade_w)

                # Durum
                if odendi == 1:
                    dl = QLabel("✅ Odendi"); dl.setStyleSheet("color:#27ae60;font-weight:bold;font-size:13px;background:transparent;"); dl.setAlignment(Qt.AlignCenter)
                    self.tablo.setCellWidget(r, 5, dl)
                else:
                    gun = vade_gun_farki(vade)
                    if gun is None:     dtxt,dclr,dbg = "Bekliyor","#7f8c8d","#f8f9fa"
                    elif gun < 0:       dtxt,dclr,dbg = f"{abs(gun)} gun gecti!","#fff","#e74c3c"
                    elif gun == 0:      dtxt,dclr,dbg = "Bugun!","#fff","#e74c3c"
                    elif gun <= 3:      dtxt,dclr,dbg = f"{gun} gun kaldi","#fff","#e67e22"
                    else:               dtxt,dclr,dbg = f"{gun} gun kaldi","#fff","#27ae60"
                    dc = QWidget(); dc.setStyleSheet("background:transparent;")
                    dcl = QHBoxLayout(dc); dcl.setContentsMargins(6,4,6,4)
                    db = QLabel(dtxt); db.setStyleSheet(f"color:{dclr};background-color:{dbg};font-weight:bold;font-size:12px;border-radius:4px;padding:3px 8px;"); db.setAlignment(Qt.AlignCenter)
                    dcl.addStretch(); dcl.addWidget(db); dcl.addStretch()
                    self.tablo.setCellWidget(r, 5, dc)

                # İşlem
                if odendi != 1:
                    btn = QPushButton("💳 Odendi Isaretle")
                    btn.setFixedHeight(30)
                    btn.setStyleSheet("background:#27ae60;color:white;font-weight:bold;font-size:11px;border-radius:4px;padding:2px 8px;")
                    btn.clicked.connect(lambda _,kid=kayit_id: self.odeme_isle(kid))
                    c2 = QWidget(); cl2 = QHBoxLayout(c2); cl2.setContentsMargins(4,4,4,4); cl2.addWidget(btn)
                    self.tablo.setCellWidget(r, 6, c2)
                else:
                    bl = QLabel("-"); bl.setAlignment(Qt.AlignCenter)
                    self.tablo.setCellWidget(r, 6, bl)

        except Exception as e:
            print(f"Finans yenileme hatasi: {e}")