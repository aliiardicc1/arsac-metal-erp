"""
Arsac Metal ERP — Otomatik Güncelleme Modülü
=============================================
GitHub Releases üzerinden EXE güncelleme.

Akış:
  1. Program açılır
  2. GitHub API'ye bağlanır → son sürüm bilgisini çeker
  3. Mevcut sürümle karşılaştırır
  4. Yeni sürüm varsa kullanıcıya sorar
  5. Onay verilirse EXE indirilir, eski yenisiyle değiştirilir
  6. Program yeniden başlar

Kurulum:
  - GitHub repo: GITHUB_REPO sabitini ayarlayın
  - Her sürüm için git tag: v1.0.1, v1.0.2 ...
  - PyInstaller ile EXE üretin → GitHub Release'e yükleyin
"""

import os
import sys
import json
import time
import shutil
import threading
import tempfile
import subprocess
from datetime import datetime

try:
    import urllib.request as urlreq
    import urllib.error as urlerr
except ImportError:
    urlreq = None

try:
    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel,
        QPushButton, QProgressBar, QMessageBox, QApplication
    )
    from PyQt5.QtCore import Qt, QThread, pyqtSignal
    PYQT_VAR = True
except ImportError:
    PYQT_VAR = False

# ═══════════════════════════════════════════════════════════════
#  AYARLAR  — sadece bunları değiştirin
# ═══════════════════════════════════════════════════════════════

# GitHub kullanıcı adı / repo adı
GITHUB_REPO   = "aliiardicc1/arsac-metal-erp"

# Token ayarlar.json'dan okunur — koda yazmayın!
GITHUB_TOKEN  = ""

# Release'deki EXE dosyasının adı (tam olarak)
EXE_ADI       = "ArsacMetalERP.exe"

# Mevcut sürüm — her güncellemede artırın (main.py ile aynı tutun)
SURUM         = "1.5.9"

# Güncelleme kontrolü kaç saniyede bir yapılsın (0 = sadece açılışta)
KONTROL_SURESI = 0

# ═══════════════════════════════════════════════════════════════
#  SÜRÜM KARŞILAŞTIRMA
# ═══════════════════════════════════════════════════════════════

def _surum_parse(v):
    """'1.2.3' → (1, 2, 3)"""
    try:
        v = v.lstrip("v").strip()
        return tuple(int(x) for x in v.split("."))
    except:
        return (0, 0, 0)

def yeni_surum_var(mevcut, uzak):
    return _surum_parse(uzak) > _surum_parse(mevcut)


# ═══════════════════════════════════════════════════════════════
#  GITHUB API
# ═══════════════════════════════════════════════════════════════

def github_son_surum_bilgi(repo=GITHUB_REPO, zaman_asimi=8):
    """
    GitHub Releases API'den son sürüm bilgisini çeker.
    Döner: {'tag': 'v1.0.1', 'url': '...', 'notlar': '...'} veya None
    """
    if not urlreq:
        return None
    try:
        api_url = "https://api.github.com/repos/{}/releases/latest".format(repo)
        # Token önce ayarlar.json'dan, sonra sabitten okunur
        _token = GITHUB_TOKEN
        if not _token:
            try:
                import json as _json, os as _os, sys as _sys
                if getattr(_sys, 'frozen', False):
                    _ayar_yol = _os.path.join(_os.path.dirname(_sys.executable), "ayarlar.json")
                else:
                    _ayar_yol = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "ayarlar.json")
                with open(_ayar_yol, "r", encoding="utf-8") as _f:
                    _token = _json.load(_f).get("github_token", "")
            except:
                pass

        hdrs = {
            "User-Agent": "ArsacMetalERP/{}".format(SURUM),
            "Accept"    : "application/vnd.github.v3+json",
        }
        if _token:
            hdrs["Authorization"] = "token {}".format(_token)
        req = urlreq.Request(api_url, headers=hdrs)
        with urlreq.urlopen(req, timeout=zaman_asimi) as r:
            veri = json.loads(r.read().decode("utf-8"))

        tag    = veri.get("tag_name", "")
        notlar = veri.get("body", "")

        # EXE indirme URL'ini bul
        exe_url = None
        for asset in veri.get("assets", []):
            if asset.get("name", "").lower() == EXE_ADI.lower():
                exe_url = asset.get("browser_download_url")
                boyut   = asset.get("size", 0)
                break

        if not exe_url:
            return None

        return {
            "tag"   : tag,
            "url"   : exe_url,
            "boyut" : boyut,
            "notlar": notlar[:500] if notlar else "",
        }
    except Exception as e:
        print("[Updater] API hatasi:", e)
        return None


# ═══════════════════════════════════════════════════════════════
#  İNDİRME İŞ PARÇACIĞI
# ═══════════════════════════════════════════════════════════════

class IndirmeThread(QThread):
    ilerleme   = pyqtSignal(int)    # 0-100
    tamamlandi = pyqtSignal(str)    # geçici dosya yolu
    hata       = pyqtSignal(str)

    def __init__(self, url, boyut=0):
        super().__init__()
        self.url   = url
        self.boyut = boyut

    def run(self):
        try:
            tmp = tempfile.NamedTemporaryFile(
                delete=False, suffix=".exe", prefix="arsac_update_")
            tmp_yol = tmp.name
            tmp.close()

            req = urlreq.Request(self.url, headers={
                "User-Agent": "ArsacMetalERP/{}".format(SURUM)
            })
            with urlreq.urlopen(req, timeout=60) as r, \
                 open(tmp_yol, "wb") as f:
                indirilen = 0
                parca = 65536  # 64 KB
                while True:
                    veri = r.read(parca)
                    if not veri:
                        break
                    f.write(veri)
                    indirilen += len(veri)
                    if self.boyut > 0:
                        yuzde = min(99, int(indirilen * 100 / self.boyut))
                        self.ilerleme.emit(yuzde)

            self.ilerleme.emit(100)
            self.tamamlandi.emit(tmp_yol)

        except Exception as e:
            self.hata.emit(str(e))


# ═══════════════════════════════════════════════════════════════
#  GÜNCELLEME DİALOGU
# ═══════════════════════════════════════════════════════════════

class GuncellemeDlg(QDialog):
    def __init__(self, bilgi, parent=None):
        super().__init__(parent)
        self.bilgi     = bilgi
        self.tmp_yol   = None
        self._thread   = None
        self.setWindowTitle("Güncelleme Mevcut")
        self.setFixedWidth(460)
        self.setWindowFlags(
            Qt.Dialog | Qt.WindowCloseButtonHint)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)

        # Başlık
        bas = QLabel("🆕  Yeni Sürüm Mevcut")
        bas.setStyleSheet(
            "font-size:16px;font-weight:bold;color:#2c3e50;")
        lay.addWidget(bas)

        # Sürüm bilgisi
        surum_lbl = QLabel(
            "Mevcut: <b>v{}</b>   →   Yeni: <b>{}</b>".format(
                SURUM, self.bilgi["tag"]))
        surum_lbl.setStyleSheet("font-size:13px;color:#555;")
        lay.addWidget(surum_lbl)

        # Boyut
        mb = round(self.bilgi.get("boyut", 0) / 1_048_576, 1)
        if mb > 0:
            boyut_lbl = QLabel("İndirme boyutu: {} MB".format(mb))
            boyut_lbl.setStyleSheet("font-size:12px;color:#888;")
            lay.addWidget(boyut_lbl)

        # Sürüm notları
        if self.bilgi.get("notlar"):
            notlar = QLabel(self.bilgi["notlar"])
            notlar.setWordWrap(True)
            notlar.setStyleSheet(
                "font-size:12px;color:#555;"
                "background:#f8f9fa;border-radius:6px;padding:8px;")
            lay.addWidget(notlar)

        # İlerleme çubuğu (gizli başlar)
        self.pb = QProgressBar()
        self.pb.setRange(0, 100)
        self.pb.setValue(0)
        self.pb.setFixedHeight(20)
        self.pb.setStyleSheet("""
            QProgressBar{border-radius:6px;background:#e0e0e0;text-align:center;}
            QProgressBar::chunk{background:#2980b9;border-radius:6px;}
        """)
        self.pb.hide()
        lay.addWidget(self.pb)

        self.durum_lbl = QLabel("")
        self.durum_lbl.setStyleSheet("font-size:12px;color:#888;")
        self.durum_lbl.hide()
        lay.addWidget(self.durum_lbl)

        # Butonlar
        bh = QHBoxLayout()
        self.btn_sonra = QPushButton("Sonra Hatırlat")
        self.btn_sonra.setFixedHeight(36)
        self.btn_sonra.setStyleSheet(
            "background:#ecf0f1;color:#555;border-radius:7px;"
            "border:none;padding:6px 16px;font-size:13px;")
        self.btn_sonra.clicked.connect(self.reject)

        self.btn_guncelle = QPushButton("⬇  Güncelle ve Yeniden Başlat")
        self.btn_guncelle.setFixedHeight(36)
        self.btn_guncelle.setStyleSheet(
            "background:#2980b9;color:white;border-radius:7px;"
            "border:none;padding:6px 16px;font-size:13px;font-weight:bold;")
        self.btn_guncelle.clicked.connect(self._indir)

        bh.addWidget(self.btn_sonra)
        bh.addStretch()
        bh.addWidget(self.btn_guncelle)
        lay.addLayout(bh)

    def _indir(self):
        self.btn_guncelle.setEnabled(False)
        self.btn_sonra.setEnabled(False)
        self.pb.show()
        self.durum_lbl.show()
        self.durum_lbl.setText("İndiriliyor...")

        self._thread = IndirmeThread(
            self.bilgi["url"], self.bilgi.get("boyut", 0))
        self._thread.ilerleme.connect(self.pb.setValue)
        self._thread.tamamlandi.connect(self._indirildi)
        self._thread.hata.connect(self._hata)
        self._thread.start()

    def _indirildi(self, tmp_yol):
        self.tmp_yol = tmp_yol
        self.durum_lbl.setText("İndirme tamamlandı, uygulanıyor...")
        self.pb.setValue(100)
        # Kısa bekleme sonrası uygula
        QApplication.processEvents()
        self._uygula()

    def _hata(self, mesaj):
        self.btn_sonra.setEnabled(True)
        self.pb.hide()
        self.durum_lbl.hide()
        QMessageBox.critical(
            self, "İndirme Hatası",
            "Güncelleme indirilemedi:\n\n{}".format(mesaj))
        self.reject()

    def _uygula(self):
        """Geçici EXE'yi mevcut EXE'nin üzerine kopyalar ve yeniden başlatır."""
        try:
            mevcut_exe = sys.executable

            # Eski EXE'yi yedekle
            yedek = mevcut_exe + ".bak"
            try:
                if os.path.exists(yedek):
                    os.remove(yedek)
                shutil.copy2(mevcut_exe, yedek)
            except:
                pass

            # Windows'ta çalışan EXE üzerine yazılamaz — bat script kullan
            if sys.platform == "win32":
                bat = tempfile.NamedTemporaryFile(
                    delete=False, suffix=".bat",
                    mode="w", encoding="mbcs")
                bat.write(
                    "@echo off\n"
                    "timeout /t 2 /nobreak >nul\n"
                    "move /Y \"{src}\" \"{dst}\"\n"
                    "start \"\" \"{dst}\"\n"
                    "del \"%~f0\"\n".format(
                        src=self.tmp_yol,
                        dst=mevcut_exe))
                bat.close()
                subprocess.Popen(
                    ["cmd", "/c", bat.name],
                    creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                # Linux/Mac
                shutil.move(self.tmp_yol, mevcut_exe)
                os.chmod(mevcut_exe, 0o755)
                subprocess.Popen([mevcut_exe])

            # Mevcut uygulamayı kapat
            QApplication.quit()

        except Exception as e:
            QMessageBox.critical(
                self, "Uygulama Hatası",
                "Güncelleme uygulanamadı:\n\n{}\n\n"
                "Lütfen manuel olarak güncelleyin.".format(e))
            self.reject()


# ═══════════════════════════════════════════════════════════════
#  ANA KONTROL FONKSİYONU  (main.py'den çağrılır)
# ═══════════════════════════════════════════════════════════════

def guncelleme_kontrol(parent=None, sessiz=False):
    """
    Program açılışında çağrılır.

    sessiz=True  → yeni sürüm varsa dialog açar, yoksa hiçbir şey yapmaz
    sessiz=False → "Güncelleme yok" mesajı da gösterir (manuel kontrol için)
    """
    # EXE olarak çalışmıyorsa kontrol etme
    if not getattr(sys, 'frozen', False):
        if not sessiz:
            QMessageBox.information(
                parent, "Güncelleme",
                "Güncelleme kontrolü sadece EXE modunda çalışır.")
        return

    if not urlreq:
        return

    bilgi = github_son_surum_bilgi()

    if bilgi is None:
        if not sessiz:
            QMessageBox.warning(
                parent, "Bağlantı Hatası",
                "Güncelleme sunucusuna bağlanılamadı.\n"
                "İnternet bağlantınızı kontrol edin.")
        return

    if yeni_surum_var(SURUM, bilgi["tag"]):
        dlg = GuncellemeDlg(bilgi, parent=parent)
        dlg.exec_()
    else:
        if not sessiz:
            QMessageBox.information(
                parent, "Güncelleme",
                "Program güncel.\nMevcut sürüm: v{}".format(SURUM))


def arka_planda_kontrol(parent=None):
    """
    Program açılışında arka planda (thread'de) kontrol yapar.
    UI'yi bloklamaz.
    """
    def _kontrol():
        time.sleep(3)  # Program tamamen açılsın
        bilgi = github_son_surum_bilgi()
        if bilgi and yeni_surum_var(SURUM, bilgi["tag"]):
            # GUI thread'inde dialog aç
            try:
                from PyQt5.QtCore import QMetaObject, Q_ARG
                # Sinyal gönder (thread-safe)
                _GUNCELLEME_BILGI[0] = bilgi
            except:
                pass

    _GUNCELLEME_BILGI = [None]
    t = threading.Thread(target=_kontrol, daemon=True)
    t.start()
    return _GUNCELLEME_BILGI
