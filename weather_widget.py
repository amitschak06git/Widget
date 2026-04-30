"""
weather_widget.py — Editorial design: compact view shows a next-6h precipitation
bar chart; expanded view shows hourly chips + 5-day forecast.
"""
import threading

from PyQt6.QtWidgets import (
    QLabel, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QFrame, QSizePolicy, QLayout
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QRectF
from PyQt6.QtGui import QFont, QPainter, QColor
from base_widget import BaseWidget
import weather_service

COMPACT_HEIGHT  = 148
EXPANDED_HEIGHT = 530
WIDGET_WIDTH    = 340


# ── Precipitation bar chart ────────────────────────────────────────────────

class PrecipBarsWidget(QWidget):
    """Next-6h precipitation bars — ink-4/blue/accent coloured, 22 px area."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        self._precip = []        # list of mm values (up to 6)
        self._labels = ["NOW", "+1H", "+2H", "+3H", "+4H", "+5H"]

    def set_data(self, precip_list):
        """Accepts a list of up to 6 mm-per-hour precipitation values."""
        self._precip = precip_list[:6]
        self.update()

    def paintEvent(self, event):
        if not self._precip:
            return

        p   = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w   = self.width()
        h   = self.height()
        n   = len(self._precip)
        if n == 0:
            p.end()
            return

        max_p    = max(self._precip) if max(self._precip) > 0 else 1.0
        bar_area = h - 10           # bottom 10 px for (tiny) labels
        gap      = 4
        bar_w    = max(4, (w - gap * (n - 1)) / n)

        dry_col  = QColor(97,  88, 72,  160)   # ink-4
        wet_col  = QColor(100, 160, 220, 200)  # blue
        peak_col = QColor(232, 168, 87,  255)  # accent

        for i, mm in enumerate(self._precip):
            bx  = int(i * (bar_w + gap))
            if mm > 0.1:
                ratio = mm / max_p
                bh    = max(3, int(ratio * (bar_area - 4)))
                by    = bar_area - bh
                col   = peak_col if (mm == max_p and mm > 0.1) else wet_col
            else:
                bh = 2
                by = bar_area - 2
                col = dry_col

            p.fillRect(bx, by, max(2, int(bar_w)), bh, col)

        p.end()


# ── Weather widget ─────────────────────────────────────────────────────────

class WeatherWidget(BaseWidget):
    _data_ready = pyqtSignal()

    def __init__(self, theme_manager=None, config_manager=None):
        super().__init__(theme_manager, config_manager, widget_id="weather")
        self.config = config_manager
        self._expanded    = False
        self._weather_data = None

        root = QVBoxLayout()
        root.setContentsMargins(20, 18, 20, 16)
        root.setSpacing(0)
        root.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        self.setLayout(root)

        # ── Compact header ────────────────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(12)

        self.lbl_temp = QLabel("—°")
        self.lbl_temp.setObjectName("weather_temp")

        meta_col = QVBoxLayout()
        meta_col.setSpacing(2)
        loc_text = (self.config.get("weather_location_name", "Set location")
                    if self.config else "Set location")
        self.lbl_location  = QLabel(loc_text)
        self.lbl_location.setObjectName("weather_location")
        self.lbl_condition = QLabel("—")
        self.lbl_condition.setObjectName("weather_condition")
        meta_col.addWidget(self.lbl_location)
        meta_col.addWidget(self.lbl_condition)

        self.lbl_emoji = QLabel("—")
        self.lbl_emoji.setObjectName("weather_emoji")
        self.lbl_emoji.setFixedWidth(40)
        self.lbl_emoji.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_expand = QPushButton("▾")
        self.btn_expand.setObjectName("weather_expand_btn")
        self.btn_expand.setFixedSize(32, 32)
        self.btn_expand.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_expand.clicked.connect(self.toggle_expand)

        header.addWidget(self.lbl_temp)
        header.addLayout(meta_col)
        header.addStretch()
        header.addWidget(self.lbl_emoji)
        header.addWidget(self.btn_expand)
        root.addLayout(header)

        # ── Next-6h precipitation bars (always visible in compact) ────────
        root.addSpacing(10)
        self.precip_bars = PrecipBarsWidget()
        root.addWidget(self.precip_bars)

        # ── Expandable section ────────────────────────────────────────────
        self.expanded_widget = QWidget()
        self.expanded_widget.setVisible(False)
        self.expanded_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        exp = QVBoxLayout()
        exp.setContentsMargins(0, 10, 0, 4)
        exp.setSpacing(10)
        self.expanded_widget.setLayout(exp)

        exp.addWidget(self._divider())
        exp.addWidget(self._section_label("HOURLY"))

        self.hourly_container = QWidget()
        self.hourly_row = QHBoxLayout()
        self.hourly_row.setSpacing(0)
        self.hourly_row.setContentsMargins(0, 0, 0, 0)
        self.hourly_container.setLayout(self.hourly_row)
        exp.addWidget(self.hourly_container)

        exp.addWidget(self._divider())
        exp.addWidget(self._section_label("5-DAY FORECAST"))

        self.forecast_container = QWidget()
        self.forecast_layout = QVBoxLayout()
        self.forecast_layout.setSpacing(6)
        self.forecast_layout.setContentsMargins(0, 0, 0, 0)
        self.forecast_container.setLayout(self.forecast_layout)
        exp.addWidget(self.forecast_container)

        exp.addWidget(self._divider())

        attr = QLabel("Weather data: MET Norway / yr.no")
        attr.setObjectName("weather_attr")
        attr.setAlignment(Qt.AlignmentFlag.AlignRight)
        exp.addWidget(attr)

        root.addWidget(self.expanded_widget)

        self._data_ready.connect(self._update_ui)

        self.apply_theme()
        self.setMinimumHeight(COMPACT_HEIGHT)
        self.setMaximumHeight(COMPACT_HEIGHT)
        self.resize(WIDGET_WIDTH, COMPACT_HEIGHT)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(30 * 60 * 1000)
        self.refresh()

    # ── Helpers ───────────────────────────────────────────────────────────

    def _divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(
            "color: rgba(255,255,255,0.06);"
            "background-color: rgba(255,255,255,0.06);"
            "max-height: 1px;")
        return line

    def _section_label(self, text):
        lbl = QLabel(text)
        lbl.setObjectName("weather_section_label")
        return lbl

    # ── Expand / collapse ─────────────────────────────────────────────────

    def toggle_expand(self):
        if self._expanded:
            self._collapse()
        else:
            self._expand()

    def _expand(self):
        self._expanded = True
        self.btn_expand.setText("▴")
        self.expanded_widget.setVisible(True)
        self._animate_height(COMPACT_HEIGHT, EXPANDED_HEIGHT)

    def _collapse(self):
        self._expanded = False
        self.btn_expand.setText("▾")
        anim = self._animate_height(self.height(), COMPACT_HEIGHT)
        anim.finished.connect(lambda: self.expanded_widget.setVisible(False))

    def _animate_height(self, start: int, end: int):
        for attr in ("_h_anim", "_h_anim2"):
            if hasattr(self, attr):
                a = getattr(self, attr)
                if a.state() == QPropertyAnimation.State.Running:
                    a.stop()

        self._h_anim = QPropertyAnimation(self, b"minimumHeight")
        self._h_anim.setDuration(280)
        self._h_anim.setStartValue(start)
        self._h_anim.setEndValue(end)
        self._h_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._h_anim2 = QPropertyAnimation(self, b"maximumHeight")
        self._h_anim2.setDuration(280)
        self._h_anim2.setStartValue(start)
        self._h_anim2.setEndValue(end)
        self._h_anim2.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._h_anim.start()
        self._h_anim2.start()
        return self._h_anim

    # ── Data fetch ────────────────────────────────────────────────────────

    def refresh(self):
        lat = self.config.get("weather_lat") if self.config else None
        lon = self.config.get("weather_lon") if self.config else None
        if lat is None or lon is None:
            self.lbl_condition.setText("Set location in Settings")
            return
        lat, lon = float(lat), float(lon)
        if lat == 0.0 and lon == 0.0:
            self.lbl_condition.setText("Set location in Settings → Weather")
            return
        threading.Thread(
            target=self._fetch, args=(lat, lon), daemon=True).start()

    def _fetch(self, lat: float, lon: float):
        self._weather_data = weather_service.fetch_forecast(lat, lon)
        self._data_ready.emit()

    def _update_ui(self):
        if not self._weather_data:
            self.lbl_condition.setText("Unable to fetch — check connection")
            return

        current = weather_service.parse_current(self._weather_data)
        if current:
            self.lbl_emoji.setText(current["emoji"])
            self.lbl_temp.setText(f"{current['temp']}°")

            unit     = self.config.get("wind_unit", "kmh") if self.config else "kmh"
            wind_fmt = weather_service.format_wind(current["wind"], unit)
            wind_str = f"{current['wind_arrow']} {current['wind_dir']}  {wind_fmt}"
            if current["wind_gust"] > current["wind"] + 1:
                gust_fmt = weather_service.format_wind(current["wind_gust"], unit)
                wind_str += f"  (gusts {gust_fmt})"
            self.lbl_condition.setText(
                f"{current['description']}  ·  {wind_str}  ·  {current['humidity']}% hum"
            )

        self._rebuild_precip_bars()
        self._rebuild_hourly()
        self._rebuild_forecast()

    # ── Precip bars (compact, next 6 h) ──────────────────────────────────

    def _rebuild_precip_bars(self):
        hourly = weather_service.parse_hourly(self._weather_data, hours=6)
        self.precip_bars.set_data([h.get("precip", 0.0) for h in hourly])

    # ── Hourly section ────────────────────────────────────────────────────

    def _rebuild_hourly(self):
        while self.hourly_row.count():
            item = self.hourly_row.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        t         = self.theme_manager.get_theme() if self.theme_manager else {}
        main_color = t.get("text_main",      "white")
        sub_color  = t.get("text_secondary", "rgba(255,255,255,0.55)")
        font_name  = (self.config.get("font_family_label", t.get("font_family", "Segoe UI"))
                      if self.config else t.get("font_family", "Segoe UI"))

        for h in weather_service.parse_hourly(self._weather_data, hours=10):
            col_widget = QWidget()
            col_widget.setFixedWidth(32)
            col = QVBoxLayout(col_widget)
            col.setSpacing(2)
            col.setContentsMargins(0, 0, 0, 0)
            col.setAlignment(Qt.AlignmentFlag.AlignHCenter)

            lbl_hr = QLabel(h["hour"])
            lbl_hr.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_hr.setFont(QFont(font_name, 8))
            lbl_hr.setStyleSheet(f"color: {sub_color}; background: transparent;")

            lbl_ico = QLabel(h["emoji"])
            lbl_ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_ico.setFont(QFont(font_name, 12))

            lbl_tmp = QLabel(f"{h['temp']}°")
            lbl_tmp.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_tmp.setFont(QFont(font_name, 9, QFont.Weight.Medium))
            lbl_tmp.setStyleSheet(f"color: {main_color}; background: transparent;")

            unit       = self.config.get("wind_unit", "kmh") if self.config else "kmh"
            wind_short = weather_service.format_wind(h["wind"], unit, short=True)
            lbl_wind   = QLabel(f"{h['wind_arrow']} {wind_short}")
            lbl_wind.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_wind.setFont(QFont(font_name, 7))
            lbl_wind.setStyleSheet(f"color: {sub_color}; background: transparent;")

            if h["precip"] > 0.1:
                lbl_pr = QLabel(f"{h['precip']:.1f}")
                lbl_pr.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_pr.setFont(QFont(font_name, 7))
                lbl_pr.setStyleSheet("color: #4FC3F7; background: transparent;")
                col.addWidget(lbl_pr)

            col.addWidget(lbl_hr)
            col.addWidget(lbl_ico)
            col.addWidget(lbl_tmp)
            col.addWidget(lbl_wind)
            self.hourly_row.addWidget(col_widget)

        self.hourly_row.addStretch()

    # ── 5-day forecast ────────────────────────────────────────────────────

    def _rebuild_forecast(self):
        while self.forecast_layout.count():
            item = self.forecast_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        t         = self.theme_manager.get_theme() if self.theme_manager else {}
        main_color = t.get("text_main",      "white")
        sub_color  = t.get("text_secondary", "rgba(255,255,255,0.55)")
        font_name  = (self.config.get("font_family_label", t.get("font_family", "Segoe UI"))
                      if self.config else t.get("font_family", "Segoe UI"))

        for d in weather_service.parse_daily(self._weather_data, days=5):
            row_w = QWidget()
            row   = QHBoxLayout(row_w)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(8)

            lbl_day = QLabel(d["day"])
            lbl_day.setFixedWidth(32)
            lbl_day.setFont(QFont(font_name, 10, QFont.Weight.Medium))
            lbl_day.setStyleSheet(f"color: {main_color}; background: transparent;")

            lbl_ico = QLabel(d["emoji"])
            lbl_ico.setFont(QFont(font_name, 14))
            lbl_ico.setFixedWidth(26)

            lbl_min = QLabel(f"{d['min']}°")
            lbl_min.setFont(QFont(font_name, 10))
            lbl_min.setStyleSheet(f"color: {sub_color}; background: transparent;")
            lbl_min.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            lbl_sep = QLabel("/")
            lbl_sep.setFont(QFont(font_name, 10))
            lbl_sep.setStyleSheet(f"color: {sub_color}; background: transparent;")

            lbl_max = QLabel(f"{d['max']}°")
            lbl_max.setFont(QFont(font_name, 10, QFont.Weight.Medium))
            lbl_max.setStyleSheet(f"color: {main_color}; background: transparent;")

            row.addWidget(lbl_day)
            row.addWidget(lbl_ico)
            row.addStretch()
            row.addWidget(lbl_min)
            row.addWidget(lbl_sep)
            row.addWidget(lbl_max)
            self.forecast_layout.addWidget(row_w)

    # ── Theme ─────────────────────────────────────────────────────────────

    def apply_theme(self):
        if not self.theme_manager:
            return
        t = self.get_theme_with_opacity()
        if not t:
            return

        base = (
            f"QWidget#weather {{"
            f"  background-color: {t['background']};"
            f"  border-radius: {t.get('border_radius', '22px')};"
            f"  border: 1px solid rgba(255, 255, 255, 36);"
            f"}}"
        )
        self.setStyleSheet(base + self.get_qss())

        font  = (self.config.get("font_family_time", t["font_family"])
                 if self.config else t["font_family"])
        font_ui = (self.config.get("font_family_label", t["font_family"])
                   if self.config else t["font_family"])

        temp_font = QFont(font, 48)
        temp_font.setWeight(QFont.Weight.Normal)
        self.lbl_temp.setFont(temp_font)
        self.lbl_temp.setStyleSheet(
            f"color: {t['text_main']}; background: transparent;")

        self.lbl_emoji.setFont(QFont(font, 22))

        self.lbl_location.setFont(QFont(font_ui, 12, QFont.Weight.Medium))
        self.lbl_location.setStyleSheet(
            f"color: {t['text_main']}; background: transparent;")

        self.lbl_condition.setFont(QFont(font_ui, 9))
        self.lbl_condition.setStyleSheet(
            f"color: {t['text_secondary']}; background: transparent;")
