"""
date_widget.py — Editorial design: large zero-padded day number (display font)
with a mono sub-row showing WEEKDAY·MONTH on the left and YEAR on the right.
"""
import logging
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QLayout
from PyQt6.QtCore import QDate, Qt, QTimer
from PyQt6.QtGui import QFont
from base_widget import BaseWidget

log = logging.getLogger("date_widget")

# ── Helpers ───────────────────────────────────────────────────────────────────
# Qt's C++ layout engine can call resizeEvent MANY times synchronously from
# inside setFont/setFixedSize before Python can reset any boolean guard.  The
# safe pattern is to defer all layout-mutating work via QTimer.singleShot(0),
# which schedules it for the next event-loop iteration and breaks the C++ re-
# entrancy that was causing STATUS_STACK_BUFFER_OVERRUN (0xC0000409).


class DateWidget(BaseWidget):
    def __init__(self, theme_manager=None, config_manager=None):
        super().__init__(theme_manager, config_manager, widget_id="date")
        self.config = config_manager

        layout = QVBoxLayout()
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(0)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        self.setLayout(layout)

        # ── Big day number ────────────────────────────────────────────────
        self.day_label = QLabel()
        self.day_label.setObjectName("date_day_num")
        self.day_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.day_label)

        layout.addStretch()

        # ── Sub row: WEEKDAY·MON  |  YEAR ────────────────────────────────
        sub_row = QHBoxLayout()
        sub_row.setSpacing(0)

        self.sub_left = QLabel()
        self.sub_left.setObjectName("date_sub")
        self.sub_left.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.sub_right = QLabel()
        self.sub_right.setObjectName("date_sub")
        self.sub_right.setAlignment(Qt.AlignmentFlag.AlignRight)

        sub_row.addWidget(self.sub_left)
        sub_row.addStretch()
        sub_row.addWidget(self.sub_right)
        layout.addLayout(sub_row)

        self.apply_theme()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_date)
        self.timer.start(60000)
        self.update_date()
        self.resize(220, 120)

    # ── Responsive scaling ────────────────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        log.debug("resize → %dx%d", self.width(), self.height())
        if not getattr(self, '_scale_pending', False):
            self._scale_pending = True
            QTimer.singleShot(0, self._do_scale)

    def _do_scale(self):
        self._scale_pending = False
        self._scale_fonts()

    def _scale_fonts(self):
        h = self.height()
        w = self.width()
        log.debug("_scale_fonts  size=%dx%d", w, h)

        # DPI-aware point-size calculation.
        # On high-DPI displays (e.g. 150 % Windows scaling → 144 DPI) the naive
        # formula  pt = k × H  produces a font whose *pixel* height = pt × DPI/72
        # = k × H × DPI/72 > H, so the label's sizeHint exceeds the widget and
        # Qt auto-grows the window → infinite loop.
        # Fix: work in pixels first, then convert to points for the actual DPI.
        #   desired_px = fraction × available_px
        #   pt = desired_px × 72 / DPI
        dpi = max(72, self.logicalDpiY())   # 96 at 100 %, 144 at 150 %, 192 at 200 %

        fallback     = self.theme_manager.get_theme().get("font_family", "Segoe UI") if self.theme_manager else "Segoe UI"
        font_display = (self.config.get("font_family_time", fallback)
                        if self.config else fallback)
        font_mono    = (self.config.get("font_stats", "Consolas")
                        if self.config else "Consolas")

        # Day number: 55 % of available height (after margins + sub-row), in pixels
        available_h = max(30, h - 56)           # 36 px margins + ~20 px sub-row
        num_pt = max(16, int(available_h * 0.55 * 72 / dpi))
        self.day_label.setFont(QFont(font_display, num_pt))

        # Sub labels: 9 % of widget height in pixels → points
        sub_pt = max(7, int(h * 0.09 * 72 / dpi))
        sub_font = QFont(font_mono, sub_pt)
        for lbl in [self.sub_left, self.sub_right]:
            lbl.setFont(sub_font)

    def apply_theme(self):
        if not self.theme_manager:
            return

        t = self.get_theme_with_opacity()
        base_style = (
            f"QWidget#date {{"
            f"  background-color: {t['background']};"
            f"  border-radius: {t.get('border_radius', '22px')};"
            f"  border: 1px solid rgba(255, 255, 255, 36);"
            f"}}"
        )
        self.setStyleSheet(base_style + self.get_qss())

        fallback     = t.get("font_family", "Segoe UI")
        font_display = (self.config.get("font_family_time", fallback)
                        if self.config else fallback)
        font_mono    = (self.config.get("font_stats", "Consolas")
                        if self.config else "Consolas")

        # Big number — use a safe placeholder size; _scale_fonts will set the
        # correct DPI-aware size once the widget is laid out.  The old static
        # 52pt caused ~110 px at 150 % scaling, exceeding the initial 120 px
        # widget height and triggering a brief startup growth loop.
        dpi = max(72, self.logicalDpiY())
        available_h = max(30, (self.height() or 120) - 56)
        initial_pt  = max(16, int(available_h * 0.55 * 72 / dpi))
        self.day_label.setFont(QFont(font_display, initial_pt))
        self.day_label.setStyleSheet(
            f"color: {t.get('text_main', '#FAF7F2')}; background: transparent;")

        # Sub labels — mono, small (also DPI-aware)
        h = self.height() or 120
        sub_pt = max(7, int(h * 0.09 * 72 / dpi))
        sub_font = QFont(font_mono, sub_pt)
        for lbl in [self.sub_left, self.sub_right]:
            lbl.setFont(sub_font)
            lbl.setStyleSheet("color: #9A8F7C; background: transparent;")

        # If already visible and sized, re-run scale immediately
        if self.width() > 50 and not getattr(self, '_scale_pending', False):
            self._scale_pending = True
            QTimer.singleShot(0, self._do_scale)

    def update_date(self):
        today = QDate.currentDate()
        self.day_label.setText(str(today.day()).zfill(2))
        weekday = today.toString("ddd").upper()
        month   = today.toString("MMM").upper()
        self.sub_left.setText(f"{weekday} · {month}")
        self.sub_right.setText(str(today.year()))
