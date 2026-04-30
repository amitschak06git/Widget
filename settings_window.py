"""
settings_window.py — drop-in replacement for amitschak06git/Widget

Diff vs. the original:
  • Fonts tab now has a Font Pairing dropdown at the top.
    Selecting one applies all per-widget font keys in one click.
  • Per-widget font rows remain (overrides).
  • A "Browse curated fonts…" dialog lists FONT_LIBRARY grouped by mood.
  • New "Editorial (Warm)", "Noir", "Paper" themes available via the
    existing Appearance tab combo (no code change needed — they come
    from theme_manager.THEMES).

Everything else is preserved from the original.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QLabel,
                             QPushButton, QHBoxLayout, QListWidget,
                             QComboBox, QFontComboBox, QSlider, QScrollArea,
                             QLineEdit, QDoubleSpinBox, QDialog, QListWidgetItem,
                             QDialogButtonBox, QCheckBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class SettingsWindow(QWidget):
    def __init__(self, config_manager, theme_manager, on_change_callback):
        super().__init__()
        self.config = config_manager
        self.theme_manager = theme_manager
        self.on_change = on_change_callback

        self.setWindowTitle("Widget Settings")
        self.resize(560, 560)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.setup_general_tab()
        self.setup_clock_tab()
        self.setup_appearance_tab()
        self.setup_fonts_tab()
        self.setup_weather_tab()
        self.setup_calendar_tab()

    # ── General ─────────────────────────────────────────────
    def setup_general_tab(self):
        import startup_manager
        tab = QWidget(); layout = QVBoxLayout(); tab.setLayout(layout)
        layout.addWidget(QLabel("Media Player Source:"))
        self.combo_media = QComboBox()
        self.combo_media.addItems(["Windows System Media (Spotify/Chrome/Etc)"])
        layout.addWidget(self.combo_media)
        layout.addSpacing(16)
        self.chk_startup = QCheckBox("Launch at Windows startup")
        self.chk_startup.setChecked(startup_manager.is_enabled())
        self.chk_startup.toggled.connect(lambda c: startup_manager.set_enabled(c))
        layout.addWidget(self.chk_startup)
        note = QLabel("Adds an entry to HKCU run registry. No admin rights needed.")
        note.setStyleSheet("color: gray; font-style: italic; font-size: 9pt;")
        layout.addWidget(note)
        layout.addStretch()
        self.tabs.addTab(tab, "General")

    # ── Appearance ──────────────────────────────────────────
    def setup_appearance_tab(self):
        tab = QWidget(); layout = QVBoxLayout(); tab.setLayout(layout)

        layout.addWidget(QLabel("Theme:"))
        self.combo_theme = QComboBox()
        themes = sorted(self.theme_manager.get_available_themes())
        self.combo_theme.addItems(themes)
        current = self.config.get("theme", "Dark (Default)")
        if current in themes:
            self.combo_theme.setCurrentText(current)
        self.combo_theme.currentTextChanged.connect(self.change_theme)
        layout.addWidget(self.combo_theme)

        self.lbl_pairing_hint = QLabel("")
        self.lbl_pairing_hint.setStyleSheet(
            "color: gray; font-style: italic; font-size: 9pt; margin-top: 2px;")
        layout.addWidget(self.lbl_pairing_hint)
        self._update_pairing_hint(current)

        layout.addSpacing(10)
        layout.addWidget(QLabel("Style Presets (.qss):"))
        self.combo_presets = QComboBox()
        self.combo_presets.addItem("None (Default qss)")
        self.combo_presets.addItems(self.theme_manager.get_available_presets())
        self.combo_presets.currentTextChanged.connect(self.apply_preset)
        layout.addWidget(self.combo_presets)

        layout.addSpacing(10)
        btn_import = QPushButton("Import Style Guide")
        btn_import.clicked.connect(self.import_style)
        layout.addWidget(btn_import)

        layout.addStretch()
        self.tabs.addTab(tab, "Appearance")

    def apply_preset(self, text):
        if text == "None (Default qss)":
            self.theme_manager.load_stylesheet("style.qss")
        else:
            self.theme_manager.load_preset(text)
        self.on_change()

    def import_style(self):
        from PyQt6.QtWidgets import QFileDialog
        fname, _ = QFileDialog.getOpenFileName(self, "Open Style Guide", "",
                                               "Style Files (*.qss);;All Files (*)")
        if fname:
            self.theme_manager.load_stylesheet(fname)
            self.on_change()

    # ── Fonts (REWRITTEN) ───────────────────────────────────
    def setup_fonts_tab(self):
        tab = QWidget()
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        content = QWidget(); layout = QVBoxLayout(); content.setLayout(layout)
        scroll.setWidget(content)
        tab_layout = QVBoxLayout(); tab_layout.addWidget(scroll); tab.setLayout(tab_layout)

        # ── Pairing selector ─────────────────────────────
        layout.addWidget(QLabel("Font Pairing:"))
        self.combo_pairing = QComboBox()
        self.combo_pairing.addItem("— Custom —")
        self.combo_pairing.addItems(self.theme_manager.get_available_pairings())
        current_pairing = self.config.get("font_pairing") or "— Custom —"
        idx = self.combo_pairing.findText(current_pairing)
        if idx >= 0:
            self.combo_pairing.setCurrentIndex(idx)
        self.combo_pairing.currentTextChanged.connect(self._change_pairing)
        layout.addWidget(self.combo_pairing)

        self.lbl_pairing_mood = QLabel("")
        self.lbl_pairing_mood.setWordWrap(True)
        self.lbl_pairing_mood.setStyleSheet(
            "color: gray; font-style: italic; font-size: 9pt; margin-top: 2px;"
        )
        layout.addWidget(self.lbl_pairing_mood)
        self._update_mood_label(current_pairing)

        layout.addSpacing(8)
        btn_browse = QPushButton("Browse curated fonts by mood…")
        btn_browse.clicked.connect(self._open_font_browser)
        layout.addWidget(btn_browse)

        layout.addSpacing(14)
        layout.addWidget(QLabel("Per-widget overrides:"))

        self._font_combos = {}

        def add_font_row(label_text, config_key):
            row = QHBoxLayout()
            lbl = QLabel(label_text); lbl.setFixedWidth(140)
            row.addWidget(lbl)
            fc = QFontComboBox()
            current = self.config.get(config_key, "Segoe UI")
            fc.setCurrentFont(QFont(current))
            fc.currentFontChanged.connect(
                lambda f, k=config_key: self.change_font(k, f))
            row.addWidget(fc, 1)
            layout.addLayout(row)
            self._font_combos[config_key] = fc

        add_font_row("Header (Day):",   "font_header")
        add_font_row("Clock (Time):",   "font_family_time")
        add_font_row("Clock (Label):",  "font_family_label")
        add_font_row("Stats:",          "font_stats")
        add_font_row("Calendar:",       "font_calendar")
        add_font_row("Media Title:",    "font_media_main")
        add_font_row("Media Artist:",   "font_media_sub")

        tip = QLabel(
            "Designer fonts from <b>Fontshare</b> (free): Satoshi, General Sans, "
            "Clash Display, Cabinet Grotesk, Boska, Supreme. Install the .ttf, "
            "then restart the app."
        )
        tip.setWordWrap(True)
        tip.setStyleSheet("color: gray; font-style: italic; margin-top: 10px;")
        tip.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(tip)

        layout.addStretch()
        self.tabs.addTab(tab, "Fonts")

    def _change_pairing(self, name):
        if name == "— Custom —":
            self.theme_manager.apply_pairing("None")
        else:
            self.theme_manager.apply_pairing(name)
        self._update_mood_label(name)
        self._refresh_font_combos()
        self.on_change()

    def _refresh_font_combos(self):
        for config_key, fc in getattr(self, "_font_combos", {}).items():
            val = self.config.get(config_key, "Segoe UI")
            fc.blockSignals(True)
            fc.setCurrentFont(QFont(val))
            fc.blockSignals(False)

    def _update_mood_label(self, name):
        p = self.theme_manager._get_all_pairings().get(name)
        if p:
            self.lbl_pairing_mood.setText(
                f"<b>{p['display']}</b> · {p['ui']} · <code>{p['mono']}</code><br>"
                f"<i>{p['mood']}</i>"
            )
            self.lbl_pairing_mood.setTextFormat(Qt.TextFormat.RichText)
        else:
            self.lbl_pairing_mood.setText("Pick fonts individually below.")

    def _open_font_browser(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Curated Fonts")
        dlg.resize(440, 520)
        v = QVBoxLayout(); dlg.setLayout(v)
        v.addWidget(QLabel(
            "Recommended fonts grouped by mood. Double-click any to copy its "
            "name to your clipboard — then paste into a per-widget row."
        ))
        lst = QListWidget()
        for group, fonts in self.theme_manager.get_font_library().items():
            header = QListWidgetItem(f"── {group} ──")
            header.setFlags(Qt.ItemFlag.NoItemFlags)
            f = QFont(); f.setBold(True); header.setFont(f)
            lst.addItem(header)
            for name in fonts:
                lst.addItem(QListWidgetItem(name))
        v.addWidget(lst, 1)

        def on_double(item):
            from PyQt6.QtWidgets import QApplication
            txt = item.text()
            if txt.startswith("──"):
                return
            QApplication.clipboard().setText(txt)
        lst.itemDoubleClicked.connect(on_double)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        bb.rejected.connect(dlg.reject)
        bb.accepted.connect(dlg.accept)
        v.addWidget(bb)
        dlg.exec()

    # ── Clocks tab (unchanged) ──────────────────────────────
    def setup_clock_tab(self):
        tab = QWidget(); layout = QVBoxLayout(); tab.setLayout(layout)
        self.clock_list = QListWidget()
        self.refresh_clock_list()
        layout.addWidget(QLabel("Active Clocks:"))
        layout.addWidget(self.clock_list)
        btn_remove = QPushButton("Remove Selected Clock")
        btn_remove.clicked.connect(self.remove_clock)
        layout.addWidget(btn_remove)

        add_layout = QHBoxLayout()
        tz_layout = QVBoxLayout()
        tz_layout.addWidget(QLabel("Timezone:"))
        self.combo_tz = QComboBox()
        try:
            import zoneinfo
            available = sorted(list(zoneinfo.available_timezones()))
            self.combo_tz.addItems(available)
            if "UTC" in available: self.combo_tz.setCurrentText("UTC")
            try:
                import tzlocal
                self.combo_tz.setCurrentText(tzlocal.get_localzone_name())
            except Exception:
                pass
        except ImportError:
            self.combo_tz.addItems(["UTC", "Local"])
        tz_layout.addWidget(self.combo_tz)
        add_layout.addLayout(tz_layout)

        name_layout = QVBoxLayout()
        name_layout.addWidget(QLabel("Label Name:"))
        self.line_edit_label = QLineEdit("New Clock")
        name_layout.addWidget(self.line_edit_label)
        add_layout.addLayout(name_layout)

        btn_add = QPushButton("Add Clock")
        btn_add.clicked.connect(self.add_clock)
        btn_add.setFixedHeight(40)
        add_layout.addWidget(btn_add)
        layout.addLayout(add_layout)
        layout.addStretch()
        self.tabs.addTab(tab, "Clocks")

    def refresh_clock_list(self):
        self.clock_list.clear()
        for c in self.config.get_clocks():
            self.clock_list.addItem(f"{c['label']} ({c['timezone']})")

    def add_clock(self):
        tz = self.combo_tz.currentText()
        name = self.line_edit_label.text().strip() or "Clock"
        self.config.add_clock(tz, name)
        self.refresh_clock_list(); self.on_change()

    def remove_clock(self):
        row = self.clock_list.currentRow()
        if row >= 0:
            clocks = self.config.get_clocks()
            if row < len(clocks):
                self.config.remove_clock(clocks[row]['id'])
                self.refresh_clock_list(); self.on_change()

    # ── Weather tab (unchanged) ─────────────────────────────
    def setup_weather_tab(self):
        tab = QWidget(); layout = QVBoxLayout(); tab.setLayout(layout)
        layout.addWidget(QLabel("Location Name (display only):"))
        self.weather_name = QLineEdit(self.config.get("weather_location_name", "My Location"))
        self.weather_name.setPlaceholderText("e.g. New Delhi")
        self.weather_name.textChanged.connect(lambda t: self.config.set("weather_location_name", t))
        layout.addWidget(self.weather_name)
        layout.addSpacing(8)
        layout.addWidget(QLabel("Latitude:"))
        self.weather_lat = QDoubleSpinBox()
        self.weather_lat.setRange(-90.0, 90.0); self.weather_lat.setDecimals(4)
        self.weather_lat.setSingleStep(0.01)
        self.weather_lat.setValue(float(self.config.get("weather_lat") or 0.0))
        self.weather_lat.valueChanged.connect(lambda v: self.config.set("weather_lat", v))
        layout.addWidget(self.weather_lat)
        layout.addWidget(QLabel("Longitude:"))
        self.weather_lon = QDoubleSpinBox()
        self.weather_lon.setRange(-180.0, 180.0); self.weather_lon.setDecimals(4)
        self.weather_lon.setSingleStep(0.01)
        self.weather_lon.setValue(float(self.config.get("weather_lon") or 0.0))
        self.weather_lon.valueChanged.connect(lambda v: self.config.set("weather_lon", v))
        layout.addWidget(self.weather_lon)
        hint = QLabel("Find your coordinates at maps.google.com — right-click any location.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: gray; font-style: italic; font-size: 9pt;")
        layout.addWidget(hint)
        layout.addSpacing(12)
        layout.addWidget(QLabel("Wind Speed Format:"))
        self.combo_wind_unit = QComboBox()
        self.combo_wind_unit.addItem("km/h", "kmh")
        self.combo_wind_unit.addItem("m/s", "ms")
        self.combo_wind_unit.addItem("Descriptive (Beaufort scale)", "bft")
        current_unit = self.config.get("wind_unit", "kmh")
        for i in range(self.combo_wind_unit.count()):
            if self.combo_wind_unit.itemData(i) == current_unit:
                self.combo_wind_unit.setCurrentIndex(i); break
        self.combo_wind_unit.currentIndexChanged.connect(
            lambda: self.config.set("wind_unit", self.combo_wind_unit.currentData()))
        layout.addWidget(self.combo_wind_unit)
        layout.addSpacing(8)
        btn_apply = QPushButton("Apply & Refresh Widget")
        btn_apply.clicked.connect(self._apply_weather)
        layout.addWidget(btn_apply)
        attr = QLabel("Weather data provided by MET Norway / yr.no (CC 4.0)")
        attr.setWordWrap(True)
        attr.setStyleSheet("color: gray; font-size: 9pt; margin-top: 12px;")
        layout.addWidget(attr)
        layout.addStretch()
        self.tabs.addTab(tab, "Weather")

    def _apply_weather(self):
        self.config.set("weather_lat", self.weather_lat.value())
        self.config.set("weather_lon", self.weather_lon.value())
        self.on_change()

    # ── Calendar tab ────────────────────────────────────────────────────────
    def setup_calendar_tab(self):
        import os
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        layout.addWidget(QLabel("<b>Calendar Source</b>"))
        src_note = QLabel(
            "The calendar widget can show events from Google Calendar.\n"
            "Without credentials it shows placeholder events."
        )
        src_note.setWordWrap(True)
        src_note.setStyleSheet("color: gray; font-size: 9pt;")
        layout.addWidget(src_note)

        layout.addSpacing(12)

        # ── Google Calendar connection ────────────────────────────────────
        layout.addWidget(QLabel("Google Calendar:"))

        # Status indicator
        self.lbl_gcal_status = QLabel()
        self.lbl_gcal_status.setWordWrap(True)
        self._refresh_gcal_status()
        layout.addWidget(self.lbl_gcal_status)

        layout.addSpacing(6)

        # credentials.json path
        creds_row = QHBoxLayout()
        creds_row.addWidget(QLabel("credentials.json:"))
        self.line_creds = QLineEdit(
            self.config.get("calendar_credentials_path", "credentials.json"))
        self.line_creds.setPlaceholderText("credentials.json")
        self.line_creds.textChanged.connect(
            lambda t: self.config.set("calendar_credentials_path", t))
        creds_row.addWidget(self.line_creds, 1)
        btn_browse_creds = QPushButton("Browse…")
        btn_browse_creds.setFixedWidth(70)
        btn_browse_creds.clicked.connect(self._browse_credentials)
        creds_row.addWidget(btn_browse_creds)
        layout.addLayout(creds_row)

        layout.addSpacing(8)

        # Connect / Disconnect buttons
        btn_row = QHBoxLayout()
        self.btn_gcal_connect = QPushButton("Connect Google Calendar")
        self.btn_gcal_connect.clicked.connect(self._connect_google_calendar)
        btn_row.addWidget(self.btn_gcal_connect)

        self.btn_gcal_disconnect = QPushButton("Disconnect")
        self.btn_gcal_disconnect.clicked.connect(self._disconnect_google_calendar)
        btn_row.addWidget(self.btn_gcal_disconnect)
        layout.addLayout(btn_row)

        layout.addSpacing(16)

        # Instructions
        instr = QLabel(
            "<b>How to connect:</b><br>"
            "1. Go to <a href='https://console.cloud.google.com/'>Google Cloud Console</a><br>"
            "2. Create a project → Enable Google Calendar API<br>"
            "3. Create OAuth 2.0 credentials (Desktop app) → Download as <code>credentials.json</code><br>"
            "4. Place <code>credentials.json</code> in the app folder (or browse above)<br>"
            "5. Click <b>Connect Google Calendar</b> — a browser window will open to authorize<br>"
            "6. After authorizing, the widget fetches today's events automatically"
        )
        instr.setWordWrap(True)
        instr.setOpenExternalLinks(True)
        instr.setTextFormat(Qt.TextFormat.RichText)
        instr.setStyleSheet("font-size: 9pt; margin-top: 4px;")
        layout.addWidget(instr)

        layout.addStretch()
        self.tabs.addTab(tab, "Calendar")

    def _refresh_gcal_status(self):
        import os
        if os.path.exists("token.json"):
            self.lbl_gcal_status.setText(
                "● Connected  —  token.json found. Events refresh every 5 minutes.")
            self.lbl_gcal_status.setStyleSheet("color: #3cb371; font-weight: 500;")
        else:
            self.lbl_gcal_status.setText(
                "○ Not connected  —  showing placeholder events.")
            self.lbl_gcal_status.setStyleSheet("color: gray;")

    def _browse_credentials(self):
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "Select credentials.json", "",
            "JSON Files (*.json);;All Files (*)")
        if path:
            self.line_creds.setText(path)
            self.config.set("calendar_credentials_path", path)

    def _connect_google_calendar(self):
        import os, threading
        from PyQt6.QtWidgets import QMessageBox

        try:
            from google_calendar import GoogleCalendarProvider, GOOGLE_DEPS_INSTALLED
        except ImportError:
            GOOGLE_DEPS_INSTALLED = False

        if not GOOGLE_DEPS_INSTALLED:
            QMessageBox.warning(self, "Missing packages",
                "Google API libraries not installed.\n\n"
                "Run in the app folder:\n"
                "pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
            return

        creds_path = self.config.get("calendar_credentials_path", "credentials.json")
        if not os.path.exists(creds_path):
            QMessageBox.warning(self, "credentials.json not found",
                f"File not found:\n{creds_path}\n\n"
                "Download it from Google Cloud Console (see instructions below).")
            return

        def do_connect():
            try:
                p = GoogleCalendarProvider(creds_path)
                ok = p.connect()
                if ok:
                    self._refresh_gcal_status()
                else:
                    QMessageBox.warning(self, "Connection failed",
                        "Could not connect to Google Calendar. Check credentials.json.")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

        threading.Thread(target=do_connect, daemon=True).start()
        QMessageBox.information(self, "Opening browser…",
            "A browser window will open to authorize access.\n"
            "After completing the authorization, close this dialog.")

    def _disconnect_google_calendar(self):
        import os
        from PyQt6.QtWidgets import QMessageBox
        if os.path.exists("token.json"):
            os.remove("token.json")
        self._refresh_gcal_status()
        QMessageBox.information(self, "Disconnected",
            "Google Calendar disconnected. The widget will now show placeholder events.")

    def _update_pairing_hint(self, theme_name):
        best = self.theme_manager.get_recommended_pairing(theme_name)
        if best:
            self.lbl_pairing_hint.setText(f"Suggested pairing: {best}")
        else:
            self.lbl_pairing_hint.setText("")

    def change_theme(self, text):
        self.config.set("theme", text)
        self.theme_manager.current_theme_name = text
        self._update_pairing_hint(text)

        # Auto-apply the recommended pairing for this theme
        best = self.theme_manager.get_recommended_pairing(text)
        if best:
            self.theme_manager.apply_pairing(best)
            if hasattr(self, "combo_pairing"):
                self.combo_pairing.blockSignals(True)
                idx = self.combo_pairing.findText(best)
                if idx >= 0:
                    self.combo_pairing.setCurrentIndex(idx)
                self.combo_pairing.blockSignals(False)
                self._update_mood_label(best)
                self._refresh_font_combos()
        self.on_change()

    def change_font(self, key, font):
        self.config.set(key, font.family())
        # User manually changed a font → drop pairing into Custom mode.
        if self.config.get("font_pairing"):
            self.config.set("font_pairing", None)
            if hasattr(self, "combo_pairing"):
                self.combo_pairing.setCurrentText("— Custom —")
                self._update_mood_label("— Custom —")
        self.on_change()
