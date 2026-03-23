from database_bulut import giris_yap, izin_yukle, baglanti_kur
conn, cursor = baglanti_kur()
r = giris_yap('emresubas', 'Arsac2024')
print('Giris:', r.get('rol'))
iz = izin_yukle(cursor, 'emresubas')
print('Izinler:', iz)
print('Siparisler:', iz.get('siparisler'))