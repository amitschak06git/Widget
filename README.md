# AntiGravity Desktop Widgets

A polished desktop widget suite for Windows built with Python and PyQt6, inspired by Apple's macOS Sonoma aesthetic.

---

## Widgets

| Widget | Description |
|---|---|
| **Clock** | Multi-timezone clocks with thin typography |
| **Date** | Day name and full date display |
| **Header** | Large day-of-week ambient display |
| **Media** | Now-playing with album art and playback controls |
| **Stats** | Live CPU / RAM / Disk circular indicators |
| **Calendar** | Monthly calendar with watermark overlay |
| **Weather** | YR/MET Norway forecast — expandable hourly + 5-day view |

---

## Features

- **Apple (Sonoma) theme** — frosted glass panels, SF Pro typography, iOS system colours
- **10 built-in themes** — Dark, Light, Material, Neon, Ubuntu, Glassmorphism, Neumorphism, Cyber HUD, Concept Dark Glass, Apple Sonoma
- **Custom QSS themes** — drop `.qss` files into the `themes/` folder
- **Smooth animations** — 200ms fade in / 150ms fade out on show/hide
- **Widget lock** — prevent accidental repositioning via tray menu
- **Multi-monitor safe** — positions clamped to visible screen on restore
- **Launch at startup** — Windows registry toggle in Settings (no admin rights needed)
- **Drag to move** — click and drag any widget
- **Resize on hover** — grab the bottom-right corner
- **Per-widget opacity** — right-click any widget for opacity control
- **System tray** — toggle each widget individually

---

## Weather Widget

Powered by the **MET Norway Locationforecast API** (yr.no) — free, no API key required.

- Current temperature, condition, wind direction + speed, humidity
- Expandable to show **hourly forecast** (12 hours) and **5-day forecast**
- Wind speed in **km/h**, **m/s**, or **Beaufort descriptive** (Calm → Gale → Hurricane)
- Wind direction as compass label (SW) + directional arrow (↗)
- Gusts shown when significantly above sustained speed
- Precipitation amounts highlighted in blue
- Respects API `Expires` header — never hammers the server
- Stale cache served on network failure

**Setup:** Settings → Weather → enter latitude, longitude, and display name.

> Weather data: [MET Norway / yr.no](https://www.yr.no) — licensed under NLOD + CC 4.0

---

## Requirements

```
Python 3.10+
PyQt6
psutil
winrt-runtime
pycaw
tzlocal
```

Install dependencies:
```bash
pip install PyQt6 psutil winrt-runtime pycaw tzlocal
```

---

## Running from Source

```bash
cd Widget
python manager.py
```

---

## Building the Executable

```bash
python -m PyInstaller --noconsole --onefile --name "DesktopWidgets" \
  --add-data "config.json;." \
  --add-data "style.qss;." \
  --add-data "themes;themes" \
  manager.py
```

Or run `build_app.bat` (cleans previous build first).

Output: `dist/DesktopWidgets.exe` — standalone, no Python installation required.

---

## Project Structure

```
Widget/
├── manager.py              # App entry point, tray, widget lifecycle
├── base_widget.py          # Base class — drag, resize, animations, hover, lock
├── config_manager.py       # JSON config persistence
├── theme_manager.py        # Theme engine + 10 built-in themes
├── settings_window.py      # Settings dialog (tabbed)
├── startup_manager.py      # Windows startup registry helper
│
├── clock_widget.py         # Multi-timezone clock
├── date_widget.py          # Date display
├── header_widget.py        # Large day-name header
├── media_widget.py         # Now-playing media widget
├── stats_widget.py         # CPU / RAM / Disk monitor
├── calendar_widget.py      # Monthly calendar
├── weather_widget.py       # YR weather — expandable forecast
│
├── weather_service.py      # YR API fetch, cache, parsing, wind formatting
├── system_media.py         # WinRT system media integration
├── calendar_service.py     # Calendar provider abstraction
├── google_calendar.py      # Google Calendar OAuth provider
├── theme_button.py         # Custom media control button
│
├── style.qss               # Global stylesheet
├── themes/                 # Additional QSS theme files
│   ├── apple.qss           # Apple (Sonoma) theme
│   ├── glass.qss
│   ├── neon.qss
│   └── ...
│
├── config.json             # User configuration
└── build_app.bat           # PyInstaller build script
```

---

## Configuration

`config.json` is created automatically on first run. Key settings:

| Key | Default | Description |
|---|---|---|
| `theme` | `"Concept (Dark Glass)"` | Active theme name |
| `locked` | `false` | Lock all widget positions |
| `weather_lat` | `null` | Location latitude |
| `weather_lon` | `null` | Location longitude |
| `wind_unit` | `"kmh"` | `"kmh"`, `"ms"`, or `"bft"` |
| `widget_opacities` | `{}` | Per-widget alpha (0–255) |
| `positions` | `{}` | Saved XY positions per widget |

---

## Attribution

- Weather data: [MET Norway / yr.no](https://api.met.no) — NLOD + CC 4.0
- Inspired by macOS Sonoma desktop widgets
