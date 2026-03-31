from PyQt6.QtCore import QTimer, Qt, QPoint, QDate
from PyQt6.QtWidgets import QLabel, QGridLayout, QVBoxLayout, QHBoxLayout, QWidget, QSizePolicy, QMenu
from PyQt6.QtGui import QFont, QColor, QAction
from base_widget import BaseWidget

class CalendarWidget(BaseWidget):
    def __init__(self, theme_manager=None, config_manager=None):
        super().__init__(theme_manager, config_manager, widget_id="calendar")
        self.config = config_manager
        
        # Root Layout: Grid to allow stacking (Overlay)
        self.root_layout = QGridLayout()
        self.root_layout.setContentsMargins(16, 16, 16, 16)
        self.setLayout(self.root_layout)
        
        # -- Layer 0: Background Big Date --
        self.lbl_big_today = QLabel()
        self.lbl_big_today.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_big_today.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        # Position at (0,0) so it's behind
        self.root_layout.addWidget(self.lbl_big_today, 0, 0)
        
        # -- Layer 1: Foreground Content --
        self.calendar_container = QWidget()
        cal_layout = QVBoxLayout()
        cal_layout.setContentsMargins(0, 0, 0, 0)
        self.calendar_container.setLayout(cal_layout)
        
        # Month Label
        self.lbl_month = QLabel()
        self.lbl_month.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.lbl_month.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        cal_layout.addWidget(self.lbl_month)

        # Grid
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(4)
        cal_layout.addLayout(self.grid_layout)

        # Add to same cell (0,0) to stack on top
        self.root_layout.addWidget(self.calendar_container, 0, 0)
        
        self.day_labels = []
        
        self.apply_theme()
        self.update_calendar()
        
        # Auto-refresh date
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_calendar)
        self.timer.start(60000) # Check every minute
        
        self.resize(220, 200)

    def resizeEvent(self, event):
        if getattr(self, "_resizing", False):
            return
        
        self._resizing = True
        try:
            super().resizeEvent(event)
            self.adjust_font_size()
        finally:
            self._resizing = False
        
    def adjust_font_size(self):
        w = self.width()
        h = self.height()
        
        # Big Date Font
        target_h = max(10, int(h * 0.6))
        f = self.lbl_big_today.font()
        if f.pointSize() != target_h: 
            f.setPointSize(target_h)
            f.setBold(True)
            self.lbl_big_today.setFont(f)
        
        # Update Text
        current_day = str(QDate.currentDate().day())
        if self.lbl_big_today.text() != current_day:
            self.lbl_big_today.setText(current_day)

        # -- Grid Scaling --
        base_w = w * 0.55
        
        header_size = max(8, int(base_w * 0.08))
        day_size = max(7, int(base_w * 0.06))
        
        # Apply to Month Label
        current_font = self.lbl_month.font()
        if current_font.pointSize() != header_size:
            current_font.setPointSize(header_size)
            self.lbl_month.setFont(current_font)
        
        # Apply to Grid Items
        for i in range(self.grid_layout.count()):
            item = self.grid_layout.itemAt(i)
            if item and item.widget():
                lbl = item.widget()
                f = lbl.font()
                target_f_size = int(day_size * 1.2) if lbl.property("is_today") else day_size

                if f.pointSize() != target_f_size:
                    f.setPointSize(target_f_size)
                    f.setBold(lbl.property("is_today") is True)
                    lbl.setFont(f)

    def contextMenuEvent(self, event):
        # Override BaseWidget context menu to add specific options
        menu = QMenu(self)
        
        # Add Base Actions (Move/Exit handled by base usually, but here we can rebuild or call super if structured differently)
        # Since BaseWidget.contextMenuEvent executes the menu, we can't easily append unless we copy logic or BaseWidget has a create_menu method.
        # Let's just create a full menu here, duplicating base items for now or calling a helper if available.
        # Actually BaseWidget logic is simple. Let's replicate + add.
        
        # Move logic is handled by BaseWidget mouse events, no explicit start method exposed.
        # action_move = QAction("Move Widget", self)
        # action_move.triggered.connect(self.start_drag_mode)
        # menu.addAction(action_move)
        
        # Styles
        style_menu = QMenu("Opacity", self)
        self.add_opacity_menu(style_menu)
        menu.addMenu(style_menu)
        
        # -- New: Watermark Strength --
        wm_menu = QMenu("Watermark Strength", self)
        wm_levels = [
            (0.0, "Hidden (0%)"), (0.05, "Ultra Subtle (5%)"), 
            (0.1, "Subtle (10%)"), (0.15, "Standard (15%)"), 
            (0.2, "Bold (20%)"), (0.3, "Heavy (30%)"), 
            (0.5, "Half (50%)"), (1.0, "Full (100%)")
        ]
        current_wm = self.config.get_value("calendar_watermark_opacity", 0.1)
        
        for val, label in wm_levels:
            act = QAction(label, self)
            act.setCheckable(True)
            if abs(current_wm - val) < 0.01: act.setChecked(True)
            act.triggered.connect(lambda checked, v=val: self.set_watermark_opacity(v))
            wm_menu.addAction(act)
        menu.addMenu(wm_menu)
        
        menu.addSeparator()
        action_exit = QAction("Exit Application", self)
        import PyQt6.QtWidgets
        action_exit.triggered.connect(PyQt6.QtWidgets.QApplication.instance().quit)
        menu.addAction(action_exit)
        
        menu.exec(event.globalPos())

    def set_watermark_opacity(self, val):
        self.config.set_value("calendar_watermark_opacity", val)
        self.apply_theme()

    def apply_theme(self):
        if not self.theme_manager: return
        t = self.get_theme_with_opacity()
        
        base_style = f"QWidget#calendar {{ background-color: {t['background']}; border-radius: {t['border_radius']}; }}"
        self.setStyleSheet(base_style + self.get_qss())
        
        font_name = self.config.get("font_calendar", t['font_family']) if self.config else t['font_family']
        
        font_header = QFont(font_name, 13, QFont.Weight.Medium)
        self.lbl_month.setFont(font_header)
        self.lbl_month.setStyleSheet(f"color: {t['accent']}; background-color: transparent; padding-left: 5px;")
        
        # Big Date Style (Overlay Watermark)
        wm_opacity = self.config.get_value("calendar_watermark_opacity", 0.1)
        self.lbl_big_today.setStyleSheet(f"color: rgba(255, 255, 255, {wm_opacity}); background-color: transparent;")
        
        # Trigger resize adjustment if visible
        if self.isVisible(): self.adjust_font_size()

    def update_calendar(self):
        # Clear existing
        import calendar
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item and item.widget():
                item.widget().setParent(None)
            
        today = QDate.currentDate()
        self.lbl_month.setText(today.toString("MMMM yyyy"))
        
        # Days Header
        days = ["M", "T", "W", "T", "F", "S", "S"]
        t = self.theme_manager.get_theme()
        secondary_color = t.get("text_secondary", "rgba(255,255,255,0.55)")
        for i, d in enumerate(days):
            l = QLabel(d)
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.setStyleSheet(f"color: {secondary_color}; font-weight: 500;")
            self.grid_layout.addWidget(l, 0, i)
            
        # Days
        year = today.year()
        month = today.month()
        current_day = today.day()
        
        cal = calendar.monthcalendar(year, month)
        
        row = 1
        for week in cal:
            for col, day in enumerate(week):
                if day != 0:
                    l = QLabel(str(day))
                    l.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    if day == current_day:
                        accent = self.theme_manager.get_theme().get("accent", "#0A84FF")
                        # Fixed square so border-radius 14px renders a perfect circle
                        l.setFixedSize(28, 28)
                        l.setStyleSheet(f"""
                            background-color: {accent};
                            color: white;
                            border-radius: 14px;
                            font-weight: 600;
                        """)
                        l.setProperty("is_today", True)
                    else:
                        text_main = self.theme_manager.get_theme().get("text_main", "white")
                        l.setStyleSheet(f"color: {text_main};")
                        l.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                    
                    self.grid_layout.addWidget(l, row, col, alignment=Qt.AlignmentFlag.AlignCenter)
            row += 1
