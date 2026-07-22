@echo off
title Flokus Academy - Sonny PC Setup Helper
cd /d "%~dp0"

echo =======================================================
echo 🎓 Flokus Academy - Setup & Launcher for Sonny's PC
echo =======================================================
echo.
echo Step 1: Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: Python is not installed or not in PATH!
    echo Please download & install Python 3.10+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b
)

echo.
echo Step 2: Installing required packages...
pip install -r requirements.txt --quiet

echo.
echo Step 3: Creating Desktop Shortcut...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0create_shortcut.ps1"

echo.
echo =======================================================
echo 🎉 Setup complete! You can now double-click the
echo 'Flokus Academy' icon on your Desktop anytime to launch!
echo =======================================================
echo.
pause
