from PyQt6.QtWidgets import QLabel, QVBoxLayout
from PyQt6.QtCore import QDate, Qt, QTimer
from PyQt6.QtGui import QFont
from base_widget import BaseWidget

class DateWidget(BaseWidget):
    def __init__(self, theme_manager=None, config_manager=None):
        super().__init__(theme_manager, config_manager, widget_id="date")
        self.config = config_manager
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Day Label (Large)
        self.day_label = QLabel()
        self.day_label.setObjectName("date_day_name")
        self.day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.apply_shadow(self.day_label)
        layout.addWidget(self.day_label)
        
        # Date Label (Smaller)
        self.date_label = QLabel()
        self.date_label.setObjectName("date_full_date")
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.apply_shadow(self.date_label)
        layout.addWidget(self.date_label)
        
        # Apply Theme
        self.apply_theme()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_date)
        self.timer.start(60000)
        
        self.update_date()
        self.resize(250, 150)

    def apply_theme(self):
        if not self.theme_manager: return

        t = self.get_theme_with_opacity()
        base_style = f"QWidget#date {{ background-color: {t['background']}; border-radius: {t['border_radius']}; }}"
        self.setStyleSheet(base_style + self.get_qss())
        
        font_family = t.get("font_family", "Segoe UI")
        
        self.day_label.setFont(QFont(font_family, 30, QFont.Weight.Medium))
        self.day_label.setStyleSheet(f"color: {t['accent']}; background-color: transparent;")

        self.date_label.setFont(QFont(font_family, 16, QFont.Weight.Normal))
        self.date_label.setStyleSheet(f"color: {t['text_main']}; background-color: transparent;")

    def update_date(self):
        current = QDate.currentDate()
        self.day_label.setText(current.toString("dddd"))
        self.date_label.setText(current.toString("MMMM d, yyyy"))
