@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   ClawAI Auto-Start Setup
echo ========================================

REM Check if running as admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Run as Administrator
    pause
    exit /b 1
)

REM Get installation path
set INSTALL_PATH=%ProgramFiles%\ClawAI
set EXE_PATH=%INSTALL_PATH%\ClawAI.exe

if not exist "%EXE_PATH%" (
    echo [ERROR] ClawAI not found at %EXE_PATH%
    pause
    exit /b 1
)

REM Add to startup
echo [1/2] Adding to Windows Startup...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "ClawAI" /t REG_SZ /d "%EXE_PATH%" /f

if %errorlevel% equ 0 (
    echo [SUCCESS] Added to startup
) else (
    echo [ERROR] Failed to add to startup
)

REM Add to context menu (optional)
echo [2/2] Adding to context menu...
reg add "HKCR\Directory\Background\shell\ClawAI" /v "" /t REG_SZ /d "Open ClawAI Here" /f
reg add "HKCR\Directory\Background\shell\ClawAI" /v "Icon" /t REG_SZ /d "%EXE_PATH%" /f
reg add "HKCR\Directory\Background\shell\ClawAI\command" /v "" /t REG_SZ /d "%EXE_PATH%" /f

if %errorlevel% equ 0 (
    echo [SUCCESS] Added to context menu
) else (
    echo [ERROR] Failed to add to context menu
)

echo ========================================
echo   Setup Complete!
echo ========================================
pause
