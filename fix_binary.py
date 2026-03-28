import os

# Cift encode edilmis Turkce karakterleri binary seviyesinde duzelt
replacements = [
    (b'\xc3\x85\xc2\x9e', b'\xc5\x9e'),  # Ş
    (b'\xc3\x85\xc2\x9f', b'\xc5\x9f'),  # ş
    (b'\xc3\x84\xc2\xb0', b'\xc4\xb0'),  # İ
    (b'\xc3\x84\xc2\xb1', b'\xc4\xb1'),  # ı
    (b'\xc3\x84\xc5\xb8', b'\xc4\x9f'),  # ğ
    (b'\xc3\x84\xc5\xbe', b'\xc4\x9e'),  # Ğ
    (b'\xc3\x83\xc2\xbc', b'\xc3\xbc'),  # ü
    (b'\xc3\x83\xc2\xb6', b'\xc3\xb6'),  # ö
    (b'\xc3\x83\xc2\xa7', b'\xc3\xa7'),  # ç
    (b'\xc3\x83\xe2\x80\x93', b'\xc3\x87'),  # Ç
    (b'\xc3\x83\xc5\x93', b'\xc3\x9c'),  # Ü
    (b'\xc3\x83\xe2\x80\x9a', b'\xc3\x82'),  # Â
]

dosyalar = [f for f in os.listdir('.') if f.endswith('.py')]
toplam = 0

for dosya in dosyalar:
    try:
        data = open(dosya, 'rb').read()
        yeni = data
        for eski, yeni_b in replacements:
            yeni = yeni.replace(eski, yeni_b)
        if yeni != data:
            open(dosya, 'wb').write(yeni)
            print(f"✓ {dosya} duzeltildi")
            toplam += 1
    except Exception as e:
        print(f"✗ {dosya}: {e}")

print(f"\nToplam {toplam} dosya duzeltildi.")