"""
Arsac Metal ERP — Gunluk Ozet Rapor
Program acilisinda otomatik olusur, A4 dikey, profesyonel gorunum.
"""
import os
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

KIRMIZI  = colors.HexColor("#c0392b")
KOYU     = colors.HexColor("#2c3e50")
YESIL    = colors.HexColor("#27ae60")
TURUNCU  = colors.HexColor("#e67e22")
MAVI     = colors.HexColor("#2980b9")
ACIK_GRI = colors.HexColor("#f4f6f9")
GRI      = colors.HexColor("#7f8c8d")
BEYAZ    = colors.white
SARI_BG  = colors.HexColor("#fef9e7")
KIRMIZI_BG = colors.HexColor("#fde8e8")
YESIL_BG   = colors.HexColor("#eafaf1")


def gunluk_rapor_olustur(cursor):
    """
    Veritabanindan verileri cekip gunluk ozet PDF olusturur.
    Dondurur: (pdf_yolu, veri_ozeti_dict)
    """
    klasor = "Gunluk Raporlar"
    if not os.path.exists(klasor):
        os.makedirs(klasor)

    bugun     = datetime.now().strftime('%d.%m.%Y')
    bugun_dosya = datetime.now().strftime('%Y%m%d')
    dosya = f"{klasor}/Rapor_{bugun_dosya}.pdf"

    # --- VERI CEK ---
    veri = _veri_cek(cursor, bugun)

    # --- PDF CIZ ---
    w, h = A4
    c = rl_canvas.Canvas(dosya, pagesize=A4)
    y = h  # Kalem pozisyonu

    y = _baslik_ciz(c, w, h, bugun)
    y = _ozet_kartlar_ciz(c, w, y, veri)
    y = _bolum_baslik(c, w, y, "💳  BUGUN VADESI GELEN ODEMELER")
    y = _vade_tablosu_ciz(c, w, y, veri["vadeler"])
    y = _bolum_baslik(c, w, y, "📦  KRITIK STOK DURUMU")
    y = _stok_tablosu_ciz(c, w, y, veri["stok"])
    y = _bolum_baslik(c, w, y, "🏗️  BEKLEYENHAMMADDETALEPLERI")
    y = _talep_tablosu_ciz(c, w, y, veri["talepler"])
    y = _bolum_baslik(c, w, y, "🚚  YOLDA / GIRIS BEKLEYENSAClar")
    y = _yolda_tablosu_ciz(c, w, y, veri["yolda"])
    _alt_bilgi_ciz(c, w, bugun)

    c.save()
    return dosya, veri


def _veri_cek(cursor, bugun):
    """Tum bolumler icin veriyi tek seferde ceker."""
    veri = {}

    # Bugun vadesi gelen odemeler
    try:
        cursor.execute("""
            SELECT firma, vade_tarihi, toplam_tutar, odeme_tipi
            FROM satinalma_kayitlari
            WHERE (odendi IS NULL OR odendi=0)
            ORDER BY vade_tarihi ASC
            LIMIT 20
        """)
        tum_vadeler = cursor.fetchall()
        # Vadesi gecmis veya bugun/bu hafta olanlari goster
        vadeler = []
        for firma, vade, tutar, tip in tum_vadeler:
            try:
                if "Gun" in str(vade):
                    vadeler.append((firma, vade, tutar, tip, "eski"))
                    continue
                gun = (datetime.strptime(vade, '%d.%m.%Y') - datetime.now()).days
                if gun <= 7:
                    vadeler.append((firma, vade, tutar, tip, gun))
            except:
                vadeler.append((firma, vade or "-", tutar, tip, None))
        veri["vadeler"] = vadeler
    except:
        veri["vadeler"] = []

    # Stok durumu
    try:
        cursor.execute("""
            SELECT malzeme, kalinlik, SUM(kg)
            FROM stok
            GROUP BY malzeme, kalinlik
            ORDER BY SUM(kg) ASC
            LIMIT 15
        """)
        veri["stok"] = cursor.fetchall()
    except:
        veri["stok"] = []

    # Bekleyen hammadde talepleri
    try:
        cursor.execute("""
            SELECT kalite, en, boy, kalinlik, kg, tarih
            FROM talepler
            WHERE durum=0
            ORDER BY tarih DESC
            LIMIT 15
        """)
        veri["talepler"] = cursor.fetchall()
    except:
        veri["talepler"] = []

    # Yolda saclar
    try:
        cursor.execute("""
            SELECT stok_kodu, malzeme, en, boy, kalinlik, kg, son_firma
            FROM stok
            WHERE durum=0
            ORDER BY id DESC
            LIMIT 15
        """)
        veri["yolda"] = cursor.fetchall()
    except:
        veri["yolda"] = []

    # Ozet sayilar
    try:
        cursor.execute("SELECT COUNT(*) FROM talepler WHERE durum=0")
        veri["bekleyen_talep"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM stok WHERE durum=0")
        veri["yolda_sac"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM stok WHERE durum=1")
        veri["depoda_sac"] = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(toplam_tutar) FROM satinalma_kayitlari WHERE odendi=0 OR odendi IS NULL")
        veri["toplam_borc"] = float(cursor.fetchone()[0] or 0)

        cursor.execute("SELECT COUNT(*) FROM satinalma_kayitlari WHERE odendi=0 OR odendi IS NULL")
        veri["bekleyen_odeme"] = cursor.fetchone()[0]

        # Kritik stok sayisi
        cursor.execute("SELECT COUNT(*) FROM (SELECT malzeme, SUM(kg) as topkg FROM stok GROUP BY malzeme HAVING topkg < 500)")
        veri["kritik_stok"] = cursor.fetchone()[0]

    except:
        veri["bekleyen_talep"] = 0
        veri["yolda_sac"]      = 0
        veri["depoda_sac"]     = 0
        veri["toplam_borc"]    = 0
        veri["bekleyen_odeme"] = 0
        veri["kritik_stok"]    = 0

    return veri


def _baslik_ciz(c, w, h, bugun):
    """Ust baslik bandi."""
    # Kirmizi arka plan
    c.setFillColor(KIRMIZI)
    c.rect(0, h - 60*mm, w, 60*mm, fill=1, stroke=0)

    # Sirket adi
    c.setFillColor(BEYAZ)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(15*mm, h - 22*mm, "ARSAC METAL")

    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#ffcccc"))
    c.drawString(15*mm, h - 30*mm, "Oksijen Plazma Lazer Kesim - Demir Celik Metal San. ve Tic. Ltd. Sti.")

    # Rapor basligi
    c.setFillColor(BEYAZ)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(w/2, h - 42*mm, "GUNLUK DURUM RAPORU")

    c.setFont("Helvetica", 10)
    c.drawCentredString(w/2, h - 52*mm, bugun)

    # Sag ust: Olusturma saati
    c.setFont("Helvetica", 8)
    c.drawRightString(w - 15*mm, h - 22*mm, f"Olusturulma: {datetime.now().strftime('%H:%M')}")

    return h - 65*mm


def _ozet_kartlar_ciz(c, w, y, veri):
    """4 ozet kart yan yana."""
    kart_w = (w - 30*mm) / 4
    kart_h = 28*mm
    baslangic_x = 15*mm
    y -= 5*mm

    kartlar = [
        ("BEKLEYEN TALEP",   str(veri["bekleyen_talep"]), MAVI),
        ("YOLDA SAC",        str(veri["yolda_sac"]),      TURUNCU),
        ("DEPODA SAC",       str(veri["depoda_sac"]),     YESIL),
        ("ACIK BORC",        f"{veri['toplam_borc']:,.0f} TL", KIRMIZI),
    ]

    for i, (baslik, deger, renk) in enumerate(kartlar):
        x = baslangic_x + i * (kart_w + 2*mm)

        # Kart arka plani
        c.setFillColor(colors.HexColor("#ffffff"))
        c.setStrokeColor(colors.HexColor("#dcdde1"))
        c.setLineWidth(0.5)
        c.roundRect(x, y - kart_h, kart_w, kart_h, 4, fill=1, stroke=1)

        # Sol renkli serit
        c.setFillColor(renk)
        c.roundRect(x, y - kart_h, 3*mm, kart_h, 2, fill=1, stroke=0)

        # Baslik
        c.setFillColor(GRI)
        c.setFont("Helvetica", 7)
        c.drawString(x + 5*mm, y - 8*mm, baslik)

        # Deger
        c.setFillColor(renk)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(x + 5*mm, y - 20*mm, deger)

    return y - kart_h - 8*mm


def _bolum_baslik(c, w, y, baslik):
    """Bolum basligi bandi."""
    if y < 40*mm:
        c.showPage()
        y = A4[1] - 20*mm

    y -= 6*mm
    c.setFillColor(KOYU)
    c.rect(15*mm, y - 8*mm, w - 30*mm, 8*mm, fill=1, stroke=0)
    c.setFillColor(BEYAZ)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(18*mm, y - 6*mm, baslik)
    return y - 10*mm


def _vade_tablosu_ciz(c, w, y, vadeler):
    if not vadeler:
        c.setFillColor(GRI)
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(18*mm, y - 6*mm, "Bu hafta vadesi gelen odeme bulunmuyor.")
        return y - 12*mm

    tablo_w = w - 30*mm
    col_w = [tablo_w*0.30, tablo_w*0.20, tablo_w*0.20, tablo_w*0.15, tablo_w*0.15]

    satirlar = [["FIRMA", "VADE TARIHI", "TUTAR", "ODEME TIPI", "DURUM"]]
    for firma, vade, tutar, tip, gun in vadeler:
        if gun == "eski":
            durum = "Eski kayit"
        elif gun is None:
            durum = "Bekliyor"
        elif gun < 0:
            durum = f"{abs(gun)} gun gecti!"
        elif gun == 0:
            durum = "BUGUN!"
        else:
            durum = f"{gun} gun kaldi"

        satirlar.append([
            firma or "-",
            str(vade),
            f"{float(tutar or 0):,.0f} TL",
            tip or "-",
            durum
        ])

    return _tablo_ciz(c, w, y, satirlar, col_w, vadeler, "vade")


def _stok_tablosu_ciz(c, w, y, stok):
    if not stok:
        c.setFillColor(GRI)
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(18*mm, y - 6*mm, "Stok verisi bulunamadi.")
        return y - 12*mm

    tablo_w = w - 30*mm
    col_w = [tablo_w*0.35, tablo_w*0.20, tablo_w*0.25, tablo_w*0.20]

    satirlar = [["MALZEME", "KALINLIK", "TOPLAM KG", "DURUM"]]
    for malzeme, kal, kg in stok:
        kg = float(kg or 0)
        if kg <= 500:
            durum = "KRITIK"
        elif kg <= 2000:
            durum = "UYARI"
        else:
            durum = "YETERLI"
        satirlar.append([malzeme or "-", f"{kal} mm", f"{kg:,.1f} KG", durum])

    return _tablo_ciz(c, w, y, satirlar, col_w, stok, "stok")


def _talep_tablosu_ciz(c, w, y, talepler):
    if not talepler:
        c.setFillColor(GRI)
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(18*mm, y - 6*mm, "Bekleyen hammadde talebi yok.")
        return y - 12*mm

    tablo_w = w - 30*mm
    col_w = [tablo_w*0.20, tablo_w*0.15, tablo_w*0.15, tablo_w*0.15, tablo_w*0.15, tablo_w*0.20]

    satirlar = [["KALITE", "EN", "BOY", "KALINLIK", "KG", "TARIH"]]
    for kalite, en, boy, kal, kg, tarih in talepler:
        satirlar.append([
            str(kalite or "-"),
            f"{en} mm", f"{boy} mm", f"{kal} mm",
            f"{float(kg or 0):,.1f}",
            str(tarih or "-")
        ])

    return _tablo_ciz(c, w, y, satirlar, col_w, talepler, "talep")


def _yolda_tablosu_ciz(c, w, y, yolda):
    if not yolda:
        c.setFillColor(GRI)
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(18*mm, y - 6*mm, "Yolda bekleven sac yok.")
        return y - 12*mm

    tablo_w = w - 30*mm
    col_w = [tablo_w*0.20, tablo_w*0.18, tablo_w*0.12, tablo_w*0.12, tablo_w*0.12, tablo_w*0.12, tablo_w*0.14]

    satirlar = [["STOK KODU", "MALZEME", "EN", "BOY", "KAL", "KG", "FIRMA"]]
    for stok_kodu, malzeme, en, boy, kal, kg, firma in yolda:
        satirlar.append([
            str(stok_kodu or "-"),
            str(malzeme or "-"),
            f"{en}",f"{boy}",f"{kal}",
            f"{float(kg or 0):,.1f}",
            str(firma or "-")
        ])

    return _tablo_ciz(c, w, y, satirlar, col_w, yolda, "yolda")


def _tablo_ciz(c, w, y, satirlar, col_w, ham_veri, tip):
    """Genel tablo cizici."""
    from reportlab.platypus import Table, TableStyle

    if y < 50*mm:
        c.showPage()
        y = A4[1] - 20*mm

    tablo = Table(satirlar, colWidths=col_w, rowHeights=[7*mm] + [6.5*mm]*(len(satirlar)-1))

    style = [
        # Baslik
        ('BACKGROUND', (0, 0), (-1, 0), KOYU),
        ('TEXTCOLOR',  (0, 0), (-1, 0), BEYAZ),
        ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0, 0), (-1, 0), 8),
        ('ALIGN',      (0, 0), (-1, 0), 'CENTER'),
        # Veri satirlari
        ('FONTNAME',   (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',   (0, 1), (-1, -1), 8),
        ('ALIGN',      (0, 1), (-1, -1), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ACIK_GRI]),
        ('GRID',       (0, 0), (-1, -1), 0.3, colors.HexColor("#dcdde1")),
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]

    # Tip bazli renk vurgulama
    for i, satir_veri in enumerate(ham_veri, start=1):
        if tip == "vade":
            gun = satir_veri[4] if len(satir_veri) > 4 else None
            if gun == "eski" or gun is None:
                pass
            elif isinstance(gun, int) and gun < 0:
                style.append(('BACKGROUND', (0, i), (-1, i), KIRMIZI_BG))
            elif isinstance(gun, int) and gun == 0:
                style.append(('BACKGROUND', (0, i), (-1, i), KIRMIZI_BG))
            elif isinstance(gun, int) and gun <= 3:
                style.append(('BACKGROUND', (0, i), (-1, i), SARI_BG))
        elif tip == "stok":
            kg = float(satir_veri[2] or 0)
            if kg <= 500:
                style.append(('BACKGROUND', (0, i), (-1, i), KIRMIZI_BG))
                style.append(('TEXTCOLOR', (3, i), (3, i), KIRMIZI))
                style.append(('FONTNAME', (3, i), (3, i), 'Helvetica-Bold'))
            elif kg <= 2000:
                style.append(('BACKGROUND', (0, i), (-1, i), SARI_BG))

    tablo.setStyle(TableStyle(style))

    tablo_h = len(satirlar) * 6.5*mm + 0.5*mm
    if y - tablo_h < 25*mm:
        c.showPage()
        y = A4[1] - 20*mm

    tablo.wrapOn(c, w - 30*mm, y)
    tablo.drawOn(c, 15*mm, y - tablo_h)

    return y - tablo_h - 5*mm


def _alt_bilgi_ciz(c, w, bugun):
    """Alt bilgi."""
    c.setStrokeColor(colors.HexColor("#dcdde1"))
    c.setLineWidth(0.5)
    c.line(15*mm, 20*mm, w - 15*mm, 20*mm)

    c.setFillColor(GRI)
    c.setFont("Helvetica", 7)
    c.drawString(15*mm, 14*mm, f"Arsac Metal ERP — Gunluk Rapor — {bugun}")
    c.drawRightString(w - 15*mm, 14*mm, "Bu rapor sistem tarafindan otomatik olusturulmustur.")