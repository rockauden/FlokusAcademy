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

:: Back up the school database before anything opens it. A missing backup
:: drive is a problem for this evening, not a reason to lose a school
:: morning, so this warns and carries on either way. backup_db.py explains
:: the retention policy and why it uses SQLite's backup API rather than
:: copying the file.
echo.
echo 💾 Backing up the school database...
python backup_db.py
if %errorlevel% neq 0 (
    echo.
    echo ⚠️ Backup did not run - check that Google Drive is running.
    echo    Starting anyway. Fix it after school.
    echo.
)

:: Launch Streamlit App
echo.
echo 🎨 Starting Streamlit Server...
streamlit run app.py

pause
