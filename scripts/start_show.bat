@echo off
echo ===================================
echo   STARTING DVD MOTOR SHOW
echo ===================================

echo.
echo Locating and running Python script...
echo.

REM --- CONFIGURE THIS SECTION ---
REM 1. Path to your Python.exe (find it by typing 'where python' in cmd)
SET PYTHON_EXE="C:\\Users\\YourName\\AppData\\Local\\Programs\\Python\\Python311\\python.exe"

REM 2. Path to the Python script you saved
SET SCRIPT_PATH="%~dp0play_and_eject.py"
REM --- END CONFIGURATION ---


%PYTHON_EXE% %SCRIPT_PATH%

echo.
echo ===================================
echo   SHOW IS COMPLETE
echo ===================================
pause
