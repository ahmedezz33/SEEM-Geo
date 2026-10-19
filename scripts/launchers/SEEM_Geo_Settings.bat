@echo off
REM =============================================================
REM  SEEM Geo Settings Dialog (standalone)
REM  Double-click to open the 6-tab settings editor without
REM  launching the full GUI. Useful for quick DPI / inversion
REM  tweaks before a batch CLI run.
REM =============================================================
title SEEM Geo Settings
python -c "from seem_geo.settings import show_dialog; show_dialog()"
if errorlevel 1 pause
