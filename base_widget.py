from PyQt6.QtWidgets import QWidget, QSizeGrip, QPushButton, QVBoxLayout, QGraphicsDropShadowEffect, QStyleOption, QStyle
from PyQt6.QtCore import Qt, QPoint, QTimer, QDate, QPropertyAnimation, QEasingCurve, QRectF
from PyQt6.QtGui import QColor, QPalette, QPainter, QPen


class CornerGrip(QSizeGrip):
    """
    Resize grip styled as concentric quarter-circle arcs at the bottom-right corner —
    mimicking macOS's subtle corner resize affordance. Inherits all QSizeGrip
    resize behaviour; only the painting is overridden.
    """
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        w = float(self.width())
        h = float(self.height())

        # Three concentric arcs centred at the bottom-right corner (w, h).
        # The grip is positioned so (w, h) lands exactly on the widget's corner.
        # Each arc spans 90° from 12 o'clock (top) CCW to 9 o'clock (left),
        # producing a ╯-shaped curve that hugs the corner and sweeps inward.
        # Radii kept small so arcs stay tight at the corner rather than
        # spreading across the grip.
        for i, r in enumerate([4, 7, 10]):
            alpha = 60 + i * 50          # 60, 110, 160 — brightest on the outermost arc
            pen = QPen(QColor(255, 255, 255, alpha))
            pen.setWidthF(1.3)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            rect = QRectF(w - r, h - r, 2 * r, 2 * r)
            painter.drawArc(rect, 90 * 16, 90 * 16)


class BaseWidget(QWidget):
    def __init__(self, theme_manager=None, config_manager=None, widget_id=None, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.config_manager = config_manager
        self.widget_id = widget_id
        if widget_id:
            self.setObjectName(widget_id)
        
        # Shared styling class for QSS targeting
        self.setProperty("class", "base_widget_frame")
        
        # Flags
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Dragging
        self.dragPosition = None
        
        # Resize grip — corner arc, shown only on hover (bottom-right, opposite close button)
        self.grip = CornerGrip(self)
        self.grip.resize(24, 24)
        self.grip.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.grip.hide()  # revealed in enterEvent

        # Close Button — macOS traffic light style: top-left, solid circle, no text
        self.btn_close = QPushButton(self)
        self.btn_close.setFixedSize(12, 12)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: #FF5F57;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #FF3B30;
            }
        """)
        self.btn_close.clicked.connect(self.hide)
        self.btn_close.hide() # Hidden by default
        
        # Mouse tracking for hover
        self.setMouseTracking(True)
        
    def paintEvent(self, event):
        # Critical for allowing Stylesheets to work on custom QWidgets with TranslucentBackground
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, p, self)
        
    def resizeEvent(self, event):
        rect = self.rect()
        # Grip bottom-right must land exactly on the widget corner so (w,h) in
        # CornerGrip.paintEvent correctly maps to the corner for arc centering.
        self.grip.move(rect.right() - 24, rect.bottom() - 24)
        # Traffic light position: top-left, 8px inset
        self.btn_close.move(rect.left() + 8, rect.top() + 8)
        self.btn_close.raise_()
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.btn_close.underMouse():
                return
            if self.config_manager and self.config_manager.get("locked", False):
                return
            self.dragPosition = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.dragPosition:
            if self.config_manager and self.config_manager.get("locked", False):
                return
            self.move(event.globalPosition().toPoint() - self.dragPosition)
            event.accept()

    def enterEvent(self, event):
        self.btn_close.show()
        self.btn_close.raise_()
        self.grip.show()
        self.grip.raise_()
        self.setProperty("hovered", True)
        self.style().unpolish(self)
        self.style().polish(self)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.btn_close.hide()
        self.grip.hide()
        self.setProperty("hovered", False)
        self.style().unpolish(self)
        self.style().polish(self)
        super().leaveEvent(event)

    def _stop_anim(self):
        if hasattr(self, "_anim") and self._anim and self._anim.state() == QPropertyAnimation.State.Running:
            self._anim.stop()

    def show_animated(self):
        self._stop_anim()
        super().show()
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(200)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()

    def hide_animated(self):
        self._stop_anim()
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(150)
        self._anim.setStartValue(self.windowOpacity())
        self._anim.setEndValue(0.0)
        self._anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self._anim.finished.connect(lambda: QWidget.hide(self))
        self._anim.start()
            
    def add_opacity_menu(self, parent_menu):
        from PyQt6.QtGui import QAction
        
        # Opacity Steps
        opacities = [
            (255, "100%"), (230, "90%"), (204, "80%"), 
            (179, "70%"), (153, "60%"), (128, "50%"), 
            (102, "40%"), (77, "30%"), (51, "20%"), 
            (25, "10%"), (13, "5%")
        ]
        
        # Current Opacity
        curr_alpha = 255
        if self.config_manager and self.widget_id:
            curr_alpha = self.config_manager.get_widget_opacity(self.widget_id)
            
        for val, label in opacities:
            act = QAction(label, self)
            act.setCheckable(True)
            if abs(curr_alpha - val) < 10: 
                act.setChecked(True)
            act.triggered.connect(lambda checked, v=val: self.set_opacity(v))
            parent_menu.addAction(act)

    def contextMenuEvent(self, event):
        from PyQt6.QtWidgets import QMenu, QApplication
        from PyQt6.QtGui import QAction, QCursor
        
        menu = QMenu(self)
        
        menu.addSeparator()
        
        # Opacity Submenu
        if self.config_manager and self.widget_id:
            opacity_menu = QMenu("Opacity", self)
            self.add_opacity_menu(opacity_menu)
            menu.addMenu(opacity_menu)
            menu.addSeparator()
        
        action_hide = QAction("Hide", self)
        action_hide.triggered.connect(self.hide_animated)
        menu.addAction(action_hide)
        
        menu.addSeparator()
        
        action_exit = QAction("Exit Application", self)
        action_exit.triggered.connect(QApplication.instance().quit)
        menu.addAction(action_exit)
        
        menu.exec(event.globalPos())

    def get_theme_with_opacity(self):
        # Helper to get theme but override alpha with this widget's specific opacity setting
        if not self.theme_manager or not self.config_manager:
            return {}
        t = self.theme_manager.get_theme().copy() # Copy to avoid mutating global theme cache

        # Get specific opacity for this widget
        alpha = self.config_manager.get_widget_opacity(self.widget_id)
        
        # Modify background color alpha
        bg = t.get("background", "rgba(0,0,0,180)")
        
        if "rgba" in bg:
            # Simple string replace for rgba(r,g,b,a) -> replace last part
            # This is a bit hacky but works if format is consistent
            try:
                parts = bg.replace("rgba(", "").replace(")", "").split(",")
                if len(parts) == 4:
                     # Reconstruct with new alpha (0-255 scaled to 0-1 if needed? NO, CSS rgba uses 0-1 for alpha usually, but QColor uses 0-255)
                     # Wait, my config saves 0-255. 
                     # Stylesheets usually want 0-255 if using rgba(r,g,b,a) where a is 0-255? 
                     # Actually standard CSS is 0-1. But Qt Stylesheets support rgba(r,g,b,alpha) where alpha is 0.0-1.0 OR 0-255?
                     # Let's check what verify what my themes use.
                     # "rgba(0, 0, 0, 180)" -> 180 looks like 0-255 range. Qt qss supports 0-255 for alpha if it's not 0-1 float.
                     
                     parts[3] = f" {alpha}" # Space for safety
                     t["background"] = f"rgba({parts[0]},{parts[1]},{parts[2]},{parts[3]})"
            except:
                pass # Fallback to theme default on parse error
        
        return t

    def get_qss(self):
        if self.theme_manager:
            return self.theme_manager.get_stylesheet()
        return ""

    def set_opacity(self, val):
        if self.config_manager and self.widget_id:
            self.config_manager.set_widget_opacity(self.widget_id, val)
            self.apply_theme()

    def apply_shadow(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        widget.setGraphicsEffect(shadow)
