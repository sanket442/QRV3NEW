@echo off
title QR Label Pro - Direct Print Launcher
echo ========================================================
echo   QR Label Pro - Direct Print Mode
echo ========================================================
echo.
echo [IMPORTANT]
echo 1. Ensure your Thermal Printer is set as the DEFAULT printer in Windows Settings.
echo 2. Ensure the App server is running (npm run dev).
echo.
echo Launching Chrome in Silent Print Mode...
echo.

if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --kiosk-printing "http://localhost:5175"
) else (
    if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
        start "" "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --kiosk-printing "http://localhost:5175"
    ) else (
        echo Chrome not found in standard locations. Trying Edge...
        start msedge --kiosk-printing "http://localhost:5175"
    )
)

echo Done. You can close this window.
pause
