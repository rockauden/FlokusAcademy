@echo off
title Flokus Academy Launcher
cd /d "%~dp0"

echo ==============================================
echo 🚀 Launching Flokus Academy...
echo ==============================================

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: Python is not installed or not in PATH!
    echo Please install Python 3.10+ and select "Add Python to PATH".
    pause
    exit /b
)

:: Verify/Install dependencies
echo 📦 Checking python dependencies...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo ⚠️ Note: Some dependencies failed to verify, attempting launch anyway...
)

:: Launch Streamlit App
echo.
echo 🎨 Starting Streamlit Server...
streamlit run app.py

pause
