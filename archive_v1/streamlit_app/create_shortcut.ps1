# PowerShell script to create Desktop shortcut for Flokus Academy
$AppDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$TargetBat = Join-Path $AppDir "run_flokus.bat"
$DesktopDir = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop)
$ShortcutPath = Join-Path $DesktopDir "Flokus Academy.lnk"

Write-Host "Creating Desktop shortcut..."
Write-Host "Target: $TargetBat"
Write-Host "Shortcut: $ShortcutPath"

$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $TargetBat
$Shortcut.WorkingDirectory = $AppDir
$Shortcut.IconLocation = "shell32.dll,14" # Rocket / Computer launcher icon
$Shortcut.Description = "Launch Flokus Academy Learning Hub"
$Shortcut.Save()

Write-Host "✅ Desktop shortcut successfully created at: $ShortcutPath"
