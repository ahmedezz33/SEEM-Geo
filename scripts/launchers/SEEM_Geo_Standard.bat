@echo off
REM =============================================================
REM  SEEM Geo Standard GUI Launcher
REM  Double-click to open the classic GUI.
REM =============================================================
title SEEM Geo
color 1F
echo.
echo  Starting SEEM Geo standard GUI...
echo.

python -m seem_geo gui

if errorlevel 1 (
    echo.
    echo  [!] Launch failed. Try:
    echo      pip install --upgrade --force-reinstall --no-deps ^
"https://github.com/ahmedezz33/SEEM-Geo/archive/refs/heads/main.zip"
    pause
)
