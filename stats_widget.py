from PyQt6.QtWidgets import QLabel, QHBoxLayout, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QFont, QPainter, QColor, QPen
from base_widget import BaseWidget
import sys

# Try import psutil
try:
    import psutil
except ImportError:
    psutil = None

class CircularProgress(QWidget):
    def __init__(self, label, color, parent=None):
        super().__init__(parent)
        self.label = label
        self.color = color
        self.value = 0
        self.setFixedSize(70, 90) # Widget size

    def set_value(self, val):
        self.value = val
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background circle
        rect = QRectF(10, 10, 50, 50)
        pen_bg = QPen(QColor(255, 255, 255, 30))
        pen_bg.setWidth(5)
        painter.setPen(pen_bg)
        painter.drawEllipse(rect)
        
        # Draw progress
        # -90 start angle (12 o clock), span is negative for clockwise
        span_angle = -int(self.value * 3.6 * 16)
        pen_prog = QPen(self.color)
        pen_prog.setWidth(5)
        pen_prog.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_prog)
        painter.drawArc(rect, 90 * 16, span_angle)
        
        # Text
        painter.setPen(QColor("white"))
        font = QFont(self.font().family(), 8)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{int(self.value)}%")
        
        # Label below
        rect_label = QRectF(0, 65, 70, 20)
        painter.drawText(rect_label, Qt.AlignmentFlag.AlignCenter, self.label)

class StatsWidget(BaseWidget):
    def __init__(self, theme_manager=None, config_manager=None):
        super().__init__(theme_manager, config_manager, widget_id="stats")
        self.config = config_manager
        
        layout = QHBoxLayout()
        self.setLayout(layout)
        
        # 4 Stats: CPU, RAM, Disk, Net (mock or real)
        self.cpu = CircularProgress("CPU", QColor("#FF453A"))   # Apple system red
        self.ram = CircularProgress("RAM", QColor("#32D74B"))   # Apple system green
        self.disk = CircularProgress("DISK", QColor("#0A84FF")) # Apple system blue
        # self.net = CircularProgress("NET", QColor("#FFFF55")) 
        
        layout.addWidget(self.cpu)
        layout.addWidget(self.ram)
        layout.addWidget(self.disk)
        
        self.apply_theme()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(2000)
        
        self.update_stats()
        self.resize(240, 110)

    def apply_theme(self):
        if not self.theme_manager: return
        t = self.get_theme_with_opacity()
        
        base_style = f"QWidget#stats {{ background-color: {t['background']}; border-radius: {t['border_radius']}; }}"
        self.setStyleSheet(base_style + self.get_qss())
        
        font_name = self.config.get("font_stats", t['font_family']) if self.config else t['font_family']
        self.setFont(QFont(font_name, 10))
        # Trigger update to repaint circles with new font
        self.update()

    def update_stats(self):
        if psutil:
            self.cpu.set_value(psutil.cpu_percent())
            self.ram.set_value(psutil.virtual_memory().percent)
            self.disk.set_value(psutil.disk_usage('/').percent)
        else:
            # Mock
            import random
            self.cpu.set_value(random.randint(10, 30))
            self.ram.set_value(random.randint(40, 60))
            self.disk.set_value(random.randint(20, 80))
