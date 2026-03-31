"""
Manages Windows registry entry for launch-at-startup.
Writes to HKCU so no admin rights are required.
"""
import os
import sys

APP_NAME = "AntiGravityWidgets"
REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _get_launch_command():
    """Returns the command to register. Uses the .exe when frozen, else python + script."""
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle
        return f'"{sys.executable}"'
    else:
        script = os.path.abspath(os.path.join(os.path.dirname(__file__), "manager.py"))
        return f'"{sys.executable}" "{script}"'


def is_enabled():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except (FileNotFoundError, OSError):
        return False


def set_enabled(enabled: bool):
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_SET_VALUE)
        if enabled:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _get_launch_command())
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except OSError as e:
        print(f"Startup registry error: {e}")
