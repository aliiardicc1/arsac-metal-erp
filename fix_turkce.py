import os

def fix_double_encoded(data):
    try:
        return data.encode('latin-1').decode('utf-8')
    except:
        return data

dosyalar = [f for f in os.listdir('.') if f.endswith('.py')]
toplam = 0

for dosya in dosyalar:
    try:
        content = open(dosya, encoding='utf-8').read()
        fixed = fix_double_encoded(content)
        if fixed != content:
            open(dosya, 'w', encoding='utf-8').write(fixed)
            print(f"✓ {dosya} duzeltildi")
            toplam += 1
    except Exception as e:
        print(f"✗ {dosya}: {e}")

print(f"\nToplam {toplam} dosya duzeltildi.")