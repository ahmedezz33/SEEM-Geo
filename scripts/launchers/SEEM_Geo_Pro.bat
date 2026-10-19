@echo off
REM =============================================================
REM  SEEM Geo Pro GUI Launcher (v1.2.2+)
REM  Double-click to open the Pro GUI with Mode selector,
REM  3-column dashboard, settings dialog, and viewer.
REM =============================================================
title SEEM Geo Pro
color 1F
echo.
echo ================================================================
echo    SEEM Geo Pro - ERT ^& MASW Processing Suite
echo ================================================================
echo.
echo  Starting Pro GUI...
echo.

python -c "from seem_geo.gui.pro_main_window import main; main()"

if errorlevel 1 (
    echo.
    echo  [!] Launch failed. Possible causes:
    echo      1. SEEM Geo not installed. Run:
    echo         pip install --upgrade --force-reinstall --no-deps ^
"https://github.com/ahmedezz33/SEEM-Geo/archive/refs/heads/main.zip"
    echo.
    echo      2. Wrong Python version. Check: python --version
    echo.
    echo      3. Missing tkinter (rare on Windows).
    echo.
    pause
)
