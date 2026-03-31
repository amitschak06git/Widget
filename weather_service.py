"""
YR / MET Norway weather service.
API: https://api.met.no/weatherapi/locationforecast/2.0/compact
No API key required. User-Agent header mandatory.
License: NLOD + CC 4.0 — attribution to MET Norway / yr.no required.
"""
import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from collections import defaultdict

CACHE_FILE = "weather_cache.json"
API_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
USER_AGENT = "DesktopWidgets/1.0 https://github.com/antigravity"

# YR symbol codes -> emoji
SYMBOL_EMOJI = {
    "clearsky":              "☀️",
    "fair":                  "🌤",
    "partlycloudy":          "⛅",
    "cloudy":                "☁️",
    "fog":                   "🌫",
    "lightrain":             "🌦",
    "rain":                  "🌧",
    "heavyrain":             "🌧",
    "lightrainshowers":      "🌦",
    "rainshowers":           "🌧",
    "heavyrainshowers":      "🌧",
    "lightrainandthunder":   "⛈",
    "rainandthunder":        "⛈",
    "heavyrainandthunder":   "⛈",
    "lightsleet":            "🌨",
    "sleet":                 "🌨",
    "heavysleet":            "🌨",
    "lightsnow":             "🌨",
    "snow":                  "❄️",
    "heavysnow":             "❄️",
    "lightsnowshowers":      "🌨",
    "snowshowers":           "❄️",
}

# Symbol code -> readable description
SYMBOL_DESC = {
    "clearsky":              "Clear sky",
    "fair":                  "Mostly clear",
    "partlycloudy":          "Partly cloudy",
    "cloudy":                "Cloudy",
    "fog":                   "Foggy",
    "lightrain":             "Light rain",
    "rain":                  "Rain",
    "heavyrain":             "Heavy rain",
    "lightrainshowers":      "Light showers",
    "rainshowers":           "Showers",
    "lightrainandthunder":   "Thunder showers",
    "rainandthunder":        "Thunderstorm",
    "lightsnow":             "Light snow",
    "snow":                  "Snow",
    "heavysnow":             "Heavy snow",
    "lightsleet":            "Light sleet",
    "sleet":                 "Sleet",
}


def _base_symbol(symbol_code: str) -> str:
    """Strip _day/_night suffix: 'partlycloudy_day' -> 'partlycloudy'."""
    return symbol_code.rsplit("_", 1)[0] if "_" in symbol_code else symbol_code


# 8-point compass — index = round(degrees / 45) % 8
_CARDINALS  = ["N",  "NE", "E",  "SE", "S",  "SW", "W",  "NW"]
# Arrow pointing in direction wind is BLOWING TO (opposite of from_direction)
_BLOW_ARROWS = ["↓",  "↙",  "←",  "↖",  "↑",  "↗",  "→",  "↘"]


# Beaufort scale: (max m/s, full label, short label)
_BEAUFORT = [
    (0.3,  "Calm",           "Calm"),
    (1.5,  "Light air",      "Lt air"),
    (3.3,  "Light breeze",   "Lt breeze"),
    (5.4,  "Gentle breeze",  "Gentle"),
    (7.9,  "Moderate",       "Moderate"),
    (10.7, "Fresh breeze",   "Fresh"),
    (13.8, "Strong breeze",  "Strong"),
    (17.1, "Near gale",      "Nr gale"),
    (20.7, "Gale",           "Gale"),
    (24.4, "Severe gale",    "Sv gale"),
    (28.4, "Storm",          "Storm"),
    (32.6, "Violent storm",  "Viol storm"),
    (float("inf"), "Hurricane", "Hurricane"),
]


def format_wind(speed_ms: float, unit: str = "kmh", short: bool = False) -> str:
    """
    Format wind speed from m/s into the requested unit string.
    unit: 'ms'  -> '3.2 m/s'
          'kmh' -> '11 km/h'
          'bft' -> 'Gentle breeze'  (short=True -> 'Gentle')
    """
    if unit == "ms":
        return f"{speed_ms:.1f} m/s"
    if unit == "kmh":
        return f"{round(speed_ms * 3.6)} km/h"
    # Beaufort
    for max_ms, label, short_label in _BEAUFORT:
        if speed_ms <= max_ms:
            return short_label if short else label
    return "Hurricane"


def degrees_to_cardinal(deg: float) -> str:
    """Convert wind_from_direction degrees to compass label, e.g. 225 -> 'SW'."""
    return _CARDINALS[round(deg / 45) % 8]


def degrees_to_arrow(deg: float) -> str:
    """Arrow pointing in the direction wind is blowing toward, e.g. from SW (225°) -> '↗'."""
    return _BLOW_ARROWS[round(deg / 45) % 8]


def get_emoji(symbol_code: str) -> str:
    return SYMBOL_EMOJI.get(_base_symbol(symbol_code), "🌡")


def get_description(symbol_code: str) -> str:
    return SYMBOL_DESC.get(_base_symbol(symbol_code), symbol_code.replace("_", " ").title())


def fetch_forecast(lat: float, lon: float) -> dict | None:
    """
    Returns raw YR API JSON, using a local cache that respects the Expires header.
    Returns None on network failure (cached data preserved if available).
    """
    cache_key = f"{lat:.4f},{lon:.4f}"

    # Try cache first
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, encoding="utf-8") as f:
                cached = json.load(f)
            if cached.get("key") == cache_key:
                expires = datetime.fromisoformat(cached["expires"])
                if datetime.now(timezone.utc) < expires:
                    return cached["data"]
        except Exception:
            pass

    # Fetch from API
    url = f"{API_URL}?lat={lat:.4f}&lon={lon:.4f}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())

            # Parse Expires header for cache duration
            expires_hdr = resp.headers.get("Expires", "")
            try:
                from email.utils import parsedate_to_datetime
                expires = parsedate_to_datetime(expires_hdr).isoformat()
            except Exception:
                expires = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()

            try:
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump({"key": cache_key, "expires": expires, "data": data}, f)
            except Exception:
                pass

            return data

    except urllib.error.URLError as e:
        print(f"[WeatherService] Network error: {e}")
        # Return stale cache if available
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, encoding="utf-8") as f:
                    return json.load(f).get("data")
            except Exception:
                pass
        return None


def parse_current(data: dict) -> dict | None:
    """Current conditions from the first timeseries entry."""
    if not data:
        return None
    try:
        ts = data["properties"]["timeseries"][0]
        details = ts["data"]["instant"]["details"]
        next1 = ts["data"].get("next_1_hours") or ts["data"].get("next_6_hours") or {}
        symbol = next1.get("summary", {}).get("symbol_code", "cloudy")
        precip = next1.get("details", {}).get("precipitation_amount", 0.0)

        wind_speed = round(details.get("wind_speed", 0), 1)
        wind_deg   = details.get("wind_from_direction", 0)
        wind_gust  = round(details.get("wind_speed_of_gust", wind_speed), 1)

        return {
            "temp":        round(details.get("air_temperature", 0)),
            "wind":        wind_speed,
            "wind_gust":   wind_gust,
            "wind_deg":    wind_deg,
            "wind_dir":    degrees_to_cardinal(wind_deg),
            "wind_arrow":  degrees_to_arrow(wind_deg),
            "humidity":    round(details.get("relative_humidity", 0)),
            "symbol":      symbol,
            "emoji":       get_emoji(symbol),
            "description": get_description(symbol),
            "precip":      precip,
        }
    except (KeyError, IndexError):
        return None


def parse_hourly(data: dict, hours: int = 12) -> list:
    """Next `hours` hourly entries."""
    if not data:
        return []
    result = []
    for ts in data["properties"]["timeseries"][:hours]:
        try:
            dt = datetime.fromisoformat(ts["time"].replace("Z", "+00:00"))
            details = ts["data"]["instant"]["details"]
            next1 = ts["data"].get("next_1_hours") or {}
            symbol = next1.get("summary", {}).get("symbol_code", "cloudy")
            precip = next1.get("details", {}).get("precipitation_amount", 0.0)
            wind_deg = details.get("wind_from_direction", 0)
            result.append({
                "hour":       dt.astimezone().strftime("%H"),
                "temp":       round(details.get("air_temperature", 0)),
                "emoji":      get_emoji(symbol),
                "precip":     precip,
                "wind":       round(details.get("wind_speed", 0), 1),
                "wind_arrow": degrees_to_arrow(wind_deg),
                "wind_dir":   degrees_to_cardinal(wind_deg),
            })
        except (KeyError, ValueError):
            continue
    return result


def parse_daily(data: dict, days: int = 5) -> list:
    """Daily min/max/dominant-symbol for the next `days` days, skipping today."""
    if not data:
        return []

    by_day = defaultdict(list)
    for ts in data["properties"]["timeseries"]:
        try:
            dt = datetime.fromisoformat(ts["time"].replace("Z", "+00:00")).astimezone()
            day_key = dt.strftime("%Y-%m-%d")
            details = ts["data"]["instant"]["details"]
            next6 = ts["data"].get("next_6_hours") or {}
            symbol = next6.get("summary", {}).get("symbol_code", "")
            by_day[day_key].append({
                "temp":   details.get("air_temperature", 0),
                "symbol": symbol,
            })
        except (KeyError, ValueError):
            continue

    today = datetime.now().strftime("%Y-%m-%d")
    result = []
    for day_key in sorted(by_day):
        if day_key == today:
            continue
        entries = by_day[day_key]
        temps = [e["temp"] for e in entries]
        symbols = [e["symbol"] for e in entries if e["symbol"]]
        dominant = max(set(symbols), key=symbols.count) if symbols else "cloudy"
        dt = datetime.strptime(day_key, "%Y-%m-%d")
        result.append({
            "day":    dt.strftime("%a"),
            "min":    round(min(temps)),
            "max":    round(max(temps)),
            "emoji":  get_emoji(dominant),
            "symbol": dominant,
        })
        if len(result) >= days:
            break

    return result
