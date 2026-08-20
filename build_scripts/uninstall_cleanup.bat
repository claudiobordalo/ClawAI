@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   ClawAI Uninstall Cleanup
echo ========================================

echo [1/4] Removing from Startup...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "ClawAI" /f >nul 2>&1

echo [2/4] Removing from Context Menu...
reg delete "HKCR\Directory\Background\shell\ClawAI" /f >nul 2>&1

echo [3/4] Removing User Data...
set USER_DATA=%APPDATA%\ClawAI
if exist "%USER_DATA%" (
    rmdir /s /q "%USER_DATA%"
    echo [SUCCESS] User data removed
)

echo [4/4] Removing Local Data...
set LOCAL_DATA=%LOCALAPPDATA%\ClawAI
if exist "%LOCAL_DATA%" (
    rmdir /s /q "%LOCAL_DATA%"
    echo [SUCCESS] Local data removed
)

echo ========================================
echo   Cleanup Complete!
echo ========================================
pause
