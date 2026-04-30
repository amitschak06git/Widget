"""
calendar_widget.py — Editorial design: month name in display font (28 pt),
year in mono beside it, today is an amber pill with a glow shadow, and a
mini agenda section below the grid shows today's events (real or mock).

Calendar source priority:
  1. Google Calendar (token.json present) — fetched in a background thread
  2. Mock events — shown when not connected
"""
import calendar
import threading
import datetime as dt

from PyQt6.QtCore import QTimer, Qt, QDate, pyqtSignal
from PyQt6.QtWidgets import (
    QLabel, QGridLayout, QVBoxLayout, QHBoxLayout,
    QWidget, QSizePolicy, QMenu, QFrame, QLayout
)
from PyQt6.QtGui import QFont, QColor, QAction
from base_widget import BaseWidget


# ── Fallback mock events ──────────────────────────────────────────────────
_MOCK_EVENTS = [
    {"time": "09:30", "title": "Design review",     "past": True},
    {"time": "11:00", "title": "Focus — widget v2"},
    {"time": "14:15", "title": "Sync"},
    {"time": "18:00", "title": "Run  ·  5 km"},
]


def _format_event_time(ev_dt):
    """Format a datetime as HH:MM string."""
    try:
        return ev_dt.strftime("%H:%M")
    except Exception:
        return ""


def _is_past(ev_dt):
    """Return True if the event's start time has passed today."""
    try:
        now = dt.datetime.now()
        return ev_dt.date() == now.date() and ev_dt < now
    except Exception:
        return False


class CalendarWidget(BaseWidget):
    _events_ready = pyqtSignal()

    def __init__(self, theme_manager=None, config_manager=None):
        super().__init__(theme_manager, config_manager, widget_id="calendar")
        self.config = config_manager

        # Root grid lets the big-today watermark sit behind the content
        self._live_events = None   # None = not yet fetched; [] = fetched but empty

        self.root_layout = QGridLayout()
        self.root_layout.setContentsMargins(20, 20, 20, 20)
        self.root_layout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        self.setLayout(self.root_layout)

        # ── Layer 0: watermark ────────────────────────────────────────────
        self.lbl_big_today = QLabel()
        self.lbl_big_today.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_big_today.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.root_layout.addWidget(self.lbl_big_today, 0, 0)

        # ── Layer 1: calendar content ─────────────────────────────────────
        self.calendar_container = QWidget()
        cal_layout = QVBoxLayout()
        cal_layout.setContentsMargins(0, 0, 0, 0)
        cal_layout.setSpacing(10)
        self.calendar_container.setLayout(cal_layout)

        # Month header row: big month name + year (mono)
        head_row = QHBoxLayout()
        head_row.setSpacing(8)
        head_row.setAlignment(Qt.AlignmentFlag.AlignBottom)

        self.lbl_month = QLabel()
        self.lbl_month.setObjectName("calendar_month")
        self.lbl_month.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.lbl_year = QLabel()
        self.lbl_year.setObjectName("calendar_year")
        self.lbl_year.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)

        head_row.addWidget(self.lbl_month)
        head_row.addWidget(self.lbl_year)
        head_row.addStretch()
        cal_layout.addLayout(head_row)

        # Day-of-week grid
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(4)
        cal_layout.addLayout(self.grid_layout)

        # Divider above agenda
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(
            "color: rgba(255,255,255,0.06);"
            "background-color: rgba(255,255,255,0.06);"
            "max-height: 1px;")
        cal_layout.addWidget(divider)

        # Agenda section
        self.agenda_layout = QVBoxLayout()
        self.agenda_layout.setSpacing(8)
        self.agenda_layout.setContentsMargins(0, 0, 0, 0)
        cal_layout.addLayout(self.agenda_layout)

        self.root_layout.addWidget(self.calendar_container, 0, 0)

        self.day_labels = []

        self._events_ready.connect(self.update_calendar)

        self.apply_theme()
        self.update_calendar()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh_events)
        self.timer.start(5 * 60 * 1000)   # re-fetch every 5 minutes
        self._refresh_events()

        self.resize(320, 420)

    # ── Event fetching ────────────────────────────────────────────────────

    def _refresh_events(self):
        """Fetch events in a background thread, then signal the UI."""
        threading.Thread(target=self._fetch_events, daemon=True).start()

    def _fetch_events(self):
        try:
            from google_calendar import GoogleCalendarProvider, GOOGLE_DEPS_INSTALLED
            import os
            creds_path = self.config.get("calendar_credentials_path", "credentials.json") if self.config else "credentials.json"
            token_path = "token.json"
            if GOOGLE_DEPS_INSTALLED and os.path.exists(token_path):
                provider = GoogleCalendarProvider(creds_path)
                now = dt.datetime.utcnow()
                start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end   = start + dt.timedelta(days=1)
                events = provider.get_events(start, end)
                self._live_events = [
                    {
                        "time":  _format_event_time(ev.start),
                        "title": ev.title,
                        "past":  _is_past(ev.start),
                    }
                    for ev in events
                ]
            else:
                self._live_events = None   # stay on mock
        except Exception as e:
            print(f"[Calendar] fetch error: {e}")
            self._live_events = None
        self._events_ready.emit()

    # ── Resize: scale watermark font ──────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not getattr(self, '_watermark_pending', False):
            self._watermark_pending = True
            QTimer.singleShot(0, self._do_watermark)

    def _do_watermark(self):
        self._watermark_pending = False
        self._adjust_watermark()

    def _adjust_watermark(self):
        h  = self.height()
        sz = max(10, int(h * 0.45))
        f  = self.lbl_big_today.font()
        if f.pointSize() != sz:
            f.setPointSize(sz)
            self.lbl_big_today.setFont(f)
        today = str(QDate.currentDate().day())
        if self.lbl_big_today.text() != today:
            self.lbl_big_today.setText(today)

    # ── Context menu ──────────────────────────────────────────────────────

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        wm_menu  = QMenu("Watermark Opacity", self)
        wm_levels = [
            (0.0, "Hidden"),
            (0.05, "5%"),
            (0.10, "10%"),
            (0.20, "20%"),
            (0.40, "40%"),
        ]
        current_wm = (self.config.get_value("calendar_watermark_opacity", 0.1)
                      if self.config else 0.1)
        for val, label in wm_levels:
            act = QAction(label, self)
            act.setCheckable(True)
            if abs(current_wm - val) < 0.01:
                act.setChecked(True)
            act.triggered.connect(
                lambda checked, v=val: self.set_watermark_opacity(v))
            wm_menu.addAction(act)
        menu.addMenu(wm_menu)

        opacity_menu = QMenu("Widget Opacity", self)
        self.add_opacity_menu(opacity_menu)
        menu.addMenu(opacity_menu)

        menu.addSeparator()
        from PyQt6.QtWidgets import QApplication
        exit_act = QAction("Exit Application", self)
        exit_act.triggered.connect(QApplication.instance().quit)
        menu.addAction(exit_act)
        menu.exec(event.globalPos())

    def set_watermark_opacity(self, val):
        if self.config:
            self.config.set_value("calendar_watermark_opacity", val)
        self.apply_theme()

    # ── Theme ─────────────────────────────────────────────────────────────

    def apply_theme(self):
        if not self.theme_manager:
            return
        t = self.get_theme_with_opacity()

        base_style = (
            f"QWidget#calendar {{"
            f"  background-color: {t['background']};"
            f"  border-radius: {t.get('border_radius', '22px')};"
            f"  border: 1px solid rgba(255, 255, 255, 36);"
            f"}}"
        )
        self.setStyleSheet(base_style + self.get_qss())

        font_display = (self.config.get("font_calendar", t.get("font_family", "Segoe UI"))
                        if self.config else t.get("font_family", "Segoe UI"))
        font_mono    = (self.config.get("font_stats", "Consolas")
                        if self.config else "Consolas")

        # Month — display font, large
        self.lbl_month.setFont(QFont(font_display, 22))
        self.lbl_month.setStyleSheet(
            f"color: {t.get('text_main', '#FAF7F2')}; background: transparent;")

        # Year — mono, small, aligned to month baseline
        self.lbl_year.setFont(QFont(font_mono, 10))
        self.lbl_year.setStyleSheet("color: #9A8F7C; background: transparent;")

        # Watermark
        wm = (self.config.get_value("calendar_watermark_opacity", 0.07)
              if self.config else 0.07)
        self.lbl_big_today.setStyleSheet(
            f"color: rgba(255, 255, 255, {wm}); background: transparent;")

        if self.isVisible():
            self._adjust_watermark()

    # ── Calendar grid ──────────────────────────────────────────────────────

    def update_calendar(self):
        # Clear grid
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item and item.widget():
                item.widget().setParent(None)

        today = QDate.currentDate()
        self.lbl_month.setText(today.toString("MMMM"))
        self.lbl_year.setText(str(today.year()))

        t          = self.theme_manager.get_theme() if self.theme_manager else {}
        secondary  = t.get("text_secondary", "rgba(255,255,255,0.55)")
        text_main  = t.get("text_main", "white")
        accent     = t.get("accent", "#E8A857")
        font_name  = (self.config.get("font_calendar", t.get("font_family", "Segoe UI"))
                      if self.config else t.get("font_family", "Segoe UI"))
        font_mono  = (self.config.get("font_stats", "Consolas")
                      if self.config else "Consolas")

        # Day-of-week headers
        for i, d in enumerate(["M", "T", "W", "T", "F", "S", "S"]):
            lbl = QLabel(d)
            lbl.setObjectName("calendar_day_header")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFont(QFont(font_mono, 8))
            lbl.setStyleSheet(f"color: #615848; background: transparent;")
            self.grid_layout.addWidget(lbl, 0, i)

        # Day cells
        month_cal = calendar.monthcalendar(today.year(), today.month())
        current_d = today.day()

        for row, week in enumerate(month_cal, start=1):
            for col, day in enumerate(week):
                if day == 0:
                    continue
                lbl = QLabel(str(day))
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl.setFont(QFont(font_mono, 11))

                if day == current_d:
                    lbl.setFixedSize(28, 28)
                    lbl.setStyleSheet(
                        f"background-color: {accent};"
                        f"color: #121212;"
                        f"border-radius: 14px;"
                        f"font-weight: 600;")
                    lbl.setProperty("is_today", True)
                else:
                    lbl.setStyleSheet(f"color: {secondary}; background: transparent;")
                    lbl.setSizePolicy(
                        QSizePolicy.Policy.Expanding,
                        QSizePolicy.Policy.Expanding)

                self.grid_layout.addWidget(
                    lbl, row, col,
                    alignment=Qt.AlignmentFlag.AlignCenter)

        # Agenda
        self._rebuild_agenda(font_mono, accent)
        self._adjust_watermark()

    def _rebuild_agenda(self, font_mono, accent):
        # Clear
        while self.agenda_layout.count():
            item = self.agenda_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        # Use live events if available, else fall back to mock
        events = self._live_events if self._live_events is not None else _MOCK_EVENTS

        if not events:
            lbl = QLabel("No events today")
            lbl.setFont(QFont(font_mono, 9))
            lbl.setStyleSheet("color: #615848; background: transparent;")
            self.agenda_layout.addWidget(lbl)
            return

        for ev in events:
            row   = QWidget()
            hbox  = QHBoxLayout(row)
            hbox.setContentsMargins(0, 0, 0, 0)
            hbox.setSpacing(10)

            lbl_time = QLabel(ev["time"])
            lbl_time.setObjectName("cal_event_time")
            lbl_time.setFixedWidth(38)
            lbl_time.setFont(QFont(font_mono, 9))
            alpha = "80" if ev.get("past") else "FF"
            lbl_time.setStyleSheet(f"color: rgba(154,143,124,{int(alpha,16)}); background: transparent;")

            # Accent dot
            dot = QLabel("●")
            dot.setFixedWidth(10)
            dot.setFont(QFont(font_mono, 6))
            if ev.get("past"):
                dot.setStyleSheet("color: #615848; background: transparent;")
            else:
                dot.setStyleSheet(f"color: {accent}; background: transparent;")

            lbl_title = QLabel(ev["title"])
            lbl_title.setObjectName("cal_event_title")
            t_font = self.theme_manager.get_theme().get("font_family", "Segoe UI") if self.theme_manager else "Segoe UI"
            lbl_title.setFont(QFont(t_font, 10))
            if ev.get("past"):
                lbl_title.setStyleSheet("color: #615848; background: transparent;")
            else:
                lbl_title.setStyleSheet("color: #FAF7F2; background: transparent;")

            hbox.addWidget(lbl_time)
            hbox.addWidget(dot)
            hbox.addWidget(lbl_title)
            hbox.addStretch()
            self.agenda_layout.addWidget(row)
