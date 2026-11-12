@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    py -3.13 -m pip install --upgrade mss opencv-python numpy
    if %errorlevel%==0 goto done
)
python -m pip install --upgrade mss opencv-python numpy
if not %errorlevel%==0 goto fail

:done
echo.
echo Installation complete. Run start.bat
pause
exit /b 0

:fail
echo.
echo Installation failed. Install Python 3.13, then try again.
pause
exit /b 1
