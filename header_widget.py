"""
header_widget.py — Editorial design: giant italic day name that auto-scales
to widget width, with an ISO-date / Week·Day mono sub-row.
"""
import logging
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy, QLayout
from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6.QtGui import QFont, QFontMetrics
from base_widget import BaseWidget

log = logging.getLogger("header_widget")


class HeaderWidget(BaseWidget):
    def __init__(self, theme_manager=None, config_manager=None):
        super().__init__(theme_manager, config_manager, widget_id="header")
        self.config = config_manager
        self._day_font_size = 80   # refined by first _do_fit call
        self._fit_pending  = False # deferred-fit gate

        layout = QVBoxLayout()
        layout.setContentsMargins(36, 24, 32, 24)
        layout.setSpacing(0)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        self.setLayout(layout)

        # ── Giant italic day name ─────────────────────────────────────────
        self.label = QLabel("Tuesday.")
        self.label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.label.setObjectName("header_label")
        # Ignored horizontal policy: the layout engine completely ignores this
        # label's sizeHint when computing the layout's preferred width.  Without
        # this, Qt nudges the window 1-2 px wider each time the font's advance
        # width is within rounding distance of target_w, causing slow-motion
        # runaway expansion (560 → 612 px observed in logs).
        self.label.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.label.setMinimumWidth(0)
        layout.addWidget(self.label, stretch=1)

        layout.addStretch()

        # ── Sub row: ISO date  |  Week · Day ─────────────────────────────
        sub_row = QHBoxLayout()
        sub_row.setSpacing(0)

        self.sub_left = QLabel()
        self.sub_left.setObjectName("header_sub_left")
        self.sub_left.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)

        self.sub_right = QLabel()
        self.sub_right.setObjectName("header_sub_right")
        self.sub_right.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)

        sub_row.addWidget(self.sub_left)
        sub_row.addStretch()
        sub_row.addWidget(self.sub_right)
        layout.addLayout(sub_row)

        self.apply_theme()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_content)
        self.timer.start(60000)
        self.update_content()
        self.resize(560, 220)

    # ── Auto-fit ──────────────────────────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        log.debug("resize → %dx%d", self.width(), self.height())
        if not getattr(self, '_fit_pending', False):
            self._fit_pending = True
            QTimer.singleShot(0, self._do_fit)

    def _do_fit(self):
        self._fit_pending = False
        self._fit_day_label()

    def _safe_fit(self):
        """Schedule _fit_day_label (deferred to break C++ resize re-entrancy)."""
        if not getattr(self, '_fit_pending', False):
            self._fit_pending = True
            QTimer.singleShot(0, self._do_fit)

    def _fit_day_label(self):
        """Binary-search the largest italic point size that fits widget width,
        then cap by height so the font never drives the layout minimum taller
        than the current widget (which would trigger the runaway-expansion loop
        on high-DPI displays)."""
        text = self.label.text()
        if not text:
            return
        # margins: 36 left + 32 right = 68.  Extra 16 px accounts for QLabel's
        # internal frame padding that horizontalAdvance() does not include —
        # without this buffer the label's sizeHint slightly exceeds target_w
        # and the layout creep-expands the window 1 px at a time.
        target_w = max(50, self.width() - 84)

        font_name = (self.config.get("font_header", "Georgia")
                     if self.config else "Georgia")

        lo, hi, best = 8, 150, 8
        while lo <= hi:
            mid = (lo + hi) // 2
            f   = QFont(font_name, mid)
            f.setItalic(True)
            if QFontMetrics(f).horizontalAdvance(text) <= target_w:
                best = mid
                lo   = mid + 1
            else:
                hi   = mid - 1

        # Also cap by height: allow at most ~72 % of available height in pixels.
        # DPI-aware: pt = desired_px × 72 / DPI.
        dpi = max(72, self.logicalDpiY())
        available_h = max(20, self.height() - 48)   # 24 top + 24 bottom margins
        max_pt_by_height = max(8, int(available_h * 0.72 * 72 / dpi))
        best = min(best, max_pt_by_height)

        log.debug("_fit_day_label  w=%d target_w=%d best_pt=%d (height_cap=%d)",
                  self.width(), target_w, best, max_pt_by_height)
        self._day_font_size = best
        f = QFont(font_name, best)
        f.setItalic(True)
        self.label.setFont(f)

    # ── Theme ─────────────────────────────────────────────────────────────

    def apply_theme(self):
        if not self.theme_manager:
            return

        t = self.get_theme_with_opacity()
        base_style = (
            f"QWidget#header {{"
            f"  background-color: {t['background']};"
            f"  border-radius: {t.get('border_radius', '22px')};"
            f"  border: 1px solid rgba(255, 255, 255, 36);"
            f"}}"
        )
        self.setStyleSheet(base_style + self.get_qss())

        font_name = (self.config.get("font_header", t.get("font_family", "Georgia"))
                     if self.config else t.get("font_family", "Georgia"))
        font_mono = (self.config.get("font_stats", "Consolas")
                     if self.config else "Consolas")

        f = QFont(font_name, self._day_font_size)
        f.setItalic(True)
        self.label.setFont(f)
        self.label.setStyleSheet(
            f"color: {t.get('text_main', '#FAF7F2')}; background: transparent;")

        sub_font = QFont(font_mono, 9)
        for lbl in [self.sub_left, self.sub_right]:
            lbl.setFont(sub_font)
            lbl.setStyleSheet("color: #9A8F7C; background: transparent;")

        self._safe_fit()

    # ── Content ───────────────────────────────────────────────────────────

    def update_content(self):
        today    = QDate.currentDate()
        self.label.setText(today.toString("dddd") + ".")

        iso_date    = today.toString("yyyy-MM-dd")
        wn_result   = today.weekNumber()   # PyQt6 returns (weekNum, yearNum)
        week_num    = wn_result[0] if isinstance(wn_result, (tuple, list)) else wn_result
        day_of_year = today.dayOfYear()

        self.sub_left.setText(f"Today  ·  {iso_date}")
        self.sub_right.setText(f"W{str(week_num).zfill(2)}  ·  {day_of_year}/365")

        self._safe_fit()
