"""
Arsac Metal ERP — Ayarlar Modülü
Tüm ayarlar ayarlar.json dosyasına kaydedilir.
"""
import json
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

AYARLAR_DOSYA = "ayarlar.json"

VARSAYILAN = {
    "firma": {
        "ad":       "ARSAC METAL",
        "unvan":    "Oksijen Plazma Lazer Kesim Demir Celik Metal San. ve Tic. Ltd. Sti.",
        "telefon":  "",
        "email":    "",
        "adres":    "",
        "vergi_no": "",
        "vergi_dairesi": ""
    },
    "stok": {
        "kritik_esik": 500,
        "uyari_esik":  2000,
        "max_tonaj":   28000
    },
    "yedekleme": {
        "gun_sayisi": 7,
        "aktif":      True
    },
    "pdf": {
        "siparis_klasor": "Satin Alma Belgeleri",
        "teklif_klasor":  "Teklifler",
        "rapor_klasor":   "Gunluk Raporlar",
        "yedek_klasor":   "Yedekler"
    },
    "bildirim": {
        "vade_gecmis":     True,
        "bugun_vadeli":    True,
        "kritik_stok":     True,
        "bekleyen_talep":  True,
        "yolda_sac":       True,
        "acilis_popup":    True
    },
    "genel": {
        "para_birimi": "TL",
        "tarih_format": "%d.%m.%Y"
    }
}


def ayar_oku():
    """Ayarları dosyadan okur, eksik anahtarları varsayılanla doldurur."""
    try:
        if os.path.exists(AYARLAR_DOSYA):
            with open(AYARLAR_DOSYA, 'r', encoding='utf-8') as f:
                kayitli = json.load(f)
            # Eksik anahtarları varsayılanla tamamla
            def _merge(v, k):
                for anahtar, deger in v.items():
                    if anahtar not in k:
                        k[anahtar] = deger
                    elif isinstance(deger, dict):
                        _merge(deger, k[anahtar])
                return k
            return _merge(VARSAYILAN, kayitli)
    except:
        pass
    return json.loads(json.dumps(VARSAYILAN))


def ayar_kaydet(ayarlar):
    """Ayarları dosyaya kaydeder."""
    try:
        with open(AYARLAR_DOSYA, 'w', encoding='utf-8') as f:
            json.dump(ayarlar, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Ayar kayıt hatası: {e}")
        return False


def ayar_al(bolum, anahtar, varsayilan=None):
    """Tek bir ayar değeri okur."""
    try:
        return ayar_oku()[bolum][anahtar]
    except:
        return varsayilan


# ─────────────────────────────────────────────
#  AYARLAR EKRANI
# ─────────────────────────────────────────────
class AyarlarDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Program Ayarları")
        self.setMinimumSize(700, 580)
        self.ayarlar = ayar_oku()
        self.setStyleSheet("""
            QDialog { background: #f4f6f9; font-family: 'Segoe UI'; }
            QTabWidget::pane { background: white; border-radius: 8px; border: 1px solid #dcdde1; }
            QTabBar::tab { background: #dcdde1; color: #2c3e50; padding: 10px 16px;
                           border-radius: 4px; margin-right: 3px; font-weight: bold; font-size: 12px;
                           min-width: 110px; }
            QTabBar::tab:selected { background: #c0392b; color: white; }
            QGroupBox { background: white; border-radius: 8px; border: 1px solid #dcdde1;
                        margin-top: 8px; padding: 12px; font-size: 13px; }
            QGroupBox::title { color: #c0392b; font-weight: bold; padding: 0 6px; }
            QLineEdit, QSpinBox, QComboBox {
                background: white; border: 1.5px solid #dcdde1;
                border-radius: 18px; padding: 7px 14px;
                font-size: 13px; color: #2c3e50;
            }
            QLineEdit:focus, QSpinBox:focus { border: 1.5px solid #c0392b; }
            QLabel { font-size: 13px; color: #2c3e50; font-weight: bold; background: transparent; }
            QCheckBox { font-size: 13px; color: #2c3e50; }
            QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 2px solid #bdc3c7; }
            QCheckBox::indicator:checked { background: #c0392b; border: 2px solid #c0392b; }
        """)
        self.init_ui()

    def init_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(15, 15, 15, 15)
        lay.setSpacing(12)

        baslik = QLabel("⚙️ PROGRAM AYARLARI")
        baslik.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        lay.addWidget(baslik)

        self.tabs = QTabWidget()

        self.tabs.addTab(self._firma_tab(),      "Firma Bilgileri")
        self.tabs.addTab(self._stok_tab(),       "Stok Eslikleri")
        self.tabs.addTab(self._pdf_tab(),        "PDF & Klasorler")
        self.tabs.addTab(self._bildirim_tab(),   "Bildirimler")
        self.tabs.addTab(self._yedekleme_tab(),  "Yedekleme")

        lay.addWidget(self.tabs)

        # Kaydet butonu
        btn_lay = QHBoxLayout()
        btn_iptal = QPushButton("İptal")
        btn_iptal.setStyleSheet("background: #dcdde1; color: #2c3e50; border-radius: 8px; padding: 12px 24px; font-weight: bold; font-size: 13px;")
        btn_iptal.clicked.connect(self.reject)

        btn_kaydet = QPushButton("💾 Kaydet")
        btn_kaydet.setStyleSheet("background: #27ae60; color: white; border-radius: 8px; padding: 12px 24px; font-weight: bold; font-size: 13px;")
        btn_kaydet.clicked.connect(self.kaydet)

        btn_lay.addStretch()
        btn_lay.addWidget(btn_iptal)
        btn_lay.addWidget(btn_kaydet)
        lay.addLayout(btn_lay)

    def _form_satir(self, form, etiket, widget):
        lbl = QLabel(etiket)
        lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #7f8c8d; min-width: 160px;")
        form.addRow(lbl, widget)

    def _le(self, deger):
        w = QLineEdit(str(deger or ""))
        return w

    def _spin(self, deger, min_=0, max_=99999):
        w = QSpinBox()
        w.setRange(min_, max_)
        w.setValue(int(deger or 0))
        w.setStyleSheet("QSpinBox { border-radius: 18px; padding: 7px 14px; }")
        return w

    def _chk(self, deger, etiket=""):
        w = QCheckBox(etiket)
        w.setChecked(bool(deger))
        return w

    # ── Firma Sekmesi ──
    def _firma_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(15, 15, 15, 15)

        grp = QGroupBox("Firma Bilgileri (PDF'lere basılır)")
        form = QFormLayout(grp)
        form.setSpacing(10)

        f = self.ayarlar["firma"]
        self.e_firma_ad       = self._le(f["ad"])
        self.e_firma_unvan    = self._le(f["unvan"])
        self.e_firma_tel      = self._le(f["telefon"])
        self.e_firma_email    = self._le(f["email"])
        self.e_firma_adres    = self._le(f["adres"])
        self.e_firma_vergi    = self._le(f["vergi_no"])
        self.e_firma_vd       = self._le(f["vergi_dairesi"])

        self._form_satir(form, "Firma Adı:",        self.e_firma_ad)
        self._form_satir(form, "Ünvan:",            self.e_firma_unvan)
        self._form_satir(form, "Telefon:",          self.e_firma_tel)
        self._form_satir(form, "Email:",            self.e_firma_email)
        self._form_satir(form, "Adres:",            self.e_firma_adres)
        self._form_satir(form, "Vergi No:",         self.e_firma_vergi)
        self._form_satir(form, "Vergi Dairesi:",    self.e_firma_vd)

        lay.addWidget(grp)
        lay.addStretch()
        return w

    # ── Stok Sekmesi ──
    def _stok_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(15, 15, 15, 15)

        grp = QGroupBox("Stok Uyarı Eşikleri")
        form = QFormLayout(grp)
        form.setSpacing(12)

        s = self.ayarlar["stok"]
        self.sp_kritik  = self._spin(s["kritik_esik"], 0, 99999)
        self.sp_uyari   = self._spin(s["uyari_esik"],  0, 99999)
        self.sp_tonaj   = self._spin(s["max_tonaj"],   0, 99999)

        self._form_satir(form, "🔴 Kritik Eşik (KG):",    self.sp_kritik)
        self._form_satir(form, "🟡 Uyarı Eşiği (KG):",    self.sp_uyari)
        self._form_satir(form, "🚛 Max Kamyon Tonajı (KG):", self.sp_tonaj)

        bilgi = QLabel("Stok bu değerlerin altına düşünce renk uyarısı verilir.")
        bilgi.setStyleSheet("color: #7f8c8d; font-size: 12px; font-weight: normal;")

        lay.addWidget(grp)
        lay.addWidget(bilgi)
        lay.addStretch()
        return w

    # ── PDF / Klasörler Sekmesi ──
    def _pdf_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(15, 15, 15, 15)
        lay.setSpacing(12)

        # Klasör yolları
        grp_kl = QGroupBox("Klasor Yollari")
        form_kl = QFormLayout(grp_kl)
        form_kl.setSpacing(10)

        p = self.ayarlar["pdf"]
        self.e_siparis_kl = self._le(p["siparis_klasor"])
        self.e_teklif_kl  = self._le(p["teklif_klasor"])
        self.e_rapor_kl   = self._le(p["rapor_klasor"])
        self.e_yedek_kl   = self._le(p["yedek_klasor"])

        self._form_satir(form_kl, "Siparis Belgeleri:", self.e_siparis_kl)
        self._form_satir(form_kl, "Teklifler:",         self.e_teklif_kl)
        self._form_satir(form_kl, "Gunluk Raporlar:",   self.e_rapor_kl)
        self._form_satir(form_kl, "Yedekler:",          self.e_yedek_kl)
        lay.addWidget(grp_kl)

        # PDF rapor içerik ayarları
        grp_pdf = QGroupBox("PDF Rapor Ayarlari")
        form_pdf = QFormLayout(grp_pdf)
        form_pdf.setSpacing(10)

        pdf_a = self.ayarlar.get("pdf_ayar", {})

        self.chk_pdf_logo     = self._chk(pdf_a.get("logo_goster", True),    "Logo goster")
        self.chk_pdf_imza     = self._chk(pdf_a.get("imza_goster", True),    "Imza alani goster")
        self.chk_pdf_stok_kod = self._chk(pdf_a.get("stok_kodu_goster", True),"Stok kodunu goster")
        self.chk_pdf_vergi    = self._chk(pdf_a.get("vergi_goster", False),  "Vergi no goster")
        self.chk_pdf_auto_ac  = self._chk(pdf_a.get("auto_ac", True),        "PDF olusunca otomatik ac")

        self.cmb_pdf_renk = QComboBox()
        self.cmb_pdf_renk.addItems(["Kirmizi (#c0392b)", "Lacivert (#2c3e50)", "Yesil (#27ae60)", "Mavi (#2980b9)"])
        self.cmb_pdf_renk.setStyleSheet("border-radius: 8px; padding: 7px 14px;")
        renk_kayitli = pdf_a.get("ana_renk", "#c0392b")
        renk_map = {"#c0392b": 0, "#2c3e50": 1, "#27ae60": 2, "#2980b9": 3}
        self.cmb_pdf_renk.setCurrentIndex(renk_map.get(renk_kayitli, 0))

        form_pdf.addRow("", self.chk_pdf_logo)
        form_pdf.addRow("", self.chk_pdf_imza)
        form_pdf.addRow("", self.chk_pdf_stok_kod)
        form_pdf.addRow("", self.chk_pdf_vergi)
        form_pdf.addRow("", self.chk_pdf_auto_ac)
        self._form_satir(form_pdf, "Ana Renk:", self.cmb_pdf_renk)
        lay.addWidget(grp_pdf)

        bilgi = QLabel("Klasorler program dizinine gore olusturulur.")
        bilgi.setStyleSheet("color: #7f8c8d; font-size: 12px; font-weight: normal;")
        lay.addWidget(bilgi)
        lay.addStretch()
        return w

    # ── Bildirimler Sekmesi ──
    def _bildirim_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(15, 15, 15, 15)

        grp = QGroupBox("Açılış Bildirimleri")
        form = QFormLayout(grp)
        form.setSpacing(12)

        b = self.ayarlar["bildirim"]
        self.chk_vade_gecmis    = self._chk(b["vade_gecmis"],    "Vadesi geçmiş ödemeler")
        self.chk_bugun_vadeli   = self._chk(b["bugun_vadeli"],   "Bugün vadeli ödemeler")
        self.chk_kritik_stok    = self._chk(b["kritik_stok"],    "Kritik stok uyarısı")
        self.chk_bekleyen_talep = self._chk(b["bekleyen_talep"], "Bekleyen hammadde talepleri")
        self.chk_yolda_sac      = self._chk(b["yolda_sac"],      "Yolda bekleyen saclar")
        self.chk_acilis_popup   = self._chk(b["acilis_popup"],   "Açılışta kritik stok popup'ı")

        for chk in [self.chk_vade_gecmis, self.chk_bugun_vadeli, self.chk_kritik_stok,
                    self.chk_bekleyen_talep, self.chk_yolda_sac, self.chk_acilis_popup]:
            form.addRow("", chk)

        lay.addWidget(grp)
        lay.addStretch()
        return w

    # ── Yedekleme Sekmesi ──
    def _yedekleme_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(15, 15, 15, 15)

        grp = QGroupBox("Otomatik Yedekleme")
        form = QFormLayout(grp)
        form.setSpacing(12)

        y = self.ayarlar["yedekleme"]
        self.chk_yedek_aktif = self._chk(y["aktif"], "Otomatik yedekleme aktif")
        self.sp_yedek_gun    = self._spin(y["gun_sayisi"], 1, 30)

        form.addRow("", self.chk_yedek_aktif)
        self._form_satir(form, "Saklanacak yedek sayısı:", self.sp_yedek_gun)

        # Manuel yedek butonu
        btn_yedek = QPushButton("💾 Şimdi Yedek Al")
        btn_yedek.setStyleSheet("background: #2980b9; color: white; border-radius: 8px; padding: 10px 20px; font-weight: bold; font-size: 13px;")
        btn_yedek.clicked.connect(self._manuel_yedek)

        btn_klasor = QPushButton("📂 Yedek Klasörünü Aç")
        btn_klasor.setStyleSheet("background: #7f8c8d; color: white; border-radius: 8px; padding: 10px 20px; font-weight: bold; font-size: 13px;")
        btn_klasor.clicked.connect(self._yedek_klasoru_ac)

        btn_lay = QHBoxLayout()
        btn_lay.addWidget(btn_yedek)
        btn_lay.addWidget(btn_klasor)
        btn_lay.addStretch()

        lay.addWidget(grp)
        lay.addLayout(btn_lay)
        lay.addStretch()
        return w

    def _manuel_yedek(self):
        try:
            import shutil
            from datetime import datetime
            klasor = self.ayarlar["pdf"]["yedek_klasor"]
            if not os.path.exists(klasor):
                os.makedirs(klasor)
            zaman  = datetime.now().strftime('%Y%m%d_%H%M%S')
            hedef  = f"{klasor}/arsac_metal_{zaman}.db"
            shutil.copy2("arsac_metal.db", hedef)
            QMessageBox.information(self, "✅ Yedek Alındı", f"Yedek kaydedildi:\n{hedef}")
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))

    def _yedek_klasoru_ac(self):
        klasor = self.ayarlar["pdf"]["yedek_klasor"]
        if not os.path.exists(klasor): os.makedirs(klasor)
        try: os.startfile(klasor)
        except: QMessageBox.information(self, "Bilgi", os.path.abspath(klasor))

    def kaydet(self):
        self.ayarlar["firma"]["ad"]              = self.e_firma_ad.text()
        self.ayarlar["firma"]["unvan"]           = self.e_firma_unvan.text()
        self.ayarlar["firma"]["telefon"]         = self.e_firma_tel.text()
        self.ayarlar["firma"]["email"]           = self.e_firma_email.text()
        self.ayarlar["firma"]["adres"]           = self.e_firma_adres.text()
        self.ayarlar["firma"]["vergi_no"]        = self.e_firma_vergi.text()
        self.ayarlar["firma"]["vergi_dairesi"]   = self.e_firma_vd.text()

        self.ayarlar["stok"]["kritik_esik"]      = self.sp_kritik.value()
        self.ayarlar["stok"]["uyari_esik"]       = self.sp_uyari.value()
        self.ayarlar["stok"]["max_tonaj"]        = self.sp_tonaj.value()

        self.ayarlar["pdf"]["siparis_klasor"]    = self.e_siparis_kl.text()
        self.ayarlar["pdf"]["teklif_klasor"]     = self.e_teklif_kl.text()
        self.ayarlar["pdf"]["rapor_klasor"]      = self.e_rapor_kl.text()
        self.ayarlar["pdf"]["yedek_klasor"]      = self.e_yedek_kl.text()

        self.ayarlar["bildirim"]["vade_gecmis"]    = self.chk_vade_gecmis.isChecked()
        self.ayarlar["bildirim"]["bugun_vadeli"]   = self.chk_bugun_vadeli.isChecked()
        self.ayarlar["bildirim"]["kritik_stok"]    = self.chk_kritik_stok.isChecked()
        self.ayarlar["bildirim"]["bekleyen_talep"] = self.chk_bekleyen_talep.isChecked()
        self.ayarlar["bildirim"]["yolda_sac"]      = self.chk_yolda_sac.isChecked()
        self.ayarlar["bildirim"]["acilis_popup"]   = self.chk_acilis_popup.isChecked()

        self.ayarlar["yedekleme"]["aktif"]       = self.chk_yedek_aktif.isChecked()
        self.ayarlar["yedekleme"]["gun_sayisi"]  = self.sp_yedek_gun.value()

        renk_list = ["#c0392b", "#2c3e50", "#27ae60", "#2980b9"]
        self.ayarlar["pdf_ayar"] = {
            "logo_goster":      self.chk_pdf_logo.isChecked(),
            "imza_goster":      self.chk_pdf_imza.isChecked(),
            "stok_kodu_goster": self.chk_pdf_stok_kod.isChecked(),
            "vergi_goster":     self.chk_pdf_vergi.isChecked(),
            "auto_ac":          self.chk_pdf_auto_ac.isChecked(),
            "ana_renk":         renk_list[self.cmb_pdf_renk.currentIndex()],
        }

        if ayar_kaydet(self.ayarlar):
            QMessageBox.information(self, "✅ Kaydedildi",
                "Ayarlar kaydedildi!\nBazı değişiklikler programı yeniden başlattıktan sonra geçerli olur.")
            self.accept()
        else:
            QMessageBox.warning(self, "Hata", "Ayarlar kaydedilemedi!")