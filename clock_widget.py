"""
clock_widget.py — Editorial design: circular world-ring with painted ticks
and a thin seconds arc in the accent colour.
"""
import math
from datetime import datetime
from zoneinfo import ZoneInfo

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QLayout
from PyQt6.QtCore import QTimer, Qt, QRectF
from PyQt6.QtGui import QFont, QPainter, QPen, QColor
from base_widget import BaseWidget


class ClockWidget(BaseWidget):
    def __init__(self, clock_id, timezone="Local", label="Local Time",
                 theme_manager=None, config_manager=None):
        super().__init__(theme_manager, config_manager,
                         widget_id=f"clock_{clock_id}")
        self.clock_id = clock_id
        self.timezone  = timezone
        self.label_text = label
        self.config    = config_manager

        self._sec = 0

        # ── Layout: labels vertically centred inside the ring ─────────────
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        self.setLayout(layout)

        layout.addStretch()

        self.time_label = QLabel("00:00")
        self.time_label.setObjectName("clock_time")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.time_label)

        self.loc_label = QLabel(self.label_text.upper())
        self.loc_label.setObjectName("clock_label")
        self.loc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.loc_label)

        self.date_label = QLabel("")
        self.date_label.setObjectName("clock_date")
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.date_label)

        layout.addStretch()

        self.apply_theme()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        self.update_time()
        self.resize(320, 320)

    # ── Ring + ticks + seconds-arc ────────────────────────────────────────

    def paintEvent(self, event):
        super().paintEvent(event)   # draw QSS background first

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = self.width()  / 2
        cy = self.height() / 2
        R  = min(cx, cy) * 0.875   # ≈ 140 px for a 320 px widget

        t = self.theme_manager.get_theme() if self.theme_manager else {}
        line_col    = QColor(255, 255, 255, 23)   # --line
        line_strong = QColor(255, 255, 255, 41)   # --line-strong
        accent_str  = t.get("accent", "#E8A857")
        accent_col  = QColor(accent_str)

        # ── Outer ring circle ──
        p.setPen(QPen(line_col, 1.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(cx - R, cy - R, R * 2, R * 2))

        # ── 24-hour ticks ──
        for h in range(24):
            angle   = -math.pi / 2 + (h / 24) * math.pi * 2
            x1      = cx + math.cos(angle) * R
            y1      = cy + math.sin(angle) * R
            major   = (h % 6 == 0)
            inner_r = R - 10 if major else R - 5
            x2      = cx + math.cos(angle) * inner_r
            y2      = cy + math.sin(angle) * inner_r
            p.setPen(QPen(line_strong if major else line_col,
                          1.2 if major else 0.6))
            p.drawLine(int(x1), int(y1), int(x2), int(y2))

        # ── Seconds arc (accent colour, sweeps clockwise from 12 o'clock) ──
        sec = self._sec
        if sec > 0:
            arc_pen = QPen(accent_col, 2.0,
                           Qt.PenStyle.SolidLine,
                           Qt.PenCapStyle.RoundCap)
            p.setPen(arc_pen)
            arc_rect   = QRectF(cx - R, cy - R, R * 2, R * 2)
            span_angle = -int((sec / 60) * 360 * 16)   # negative = clockwise
            p.drawArc(arc_rect, 90 * 16, span_angle)

        p.end()

    # ── Theme ─────────────────────────────────────────────────────────────

    def apply_theme(self):
        if not self.theme_manager:
            return

        t = self.get_theme_with_opacity()
        base_style = (
            f"QWidget#clock_{self.clock_id} {{"
            f"  background-color: {t['background']};"
            f"  border-radius: {t.get('border_radius', '22px')};"
            f"  border: 1px solid rgba(255, 255, 255, 36);"
            f"}}"
        )
        self.setStyleSheet(base_style + self.get_qss())

        font_time  = (self.config.get("font_family_time",  t.get("font_family", "Segoe UI"))
                      if self.config else t.get("font_family", "Segoe UI"))
        font_label = (self.config.get("font_family_label", t.get("font_family", "Segoe UI"))
                      if self.config else t.get("font_family", "Segoe UI"))
        font_mono  = (self.config.get("font_stats", "Consolas")
                      if self.config else "Consolas")

        # Large time — display font, normal weight
        tf = QFont(font_time, 48)
        tf.setWeight(QFont.Weight.Normal)
        self.time_label.setFont(tf)
        self.time_label.setStyleSheet(
            f"color: {t.get('text_main', '#FAF7F2')}; background: transparent;")

        # City — small-caps treatment via tracking
        self.loc_label.setFont(QFont(font_label, 9, QFont.Weight.Medium))
        self.loc_label.setStyleSheet("color: #9A8F7C; background: transparent;")

        # Date — mono
        self.date_label.setFont(QFont(font_mono, 8))
        self.date_label.setStyleSheet("color: #9A8F7C; background: transparent;")

        self.update()   # repaint ring

    # ── Time update ───────────────────────────────────────────────────────

    def update_time(self):
        if self.timezone == "Local":
            now = datetime.now()
        else:
            try:
                now = datetime.now(ZoneInfo(self.timezone))
            except Exception:
                now = datetime.now()

        self._sec = now.second
        self.time_label.setText(now.strftime("%H:%M"))
        self.date_label.setText(now.strftime("%b %d").upper())
        self.update()   # repaint arc
