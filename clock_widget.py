from PyQt6.QtWidgets import QLabel, QVBoxLayout
from PyQt6.QtCore import QTimer, QTime, Qt
from PyQt6.QtGui import QFont
from base_widget import BaseWidget
from zoneinfo import ZoneInfo
from datetime import datetime

class ClockWidget(BaseWidget):
    def __init__(self, clock_id, timezone="Local", label="Local Time", theme_manager=None, config_manager=None):
        super().__init__(theme_manager, config_manager, widget_id=f"clock_{clock_id}")
        self.clock_id = clock_id
        self.timezone = timezone
        self.label_text = label
        self.config = config_manager
        
        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(4)
        self.setLayout(layout)

        # Time Label
        self.time_label = QLabel()
        self.time_label.setObjectName("clock_time")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.apply_shadow(self.time_label)
        layout.addWidget(self.time_label)
        
        # Location Label
        self.loc_label = QLabel(self.label_text)
        self.loc_label.setObjectName("clock_label")
        self.loc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.apply_shadow(self.loc_label)
        layout.addWidget(self.loc_label)
        
        # Date Label (New)
        self.date_label = QLabel()
        self.date_label.setObjectName("clock_date")
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.apply_shadow(self.date_label)
        layout.addWidget(self.date_label)

        # Apply Theme
        self.apply_theme()

        # Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)

        self.update_time()
        self.resize(300, 150) # Increased height for date

    def apply_theme(self):
        if not self.theme_manager:
            return

        t = self.get_theme_with_opacity()
        
        # Base ID-based style for the container
        base_style = f"QWidget#clock_{self.clock_id} {{ background-color: {t['background']}; border-radius: {t['border_radius']}; }}"
        self.setStyleSheet(base_style + self.get_qss())
        
        # Fonts
        font_time_name = self.config.get("font_family_time", t["font_family"]) if self.config else t["font_family"]
        font_label_name = self.config.get("font_family_label", t["font_family"]) if self.config else t["font_family"]
        
        time_font = QFont(font_time_name, 40)
        time_font.setWeight(QFont.Weight.Thin)
        self.time_label.setFont(time_font)
        self.time_label.setStyleSheet(f"color: {t['text_main']}; background-color: transparent;")

        self.loc_label.setFont(QFont(font_label_name, 11, QFont.Weight.Medium))
        self.loc_label.setStyleSheet(f"color: {t['text_secondary']}; background-color: transparent;")

        self.date_label.setFont(QFont(font_label_name, 11, QFont.Weight.Normal))
        self.date_label.setStyleSheet(f"color: {t['text_secondary']}; background-color: transparent;")

    def update_time(self):
        current_date_str = ""
        current_time = ""
        
        if self.timezone == "Local":
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            current_date_str = now.strftime("%A, %B %d, %Y")
        else:
            try:
                dt = datetime.now(ZoneInfo(self.timezone))
                current_time = dt.strftime("%H:%M:%S")
                current_date_str = dt.strftime("%A, %B %d, %Y")
            except Exception:
                current_time = "Error"
                current_date_str = "Invalid TZ"
        
        self.time_label.setText(current_time)
        self.date_label.setText(current_date_str)
