from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon
import sys, os, random

class GlyphWidget(QSvgWidget):
    def __init__(self, glyph_folder="assets/glyphs", parent=None):
        super().__init__(parent)
        self.setMinimumSize(120, 120)
        self.timer = QTimer()
        self.timer.timeout.connect(self.show_random_glyph)

        # 🔍 Resolve path for onefile or normal mode
        if hasattr(sys, "_MEIPASS"):
            self.glyph_folder = os.path.join(sys._MEIPASS, glyph_folder)
        else:
            self.glyph_folder = os.path.abspath(glyph_folder)

        # ⛺ Create folder if missing
        if not os.path.exists(self.glyph_folder):
            os.makedirs(self.glyph_folder)

    def start_loop(self, interval_ms=800):
        self.timer.start(interval_ms)

    def stop_loop(self):
        self.timer.stop()

    def show_random_glyph(self):
        try:
            glyphs = [f for f in os.listdir(self.glyph_folder) if f.endswith(".svg")]
            if glyphs:
                choice = random.choice(glyphs)
                self.load(os.path.join(self.glyph_folder, choice))
            else:
                print("⚠️ Tidak ada glyph SVG ditemukan di folder:", self.glyph_folder)
        except Exception as e:
            print(f"❌ Gagal load glyph: {e}")