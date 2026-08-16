@echo off
title Flokus Academy - Create Desktop Shortcut
cd /d "%~dp0"

echo ==============================================
echo 🚀 Creating Flokus Academy Desktop Shortcut...
echo ==============================================

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0create_shortcut.ps1"

echo.
echo Press any key to exit.
pause >nul
