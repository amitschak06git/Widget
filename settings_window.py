from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QLabel,
                             QPushButton, QHBoxLayout, QListWidget,
                             QComboBox, QFontComboBox, QSlider, QScrollArea, QLineEdit,
                             QDoubleSpinBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class SettingsWindow(QWidget):
    def __init__(self, config_manager, theme_manager, on_change_callback):
        super().__init__()
        self.config = config_manager
        self.theme_manager = theme_manager
        self.on_change = on_change_callback
        
        self.setWindowTitle("Widget Settings")
        self.resize(550, 500)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Tabs
        self.setup_general_tab()
        self.setup_clock_tab()
        self.setup_appearance_tab()
        self.setup_fonts_tab()
        self.setup_weather_tab()
        
    def setup_general_tab(self):
        import startup_manager

        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        layout.addWidget(QLabel("Media Player Source:"))
        self.combo_media = QComboBox()
        self.combo_media.addItems(["Windows System Media (Spotify/Chrome/Etc)"])
        layout.addWidget(self.combo_media)

        layout.addSpacing(16)

        from PyQt6.QtWidgets import QCheckBox
        self.chk_startup = QCheckBox("Launch at Windows startup")
        self.chk_startup.setChecked(startup_manager.is_enabled())
        self.chk_startup.toggled.connect(lambda checked: startup_manager.set_enabled(checked))
        layout.addWidget(self.chk_startup)

        startup_note = QLabel("Adds an entry to HKCU run registry. No admin rights needed.")
        startup_note.setStyleSheet("color: gray; font-style: italic; font-size: 9pt;")
        layout.addWidget(startup_note)

        layout.addStretch()
        self.tabs.addTab(tab, "General")

    # setup_clock_tab is defined below with full timezone support.
    # Removing duplicate.
        
    def setup_appearance_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Theme
        layout.addWidget(QLabel("Theme:"))
        self.combo_theme = QComboBox()
        themes = sorted(self.theme_manager.get_available_themes())
        self.combo_theme.addItems(themes)
        current = self.config.get("theme", "Dark (Default)")
        if current in themes:
            self.combo_theme.setCurrentText(current)
        self.combo_theme.currentTextChanged.connect(self.change_theme)
        layout.addWidget(self.combo_theme)

        layout.addSpacing(10)
        
        # Presets
        layout.addWidget(QLabel("Style Presets:"))
        self.combo_presets = QComboBox()
        self.combo_presets.addItem("None (Default qss)")
        self.combo_presets.addItems(self.theme_manager.get_available_presets())
        self.combo_presets.currentTextChanged.connect(self.apply_preset)
        layout.addWidget(self.combo_presets)

        layout.addSpacing(10)

        # Transparency (Now handled via Context Menu per widget)
        # layout.addWidget(QLabel("Transparency: Use Right-Click Menu on Widgets"))

        layout.addSpacing(10)

        # Import Style Guide
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
        fname, _ = QFileDialog.getOpenFileName(self, "Open Style Guide", "", "Style Files (*.qss);;All Files (*)")
        if fname:
            self.theme_manager.load_stylesheet(fname)
            self.on_change()

    def setup_fonts_tab(self):
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout()
        content.setLayout(layout)
        scroll.setWidget(content)
        
        # Add Scroll to Tab
        tab_layout = QVBoxLayout()
        tab_layout.addWidget(scroll)
        tab.setLayout(tab_layout)

        # Helper to create rows
        def add_font_row(label_text, config_key):
            layout.addWidget(QLabel(label_text))
            fc = QFontComboBox()
            current = self.config.get(config_key, "Segoe UI")
            fc.setCurrentFont(QFont(current))
            # Use lambda with default arg to capture key correctly
            fc.currentFontChanged.connect(lambda f, k=config_key: self.change_font(k, f))
            layout.addWidget(fc)
            layout.addSpacing(5)

        add_font_row("Header (Day Name):", "font_header")
        add_font_row("Clock (Time):", "font_family_time")
        add_font_row("Clock (Label):", "font_family_label")
        add_font_row("Stats Widget:", "font_stats")
        add_font_row("Calendar Widget:", "font_calendar")
        add_font_row("Media Title:", "font_media_main")
        add_font_row("Media Artist:", "font_media_sub")

        # Font Tip
        tip = QLabel("Tip: Download 'Satoshi' or 'Clash Display' from Fontshare.com for the best look.")
        tip.setWordWrap(True)
        tip.setStyleSheet("color: gray; font-style: italic; margin-top: 10px;")
        layout.addWidget(tip)

        layout.addStretch()
        self.tabs.addTab(tab, "Fonts")

    def setup_clock_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        self.clock_list = QListWidget()
        self.refresh_clock_list()
        layout.addWidget(QLabel("Active Clocks:"))
        layout.addWidget(self.clock_list)
        
        btn_remove = QPushButton("Remove Selected Clock")
        btn_remove.clicked.connect(self.remove_clock)
        layout.addWidget(btn_remove)
        
        # Add Clock Section
        add_layout = QHBoxLayout()
        
        # Timezone
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
                local = tzlocal.get_localzone_name()
                self.combo_tz.setCurrentText(local)
            except Exception:
                pass
        except ImportError:
            self.combo_tz.addItem("UTC")
            self.combo_tz.addItem("Local")
        tz_layout.addWidget(self.combo_tz)
        add_layout.addLayout(tz_layout)
        
        # Name
        name_layout = QVBoxLayout()
        name_layout.addWidget(QLabel("Label Name:"))
        self.line_edit_label = QLineEdit("New Clock")
        name_layout.addWidget(self.line_edit_label)
        add_layout.addLayout(name_layout)
        
        btn_add = QPushButton("Add Clock")
        btn_add.clicked.connect(self.add_clock)
        # Make button taller to match
        btn_add.setFixedHeight(40)
        add_layout.addWidget(btn_add)
        
        layout.addLayout(add_layout)
        
        layout.addStretch()
        self.tabs.addTab(tab, "Clocks")

    def refresh_clock_list(self):
        self.clock_list.clear()
        clocks = self.config.get_clocks()
        for c in clocks:
            self.clock_list.addItem(f"{c['label']} ({c['timezone']})")

    def add_clock(self):
        tz = self.combo_tz.currentText()
        name = self.line_edit_label.text().strip() or "Clock"
        self.config.add_clock(tz, name)
        self.refresh_clock_list()
        self.on_change()

    def remove_clock(self):
        row = self.clock_list.currentRow()
        if row >= 0:
            clocks = self.config.get_clocks()
            if row < len(clocks):
                cid = clocks[row]['id']
                self.config.remove_clock(cid)
                self.refresh_clock_list()
                self.on_change()

    def setup_weather_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        layout.addWidget(QLabel("Location Name (display only):"))
        self.weather_name = QLineEdit(self.config.get("weather_location_name", "My Location"))
        self.weather_name.setPlaceholderText("e.g. New Delhi")
        self.weather_name.textChanged.connect(lambda t: self.config.set("weather_location_name", t))
        layout.addWidget(self.weather_name)

        layout.addSpacing(8)

        layout.addWidget(QLabel("Latitude:"))
        self.weather_lat = QDoubleSpinBox()
        self.weather_lat.setRange(-90.0, 90.0)
        self.weather_lat.setDecimals(4)
        self.weather_lat.setSingleStep(0.01)
        self.weather_lat.setValue(float(self.config.get("weather_lat") or 0.0))
        self.weather_lat.valueChanged.connect(lambda v: self.config.set("weather_lat", v))
        layout.addWidget(self.weather_lat)

        layout.addWidget(QLabel("Longitude:"))
        self.weather_lon = QDoubleSpinBox()
        self.weather_lon.setRange(-180.0, 180.0)
        self.weather_lon.setDecimals(4)
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
        self.combo_wind_unit.addItem("km/h",            "kmh")
        self.combo_wind_unit.addItem("m/s",             "ms")
        self.combo_wind_unit.addItem("Descriptive (Beaufort scale)", "bft")
        current_unit = self.config.get("wind_unit", "kmh")
        for i in range(self.combo_wind_unit.count()):
            if self.combo_wind_unit.itemData(i) == current_unit:
                self.combo_wind_unit.setCurrentIndex(i)
                break
        self.combo_wind_unit.currentIndexChanged.connect(
            lambda: self.config.set("wind_unit", self.combo_wind_unit.currentData())
        )
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

    def change_theme(self, text):
        self.config.set("theme", text)
        self.theme_manager.current_theme_name = text
        self.on_change()
        
    # Transparency methods removed (User preferred Context Menu)

    def change_font(self, key, font):
        self.config.set(key, font.family())
        self.on_change()
