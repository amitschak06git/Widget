@echo off
echo Installing PyInstaller...
py -m pip install pyinstaller

echo Cleaning up previous builds...
rmdir /s /q build
rmdir /s /q dist
del *.spec

echo Building DesktopWidgets...
py -m PyInstaller --noconsole --onefile --name "DesktopWidgets" --add-data "config.json;." --add-data "style.qss;." --add-data "themes;themes" manager.py

echo Build Complete!
echo You can find the executable in the 'dist' folder.
