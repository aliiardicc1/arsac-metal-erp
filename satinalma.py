import os
from datetime import datetime, timedelta
try:
    from log import log_yaz
except Exception:
    def log_yaz(c,n,i,d=""): pass
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def tr(s):
    """Türkçe karakterleri PDF için ASCII'ye çevirir."""
    s = str(s)
    tablo = str.maketrans(
        'ÇçĞğIiÖöŞşÜü',
        'CcGgIiOoSsUu'
    )
    return s.translate(tablo)


def _pdf_olustur(baslik_txt, siparis_no, firma, kalemler, nakliye, toplam_tutar, vade, odeme, tarih, klasor="Satin Alma Belgeleri"):
    if not os.path.exists(klasor):
        os.makedirs(klasor)
    dosya = f"{klasor}/{baslik_txt.replace(' ','_')}_{siparis_no}.pdf"

    KIRMIZI  = colors.HexColor("#c0392b")
    KOYU     = colors.HexColor("#2c3e50")
    ACIK_GRI = colors.HexColor("#f4f6f9")
    SARI     = colors.HexColor("#f1c40f")
    BEYAZ    = colors.white

    doc   = SimpleDocTemplate(dosya, pagesize=A4,
                               rightMargin=1.5*cm, leftMargin=1.5*cm,
                               topMargin=1.5*cm,  bottomMargin=1.5*cm)
    story = []
    kk    = ParagraphStyle("kk", fontSize=9, fontName="Helvetica-Bold",   textColor=KOYU)
    kn    = ParagraphStyle("kn", fontSize=9, fontName="Helvetica",        textColor=KOYU)

    # Header
    hdr = Table([[
        Paragraph("<b>ARSAC METAL</b>", ParagraphStyle("s", fontSize=18, fontName="Helvetica-Bold", textColor=KIRMIZI)),
        Paragraph("OKSIJEN PLAZMA LAZER KESIM<br/>DEMIR CELIK METAL SAN. VE TIC. LTD. STI.",
                  ParagraphStyle("s2", fontSize=9, fontName="Helvetica", textColor=KOYU, alignment=TA_RIGHT))
    ]], colWidths=[9*cm, 9*cm])
    hdr.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                              ('LINEBELOW',(0,0),(-1,-1),1.5,KIRMIZI),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
    story.append(hdr)
    story.append(Spacer(1, 0.4*cm))

    # Form basligi
    bt = Table([[Paragraph(baslik_txt, ParagraphStyle("b", fontSize=16, fontName="Helvetica-Bold",
                                                       textColor=BEYAZ, alignment=TA_CENTER))]], colWidths=[18*cm])
    bt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),KIRMIZI),
                             ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
    story.append(bt)
    story.append(Spacer(1, 0.4*cm))

    # Bilgi karti
    bilgi = Table([
        [Paragraph("<b>NO</b>", kk), Paragraph(f"#{siparis_no}", kn),
         Paragraph("<b>TARIH</b>", kk), Paragraph(tarih, kn)],
        [Paragraph("<b>FIRMA</b>", kk), Paragraph(firma, kn),
         Paragraph("<b>VADE</b>", kk), Paragraph(str(vade), kn)],
        [Paragraph("<b>ODEME</b>", kk), Paragraph(odeme, kn),
         Paragraph("<b>DURUM</b>", kk), Paragraph(baslik_txt.split()[0], kn)],
    ], colWidths=[3.5*cm, 5.5*cm, 3.5*cm, 5.5*cm])
    bilgi.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),ACIK_GRI),('ROWBACKGROUNDS',(0,0),(-1,-1),[ACIK_GRI,BEYAZ]),
        ('GRID',(0,0),(-1,-1),0.5,colors.HexColor("#dcdde1")),
        ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
        ('LEFTPADDING',(0,0),(-1,-1),8),('FONTNAME',(0,0),(-1,-1),'Helvetica'),('FONTSIZE',(0,0),(-1,-1),9),
    ]))
    story.append(bilgi)
    story.append(Spacer(1, 0.5*cm))

    # Kalem tablosu
    story.append(Paragraph("<b>KALEMLER</b>", ParagraphStyle("sh", fontSize=11, fontName="Helvetica-Bold", textColor=KOYU, spaceAfter=5)))
    tv = [["#","Malzeme","En","Boy","Kal.","KG","Birim Fiyat","Tutar"]]
    toplam_kg = 0.0; malzeme_top = 0.0
    for idx, k in enumerate(kalemler, 1):
        kalite, en, boy, kal, kg, bf = k[:6]
        kg_f = float(kg or 0); bf_f = float(bf or 0); tutar = kg_f * bf_f
        toplam_kg += kg_f; malzeme_top += tutar
        tv.append([str(idx), kalite, str(en), str(boy), str(kal),
                   f"{kg_f:,.2f}", f"{bf_f:,.2f} TL", f"{tutar:,.2f} TL"])
    kt = Table(tv, colWidths=[0.6*cm,3.8*cm,1.8*cm,1.8*cm,1.4*cm,2*cm,2.6*cm,3*cm])
    kt.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),KOYU),('TEXTCOLOR',(0,0),(-1,0),BEYAZ),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,0),8),
        ('FONTNAME',(0,1),(-1,-1),'Helvetica'),('FONTSIZE',(0,1),(-1,-1),8),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[BEYAZ,ACIK_GRI]),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),('ALIGN',(7,1),(7,-1),'RIGHT'),
        ('GRID',(0,0),(-1,-1),0.5,colors.HexColor("#dcdde1")),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
    ]))
    story.append(kt)
    story.append(Spacer(1, 0.4*cm))

    # Toplam
    nakliye_f = float(nakliye or 0)
    genel     = malzeme_top + nakliye_f
    ozet = Table([
        [Paragraph("<b>Malzeme Bedeli:</b>", kk), Paragraph(f"{malzeme_top:,.2f} TL", ParagraphStyle("r", fontSize=9, fontName="Helvetica", alignment=TA_RIGHT))],
        [Paragraph("<b>Nakliye:</b>", kk),        Paragraph(f"{nakliye_f:,.2f} TL",   ParagraphStyle("r", fontSize=9, fontName="Helvetica", alignment=TA_RIGHT))],
        [Paragraph("<b>GENEL TOPLAM:</b>",         ParagraphStyle("gt", fontSize=12, fontName="Helvetica-Bold", textColor=BEYAZ)),
         Paragraph(f"{genel:,.2f} TL",             ParagraphStyle("gtr",fontSize=12, fontName="Helvetica-Bold", textColor=SARI, alignment=TA_RIGHT))],
    ], colWidths=[12*cm, 6*cm])
    ozet.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,1),ACIK_GRI),('BACKGROUND',(0,2),(-1,2),KIRMIZI),
        ('GRID',(0,0),(-1,1),0.5,colors.HexColor("#dcdde1")),
        ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
        ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
    ]))
    story.append(ozet)
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=KIRMIZI))
    story.append(Paragraph(f"Arsac Metal ERP | {tarih}", ParagraphStyle("alt", fontSize=7, fontName="Helvetica", textColor=colors.grey, alignment=TA_CENTER)))
    doc.build(story)
    return dosya


# ─────────────────────────────────────────────
#  TEKLIF POPUP — Talepler → Teklif Oluştur
# ─────────────────────────────────────────────
class TeklifPopUp(QDialog):
    def __init__(self, veri_listesi, cursor, conn, callback):
        super().__init__()
        self.veri_listesi = veri_listesi
        self.cursor = cursor
        self.conn   = conn
        self.callback = callback
        self.setWindowTitle("📋 Teklif Oluştur")
        self.setMinimumWidth(1100)
        self.setMinimumHeight(580)
        self.setStyleSheet("""
            QDialog { background: #f4f6f9; }
            QLabel  { font-weight: bold; color: #2c3e50; font-size: 13px; }
            QLineEdit, QComboBox {
                padding: 6px 10px; border: 1px solid #bdc3c7;
                border-radius: 6px; background: white;
                color: #2c3e50; font-size: 13px; min-height: 28px;
            }
            QLineEdit:focus { border: 1px solid #c0392b; }
            QTableWidget { background: white; border-radius: 8px; border: 1px solid #dcdde1; font-size: 13px; }
            QHeaderView::section { background: #2c3e50; color: white; padding: 8px; font-weight: bold; border: none; }
            #AltPanel { background: #2c3e50; border-radius: 10px; }
            #TutarLbl { color: #f1c40f; font-size: 17px; font-weight: bold; }
        """)
        self.init_ui()

    def init_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(15,15,15,15)
        lay.setSpacing(10)

        # Başlik + satır sil butonu
        hdr = QHBoxLayout()
        hdr.addWidget(QLabel("📋 Teklif Kalemleri — Fiyat ve Tedarikçi Girin:"))
        hdr.addStretch()
        uyari = QLabel("⚠️ Değiştirilen satirlar sari işaretlenir")
        uyari.setStyleSheet("color: #e67e22; font-size: 12px;")
        hdr.addWidget(uyari)
        btn_satir_sil = QPushButton("🗑️ Seçili Satırı Sil")
        btn_satir_sil.setFixedHeight(30)
        btn_satir_sil.setStyleSheet("background:#e74c3c;color:white;font-weight:bold;font-size:12px;border-radius:5px;padding:4px 12px;")
        btn_satir_sil.clicked.connect(self._satir_sil)
        hdr.addWidget(btn_satir_sil)
        lay.addLayout(hdr)

        # Tablo — Adet kolonu eklendi (kolon 4), ID kolonu 8'e taşındı
        self.tablo = QTableWidget(len(self.veri_listesi), 9)
        self.tablo.setHorizontalHeaderLabels(["Kalite","En (mm)","Boy (mm)","Kalinlik (mm)","Adet","KG (Oto)","Tedarikçi","Birim Fiyat","ID"])
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo.setColumnHidden(8, True)
        self.tablo.verticalHeader().setVisible(False)
        self.tablo.setAlternatingRowColors(True)
        self.tablo.verticalHeader().setDefaultSectionSize(38)
        self.tablo.setSelectionBehavior(QAbstractItemView.SelectRows)

        tedarikciler = self._tedarikcileri_getir()
        self.orijinal = []

        for i, veri in enumerate(self.veri_listesi):
            self.orijinal.append({'kalite':str(veri[1]),'en':str(veri[2]),'boy':str(veri[3]),'kal':str(veri[4])})

            def _le(txt, center=False):
                w = QLineEdit(txt)
                if center: w.setAlignment(Qt.AlignCenter)
                return w

            t_kalite = _le(str(veri[1]))
            t_en     = _le(str(veri[2]), True)
            t_boy    = _le(str(veri[3]), True)
            t_kal    = _le(str(veri[4]), True)

            t_kalite.textChanged.connect(lambda _,r=i: self._kontrol(r))
            t_en.textChanged.connect(lambda _,r=i: self._olcu(r))
            t_boy.textChanged.connect(lambda _,r=i: self._olcu(r))
            t_kal.textChanged.connect(lambda _,r=i: self._olcu(r))

            # Adet — değiştirilebilir, KG'yi otomatik günceller
            t_adet = _le("1", True)
            t_adet.textChanged.connect(lambda _,r=i: self._olcu(r))

            kg_val = float(veri[5] or 0)
            t_kg = QLineEdit(f"{kg_val:.2f}")
            t_kg.setAlignment(Qt.AlignCenter)
            t_kg.setReadOnly(True)
            t_kg.setStyleSheet("background:#eaf4fb;border:2px solid #3498db;color:#2980b9;font-weight:bold;border-radius:5px;padding:6px;")

            cmb = QComboBox()
            cmb.addItems(tedarikciler)
            cmb.currentTextChanged.connect(self.hesapla)

            t_fiyat = _le("0.00", True)
            t_fiyat.textChanged.connect(self.hesapla)

            self.tablo.setCellWidget(i,0,t_kalite)
            self.tablo.setCellWidget(i,1,t_en)
            self.tablo.setCellWidget(i,2,t_boy)
            self.tablo.setCellWidget(i,3,t_kal)
            self.tablo.setCellWidget(i,4,t_adet)
            self.tablo.setCellWidget(i,5,t_kg)
            self.tablo.setCellWidget(i,6,cmb)
            self.tablo.setCellWidget(i,7,t_fiyat)
            self.tablo.setItem(i,8,QTableWidgetItem(str(veri[0])))

        lay.addWidget(self.tablo)

        # Ortak alanlar
        ff = QFrame()
        ff.setStyleSheet("background:white;border-radius:10px;border:1px solid #dcdde1;padding:10px;")
        grid = QGridLayout(ff)
        grid.setSpacing(10)

        grid.addWidget(QLabel("NAKLIYE (TL):"), 0, 0)
        self.txt_nakliye = QLineEdit("0")
        self.txt_nakliye.textChanged.connect(self.hesapla)
        grid.addWidget(self.txt_nakliye, 0, 1)

        grid.addWidget(QLabel("VADE (GÜN):"), 0, 2)
        self.txt_vade = QLineEdit("30")
        grid.addWidget(self.txt_vade, 0, 3)

        grid.addWidget(QLabel("ÖDEME TIPI:"), 1, 0)
        self.cmb_odeme = QComboBox()
        self.cmb_odeme.addItems(["Nakit","Müşteri Çeki","Kendi Çekimiz","Havale/EFT","DBS"])
        grid.addWidget(self.cmb_odeme, 1, 1)

        grid.addWidget(QLabel("TEKLIF NOTU:"), 1, 2)
        self.txt_not = QLineEdit()
        self.txt_not.setPlaceholderText("Opsiyonel not...")
        grid.addWidget(self.txt_not, 1, 3)
        lay.addWidget(ff)

        # Özet panel
        self.alt = QFrame(); self.alt.setObjectName("AltPanel")
        alt_lay = QHBoxLayout(self.alt)
        self.lbl_ozet   = QLabel("Toplam: 0 KG  |  Ort: 0.00 TL/KG")
        self.lbl_ozet.setStyleSheet("color:#ecf0f1;font-size:13px;font-weight:bold;")
        self.lbl_toplam = QLabel("TOPLAM: 0.00 TL"); self.lbl_toplam.setObjectName("TutarLbl")
        alt_lay.addWidget(self.lbl_ozet); alt_lay.addStretch(); alt_lay.addWidget(self.lbl_toplam)
        lay.addWidget(self.alt)

        # Butonlar
        btn_lay = QHBoxLayout()

        btn_pdf = QPushButton("📄 PDF Teklif Oluştur")
        btn_pdf.setStyleSheet("background:#2980b9;color:white;padding:12px;font-weight:bold;font-size:14px;border-radius:8px;")
        btn_pdf.clicked.connect(self.teklif_pdf)

        btn_kaydet = QPushButton("💾 Teklifi Kaydet (Beklet)")
        btn_kaydet.setStyleSheet("background:#e67e22;color:white;padding:12px;font-weight:bold;font-size:14px;border-radius:8px;")
        btn_kaydet.clicked.connect(lambda: self.kaydet(sipariste_don=False))

        btn_siparis = QPushButton("✅ Teklifi Onayla → Siparişe Dönüştür")
        btn_siparis.setStyleSheet("background:#27ae60;color:white;padding:12px;font-weight:bold;font-size:14px;border-radius:8px;")
        btn_siparis.clicked.connect(lambda: self.kaydet(sipariste_don=True))

        btn_lay.addWidget(btn_pdf)
        btn_lay.addWidget(btn_kaydet)
        btn_lay.addWidget(btn_siparis)
        lay.addLayout(btn_lay)
        self.hesapla()

    def _tedarikcileri_getir(self):
        try:
            self.cursor.execute("SELECT firma_adi FROM tedarikciler ORDER BY firma_adi")
            return [r[0] for r in self.cursor.fetchall()] or ["Tedarikçi Yok"]
        except:
            return ["Tedarikçi Yok"]

    def _olcu(self, row):
        try:
            en   = float(self.tablo.cellWidget(row,1).text().replace(',','.') or 0)
            boy  = float(self.tablo.cellWidget(row,2).text().replace(',','.') or 0)
            kal  = float(self.tablo.cellWidget(row,3).text().replace(',','.') or 0)
            adet = float(self.tablo.cellWidget(row,4).text().replace(',','.') or 1)
            if adet <= 0: adet = 1
            if en>0 and boy>0 and kal>0:
                kg = (en*boy*kal*7.85)/1_000_000 * adet
                self.tablo.cellWidget(row,5).setText(f"{kg:.2f}")
            else:
                self.tablo.cellWidget(row,5).setText("0.00")
        except: pass
        self._kontrol(row)
        self.hesapla()

    def _kontrol(self, row):
        try:
            orig = self.orijinal[row]
            degisti = (
                self.tablo.cellWidget(row,0).text().strip() != orig['kalite'] or
                self.tablo.cellWidget(row,1).text().strip() != orig['en'] or
                self.tablo.cellWidget(row,2).text().strip() != orig['boy'] or
                self.tablo.cellWidget(row,3).text().strip() != orig['kal']
            )
            stil = ("background:#fff9c4;border:2px solid #f39c12;border-radius:5px;padding:6px;color:black;"
                    if degisti else
                    "background:white;border:1px solid #bdc3c7;border-radius:5px;padding:6px;color:black;")
            for col in [0,1,2,3,4,6,7]:
                w = self.tablo.cellWidget(row, col)
                if w: w.setStyleSheet(stil)
        except: pass

    def _satir_sil(self):
        """Seçili satırı teklif listesinden kaldırır (talep silinmez, sadece teklif dışı kalır)."""
        row = self.tablo.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen silmek istediğiniz satırı seçin.")
            return
        kalite = self.tablo.cellWidget(row, 0).text() if self.tablo.cellWidget(row, 0) else "?"
        cevap = QMessageBox.question(self, "Satırı Kaldır",
            f"'{kalite}' kalemi teklif listesinden kaldırılsın mı?\n(Talep silinmez, sadece bu tekliften çıkarılır)",
            QMessageBox.Yes | QMessageBox.No)
        if cevap == QMessageBox.Yes:
            if row < len(self.orijinal):
                self.orijinal.pop(row)
            self.tablo.removeRow(row)
            self.hesapla()

    def hesapla(self):
        try:
            toplam_bedel = 0.0; toplam_kg = 0.0
            for i in range(self.tablo.rowCount()):
                kg = float(self.tablo.cellWidget(i,5).text().replace(',','') or 0)
                try: fiyat = float(self.tablo.cellWidget(i,7).text().replace(',','.') or 0)
                except: fiyat = 0.0
                toplam_bedel += kg * fiyat; toplam_kg += kg
            try: nakliye = float(self.txt_nakliye.text().replace(',','.') or 0)
            except: nakliye = 0.0
            genel = toplam_bedel + nakliye
            ort   = genel / toplam_kg if toplam_kg > 0 else 0
            self._toplam_kg = toplam_kg
            self.lbl_ozet.setText(f"Toplam: {toplam_kg:,.0f} KG  |  Ort: {ort:.2f} TL/KG")
            self.lbl_toplam.setText(f"TOPLAM: {genel:,.2f} TL")
            return genel, nakliye, toplam_kg
        except: return 0.0, 0.0, 0.0

    def _kalem_verisi(self):
        """Tüm satirlardan veri toplar."""
        kalemler = []
        for i in range(self.tablo.rowCount()):
            talep_id = self.tablo.item(i,8).text() if self.tablo.item(i,8) else "0"
            kalite   = self.tablo.cellWidget(i,0).text().strip()
            en       = self.tablo.cellWidget(i,1).text().strip()
            boy      = self.tablo.cellWidget(i,2).text().strip()
            kal      = self.tablo.cellWidget(i,3).text().strip()
            adet     = self.tablo.cellWidget(i,4).text().strip()
            kg       = self.tablo.cellWidget(i,5).text().replace(',','')
            firma    = self.tablo.cellWidget(i,6).currentText()
            try: bf  = float(self.tablo.cellWidget(i,7).text().replace(',','.') or 0)
            except: bf = 0.0
            kalemler.append({'talep_id':talep_id,'kalite':kalite,'en':en,
                             'boy':boy,'kal':kal,'adet':adet,'kg':kg,'firma':firma,'bf':bf})
        return kalemler

    def teklif_pdf(self):
        try:
            genel, nakliye, _ = self.hesapla()
            kalemler = self._kalem_verisi()
            tarih    = datetime.now().strftime('%d.%m.%Y')
            teklif_no = datetime.now().strftime('%Y%m%d%H%M%S')
            # Firma bazli gruplama
            firma_gruplari = {}
            for k in kalemler:
                firma_gruplari.setdefault(k['firma'], []).append(k)

            for firma, fk in firma_gruplari.items():
                pdf_kalemler = [(k['kalite'],k['en'],k['boy'],k['kal'],k['kg'],k['bf']) for k in fk]
                firma_kg  = sum(float(k['kg'] or 0) for k in fk)
                firma_nak = (firma_kg / self._toplam_kg * nakliye) if self._toplam_kg > 0 else 0
                pdf = _pdf_olustur("TEKLIF FORMU", teklif_no, firma, pdf_kalemler,
                                   firma_nak, genel, self.txt_vade.text(),
                                   self.cmb_odeme.currentText(), tarih, "Teklifler")
                try: os.startfile(pdf)
                except: pass
            QMessageBox.information(self,"✅ PDF","Teklif PDF'i 'Teklifler' klasörüne kaydedildi.")
        except Exception as e:
            QMessageBox.critical(self,"Hata",str(e))

    def kaydet(self, sipariste_don=False):
        try:
            genel, nakliye, toplam_kg = self.hesapla()
            kalemler  = self._kalem_verisi()

            # Fiyat kontrolü
            sifir_fiyat = [k for k in kalemler if k['bf'] <= 0]
            if sifir_fiyat:
                uyari = QMessageBox.question(self, "⚠️ Fiyat Uyarısı",
                    f"{len(sifir_fiyat)} kalemin birim fiyatı 0 TL olarak girilmiş!\n\n"
                    "Fiyatı 0 olan kalemlerle devam etmek istiyor musunuz?",
                    QMessageBox.Yes | QMessageBox.No)
                if uyari != QMessageBox.Yes:
                    return

            tarih = datetime.now().strftime('%d.%m.%Y')
            vade      = self.txt_vade.text().strip() or "30"
            odeme     = self.cmb_odeme.currentText()
            teklif_no = datetime.now().strftime('%Y%m%d%H%M%S')
            durum     = "Siparis" if sipariste_don else "Bekliyor"

            # Ana firma (ilk kalemden al)
            firma = kalemler[0]['firma'] if kalemler else "-"

            # Teklif kaydi
            self.cursor.execute("""
                INSERT INTO teklifler (teklif_no, firma, durum, toplam_tutar, nakliye, vade, odeme_tipi, tarih, notlar)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (teklif_no, firma, durum, genel, nakliye, vade, odeme, tarih, self.txt_not.text()))
            teklif_id = self.cursor.lastrowid

            # Kalem kayitlari
            for k in kalemler:
                tutar = float(k['kg'] or 0) * k['bf']
                self.cursor.execute("""
                    INSERT INTO teklif_kalemleri (teklif_id, talep_id, kalite, en, boy, kalinlik, kg, birim_fiyat, tutar)
                    VALUES (?,?,?,?,?,?,?,?,?)
                """, (teklif_id, k['talep_id'], k['kalite'], k['en'], k['boy'],
                      k['kal'], k['kg'], k['bf'], tutar))

            if sipariste_don:
                self._sipariste_don(kalemler, firma, genel, nakliye, toplam_kg,
                                    vade, odeme, tarih, teklif_no, teklif_id)
            else:
                self.conn.commit()
                if self.callback: self.callback()
                QMessageBox.information(self, "💾 Kaydedildi",
                    f"Teklif #{teklif_no} kaydedildi!\nSatin Alma → Teklifler sekmesinden siparişe dönüştürebilirsiniz.")
                self.accept()
        except Exception as e:
            QMessageBox.critical(self,"❌ Hata",str(e))

    def _sipariste_don(self, kalemler, ana_firma, genel, nakliye, toplam_kg, vade, odeme, tarih, siparis_no, teklif_id):
        """Teklifi direkt siparişe dönüştür."""
        try:
            firma_gruplari = {}
            for k in kalemler:
                firma_gruplari.setdefault(k['firma'], []).append(k)

            for firma, fk in firma_gruplari.items():
                firma_kg    = sum(float(k['kg'] or 0) for k in fk)
                firma_bedel = sum(float(k['kg'] or 0)*k['bf'] for k in fk)
                firma_nak   = (firma_kg/toplam_kg*nakliye) if toplam_kg > 0 else 0
                firma_top   = firma_bedel + firma_nak

                vade_tarihi = (datetime.now() + timedelta(days=int(vade or 0))).strftime('%d.%m.%Y')
                self.cursor.execute("""
                    INSERT INTO satinalma_kayitlari
                    (firma, malzeme, miktar, birim_fiyat, nakliye, toplam_tutar, vade_tarihi, odeme_tipi, tarih)
                    VALUES (?,?,?,?,?,?,?,?,?)
                """, (firma, f"{len(fk)} Kalem Sac", round(firma_kg,2),
                      round(firma_bedel/firma_kg,2) if firma_kg>0 else 0,
                      round(firma_nak,2), round(firma_top,2), vade_tarihi, odeme, tarih))

            # Stok ekle
            satir_verileri = []
            for i, k in enumerate(kalemler):
                tarih_kisa = datetime.now().strftime('%y%m%d')
                self.cursor.execute("SELECT COUNT(*) FROM stok WHERE stok_kodu LIKE ?", (f"AR-{tarih_kisa}-%",))
                sira = (self.cursor.fetchone()[0] or 0) + i + 1
                stok_kodu = f"AR-{tarih_kisa}-{sira:03d}"

                self.cursor.execute("""
                    INSERT INTO stok (stok_kodu, malzeme, adet, en, boy, kalinlik, kg, son_firma, son_tarih, durum)
                    VALUES (?,?,?,?,?,?,?,?,?,0)
                """, (stok_kodu, k['kalite'], 1, k['en'], k['boy'], k['kal'], k['kg'], k['firma'], tarih))

                self.cursor.execute("DELETE FROM talepler WHERE id=?", (k['talep_id'],))
                satir_verileri.append({**k, 'stok_kodu': stok_kodu})

            # Teklif durumunu güncelle
            self.cursor.execute("UPDATE teklifler SET durum='Siparis' WHERE id=?", (teklif_id,))
            self.conn.commit()
            log_yaz(self.cursor, self.conn, "SIPARIS_VERILDI",
                    f"No:{siparis_no} | {ana_firma} | {genel:,.2f} TL | {len(kalemler)} kalem")
            if self.callback: self.callback()

            # PDF
            for firma, fk_idx in firma_gruplari.items():
                fk = [sv for sv in satir_verileri if sv['firma'] == firma]
                pdf_k = [(k['kalite'],k['en'],k['boy'],k['kal'],k['kg'],k['bf']) for k in fk]
                firma_kg  = sum(float(k['kg'] or 0) for k in fk)
                firma_nak = (firma_kg/toplam_kg*nakliye) if toplam_kg > 0 else 0
                pdf = _pdf_olustur("SIPARIŞ FORMU", siparis_no, firma, pdf_k,
                                   firma_nak, genel, vade, odeme, tarih)
                try: os.startfile(pdf)
                except: pass

            QMessageBox.information(self,"✅ Sipariş Verildi",
                f"Teklif onaylandi, sipariş oluşturuldu!\n\n"
                f"• {len(kalemler)} kalem stoka eklendi (Yolda)\n"
                f"• Toplam: {genel:,.2f} TL\n"
                f"• PDF sipariş formu oluşturuldu")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self,"❌ Hata",str(e))


# ─────────────────────────────────────────────
#  TEKLIFLER LISTESI — Bekleyen teklifleri göster
# ─────────────────────────────────────────────
class TekliflerListesi(QWidget):
    def __init__(self, cursor, conn, callback):
        super().__init__()
        self.cursor   = cursor
        self.conn     = conn
        self.callback = callback
        self.init_ui()
        self.yenile()

    def init_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0,10,0,0)
        lay.setSpacing(10)

        hdr = QHBoxLayout()
        lbl = QLabel("📋 KAYITLI TEKLIFLER")
        lbl.setStyleSheet("font-size:14px;font-weight:bold;color:#2c3e50;")
        hdr.addWidget(lbl)
        hdr.addStretch()

        btn_siparis = QPushButton("✅ Seçili Teklifi Siparişe Dönüştür")
        btn_siparis.setStyleSheet("background:#27ae60;color:white;padding:10px 18px;font-weight:bold;border-radius:6px;font-size:13px;")
        btn_siparis.clicked.connect(self.sipariste_don)

        btn_sil = QPushButton("🗑️ Teklifi Sil")
        btn_sil.setStyleSheet("background:#e74c3c;color:white;padding:10px 18px;font-weight:bold;border-radius:6px;font-size:13px;")
        btn_sil.clicked.connect(self.teklif_sil)

        hdr.addWidget(btn_siparis)
        hdr.addWidget(btn_sil)
        lay.addLayout(hdr)

        self.tablo = QTableWidget(0, 7)
        self.tablo.setHorizontalHeaderLabels(["ID","Teklif No","Firma","Tutar","Vade","Durum","Tarih"])
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tablo.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tablo.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tablo.setAlternatingRowColors(True)
        self.tablo.verticalHeader().setVisible(False)
        lay.addWidget(self.tablo)

    def yenile(self):
        try:
            self.cursor.execute("""
                SELECT id, teklif_no, firma, toplam_tutar, vade, durum, tarih
                FROM teklifler ORDER BY id DESC
            """)
            self.tablo.setRowCount(0)
            for i, row in enumerate(self.cursor.fetchall()):
                self.tablo.insertRow(i)
                durum = str(row[5] or "Bekliyor")
                for j, val in enumerate(row):
                    txt = f"{float(val):,.2f} TL" if j==3 else str(val or "-")
                    item = QTableWidgetItem(txt)
                    item.setTextAlignment(Qt.AlignCenter)
                    if durum == "Siparis":
                        item.setBackground(QColor("#eafaf1"))
                    elif durum == "Bekliyor":
                        item.setBackground(QColor("#fef9e7"))
                    self.tablo.setItem(i, j, item)
        except Exception as e:
            print(f"Teklif listesi hatasi: {e}")

    def sipariste_don(self):
        row = self.tablo.currentRow()
        if row < 0:
            QMessageBox.warning(self,"Uyari","Lütfen bir teklif seçin."); return

        teklif_id  = self.tablo.item(row,0).text()
        durum      = self.tablo.item(row,5).text()
        teklif_no  = self.tablo.item(row,1).text()

        if durum == "Siparis":
            QMessageBox.information(self,"Bilgi","Bu teklif zaten siparişe dönüştürülmüş."); return

        cevap = QMessageBox.question(self,"Siparişe Dönüştür",
            f"Teklif #{teklif_no} siparişe dönüştürülsün mü?",
            QMessageBox.Yes | QMessageBox.No)
        if cevap != QMessageBox.Yes: return

        try:
            self.cursor.execute("""
                SELECT tk.kalite, tk.en, tk.boy, tk.kalinlik, tk.kg, tk.birim_fiyat, tk.talep_id,
                       t.firma, t.nakliye, t.vade, t.odeme_tipi, t.tarih, t.toplam_tutar
                FROM teklif_kalemleri tk
                JOIN teklifler t ON t.id = tk.teklif_id
                WHERE tk.teklif_id=?
            """, (teklif_id,))
            rows = self.cursor.fetchall()
            if not rows:
                QMessageBox.warning(self,"Hata","Teklif kalemleri bulunamadi."); return

            firma     = rows[0][7]
            nakliye   = float(rows[0][8] or 0)
            vade      = rows[0][9] or "30"
            odeme     = rows[0][10] or "Nakit"
            tarih     = datetime.now().strftime('%d.%m.%Y')
            genel     = float(rows[0][12] or 0)
            toplam_kg = sum(float(r[4] or 0) for r in rows)

            # Finans kaydi
            vade_tarihi = (datetime.now() + timedelta(days=int(vade or 0))).strftime('%d.%m.%Y')
            self.cursor.execute("""
                INSERT INTO satinalma_kayitlari
                (firma, malzeme, miktar, birim_fiyat, nakliye, toplam_tutar, vade_tarihi, odeme_tipi, tarih)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (firma, f"{len(rows)} Kalem Sac", round(toplam_kg,2),
                  round(genel/toplam_kg,2) if toplam_kg>0 else 0,
                  round(nakliye,2), round(genel,2), vade_tarihi, odeme, tarih))

            # Stok
            tarih_kisa = datetime.now().strftime('%y%m%d')
            for i, r in enumerate(rows):
                kalite, en, boy, kal, kg, bf, talep_id = r[:7]
                self.cursor.execute("SELECT COUNT(*) FROM stok WHERE stok_kodu LIKE ?", (f"AR-{tarih_kisa}-%",))
                sira = (self.cursor.fetchone()[0] or 0) + i + 1
                stok_kodu = f"AR-{tarih_kisa}-{sira:03d}"
                self.cursor.execute("""
                    INSERT INTO stok (stok_kodu, malzeme, adet, en, boy, kalinlik, kg, son_firma, son_tarih, durum)
                    VALUES (?,?,?,?,?,?,?,?,?,0)
                """, (stok_kodu, kalite, 1, en, boy, kal, kg, firma, tarih))
                if talep_id:
                    self.cursor.execute("DELETE FROM talepler WHERE id=?", (talep_id,))

            self.cursor.execute("UPDATE teklifler SET durum='Siparis' WHERE id=?", (teklif_id,))
            self.conn.commit()
            log_yaz(self.cursor, self.conn, "SIPARIS_VERILDI",
                    f"No:{siparis_no} | {ana_firma} | {genel:,.2f} TL | {len(kalemler)} kalem")
            if self.callback: self.callback()
            self.yenile()
            QMessageBox.information(self,"✅ Başarili",
                f"Teklif siparişe dönüştürüldü!\n{len(rows)} kalem stoka eklendi (Yolda).")
        except Exception as e:
            QMessageBox.critical(self,"❌ Hata",str(e))

    def teklif_sil(self):
        row = self.tablo.currentRow()
        if row < 0:
            QMessageBox.warning(self,"Uyari","Lütfen bir teklif seçin."); return
        teklif_id = self.tablo.item(row,0).text()
        cevap = QMessageBox.question(self,"Sil","Teklif silinsin mi?",QMessageBox.Yes|QMessageBox.No)
        if cevap == QMessageBox.Yes:
            self.cursor.execute("DELETE FROM teklif_kalemleri WHERE teklif_id=?", (teklif_id,))
            self.cursor.execute("DELETE FROM teklifler WHERE id=?", (teklif_id,))
            self.conn.commit()
            self.yenile()


# ─────────────────────────────────────────────
#  ANA PANEL
# ─────────────────────────────────────────────
class SatinalmaSayfasi(QWidget):
    def __init__(self, cursor, conn, callback, user_role):
        super().__init__()
        self.cursor   = cursor
        self.conn     = conn
        self.callback = callback
        self.user_role = user_role
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QLabel { font-size:15px;font-weight:bold;color:#2c3e50; }
            QTableWidget { background:white;border-radius:8px;border:1px solid #dcdde1;font-size:13px; }
            QHeaderView::section { background:#2c3e50;color:white;padding:10px;font-weight:bold;border:none; }
            QTabWidget::pane { background:white;border-radius:8px;border:1px solid #dcdde1; }
            QTabBar::tab { background:#dcdde1;color:#2c3e50;padding:10px 22px;border-radius:4px;margin-right:3px;font-weight:bold;font-size:13px; }
            QTabBar::tab:selected { background:#c0392b;color:white; }
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20,15,20,15)
        lay.setSpacing(0)

        self.tabs = QTabWidget()

        # ── Sekme 1: Talepler ──
        talep_widget = QWidget()
        talep_lay    = QVBoxLayout(talep_widget)
        talep_lay.setContentsMargins(0,10,0,0)
        talep_lay.setSpacing(10)

        hdr = QHBoxLayout()
        hdr.addWidget(QLabel("🚚 BEKLEYEN SATINALMA TALEPLERI"))
        hdr.addStretch()

        self.lbl_adet = QLabel("0 talep")
        self.lbl_adet.setStyleSheet("font-size:13px;color:#7f8c8d;font-weight:normal;")
        hdr.addWidget(self.lbl_adet)

        btn_belgeler = QPushButton("📂 BELGELERI AÇ")
        btn_belgeler.setStyleSheet("background:#2980b9;color:white;padding:10px 18px;font-weight:bold;border-radius:6px;font-size:13px;")
        btn_belgeler.clicked.connect(self.belgeleri_ac)
        hdr.addWidget(btn_belgeler)

        self.btn_teklif = QPushButton("📋 TEKLIF OLUŞTUR")
        self.btn_teklif.setStyleSheet("background:#c0392b;color:white;padding:10px 18px;font-weight:bold;border-radius:6px;font-size:13px;")
        self.btn_teklif.clicked.connect(self.teklif_ac)
        hdr.addWidget(self.btn_teklif)
        talep_lay.addLayout(hdr)

        bilgi = QLabel("💡 CTRL ile birden fazla talep seçebilirsiniz.")
        bilgi.setStyleSheet("font-size:12px;color:#7f8c8d;font-weight:normal;")
        talep_lay.addWidget(bilgi)

        self.tablo = QTableWidget(0,7)
        self.tablo.setHorizontalHeaderLabels(["ID","Kalite","En (mm)","Boy (mm)","Kalinlik (mm)","KG","Tarih"])
        self.tablo.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tablo.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo.setAlternatingRowColors(True)
        self.tablo.verticalHeader().setVisible(False)
        talep_lay.addWidget(self.tablo)
        self.tabs.addTab(talep_widget, "🚚 Talepler")

        # ── Sekme 2: Teklifler ──
        self.teklifler_widget = TekliflerListesi(self.cursor, self.conn, self._tam_yenile)
        self.tabs.addTab(self.teklifler_widget, "📋 Teklifler")

        lay.addWidget(self.tabs)
        self.tablo_yenile()

    def _tam_yenile(self):
        self.tablo_yenile()
        self.teklifler_widget.yenile()
        if self.callback: self.callback()

    def tablo_yenile(self):
        try:
            self.tablo.setRowCount(0)
            self.cursor.execute("SELECT id,kalite,en,boy,kalinlik,kg,tarih FROM talepler WHERE durum=0 ORDER BY id DESC")
            rows = self.cursor.fetchall()
            for i, row in enumerate(rows):
                self.tablo.insertRow(i)
                for j, val in enumerate(row):
                    it = QTableWidgetItem(str(val) if val is not None else "")
                    it.setTextAlignment(Qt.AlignCenter)
                    it.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable)
                    self.tablo.setItem(i,j,it)
            self.lbl_adet.setText(f"{len(rows)} talep bekliyor")
        except Exception as e:
            print(f"Tablo hatasi: {e}")

    def belgeleri_ac(self):
        klasor = "Satin Alma Belgeleri"
        if not os.path.exists(klasor): os.makedirs(klasor)
        try: os.startfile(klasor)
        except: QMessageBox.information(self,"Bilgi",os.path.abspath(klasor))

    def teklif_ac(self):
        secili = self.tablo.selectionModel().selectedRows()
        if not secili:
            QMessageBox.warning(self,"Uyari","Teklif oluşturmak için talep seçin.\n(CTRL ile birden fazla seçebilirsiniz)"); return

        data = []
        for idx in secili:
            data.append([self.tablo.item(idx.row(),col).text() for col in range(self.tablo.columnCount())])

        pop = TeklifPopUp(data, self.cursor, self.conn, self._tam_yenile)
        pop.exec_()
        self.teklifler_widget.yenile()
