import os
import sys
import json
import uuid

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

CONFIG_FILE = resource_path("config.json")

DEFAULT_CONFIG = {
    "clocks": [
        {"id": "default_local", "timezone": "Local", "label": "Local Time", "pos": [100, 100], "visible": True}
    ],
    "show_date": True,
    "show_media": True,
    "show_header": True,
    "show_stats": False,
    "show_calendar": False,
    "show_weather": False,
    "use_system_media": True,
    "locked": False,
    "weather_lat": None,
    "weather_lon": None,
    "weather_location_name": "My Location",
    "wind_unit": "kmh",
    "theme": "Concept (Dark Glass)",
    "transparency": 200, # 0-255
    "font_family_time": "Segoe UI",
    "font_family_label": "Segoe UI",
    "font_header": "Segoe UI",
    "font_stats": "Segoe UI",
    "font_calendar": "Segoe UI",
    "font_media_main": "Segoe UI",
    "font_media_sub": "Segoe UI",
    "positions": {
        "date": [100, 250],
        "media": [100, 450]
    }
}

class ConfigManager:
    def __init__(self):
        self.config = self.load_config()
        # Migration check could go here

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return DEFAULT_CONFIG.copy()
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                # Simple migration: if "show_clock" exists, convert to list
                if "show_clock" in data:
                    data["clocks"] = DEFAULT_CONFIG["clocks"]
                    if data["show_clock"] == False:
                        data["clocks"][0]["visible"] = False
                    del data["show_clock"]
                return data
        except Exception as e:
            print(f"Error loading config: {e}")
            return DEFAULT_CONFIG.copy()

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()

    def get_widget_opacity(self, widget_id):
        # Default to 255 (fully opaque) if not set
        opacities = self.config.get("widget_opacities", {})
        return opacities.get(widget_id, 255)

    def set_widget_opacity(self, widget_id, alpha):
        if "widget_opacities" not in self.config:
            self.config["widget_opacities"] = {}
        self.config["widget_opacities"][widget_id] = int(alpha)
        self.save_config()
        
    def get_value(self, key, default=None):
        return self.config.get(key, default)
        
    def set_value(self, key, value):
        self.config[key] = value
        self.save_config()

    def get_clocks(self):
        return self.config.get("clocks", [])

    def add_clock(self, timezone="Local", label="New Clock"):
        new_clock = {
            "id": str(uuid.uuid4()),
            "timezone": timezone,
            "label": label,
            "pos": [150, 150],
            "visible": True
        }
        if "clocks" not in self.config:
            self.config["clocks"] = []
        self.config["clocks"].append(new_clock)
        self.save_config()
        return new_clock

    def remove_clock(self, clock_id):
        self.config["clocks"] = [c for c in self.config["clocks"] if c["id"] != clock_id]
        self.save_config()

    def update_clock_pos(self, clock_id, x, y):
        for c in self.config["clocks"]:
            if c["id"] == clock_id:
                c["pos"] = [x, y]
                break
    
    def get_position(self, widget_name):
        return self.config.get("positions", {}).get(widget_name, DEFAULT_CONFIG["positions"].get(widget_name))

    def set_position(self, widget_name, x, y):
        if "positions" not in self.config:
            self.config["positions"] = {}
        self.config["positions"][widget_name] = [x, y]
