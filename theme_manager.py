
import os
THEMES = {
    "Dark (Default)": {
        "background": "rgba(0, 0, 0, 180)", 
        "text_main": "white",
        "text_secondary": "#cccccc",
        "accent": "#FFD700", # Gold
        "border_radius": "15px",
        "font_family": "Segoe UI"
    },
    "Light (macOS)": {
        "background": "rgba(255, 255, 255, 120)", # Higher transparency for blur
        "text_main": "black",
        "text_secondary": "#555555",
        "accent": "#007AFF", # Apple Blue
        "border_radius": "20px", 
        "font_family": "SF Pro Display, Segoe UI"
    },
    "Material (Pastel)": {
        "background": "#F0F0F0", 
        "text_main": "#333333",
        "text_secondary": "#757575",
        "accent": "#FF4081", # Pink/Red
        "border_radius": "25px", # Pill shape
        "font_family": "Roboto, Segoe UI"
    },
    "Neon (Cyberpunk)": {
        "background": "rgba(5, 5, 10, 240)",
        "text_main": "#00FFEA", # Cyan
        "text_secondary": "#FF00FF", # Magenta
        "accent": "#00FFEA", 
        "border_radius": "4px",
        "font_family": "Consolas"
    },
    "Ubuntu (Orange)": {
        "background": "rgba(44, 0, 30, 220)", 
        "text_main": "white",
        "text_secondary": "#E95420", 
        "accent": "#E95420",
        "border_radius": "8px",
        "font_family": "Ubuntu"
    },
    "Concept (Dark Glass)": {
        "background": "rgba(30, 30, 30, 240)", # Dark Grey, high opacity
        "text_main": "white",
        "text_secondary": "#aaaaaa",
        "accent": "#FF5555", # Red accent
        "border_radius": "12px",
        "font_family": "Segoe UI Black, Impact, Arial" 
    },
    "Glassmorphism (Aero)": {
        "background": "rgba(255, 255, 255, 1)", # Almost transparent for blur effect
        "text_main": "white",
        "text_secondary": "#E0E0E0", 
        "accent": "#FFFFFF", 
        "border_radius": "20px",
        "font_family": "Segoe UI Semilight"
    },
    "Neumorphism (Tactile)": {
        "background": "#e0e5ec", # Soft grey
        "text_main": "#4a4a4a",
        "text_secondary": "#a3b1c6", 
        "accent": "#4a4a4a",
        "border_radius": "30px",
        "font_family": "Segoe UI"
    },
    "Cyber-Cyber (HUD)": {
        "background": "#000000", # Obsidian
        "text_main": "#00FF99", # Leapmotor Tealish
        "text_secondary": "#008F5D",
        "accent": "#00FF99",
        "border_radius": "0px",
        "font_family": "JetBrains Mono, Consolas, monospace"
    },
    "Apple (Sonoma)": {
        "background": "rgba(28, 28, 30, 0.78)",
        "text_main": "rgba(255, 255, 255, 0.95)",
        "text_secondary": "rgba(255, 255, 255, 0.55)",
        "accent": "#0A84FF",
        "border_radius": "16px",
        "font_family": "SF Pro Display, SF Pro Text, -apple-system, Segoe UI"
    }
}

class ThemeManager:
    def __init__(self, current_theme_name="Dark (Default)", config_manager=None):
        self.current_theme_name = current_theme_name
        self.config = config_manager
        self.load_stylesheet("style.qss")
        
    def get_theme(self):
        t = THEMES.get(self.current_theme_name, THEMES["Dark (Default)"]).copy()
        
        # Apply transparency override if config exists
        if self.config:
            alpha = self.config.get("transparency", 200)
            bg = t["background"]
            
            if "rgba" in bg:
                # Basic parsing to replace alpha
                parts = bg.replace("rgba(", "").replace(")", "").split(",")
                if len(parts) >= 3:
                     t["background"] = f"rgba({parts[0].strip()}, {parts[1].strip()}, {parts[2].strip()}, {alpha})"
            elif "#" in bg:
                # Convert hex to rgba? Or just assume Dark Grey base for custom transparency for ease
                t["background"] = f"rgba(30, 30, 30, {alpha})"
                
        return t
        
    def get_style(self, element):
        t = self.get_theme()
        return ""

    def get_available_themes(self):
        return list(THEMES.keys())

    def get_available_presets(self):
         import os
         import sys
         
         presets = set()
         
         # 1. Local 'themes' folder (Editable by user)
         if os.path.exists("themes"):
             for f in os.listdir("themes"):
                 if f.endswith(".qss"):
                     presets.add(f)

         # 2. Bundled 'themes' folder (PyInstaller)
         if hasattr(sys, '_MEIPASS'):
             bundled_path = os.path.join(sys._MEIPASS, "themes")
             if os.path.exists(bundled_path):
                 for f in os.listdir(bundled_path):
                     if f.endswith(".qss"):
                         presets.add(f)
                         
         return sorted(list(presets))

    def load_preset(self, filename):
        import os
        import sys
        
        # Priority 1: Local file
        path = os.path.join("themes", filename)
        if not os.path.exists(path):
            # Priority 2: Bundled file
            if hasattr(sys, '_MEIPASS'):
                path = os.path.join(sys._MEIPASS, "themes", filename)
        
        self.load_stylesheet(path)

    def load_stylesheet(self, path):
         try:
             with open(path, "r") as f:
                 self.loaded_stylesheet = f.read()
                 print(f"Loaded stylesheet from {path}")
         except Exception as e:
             print(f"Error loading stylesheet: {e}")
             self.loaded_stylesheet = ""
             
    def get_stylesheet(self):
        return getattr(self, 'loaded_stylesheet', "")
