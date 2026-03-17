import os
from datetime import datetime
from reportlab.lib.pagesizes import A6, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.graphics.barcode import code128
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.pdfgen import canvas as rl_canvas


KIRMIZI = colors.HexColor("#c0392b")
KOYU    = colors.HexColor("#2c3e50")
ACIK    = colors.HexColor("#f4f6f9")
BEYAZ   = colors.white


def stok_fisi_olustur(stok_bilgileri):
    """
    stok_bilgileri: liste — her eleman bir sac için dict:
    {stok_kodu, malzeme, en, boy, kalinlik, kg, son_firma, son_tarih}
    A6 boyutunda, yatay — depoda kolayca okunur etiket boyutu.
    Birden fazla sac varsa tek PDF'e arka arkaya eklenir.
    """
    klasor = "Satin Alma Belgeleri"
    if not os.path.exists(klasor):
        os.makedirs(klasor)

    zaman = datetime.now().strftime('%Y%m%d_%H%M%S')
    dosya = f"{klasor}/StokFis_{zaman}.pdf"

    # A6 yatay: 148 x 105 mm
    sayfa_w, sayfa_h = landscape(A6)

    c = rl_canvas.Canvas(dosya, pagesize=landscape(A6))

    for idx, s in enumerate(stok_bilgileri):
        _fis_ciz(c, s, sayfa_w, sayfa_h)
        if idx < len(stok_bilgileri) - 1:
            c.showPage()

    c.save()
    return dosya


def _fis_ciz(c, s, w, h):
    """Tek bir stok fişi sayfası çizer."""
    stok_kodu = s.get('stok_kodu', '-')
    malzeme   = s.get('malzeme', '-')
    en        = s.get('en', '-')
    boy       = s.get('boy', '-')
    kal       = s.get('kalinlik', '-')
    kg        = s.get('kg', '-')
    firma     = s.get('son_firma', '-')
    tarih     = s.get('son_tarih', datetime.now().strftime('%d.%m.%Y'))

    kenar = 8 * mm

    # --- ARKA PLAN ---
    c.setFillColor(BEYAZ)
    c.rect(0, 0, w, h, fill=1, stroke=0)

    # --- ÜST KIRMIZI BANT ---
    c.setFillColor(KIRMIZI)
    c.rect(0, h - 22*mm, w, 22*mm, fill=1, stroke=0)

    # Şirket adı
    c.setFillColor(BEYAZ)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(kenar, h - 11*mm, "ARSAC METAL")

    # Fiş türü
    c.setFont("Helvetica", 8)
    c.drawRightString(w - kenar, h - 9*mm, "STOK GİRİŞ FİŞİ")
    c.drawRightString(w - kenar, h - 16*mm, tarih)

    # --- STOK KODU (büyük, belirgin) ---
    c.setFillColor(KOYU)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(w / 2, h - 32*mm, stok_kodu)

    # Alt çizgi
    c.setStrokeColor(KIRMIZI)
    c.setLineWidth(1.5)
    c.line(kenar, h - 34*mm, w - kenar, h - 34*mm)

    # --- BARKOD ---
    try:
        barkod = code128.Code128(stok_kodu, barHeight=12*mm, barWidth=0.8)
        barkod_w = barkod.width
        barkod_x = (w - barkod_w) / 2
        barkod.drawOn(c, barkod_x, h - 50*mm)
    except Exception as e:
        # Barkod çizilmezse stok kodunu tekrar yaz
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.grey)
        c.drawCentredString(w / 2, h - 48*mm, f"[{stok_kodu}]")

    # --- BİLGİ SATIRLARI ---
    c.setLineWidth(0.5)
    c.setStrokeColor(colors.HexColor("#dcdde1"))

    satirlar = [
        ("MALZEMESi / KALİTE",  malzeme),
        ("ÖLÇÜLER (En x Boy x Kal)", f"{en} x {boy} x {kal} mm"),
        ("AĞIRLIK",              f"{float(kg or 0):,.2f} KG"),
        ("TEDARİKÇİ FİRMA",     firma),
    ]

    y = h - 57*mm
    satir_h = 9.5*mm
    sol_w = 52*mm

    for baslik, deger in satirlar:
        # Arka plan (alternatif)
        if satirlar.index((baslik, deger)) % 2 == 0:
            c.setFillColor(ACIK)
            c.rect(kenar, y - satir_h + 2*mm, w - 2*kenar, satir_h, fill=1, stroke=0)

        c.setFillColor(colors.HexColor("#7f8c8d"))
        c.setFont("Helvetica", 7)
        c.drawString(kenar + 2*mm, y - 2*mm, baslik)

        c.setFillColor(KOYU)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(kenar + sol_w, y - 2*mm, str(deger))

        # Ayırıcı çizgi
        c.setStrokeColor(colors.HexColor("#dcdde1"))
        c.line(kenar, y - satir_h + 2*mm, w - kenar, y - satir_h + 2*mm)

        y -= satir_h

    # --- ALT BİLGİ ---
    c.setFillColor(KOYU)
    c.setFont("Helvetica", 6)
    c.drawCentredString(w / 2, 4*mm,
        "Bu fiş Arsac Metal ERP sistemi tarafından otomatik oluşturulmuştur.")