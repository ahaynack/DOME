# ui/launcher.py
import sys
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QPushButton, 
                             QLabel, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, QSize, QEvent
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPainter, QColor
from PyQt5.QtSvg import QSvgRenderer

# Import sub-windows
from ui.window_generator import GeneratorWindow
from ui.window_comparator import ComparatorWindow
from ui.window_simulation import SimulationWindow

class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DOME - Suite Launcher")
        self.resize(500, 550)
        
        self.setWindowIcon(QIcon(self.resource_path("assets/icon_black_gray.svg")))
        
        # --- PRE-LOAD LOGOS ---
        self.pix_default = self.get_high_res_pixmap(self.resource_path("assets/icon_black_gray.svg"), 128, 128)
        self.pix_gen = self.get_high_res_pixmap(self.resource_path("assets/icon_blue_gray.svg"), 128, 128)
        self.pix_comp = self.get_high_res_pixmap(self.resource_path("assets/icon_green_gray.svg"), 128, 128)
        self.pix_sim = self.get_high_res_pixmap(self.resource_path("assets/icon_purple_gray.svg"), 128, 128)

        # Fallback: If custom logos missing, use default for all
        if not self.pix_gen: self.pix_gen = self.pix_default
        if not self.pix_comp: self.pix_comp = self.pix_default
        if not self.pix_sim: self.pix_sim = self.pix_default

        self.init_ui()

    def resource_path(self, relative_path):
        """ Get absolute path to resource """
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def get_high_res_pixmap(self, svg_path, width, height):
        """
        Renders an SVG file directly onto a QPixmap of the specified size.
        This avoids pixelation because it rasterizes at the target resolution.
        """
        if not os.path.exists(svg_path):
            return None

        # Create a QSvgRenderer for the file
        renderer = QSvgRenderer(svg_path)

        # Create a high-res, transparent Pixmap
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.transparent)

        # Use QPainter to render the SVG onto the Pixmap
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        return pixmap

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(50, 40, 50, 40)

        # --- LOGO ---
        self.lbl_logo = QLabel()
        
        if self.pix_default:
            self.lbl_logo.setPixmap(self.pix_default)
            self.lbl_logo.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.lbl_logo)
        else:
            print("Warning: Default Logo not found")

        # --- TITLE ---
        lbl_title = QLabel("DOME\nMesostructure Suite")
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet("font-family: 'Segoe UI', sans-serif; font-size: 22pt; font-weight: bold; color: #333;")
        layout.addWidget(lbl_title)

        layout.addSpacing(10)

        # --- GENERATOR BUTTON ---
        self.btn_gen = QPushButton("  Mesostructure Generator")
        self.btn_gen.setMinimumHeight(65)
        self.btn_gen.setCursor(Qt.PointingHandCursor)
        self.btn_gen.setStyleSheet("""
            QPushButton {
                background-color: #0078d4; color: white; font-size: 13pt; font-weight: bold; border-radius: 8px; padding: 5px;
            }
            QPushButton:hover { background-color: #0063b1; }
            QPushButton:pressed { background-color: #004e8c; }
        """)
        self.btn_gen.clicked.connect(self.open_generator)
        
        # Install event filter (to detect hover)
        self.btn_gen.installEventFilter(self)
        
        layout.addWidget(self.btn_gen)

        # --- COMPARATOR BUTTON ---
        self.btn_comp = QPushButton("  Mesostructure Comparator")
        self.btn_comp.setMinimumHeight(65)
        self.btn_comp.setCursor(Qt.PointingHandCursor)
        self.btn_comp.setStyleSheet("""
            QPushButton {
                background-color: #107c10; color: white; font-size: 13pt; font-weight: bold; border-radius: 8px; padding: 5px;
            }
            QPushButton:hover { background-color: #0c5d0c; }
            QPushButton:pressed { background-color: #083b08; }
        """)
        self.btn_comp.clicked.connect(self.open_comparator)
        
        # Install event filter (to detect hover)
        self.btn_comp.installEventFilter(self)
        
        layout.addWidget(self.btn_comp)
        
        # Currently disabled - will be re-added in the future
        # # --- SIMULATION BUTTON ---
        # self.btn_sim = QPushButton("  Simulate Surface Scaling")
        # self.btn_sim.setMinimumHeight(65)
        # self.btn_sim.setCursor(Qt.PointingHandCursor)
        # self.btn_sim.setStyleSheet("""
        #     QPushButton {
        #         background-color: #7030a0; 
        #         color: white; 
        #         font-size: 13pt; 
        #         font-weight: bold;
        #         border-radius: 8px;
        #         padding: 5px;
        #     }
        #     QPushButton:hover { background-color: #5c2682; }
        #     QPushButton:pressed { background-color: #4a1e69; }
        # """)
        # self.btn_sim.clicked.connect(self.open_simulation)
        
        # # Install event filter (to detect hover)
        # self.btn_sim.installEventFilter(self)
        
        # layout.addWidget(self.btn_sim)

        layout.addStretch()
        
        # --- FOOTER ---
        lbl_footer = QLabel("Distribution-Optimized Mesostructure Estimation\nDOME v1.0")
        lbl_footer.setAlignment(Qt.AlignCenter)
        lbl_footer.setStyleSheet("color: #888; font-size: 9pt;")
        layout.addWidget(lbl_footer)

    def eventFilter(self, source, event):
        """
        Detects mouse Enter/Leave events on the buttons to change the logo.
        """
        if event.type() == QEvent.Enter:
            if source == self.btn_gen and self.pix_gen:
                self.lbl_logo.setPixmap(self.pix_gen)
            elif source == self.btn_comp and self.pix_comp:
                self.lbl_logo.setPixmap(self.pix_comp)
            elif source == self.btn_sim and self.pix_sim:
                self.lbl_logo.setPixmap(self.pix_sim)
                
        elif event.type() == QEvent.Leave:
            if self.pix_default:
                self.lbl_logo.setPixmap(self.pix_default)
                
        return super().eventFilter(source, event)

    def open_generator(self):
        self.generator_win = GeneratorWindow(launcher=self)
        self.generator_win.show()
        self.hide()

    def open_comparator(self):
        self.comparator_win = ComparatorWindow(launcher=self)
        self.comparator_win.show()
        self.hide()
    
    def open_simulation(self):
        self.sim_win = SimulationWindow(launcher=self)
        self.sim_win.show()
        self.hide()