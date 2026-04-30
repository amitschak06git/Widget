"""
theme_manager.py — drop-in replacement for amitschak06git/Widget

Additions over the original:
  • FONT_PAIRINGS — curated modern & designer font pairings, each defining
        display / ui / mono / label roles. Apply one via
        config.set("font_pairing", "Editorial") and all widget fonts update.
  • FONT_LIBRARY — flat list of recommended fonts grouped by mood:
        Modern, Designer (Fontshare), Editorial, Technical, Classic.
  • ThemeManager.get_pairing() / apply_pairing() helpers.
  • New themes: "Editorial (Warm)", "Noir", "Paper".

Fonts with an asterisk (*) are designer fonts from Fontshare — free, but
must be installed on the system. See FONT_INSTALL_NOTES at the bottom.
"""

import os
import sys

# ─────────────────────────────────────────────────────────────
#  Theme → font style hint.  Used by get_recommended_pairing()
#  to pick an installed font that matches the theme's aesthetic.
#  Values: "serif" | "sans" | "mono"
# ─────────────────────────────────────────────────────────────
THEME_PAIRING_STYLE = {
    "Dark (Default)":        "sans",
    "Light (macOS)":         "sans",
    "Material (Pastel)":     "sans",
    "Neon (Cyberpunk)":      "mono",
    "Ubuntu (Orange)":       "sans",
    "Concept (Dark Glass)":  "sans",
    "Glassmorphism (Aero)":  "sans",
    "Neumorphism (Tactile)": "sans",
    "Cyber-Cyber (HUD)":     "mono",
    "Apple (Sonoma)":        "sans",
    "Editorial (Warm)":      "serif",
    "Noir":                  "sans",
    "Paper":                 "serif",
}

# Windows / common serif fonts not in FONT_LIBRARY
KNOWN_SERIF_FONTS = {
    "Georgia", "Times New Roman", "Cambria", "Garamond", "Palatino Linotype",
    "Book Antiqua", "Constantia", "Bookman Old Style", "Bell MT", "Calisto MT",
    "Goudy Old Style", "Perpetua", "Rockwell", "Sylfaen", "Bodoni MT",
    "Century Schoolbook", "High Tower Text", "Footlight MT Light",
    # also curated editorial serifs from FONT_LIBRARY
    "Instrument Serif", "Fraunces", "DM Serif Display", "Playfair Display",
    "EB Garamond", "Cormorant Garamond", "Spectral", "Literata",
}

# ─────────────────────────────────────────────────────────────
#  Color / radius themes (kept compatible with original keys)
# ─────────────────────────────────────────────────────────────
THEMES = {
    "Dark (Default)": {
        "background": "rgba(0, 0, 0, 180)",
        "text_main": "white",
        "text_secondary": "#cccccc",
        "accent": "#FFD700",
        "border_radius": "15px",
        "font_family": "Segoe UI",
    },
    "Light (macOS)": {
        "background": "rgba(255, 255, 255, 120)",
        "text_main": "black",
        "text_secondary": "#555555",
        "accent": "#007AFF",
        "border_radius": "20px",
        "font_family": "SF Pro Display, Segoe UI",
    },
    "Material (Pastel)": {
        "background": "#F0F0F0",
        "text_main": "#333333",
        "text_secondary": "#757575",
        "accent": "#FF4081",
        "border_radius": "25px",
        "font_family": "Roboto, Segoe UI",
    },
    "Neon (Cyberpunk)": {
        "background": "rgba(5, 5, 10, 240)",
        "text_main": "#00FFEA",
        "text_secondary": "#FF00FF",
        "accent": "#00FFEA",
        "border_radius": "4px",
        "font_family": "Consolas",
    },
    "Ubuntu (Orange)": {
        "background": "rgba(44, 0, 30, 220)",
        "text_main": "white",
        "text_secondary": "#E95420",
        "accent": "#E95420",
        "border_radius": "8px",
        "font_family": "Ubuntu",
    },
    "Concept (Dark Glass)": {
        "background": "rgba(30, 30, 30, 240)",
        "text_main": "white",
        "text_secondary": "#aaaaaa",
        "accent": "#FF5555",
        "border_radius": "12px",
        "font_family": "Segoe UI Black, Impact, Arial",
    },
    "Glassmorphism (Aero)": {
        "background": "rgba(255, 255, 255, 1)",
        "text_main": "white",
        "text_secondary": "#E0E0E0",
        "accent": "#FFFFFF",
        "border_radius": "20px",
        "font_family": "Segoe UI Semilight",
    },
    "Neumorphism (Tactile)": {
        "background": "#e0e5ec",
        "text_main": "#4a4a4a",
        "text_secondary": "#a3b1c6",
        "accent": "#4a4a4a",
        "border_radius": "30px",
        "font_family": "Segoe UI",
    },
    "Cyber-Cyber (HUD)": {
        "background": "#000000",
        "text_main": "#00FF99",
        "text_secondary": "#008F5D",
        "accent": "#00FF99",
        "border_radius": "0px",
        "font_family": "JetBrains Mono, Consolas, monospace",
    },
    "Apple (Sonoma)": {
        "background": "rgba(28, 28, 30, 0.78)",
        "text_main": "rgba(255, 255, 255, 0.95)",
        "text_secondary": "rgba(255, 255, 255, 0.55)",
        "accent": "#0A84FF",
        "border_radius": "16px",
        "font_family": "SF Pro Display, SF Pro Text, -apple-system, Segoe UI",
    },
    # ── New themes ───────────────────────────────────────────
    "Editorial (Warm)": {
        "background": "rgba(26, 22, 20, 0.75)",
        "text_main": "#F8F2EA",
        "text_secondary": "rgba(248, 242, 234, 0.55)",
        "accent": "#E8A857",  # warm amber
        "border_radius": "22px",
        "font_family": "Instrument Serif, Georgia, serif",
    },
    "Noir": {
        "background": "rgba(12, 12, 14, 0.82)",
        "text_main": "#EDEDED",
        "text_secondary": "rgba(237, 237, 237, 0.5)",
        "accent": "#CFCFCF",
        "border_radius": "10px",
        "font_family": "Helvetica Neue, Helvetica, Arial",
    },
    "Paper": {
        "background": "rgba(248, 244, 236, 0.88)",
        "text_main": "#2A241F",
        "text_secondary": "rgba(42, 36, 31, 0.55)",
        "accent": "#B8562E",
        "border_radius": "18px",
        "font_family": "Fraunces, Georgia, serif",
    },
}


# ─────────────────────────────────────────────────────────────
#  FONT LIBRARY — recommended fonts grouped by mood.
#  Mark (*) = Fontshare designer font, (**) = Google Fonts,
#  (no mark) = OS-native / commonly installed.
# ─────────────────────────────────────────────────────────────
FONT_LIBRARY = {
    "Modern Sans": [
        "Inter",                    # **
        "Space Grotesk",            # **
        "General Sans",             # *
        "Satoshi",                  # *
        "Manrope",                  # **
        "Plus Jakarta Sans",        # **
        "DM Sans",                  # **
        "Outfit",                   # **
        "Geist",                    # **  (Vercel)
        "Switzer",                  # *
        "Helvetica Neue",
        "Segoe UI Variable",
    ],
    "Designer Display": [
        "Clash Display",            # *
        "Clash Grotesk",            # *
        "Cabinet Grotesk",          # *
        "Boska",                    # *
        "Erode",                    # *
        "Gambarino",                # *
        "Melodrama",                # *
        "Ranade",                   # *
        "Supreme",                  # *
        "Zodiak",                   # *
        "Author",                   # *
        "Panchang",                 # *
    ],
    "Editorial Serif": [
        "Instrument Serif",         # **
        "Fraunces",                 # **
        "DM Serif Display",         # **
        "Playfair Display",         # **
        "EB Garamond",              # **
        "Cormorant Garamond",       # **
        "Spectral",                 # **
        "Literata",                 # **
    ],
    "Technical / Mono": [
        "JetBrains Mono",           # **
        "Geist Mono",               # **
        "IBM Plex Mono",            # **
        "Space Mono",               # **
        "Fira Code",                # **
        "Cascadia Code",
        "Consolas",
    ],
    "Classic / Safe": [
        "Helvetica Neue",
        "Arial",
        "Georgia",
        "Times New Roman",
        "Courier New",
        "Segoe UI",
        "Verdana",
    ],
}


# ─────────────────────────────────────────────────────────────
#  FONT PAIRINGS — named, curated combos that map roles to fonts.
#  Roles:
#     display — large numeric / hero type (clock time, weather temp, day name)
#     ui      — labels, nav, metadata
#     mono    — telemetry, timestamps, data
#     label   — small caps micro labels (falls back to ui if absent)
#
#  The existing per-widget keys (font_family_time, font_header, font_media_main,
#  font_calendar, font_stats, font_family_label, font_media_sub) are still
#  honoured; if a pairing is active they're derived from its roles unless
#  the user has set an override.
# ─────────────────────────────────────────────────────────────
FONT_PAIRINGS = {
    "Editorial": {
        "display": "Instrument Serif",
        "ui": "Inter",
        "mono": "JetBrains Mono",
        "label": "Inter",
        "mood": "Warm, print-inspired. Italic serif numerics, clean sans labels.",
    },
    "Swiss Modern": {
        "display": "Fraunces",
        "ui": "Inter",
        "mono": "JetBrains Mono",
        "label": "Inter",
        "mood": "Variable-axis serif paired with neutral sans. Versatile.",
    },
    "Designer Studio": {
        "display": "Clash Display",
        "ui": "General Sans",
        "mono": "Geist Mono",
        "label": "General Sans",
        "mood": "Boutique Fontshare combo. Modern, a little opinionated.",
    },
    "Technical HUD": {
        "display": "Space Grotesk",
        "ui": "Space Grotesk",
        "mono": "JetBrains Mono",
        "label": "JetBrains Mono",
        "mood": "All-sans/mono telemetry look. Monospace labels for data density.",
    },
    "Soft Editorial": {
        "display": "DM Serif Display",
        "ui": "DM Sans",
        "mono": "IBM Plex Mono",
        "label": "DM Sans",
        "mood": "Google Fonts stack. Warm, literary, widely installed.",
    },
    "Ambient Minimal": {
        "display": "Boska",
        "ui": "Satoshi",
        "mono": "Geist Mono",
        "label": "Satoshi",
        "mood": "Fontshare combo. Ultra-thin display, friendly sans.",
    },
    "Brutalist": {
        "display": "Cabinet Grotesk",
        "ui": "Supreme",
        "mono": "Space Mono",
        "label": "Supreme",
        "mood": "Heavy, angular. High-contrast, opinionated.",
    },
    "Classic Sonoma": {
        "display": "SF Pro Display, Segoe UI, Helvetica Neue",
        "ui": "SF Pro Text, Segoe UI",
        "mono": "SF Mono, Consolas, monospace",
        "label": "SF Pro Text, Segoe UI",
        "mood": "OS-default, Sonoma-like. Uses system fonts — no install needed.",
    },
    "System Safe": {
        "display": "Helvetica Neue, Arial",
        "ui": "Helvetica Neue, Arial",
        "mono": "Courier New",
        "label": "Helvetica Neue, Arial",
        "mood": "Works without installing anything.",
    },
}


# ─────────────────────────────────────────────────────────────
#  ThemeManager
# ─────────────────────────────────────────────────────────────
class ThemeManager:
    def __init__(self, current_theme_name="Dark (Default)", config_manager=None):
        self.current_theme_name = current_theme_name
        self.config = config_manager
        self.load_stylesheet("style.qss")

    # ── theme ──────────────────────────────────────────────
    def get_theme(self):
        t = THEMES.get(self.current_theme_name, THEMES["Dark (Default)"]).copy()

        # If a pairing is active, swap font_family to its `display` (hero)
        pairing = self.get_pairing()
        if pairing:
            t["font_family"] = pairing["display"]

        if self.config:
            alpha = self.config.get("transparency", 200)
            bg = t["background"]
            if "rgba" in bg:
                parts = bg.replace("rgba(", "").replace(")", "").split(",")
                if len(parts) >= 3:
                    t["background"] = (
                        f"rgba({parts[0].strip()}, {parts[1].strip()}, "
                        f"{parts[2].strip()}, {alpha})"
                    )
            elif "#" in bg:
                t["background"] = f"rgba(30, 30, 30, {alpha})"
        return t

    def get_style(self, element):
        return ""

    def get_available_themes(self):
        return list(THEMES.keys())

    # ── font pairings ──────────────────────────────────────
    @staticmethod
    def _classify_installed_fonts():
        """Read every font QFontDatabase knows about and classify into roles.

        Returns (display_list, ui_list, mono_list).
        Curated FONT_LIBRARY entries come first; remaining system fonts follow
        alphabetically. Monospace is detected by comparing advance widths of
        'i' and 'W'. Serifs are identified via KNOWN_SERIF_FONTS.
        """
        from PyQt6.QtGui import QFontDatabase, QFont, QFontMetrics

        all_families = QFontDatabase.families()
        available_lower = {f.lower(): f for f in all_families}

        def is_monospace(family):
            try:
                m = QFontMetrics(QFont(family, 12))
                return m.horizontalAdvance("i") == m.horizontalAdvance("W")
            except Exception:
                return False

        def curated_installed(groups):
            out = []
            for g in groups:
                for name in FONT_LIBRARY.get(g, []):
                    canon = available_lower.get(name.split(",")[0].strip().lower())
                    if canon and canon not in out:
                        out.append(canon)
            return out

        lib_display = curated_installed(["Designer Display", "Editorial Serif", "Modern Sans"])
        lib_ui      = curated_installed(["Modern Sans", "Classic / Safe"])
        lib_mono    = curated_installed(["Technical / Mono"])

        SKIP = ("@", "marlett", "symbol", "webdings", "wingdings", "ms outlook",
                "small fonts", "segoe mdl", "segoe ui emoji", "segoe ui symbol",
                "holo ", "nirmala", "mt extra", "bookshelf")

        def should_skip(name):
            nl = name.lower()
            return any(p in nl for p in SKIP)

        curated = set(lib_display) | set(lib_ui) | set(lib_mono)
        extra_mono, extra_proportional = [], []

        for family in sorted(all_families):
            if should_skip(family) or family in curated:
                continue
            fl = family.lower()
            if any(k in fl for k in ("mono", "code", "console", "courier", "typewriter", "fixed")):
                extra_mono.append(family)
            elif is_monospace(family):
                extra_mono.append(family)
            else:
                extra_proportional.append(family)

        def dedup(lst):
            seen = set(); out = []
            for x in lst:
                if x not in seen:
                    seen.add(x); out.append(x)
            return out

        display_pool = dedup(lib_display + extra_proportional)
        ui_pool      = dedup(lib_ui      + extra_proportional)
        mono_pool    = dedup(lib_mono    + extra_mono + ["Consolas", "Courier New"])
        return display_pool, ui_pool, mono_pool

    def _get_all_pairings(self):
        """Build pairings from every font installed on this system.

        Uses QFontDatabase to read all families (including Windows system fonts),
        classifies them as display / ui / mono, then generates one pairing per
        display font. Curated FONT_LIBRARY fonts are listed first. Result is
        cached for the app lifetime.
        """
        if hasattr(self, "_cached_pairings"):
            return self._cached_pairings

        try:
            display_pool, ui_pool, mono_pool = self._classify_installed_fonts()
        except Exception:
            self._cached_pairings = dict(FONT_PAIRINGS)
            return self._cached_pairings

        best_ui   = ui_pool[0]   if ui_pool   else "Segoe UI"
        best_mono = mono_pool[0] if mono_pool else "Courier New"

        result = {}

        # ── Proportional display pairings (sans + serif) ──────────────
        for display_font in display_pool[:12]:
            ui_font   = next((f for f in ui_pool   if f != display_font), best_ui)
            mono_font = next((f for f in mono_pool if f != display_font), best_mono)
            result[display_font] = {
                "display": display_font,
                "ui":      ui_font,
                "mono":    mono_font,
                "label":   ui_font,
                "mood":    f"{display_font}  ·  {ui_font}  ·  {mono_font}",
            }

        # ── Mono-display pairings for HUD / terminal themes ───────────
        for mono_font in mono_pool[:4]:
            hud_name = f"{mono_font} · HUD"
            if hud_name not in result:
                result[hud_name] = {
                    "display": mono_font,
                    "ui":      mono_font,
                    "mono":    mono_font,
                    "label":   mono_font,
                    "mood":    f"All-mono. {mono_font} across every widget role.",
                }

        # ── Static pairings whose fonts are fully installed ───────────
        from PyQt6.QtGui import QFontDatabase
        avail = {f.lower() for f in QFontDatabase.families()}

        def inst(n):
            return any(p.strip().lower() in avail for p in n.split(","))

        for name, p in FONT_PAIRINGS.items():
            if name not in result and inst(p["display"]) and inst(p["ui"]):
                result[name] = p

        if "System Safe" not in result:
            result["System Safe"] = FONT_PAIRINGS["System Safe"]

        self._cached_pairings = result
        return result

    def get_recommended_pairing(self, theme_name):
        """Return the best installed pairing name for the given theme."""
        style = THEME_PAIRING_STYLE.get(theme_name, "sans")
        all_pairings = self._get_all_pairings()

        serif_set = KNOWN_SERIF_FONTS | set(FONT_LIBRARY.get("Editorial Serif", []))
        mono_kw   = ("mono", "code", "console", "courier", "typewriter", "hud")

        def is_serif(font):
            return font in serif_set or any(
                s in font.lower() for s in ("serif", "garamond", "roman", "antiqua"))

        def is_mono(font):
            return any(k in font.lower() for k in mono_kw)

        for name, p in all_pairings.items():
            d = p["display"]
            if style == "serif" and is_serif(d):
                return name
            if style == "mono" and is_mono(d):
                return name
            if style == "sans" and not is_serif(d) and not is_mono(d):
                return name

        return next(iter(all_pairings), None)

    def get_available_pairings(self):
        return list(self._get_all_pairings().keys())

    def get_pairing(self):
        """Return currently-selected pairing dict, or None."""
        if not self.config:
            return None
        name = self.config.get("font_pairing")
        if not name:
            return None
        return self._get_all_pairings().get(name)

    def apply_pairing(self, name):
        """Apply a pairing by name, writing all per-widget font keys."""
        all_pairings = self._get_all_pairings()
        if name not in all_pairings and name != "None":
            return
        if not self.config:
            return

        if name == "None":
            self.config.set("font_pairing", None)
            return

        p = all_pairings[name]
        self.config.set("font_pairing", name)

        role_mapping = [
            ("font_family_time",  "display"),
            ("font_header",       "display"),
            ("font_media_main",   "ui"),
            ("font_calendar",     "ui"),
            ("font_stats",        "mono"),
            ("font_family_label", "label"),
            ("font_media_sub",    "ui"),
        ]
        for key, role in role_mapping:
            self.config.set(key, p[role])

    def get_font_library(self):
        """Return {group: [fonts...]} for UI pickers."""
        return FONT_LIBRARY

    # ── qss presets (unchanged) ────────────────────────────
    def get_available_presets(self):
        presets = set()
        if os.path.exists("themes"):
            for f in os.listdir("themes"):
                if f.endswith(".qss"):
                    presets.add(f)
        if hasattr(sys, "_MEIPASS"):
            bundled_path = os.path.join(sys._MEIPASS, "themes")
            if os.path.exists(bundled_path):
                for f in os.listdir(bundled_path):
                    if f.endswith(".qss"):
                        presets.add(f)
        return sorted(list(presets))

    def load_preset(self, filename):
        path = os.path.join("themes", filename)
        if not os.path.exists(path):
            if hasattr(sys, "_MEIPASS"):
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
        return getattr(self, "loaded_stylesheet", "")


# ─────────────────────────────────────────────────────────────
#  Install notes — show in a settings dialog tooltip.
# ─────────────────────────────────────────────────────────────
FONT_INSTALL_NOTES = """\
FONT SOURCES
────────────
• Google Fonts  — fonts.google.com (free, wide selection)
• Fontshare     — fontshare.com     (free designer fonts by ITF)
• System fonts  — already on Windows (Segoe UI, Helvetica Neue, etc.)

RECOMMENDED INSTALLS (free)
───────────────────────────
Google:     Inter, Space Grotesk, Fraunces, Instrument Serif,
            JetBrains Mono, DM Sans, DM Serif Display, Manrope,
            Plus Jakarta Sans, Outfit, Geist, Geist Mono,
            Playfair Display, Spectral, IBM Plex Mono, Space Mono

Fontshare:  Satoshi, General Sans, Clash Display, Clash Grotesk,
            Cabinet Grotesk, Switzer, Boska, Erode, Supreme,
            Melodrama, Ranade, Gambarino, Author, Panchang

To install on Windows: download the .ttf/.otf, right-click → Install.
Restart the widget app so Qt picks up the new fonts.
"""
