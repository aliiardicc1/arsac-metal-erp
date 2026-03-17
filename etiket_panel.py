from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame, QGridLayout, QLabel, QPushButton
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import os

class EtiketPaneli(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        
        header = QLabel("🏷️ Üretilen Barkod Etiketleri")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background: transparent;")
        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.grid.setSpacing(20)
        self.scroll.setWidget(self.container)
        
        layout.addWidget(self.scroll)

    def yenile(self):
        # Önce paneli temizle
        for i in reversed(range(self.grid.count())): 
            w = self.grid.itemAt(i).widget()
            if w: w.setParent(None)

        yol = "etiketler"
        if not os.path.exists(yol):
            return

        # Klasördeki tüm barkod resimlerini tara
        dosyalar = [f for f in os.listdir(yol) if f.endswith('.png')]
        
        for sira, dosya_adi in enumerate(dosyalar):
            kart = QFrame()
            kart.setFixedSize(250, 200)
            kart.setStyleSheet("background: white; border-radius: 10px; border: 1px solid #ddd;")
            
            v_lay = QVBoxLayout(kart)
            
            # Barkod Resmi
            img_lbl = QLabel()
            pixmap = QPixmap(os.path.join(yol, dosya_adi))
            img_lbl.setPixmap(pixmap.scaled(200, 100, Qt.KeepAspectRatio))
            img_lbl.setAlignment(Qt.AlignCenter)
            
            # Stok Kodu Yazısı
            txt_lbl = QLabel(dosya_adi.replace(".png", ""))
            txt_lbl.setStyleSheet("font-weight: bold; font-size: 14px; color: #34495e;")
            txt_lbl.setAlignment(Qt.AlignCenter)
            
            v_lay.addWidget(img_lbl)
            v_lay.addWidget(txt_lbl)
            
            self.grid.addWidget(kart, sira // 4, sira % 4)