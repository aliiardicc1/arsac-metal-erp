"""
Arsac Metal ERP — Metalix Entegrasyon Modülü
Sipariş klasörü oluşturur, DWG ekler, bilgi kartı yazar, Metalix açar.
"""
import os, sys, shutil, subprocess, json
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

try:
    from log import log_yaz
except:
    def log_yaz(c, n, i, d=""): pass

# ── Ayar yardımcıları ──
def _ayar_dosyasi():
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), "ayarlar.json")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "ayarlar.json")

def _ayar_al(anahtar, varsayilan=""):
    try:
        with open(_ayar_dosyasi(), encoding="utf-8") as f:
            return json.load(f).get(anahtar, varsayilan)
    except:
        return varsayilan

def _ayar_kaydet(anahtar, deger):
    try:
        yol = _ayar_dosyasi()
        veriler = {}
        if os.path.exists(yol):
            with open(yol, encoding="utf-8") as f:
                veriler = json.load(f)
        veriler[anahtar] = deger
        with open(yol, "w", encoding="utf-8") as f:
            json.dump(veriler, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Ayar kaydetme hatası: {e}")


# ── Sipariş Klasörü Yolu ──
def siparis_klasor_yolu(sip_no, musteri):
    """Z:\\2026\\İŞLER\\ARSC-2026-0001_MüşteriAdı"""
    ana_yol = _ayar_al("is_klasor_yolu", r"Z:\2026\İŞLER")
    # Dosya adında yasak karakter temizle
    temiz = "".join(c for c in musteri if c not in r'\/:*?"<>|').strip()[:30]
    klasor_adi = f"{sip_no}_{temiz}"
    return os.path.join(ana_yol, klasor_adi)


# ── Sipariş Bilgi Kartı (.txt) ──


# ── Metalix CSV Oluşturma ──────────────────────────────────────
def _dosya_adini_parse(dosya_adi):
    """
    Dosya adından malzeme, kalınlık ve adet bilgisini çıkarır.
    Örnek: EMNİYET MAPASI_10MM_2ADET.dwg → (ST37, 10, 2)
    Örnek: PARCA_ST52_15MM_4ADET.dwg     → (ST52, 15, 4)
    """
    import re
    ad = re.sub(r'\.(dxf|dwg)$', '', dosya_adi, flags=re.IGNORECASE).strip()
    
    # Malzeme: ST37, ST52, S355 gibi
    malzeme = "ST37"
    m = re.search(r'_(ST\d+|S\d+|DKP|HARDOX|STAINLESS|304|316)_', ad, re.IGNORECASE)
    if m:
        malzeme = m.group(1).upper()
    
    # Kalınlık: 10MM, 15MM gibi
    kalinlik = 0
    m = re.search(r'_(\d+(?:[.,]\d+)?)MM_', ad, re.IGNORECASE)
    if m:
        try:
            kalinlik = float(m.group(1).replace(',', '.'))
        except:
            kalinlik = 0
    
    # Adet: 2ADET, 4ADET gibi
    adet = 1
    m = re.search(r'_(\d+)ADET', ad, re.IGNORECASE)
    if m:
        try:
            adet = int(m.group(1))
        except:
            adet = 1
    
    return malzeme, kalinlik, adet


def metalix_csv_olustur(klasor, sip_no, musteri):
    """
    Klasördeki DXF/DWG dosyalarını tarayıp Metalix CSV formatında dosya oluşturur.
    Döner: (csv_yolu, hata) 
    """
    import os, re
    
    # DXF/DWG dosyalarını tara
    dosyalar = []
    
    # Ana klasör
    if os.path.isdir(klasor):
        for f in os.listdir(klasor):
            if f.lower().endswith(('.dxf', '.dwg')):
                dosyalar.append(os.path.join(klasor, f))
    
    # DOSYALAR alt klasörü
    dosyalar_alt = os.path.join(klasor, "DOSYALAR")
    if os.path.isdir(dosyalar_alt):
        for f in os.listdir(dosyalar_alt):
            if f.lower().endswith(('.dxf', '.dwg')):
                dosyalar.append(os.path.join(dosyalar_alt, f))
    
    # DWG alt klasörü
    dwg_alt = os.path.join(klasor, "DWG")
    if os.path.isdir(dwg_alt):
        for f in os.listdir(dwg_alt):
            if f.lower().endswith(('.dxf', '.dwg')):
                dosyalar.append(os.path.join(dwg_alt, f))
    
    if not dosyalar:
        return None, "Klasörde DXF/DWG dosyası bulunamadı!\n{}".format(klasor)
    
    # CSV oluştur
    csv_yolu = os.path.join(klasor, "{}.csv".format(sip_no))
    
    try:
        satirlar = []
        # BOM + header
        satirlar.append("\ufeffParça Adresi;Klasör;Parça Adı;Malzeme;Kalınlık;Min. Adet;Maks. Adet;İş Sırası;İş 2;İş 3;Sonraki;Kutu;Öncelik;Yönler;Açı;Müşteri;Proje;CizimNo")
        
        for dosya_yolu in sorted(dosyalar):
            dosya_adi   = os.path.basename(dosya_yolu)
            dosya_klasor = os.path.dirname(dosya_yolu)
            malzeme, kalinlik, adet = _dosya_adini_parse(dosya_adi)
            
            satirlar.append(
                "{};{};{};{};{};{};{};1;;;;;0;15;0;{};{};".format(
                    dosya_yolu,
                    dosya_klasor,
                    dosya_adi,
                    malzeme,
                    int(kalinlik) if kalinlik == int(kalinlik) else kalinlik,
                    adet,
                    adet,
                    musteri,
                    sip_no
                )
            )
        
        with open(csv_yolu, "w", encoding="utf-8-sig", newline="\r\n") as f:
            f.write("\r\n".join(satirlar))
        
        return csv_yolu, None
    
    except Exception as e:
        return None, "CSV oluşturma hatası: {}".format(e)


def metalix_csv_guncelle(klasor, sip_no, musteri):
    """
    Klasörü tekrar tarayıp CSV'yi günceller.
    Yeni eklenen DXF/DWG dosyaları dahil edilir.
    """
    return metalix_csv_olustur(klasor, sip_no, musteri)


def bilgi_karti_olustur(klasor, sip_no, musteri, yetkili, telefon,
                         tarih, termin, notlar, kalemler, toplam):
    yol = os.path.join(klasor, f"{sip_no}_BILGI.txt")
    satirlar = [
        "=" * 55,
        "  ARSAC METAL — SİPARİŞ BİLGİ KARTI",
        "=" * 55,
        f"  Sipariş No  : {sip_no}",
        f"  Müşteri     : {musteri}",
        f"  Yetkili     : {yetkili or '-'}",
        f"  Telefon     : {telefon or '-'}",
        f"  Tarih       : {tarih}",
        f"  Termin      : {termin}",
        "=" * 55,
        "  KALEMLER",
        "-" * 55,
    ]
    for i, k in enumerate(kalemler, 1):
        satirlar.append(
            f"  {i}. {k.get('urun_adi','-'):<25} "
            f"{k.get('adet',1):>6g} {k.get('birim','Adet'):<6}  "
            f"{k.get('birim_fiyat',0):>10,.2f} TL"
        )
    satirlar += [
        "-" * 55,
        f"  {'TOPLAM':<35} {toplam:>10,.2f} TL",
        "=" * 55,
    ]
    if notlar:
        satirlar += ["  NOTLAR:", f"  {notlar}", "=" * 55]
    satirlar.append(f"  Oluşturulma: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    try:
        with open(yol, "w", encoding="utf-8") as f:
            f.write("\n".join(satirlar))
        return yol
    except Exception as e:
        print(f"Bilgi kartı hatası: {e}")
        return None


# ── Metalix Proje Dosyası (.mxt) ──
def metalix_proje_olustur(klasor, sip_no, musteri, dwg_dosyalari):
    """
    Basit bir Metalix proje dosyası (.mxt) oluşturur.
    Metalix bu dosyayı açınca siparişi doğrudan yükler.
    """
    yol = os.path.join(klasor, f"{sip_no}.mxt")
    dwg_satirlar = "\n".join(
        f'    <Part file="{os.path.basename(d)}" />'
        for d in dwg_dosyalari
    )
    icerik = f"""<?xml version="1.0" encoding="UTF-8"?>
<MetalixProject version="1.0">
  <JobInfo>
    <JobNumber>{sip_no}</JobNumber>
    <Customer>{musteri}</Customer>
    <CreatedDate>{datetime.now().strftime('%Y-%m-%d')}</CreatedDate>
    <Description>ARSAC METAL ERP - Otomatik Olusturuldu</Description>
  </JobInfo>
  <Parts>
{dwg_satirlar}
  </Parts>
</MetalixProject>
"""
    try:
        with open(yol, "w", encoding="utf-8") as f:
            f.write(icerik)
        return yol
    except Exception as e:
        print(f"Metalix proje dosyası hatası: {e}")
        return None


# ── Ana Klasör Oluşturma ──
def siparis_klasoru_olustur(sip_no, musteri, yetkili, telefon,
                             tarih, termin, notlar, kalemler, toplam,
                             dwg_dosyalari=None):
    """
    Tüm klasör yapısını oluşturur:
      ARSC-2026-0001_Musteri/
        ├── DWG/          ← DWG dosyaları buraya kopyalanır
        ├── ARSC-2026-0001_BILGI.txt
        └── ARSC-2026-0001.mxt
    Döner: (klasor_yolu, hata_mesaji)
    """
    klasor = siparis_klasor_yolu(sip_no, musteri)

    # Ana yol erişim kontrolü
    ana_yol = _ayar_al("is_klasor_yolu", r"Z:\2026\İŞLER")
    if not os.path.exists(ana_yol):
        return None, (
            f"Klasör yolu bulunamadı:\n{ana_yol}\n\n"
            "Program Ayarları → 'İş Klasörü Yolu' alanını kontrol edin."
        )

    try:
        # Alt klasörler
        os.makedirs(klasor, exist_ok=True)
        os.makedirs(os.path.join(klasor, "DWG"), exist_ok=True)
        os.makedirs(os.path.join(klasor, "CIKTI"), exist_ok=True)

        # DWG dosyalarını kopyala
        kopyalanan = []
        if dwg_dosyalari:
            for dwg in dwg_dosyalari:
                if os.path.exists(dwg):
                    hedef = os.path.join(klasor, "DWG", os.path.basename(dwg))
                    shutil.copy2(dwg, hedef)
                    kopyalanan.append(hedef)

        # Bilgi kartı
        bilgi_karti_olustur(klasor, sip_no, musteri, yetkili, telefon,
                             tarih, termin, notlar, kalemler, toplam)

        # Metalix proje dosyası
        metalix_proje_olustur(klasor, sip_no, musteri, kopyalanan)

        return klasor, None

    except PermissionError:
        return None, f"Klasör oluşturma izni yok:\n{klasor}"
    except Exception as e:
        return None, str(e)


# ── Metalix Aç ──
def metalix_ac(klasor_yolu):
    """
    Metalix'i açar ve sipariş klasörüne yönlendirir.
    Döner: (basarili, hata_mesaji)
    """
    metalix_exe = _ayar_al(
        "metalix_exe",
        r"C:\Program Files\Metalix\CIM-CNC\CIM-CNC.exe"
    )

    if not os.path.exists(metalix_exe):
        return False, (
            f"Metalix bulunamadı:\n{metalix_exe}\n\n"
            "Program Ayarları → 'Metalix Yolu' alanını güncelleyin."
        )

    # .mxt dosyasını bul
    mxt_dosyasi = None
    try:
        for f in os.listdir(klasor_yolu):
            if f.endswith(".mxt"):
                mxt_dosyasi = os.path.join(klasor_yolu, f)
                break
    except:
        pass

    try:
        if mxt_dosyasi and os.path.exists(mxt_dosyasi):
            # Proje dosyasıyla aç
            subprocess.Popen([metalix_exe, mxt_dosyasi])
        else:
            # Sadece Metalix'i aç, klasörü explorer'da göster
            subprocess.Popen([metalix_exe])
            subprocess.Popen(["explorer", klasor_yolu])
        return True, None
    except Exception as e:
        return False, str(e)


# ── DWG Yükleme Dialog ──
# Dosya tipi ikonları
def _dosya_ikonu(dosya_adi):
    ext = os.path.splitext(dosya_adi)[1].lower()
    return {
        ".dwg": "📐", ".dxf": "📐",
        ".pdf": "📄", ".PDF": "📄",
        ".xlsx": "📊", ".xls": "📊",
        ".docx": "📝", ".doc": "📝",
        ".jpg": "🖼️", ".jpeg": "🖼️", ".png": "🖼️",
        ".zip": "📦", ".rar": "📦",
        ".step": "🔩", ".stp": "🔩", ".iges": "🔩",
    }.get(ext, "📎")


class DwgYukleDialog(QDialog):
    def __init__(self, sip_no, musteri, parent=None):
        super().__init__(parent)
        self.sip_no      = sip_no
        self.musteri     = musteri
        self.dwg_listesi = []
        self.setWindowTitle("Musteri Dosyalari — " + sip_no)
        self.setMinimumSize(640, 540)
        self.setStyleSheet(
            "QDialog { background:#f4f6f9; font-family:'Segoe UI'; }"
            "QGroupBox { background:white; border-radius:10px;"
            "  border:1px solid #dcdde1; margin-top:8px; padding:10px; }"
            "QGroupBox::title { color:#8e44ad; font-weight:bold;"
            "  padding:0 6px; font-size:13px; }"
            "QListWidget { background:white; border:none; font-size:13px; }"
            "QListWidget::item { padding:10px 12px;"
            "  border-bottom:1px solid #f4f6f8; border-radius:4px; }"
            "QListWidget::item:selected { background:#f5eef8; color:#8e44ad; }"
            "QListWidget::item:hover { background:#fafafa; }"
        )
        self._init_ui()

    def _init_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(12)

        # Baslik
        baslik = QLabel("📎  " + self.sip_no + "  —  " + self.musteri)
        baslik.setStyleSheet("font-size:15px;font-weight:bold;color:#2c3e50;")
        lay.addWidget(baslik)

        bilgi = QLabel(
            "Musteriden gelen tum dosyalari ekleyin — DWG, PDF, siparis formu, resim, Excel.\n"
            "Siparis klasorune otomatik kopyalanir ve izlenebilir olur."
        )
        bilgi.setStyleSheet(
            "font-size:12px;color:#7f8c8d;font-weight:normal;background:transparent;"
        )
        bilgi.setWordWrap(True)
        lay.addWidget(bilgi)

        # Ekleme butonlari — tip bazli
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        def _stilBtn(renk):
            return (
                "QPushButton { background:" + renk + "; color:white; border-radius:8px;"
                "  padding:6px 12px; font-weight:bold; font-size:12px; border:none; }"
                "QPushButton:hover { opacity:0.85; }"
            )

        b_dwg = QPushButton("📐 DWG / DXF")
        b_dwg.setStyleSheet(_stilBtn("#8e44ad"))
        b_dwg.setFixedHeight(36)
        b_dwg.clicked.connect(self._ekle_dwg)

        b_pdf = QPushButton("📄 PDF / Form")
        b_pdf.setStyleSheet(_stilBtn("#c0392b"))
        b_pdf.setFixedHeight(36)
        b_pdf.clicked.connect(self._ekle_pdf)

        b_office = QPushButton("📊 Excel / Word")
        b_office.setStyleSheet(_stilBtn("#2980b9"))
        b_office.setFixedHeight(36)
        b_office.clicked.connect(self._ekle_office)

        b_resim = QPushButton("🖼️ Resim")
        b_resim.setStyleSheet(_stilBtn("#27ae60"))
        b_resim.setFixedHeight(36)
        b_resim.clicked.connect(self._ekle_resim)

        b_diger = QPushButton("📎 Diger")
        b_diger.setStyleSheet(_stilBtn("#7f8c8d"))
        b_diger.setFixedHeight(36)
        b_diger.clicked.connect(self._ekle_diger)

        for b in [b_dwg, b_pdf, b_office, b_resim, b_diger]:
            btn_row.addWidget(b)
        lay.addLayout(btn_row)

        # Dosya listesi
        self.grp = QGroupBox("Eklenecek Dosyalar")
        gv = QVBoxLayout(self.grp)
        gv.setContentsMargins(8, 8, 8, 8)

        self.lbl_bos = QLabel("Henuz dosya eklenmedi.\nYukaridaki butonlarla dosya ekleyin.")
        self.lbl_bos.setAlignment(Qt.AlignCenter)
        self.lbl_bos.setStyleSheet(
            "color:#bdc3c7;font-size:13px;font-weight:normal;padding:20px;"
        )

        self.liste = QListWidget()
        self.liste.setMinimumHeight(180)
        self.liste.hide()

        gv.addWidget(self.lbl_bos)
        gv.addWidget(self.liste)
        lay.addWidget(self.grp)

        # Kaldir butonu
        sil_row = QHBoxLayout()
        btn_sil = QPushButton("✕  Secili Dosyayi Kaldir")
        btn_sil.setStyleSheet(
            "background:#e74c3c;color:white;border-radius:8px;"
            "padding:6px 14px;font-weight:bold;font-size:12px;border:none;"
        )
        btn_sil.clicked.connect(self._sil)
        sil_row.addWidget(btn_sil)
        sil_row.addStretch()
        lay.addLayout(sil_row)

        # Alt butonlar
        alt = QHBoxLayout()
        btn_atla = QPushButton("Simdi Degil — Sonra Eklerim")
        btn_atla.setStyleSheet(
            "background:#dcdde1;color:#2c3e50;border-radius:8px;"
            "padding:10px 16px;font-weight:bold;"
        )
        btn_atla.clicked.connect(self.reject)

        btn_olustur = QPushButton("✅  Klasoru Olustur & Metalix Ac")
        btn_olustur.setFixedHeight(44)
        btn_olustur.setStyleSheet(
            "background:#c0392b;color:white;border-radius:8px;"
            "padding:10px 24px;font-weight:bold;font-size:13px;border:none;"
        )
        btn_olustur.clicked.connect(self.accept)

        alt.addWidget(btn_atla)
        alt.addStretch()
        alt.addWidget(btn_olustur)
        lay.addLayout(alt)

    # ── Dosya ekleme yardimcisi ──
    def _dosya_ekle(self, baslik, filtre):
        dosyalar, _ = QFileDialog.getOpenFileNames(self, baslik, "", filtre)
        for d in dosyalar:
            if d not in self.dwg_listesi:
                self.dwg_listesi.append(d)
                ikon   = _dosya_ikonu(d)
                boyut  = os.path.getsize(d) / 1024
                boyut_str = (
                    "{:.0f} KB".format(boyut)
                    if boyut < 1024
                    else "{:.1f} MB".format(boyut / 1024)
                )
                satir = "{}  {}   ({})".format(ikon, os.path.basename(d), boyut_str)
                item  = QListWidgetItem(satir)
                item.setToolTip(d)
                self.liste.addItem(item)
        self._guncelle()

    def _ekle_dwg(self):
        self._dosya_ekle(
            "CAD Dosyasi Sec",
            "CAD (*.dwg *.dxf *.DWG *.DXF *.step *.stp *.iges);;Tum Dosyalar (*.*)"
        )

    def _ekle_pdf(self):
        self._dosya_ekle(
            "PDF / Form Sec",
            "PDF (*.pdf *.PDF);;Tum Dosyalar (*.*)"
        )

    def _ekle_office(self):
        self._dosya_ekle(
            "Excel / Word Sec",
            "Office (*.xlsx *.xls *.docx *.doc *.csv);;Tum Dosyalar (*.*)"
        )

    def _ekle_resim(self):
        self._dosya_ekle(
            "Resim Sec",
            "Resimler (*.jpg *.jpeg *.png *.bmp *.tif *.tiff);;Tum Dosyalar (*.*)"
        )

    def _ekle_diger(self):
        self._dosya_ekle("Dosya Sec", "Tum Dosyalar (*.*)")

    def _sil(self):
        row = self.liste.currentRow()
        if row >= 0:
            self.dwg_listesi.pop(row)
            self.liste.takeItem(row)
            self._guncelle()

    def _guncelle(self):
        adet = len(self.dwg_listesi)
        if adet > 0:
            self.lbl_bos.hide()
            self.liste.show()
            self.grp.setTitle("{} dosya eklendi".format(adet))
        else:
            self.lbl_bos.show()
            self.liste.hide()
            self.grp.setTitle("Eklenecek Dosyalar")



# ── Sipariş Klasörü Ayarları Dialog ──
class MetalixAyarDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Metalix & Klasor Ayarlari")
        self.setFixedSize(520, 240)
        self.setStyleSheet(
            "QDialog { background:#f4f6f9; font-family:'Segoe UI'; }"
            "QLineEdit { border:1.5px solid #dcdde1; border-radius:8px;"
            "  padding:8px 12px; font-size:13px; background:white; }"
            "QLineEdit:focus { border:1.5px solid #c0392b; }"
            "QLabel { font-size:12px; font-weight:bold; color:#7f8c8d; }"
        )
        self._init_ui()

    def _init_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(10)

        def _satir(lbl_txt, txt_w, btn_w=None):
            h = QHBoxLayout()
            l = QLabel(lbl_txt)
            l.setFixedWidth(130)
            h.addWidget(l)
            h.addWidget(txt_w)
            if btn_w:
                h.addWidget(btn_w)
            lay.addLayout(h)

        self.txt_klasor = QLineEdit(_ayar_al("is_klasor_yolu", r"Z:\2026\ISLER"))
        self.txt_klasor.setFixedHeight(40)
        btn_k = QPushButton("📂")
        btn_k.setFixedSize(40, 40)
        btn_k.setStyleSheet(
            "background:#2980b9;color:white;border-radius:8px;font-size:16px;border:none;"
        )
        btn_k.clicked.connect(lambda: self._sec_klasor(self.txt_klasor))
        _satir("Is Klasoru:", self.txt_klasor, btn_k)

        self.txt_metalix = QLineEdit(
            _ayar_al("metalix_exe", r"C:\Program Files\Metalix\CIM-CNC\CIM-CNC.exe")
        )
        self.txt_metalix.setFixedHeight(40)
        btn_m = QPushButton("📂")
        btn_m.setFixedSize(40, 40)
        btn_m.setStyleSheet(
            "background:#8e44ad;color:white;border-radius:8px;font-size:16px;border:none;"
        )
        btn_m.clicked.connect(lambda: self._sec_exe(self.txt_metalix))
        _satir("Metalix Yolu:", self.txt_metalix, btn_m)

        lay.addSpacing(8)
        bl = QHBoxLayout()
        btn_iptal = QPushButton("Iptal")
        btn_iptal.setStyleSheet(
            "background:#dcdde1;color:#2c3e50;border-radius:8px;padding:10px 24px;font-weight:bold;"
        )
        btn_iptal.clicked.connect(self.reject)
        btn_kaydet = QPushButton("Kaydet")
        btn_kaydet.setStyleSheet(
            "background:#c0392b;color:white;border-radius:8px;"
            "padding:10px 24px;font-weight:bold;font-size:13px;"
        )
        btn_kaydet.clicked.connect(self._kaydet)
        bl.addWidget(btn_iptal)
        bl.addStretch()
        bl.addWidget(btn_kaydet)
        lay.addLayout(bl)

    def _sec_klasor(self, txt):
        yol = QFileDialog.getExistingDirectory(self, "Klasor Sec")
        if yol:
            txt.setText(yol)

    def _sec_exe(self, txt):
        yol, _ = QFileDialog.getOpenFileName(self, "EXE Sec", "", "Calistirilanilabilir (*.exe)")
        if yol:
            txt.setText(yol)

    def _kaydet(self):
        _ayar_kaydet("is_klasor_yolu", self.txt_klasor.text().strip())
        _ayar_kaydet("metalix_exe", self.txt_metalix.text().strip())
        QMessageBox.information(self, "Kaydedildi", "Ayarlar guncellendi.")
        self.accept()
