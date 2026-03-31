import sys
import traceback
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QStyle
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QPoint
from PyQt6.QtGui import QGuiApplication
from clock_widget import ClockWidget
from date_widget import DateWidget
from media_widget import MediaWidget
from config_manager import ConfigManager
from settings_window import SettingsWindow
from system_media import SystemMediaManager
from theme_manager import ThemeManager
from header_widget import HeaderWidget
from stats_widget import StatsWidget
from calendar_widget import CalendarWidget
from weather_widget import WeatherWidget

def exception_hook(exctype, value, tb):
    with open("crash.log", "a") as f:
        f.write(f"[{datetime.now()}] Uncaught exception:\n")
        traceback.print_exception(exctype, value, tb, file=f)
    sys.__excepthook__(exctype, value, tb)

sys.excepthook = exception_hook

class WidgetManager:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        # Core Systems
        try:
            self.config = ConfigManager()
            self.theme_manager = ThemeManager(self.config.get("theme", "Dark (Default)"))
            self.system_media = SystemMediaManager()
            
            # Widgets Containers
            self.clocks = {} # id -> widget_instance
            
            # Static Widgets
            self.date = DateWidget(theme_manager=self.theme_manager, config_manager=self.config)
            self.media = MediaWidget(system_media=self.system_media, theme_manager=self.theme_manager, config_manager=self.config)
            
            self.header = HeaderWidget(theme_manager=self.theme_manager, config_manager=self.config)
            self.stats = StatsWidget(theme_manager=self.theme_manager, config_manager=self.config)
            self.calendar = CalendarWidget(theme_manager=self.theme_manager, config_manager=self.config)
            self.weather = WeatherWidget(theme_manager=self.theme_manager, config_manager=self.config)
            
            # Initialize Clocks
            self.sync_clocks()
            
            # Restore Positions (Static)
            self.restore_static_positions()
            
            # Initial Visibility
            if self.config.get("show_date", True): self.date.show()
            if self.config.get("show_media", True): self.media.show()
            
            # Concept Defaults (Mixed defaults based on user feedback)
            if self.config.get("show_header", True): self.header.show()
            if self.config.get("show_stats", False): self.stats.show()
            if self.config.get("show_calendar", False): self.calendar.show()
            if self.config.get("show_weather", False): self.weather.show()
            
            self.create_tray()
            
            self.settings_window = SettingsWindow(self.config, self.theme_manager, self.refresh_state)
        except Exception as e:
            with open("crash.log", "a") as f:
                f.write(f"[{datetime.now()}] Init error: {str(e)}\n")
            raise e

    def sync_clocks(self):
        config_clocks = self.config.get_clocks()
        current_ids = set(self.clocks.keys())
        target_ids = set([c["id"] for c in config_clocks])
        
        # Remove deleted
        for cid in current_ids - target_ids:
            self.clocks[cid].close()
            del self.clocks[cid]
            
        # Add new or update
        for c_data in config_clocks:
            cid = c_data["id"]
            if cid in self.clocks:
                self.clocks[cid].apply_theme()
            else:
                w = ClockWidget(cid, c_data["timezone"], c_data["label"], self.theme_manager, self.config)
                pos = c_data.get("pos", [100, 100])
                w.move(*pos)
                if c_data.get("visible", True):
                    w.show()
                self.clocks[cid] = w

    def safe_move(self, widget, x, y):
        """Move widget to (x, y), clamping to a visible screen if the position is off all monitors."""
        point = QPoint(x, y)
        for screen in QGuiApplication.screens():
            if screen.availableGeometry().contains(point):
                widget.move(x, y)
                return
        # Position is off all screens — fall back to primary screen top-left area
        primary = QGuiApplication.primaryScreen().availableGeometry()
        widget.move(primary.x() + 100, primary.y() + 100)

    def restore_static_positions(self):
        pos_date = self.config.get_position("date")
        self.safe_move(self.date, *(pos_date if pos_date else [100, 250]))

        pos_media = self.config.get_position("media")
        self.safe_move(self.media, *(pos_media if pos_media else [100, 450]))

        pos_header = self.config.get_position("header")
        self.safe_move(self.header, *(pos_header if pos_header else [100, 50]))

        pos_stats = self.config.get_position("stats")
        self.safe_move(self.stats, *(pos_stats if pos_stats else [100, 600]))

        pos_cal = self.config.get_position("calendar")
        self.safe_move(self.calendar, *(pos_cal if pos_cal else [100, 300]))

        pos_weather = self.config.get_position("weather")
        self.safe_move(self.weather, *(pos_weather if pos_weather else [400, 50]))

    def save_positions(self):
        self.config.set_position("date", self.date.x(), self.date.y())
        self.config.set_position("media", self.media.x(), self.media.y())
        self.config.set_position("header", self.header.x(), self.header.y())
        self.config.set_position("stats", self.stats.x(), self.stats.y())
        self.config.set_position("calendar", self.calendar.x(), self.calendar.y())
        self.config.set_position("weather", self.weather.x(), self.weather.y())

        for cid, w in self.clocks.items():
            self.config.update_clock_pos(cid, w.x(), w.y())
            
        self.config.save_config()

    def create_tray(self):
        icon = QIcon("icon.png")
        if icon.isNull():
            icon = self.app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
            
        self.tray_icon = QSystemTrayIcon(icon, self.app)
        self.update_tray_menu()
        self.tray_icon.show()

    def update_tray_menu(self):
        self.menu = QMenu()
        
        # Standard
        self.action_date = QAction("Toggle Date", triggered=lambda: self.toggle_widget(self.date, "show_date"))
        self.action_date.setCheckable(True); self.action_date.setChecked(self.date.isVisible())
        self.menu.addAction(self.action_date)
        
        self.action_media = QAction("Toggle Media", triggered=lambda: self.toggle_widget(self.media, "show_media"))
        self.action_media.setCheckable(True); self.action_media.setChecked(self.media.isVisible())
        self.menu.addAction(self.action_media)
        
        self.menu.addSeparator()
        
        # Concept
        self.action_header = QAction("Toggle Header (Day)", triggered=lambda: self.toggle_widget(self.header, "show_header"))
        self.action_header.setCheckable(True); self.action_header.setChecked(self.header.isVisible())
        self.menu.addAction(self.action_header)
        
        self.action_stats = QAction("Toggle Stats", triggered=lambda: self.toggle_widget(self.stats, "show_stats"))
        self.action_stats.setCheckable(True); self.action_stats.setChecked(self.stats.isVisible())
        self.menu.addAction(self.action_stats)
        
        self.action_cal = QAction("Toggle Calendar", triggered=lambda: self.toggle_widget(self.calendar, "show_calendar"))
        self.action_cal.setCheckable(True); self.action_cal.setChecked(self.calendar.isVisible())
        self.menu.addAction(self.action_cal)

        self.action_weather = QAction("Toggle Weather", triggered=lambda: self.toggle_widget(self.weather, "show_weather"))
        self.action_weather.setCheckable(True); self.action_weather.setChecked(self.weather.isVisible())
        self.menu.addAction(self.action_weather)
        
        self.menu.addSeparator()

        self.action_lock = QAction("Lock Widget Positions", triggered=self.toggle_lock)
        self.action_lock.setCheckable(True)
        self.action_lock.setChecked(self.config.get("locked", False))
        self.menu.addAction(self.action_lock)

        self.menu.addSeparator()

        self.action_settings = QAction("Settings", triggered=self.open_settings)
        self.menu.addAction(self.action_settings)

        self.action_exit = QAction("Exit", triggered=self.exit_app)
        self.menu.addAction(self.action_exit)
        
        self.tray_icon.setContextMenu(self.menu)

    def toggle_widget(self, widget, config_key):
        if widget.isVisible():
            widget.hide_animated()
            self.config.set(config_key, False)
        else:
            widget.show_animated()
            self.config.set(config_key, True)
        self.config.save_config()

    def toggle_lock(self):
        locked = not self.config.get("locked", False)
        self.config.set("locked", locked)
        self.action_lock.setChecked(locked)
        
    def open_settings(self):
        self.settings_window.show()
        
    def refresh_state(self):
        # Called when settings change (theme, etc)
        self.date.apply_theme()
        self.media.apply_theme()
        self.header.apply_theme()
        self.stats.apply_theme()
        self.calendar.apply_theme()
        self.weather.apply_theme()
        self.weather.refresh()
        self.sync_clocks()
        # Also force update clocks themes in case sync didn't recreate them
        for w in self.clocks.values():
            w.apply_theme()
            
    def exit_app(self):
        self.save_positions()
        self.system_media.running = False
        self.app.quit()

    def run(self):
        sys.exit(self.app.exec())

if __name__ == '__main__':
    manager = WidgetManager()
    manager.run()
