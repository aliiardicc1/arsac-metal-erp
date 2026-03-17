import barcode
from barcode.writer import ImageWriter
import os

def barkod_uret(stok_kodu):
    try:
        # Barkod tipini seç (Code128 endüstriyel standarttır)
        COD = barcode.get_barcode_class('code128')
        my_code = COD(stok_kodu, writer=ImageWriter())
        
        if not os.path.exists('etiketler'):
            os.makedirs('etiketler')
            
        dosya_yolu = f"etiketler/{stok_kodu}"
        my_code.save(dosya_yolu)
        return f"{dosya_yolu}.png"
    except Exception as e:
        print(f"Barkod hatası: {e}")
        return None