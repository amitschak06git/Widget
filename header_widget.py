from PyQt6.QtWidgets import QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6.QtGui import QFont
from base_widget import BaseWidget

class HeaderWidget(BaseWidget):
    def __init__(self, theme_manager=None, config_manager=None):
        super().__init__(theme_manager, config_manager, widget_id="header")
        self.config = config_manager
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.label = QLabel("TUESDAY")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setObjectName("header_label")
        self.apply_shadow(self.label)
        layout.addWidget(self.label)
        
        self.apply_theme()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_content)
        self.timer.start(60000) # Every min
        
        self.update_content()
        self.resize(600, 150) # Large width

    def apply_theme(self):
        if not self.theme_manager: return
        t = self.get_theme_with_opacity()
        
        # Header often uses transparent BG to let text float, but we'll use theme background with user opacity
        base_style = f"background-color: {t['background']}; border-radius: {t['border_radius']};"
        self.setStyleSheet(base_style + self.get_qss())
        
        # Font - Massive, spaced
        font_name = self.config.get("font_header", t['font_family']) if self.config else t['font_family']
        font = QFont(font_name, 80, QFont.Weight.Black)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 10)
        self.label.setFont(font)
        
        # Default internal style, can be overridden by QSS #header_label
        self.label.setStyleSheet(f"color: {t['text_main']}; background-color: transparent;")

    def update_content(self):
        self.label.setText(QDate.currentDate().toString("dddd").upper())
