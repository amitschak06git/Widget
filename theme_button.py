from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, QSize, QPointF
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QPen, QBrush

class ThemeButton(QPushButton):
    def __init__(self, icon_type="play", theme_manager=None, parent=None):
        super().__init__(parent)
        self.icon_type = icon_type # play, pause, next, prev
        self.theme_manager = theme_manager
        self.setFixedSize(40, 40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        t = self.theme_manager.get_theme() if self.theme_manager else {}
        theme_name = self.theme_manager.current_theme_name if self.theme_manager else "Dark (Default)"
        
        # Determine Check state for Play/Pause text
        # But actually icon_type should be updated by caller or we check text
        # Simpler: Caller sets text to "play" or "pause" or we use icon_type + internal state?
        # Let's rely on parent updating 'icon_type' or using standardsetText and we parse it?
        # Actually caller usually sets Text for Play/Pause in MediaWidget. 
        # Let's override setText to update icon_type for play/pause toggle.
        
        width = self.width()
        height = self.height()
        rect = self.rect()
        
        # 1. Background
        bg_color = QColor(t.get("accent", "#ffffff"))
        text_color = QColor(t.get("text_main", "#000000"))
        
        if "Neon" in theme_name:
            # Hollow, Glow
            painter.setBrush(Qt.BrushStyle.NoBrush)
            pen = QPen(bg_color)
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawEllipse(2, 2, width-4, height-4)
            # Icon Color is same as accent
            icon_color = bg_color
            
        elif "Material" in theme_name:
            # Solid Circle
            painter.setBrush(QBrush(bg_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(0, 0, width, height)
            # Icon Color is white or contrasting
            icon_color = QColor("white")
            
        elif "Glass" in theme_name:
            # Minimalist, Thin Ring or specific transparency
            painter.setBrush(QBrush(QColor(255, 255, 255, 30)))
            painter.setPen(QPen(QColor(255, 255, 255, 100), 1))
            painter.drawEllipse(1, 1, width-2, height-2)
            icon_color = QColor("white")
            
        else: # Default/Dark
             # Standard Circle or rounded rect
            painter.setBrush(QBrush(QColor(255, 255, 255, 20)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 10, 10)
            icon_color = QColor("white")

        # 2. Icon Drawing
        painter.setBrush(QBrush(icon_color))
        painter.setPen(Qt.PenStyle.NoPen)
        
        path = QPainterPath()
        center_x = width / 2
        center_y = height / 2
        size = width * 0.4 # icon size
        
        type_to_draw = self.icon_type
        # mapping text to type if needed
        txt = self.text()
        if "⏸" in txt: type_to_draw = "pause"
        elif "▶" in txt: type_to_draw = "play"
        
        if type_to_draw == "play":
            # Triangle
            # Center it visually (triangles look off-center if mathematical center)
            offset_x = size * 0.1 
            path.moveTo(center_x - size/2 + offset_x, center_y - size/2)
            path.lineTo(center_x + size/2 + offset_x, center_y)
            path.lineTo(center_x - size/2 + offset_x, center_y + size/2)
            path.closeSubpath()
            
        elif type_to_draw == "pause":
            # Two bars
            bar_w = size / 3
            path.addRect(center_x - size/2, center_y - size/2, bar_w, size)
            path.addRect(center_x + size/6, center_y - size/2, bar_w, size)
            
        elif type_to_draw == "next":
            # |>|
            # Triangle
            path.moveTo(center_x - size/2, center_y - size/2)
            path.lineTo(center_x + size/6, center_y)
            path.lineTo(center_x - size/2, center_y + size/2)
            # Bar
            path.addRect(center_x + size/6, center_y - size/2, size/3, size)
            
        elif type_to_draw == "prev":
            # |<|
            # Bar
            path.addRect(center_x - size/2, center_y - size/2, size/3, size)
            # Triangle
            path.moveTo(center_x + size/2, center_y - size/2)
            path.lineTo(center_x - size/6, center_y)
            path.lineTo(center_x + size/2, center_y + size/2)
            
        painter.drawPath(path)
