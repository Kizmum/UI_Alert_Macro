@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    py -3.13 ui_alert_macro_gui.py
    if %errorlevel%==0 exit /b 0
)
python ui_alert_macro_gui.py
if %errorlevel%==0 exit /b 0

echo.
echo Could not launch UI Alert Macro v5.3.
echo Run install.bat and verify Python 3.13 is installed.
pause
exit /b 1
