@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   ClawAI Build Validation
echo ========================================

set ERRORS=0

REM Check Python portable
echo [1/6] Checking Python portable...
if exist "python\python.exe" (
    echo [OK] Python executable found
) else (
    echo [ERROR] Python executable not found
    set /a ERRORS+=1
)

REM Check clawai source
echo [2/6] Checking clawai source...
if exist "clawai\server.py" (
    echo [OK] clawai source found
) else (
    echo [ERROR] clawai source not found
    set /a ERRORS+=1
)

REM Check frontend build
echo [3/6] Checking frontend build...
if exist "frontend\dist\index.html" (
    echo [OK] Frontend build found
) else (
    echo [ERROR] Frontend build not found
    set /a ERRORS+=1
)

REM Check electron-builder config
echo [4/6] Checking electron-builder config...
findstr /C:"electron-builder" package.json >nul
if %errorlevel% equ 0 (
    echo [OK] electron-builder configured
) else (
    echo [ERROR] electron-builder not configured
    set /a ERRORS+=1
)

REM Check NSIS config
echo [5/6] Checking NSIS config...
findstr /C:"nsis" package.json >nul
if %errorlevel% equ 0 (
    echo [OK] NSIS configured
) else (
    echo [ERROR] NSIS not configured
    set /a ERRORS+=1
)

REM Check Inno Setup
echo [6/6] Checking Inno Setup...
if exist "build_scripts\installer.iss" (
    echo [OK] Inno Setup script found
) else (
    echo [ERROR] Inno Setup script not found
    set /a ERRORS+=1
)

echo.
if %ERRORS% equ 0 (
    echo [SUCCESS] All checks passed!
) else (
    echo [FAILED] %ERRORS% check(s) failed
    exit /b 1
)

echo ========================================
pause
