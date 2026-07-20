@echo off
REM Simple build script for ClawAI

echo Building ClawAI executable...
echo.

cd /d "D:\ClawAI"

REM Check if frontend is built
if not exist "frontend\dist" (
    echo Frontend dist directory not found. Building frontend with npm...
    call npm run build
)

if not exist "frontend\dist\index.html" (
    echo Error: Could not find built frontend files.
    pause
    exit /b 1
)

echo Installing PyInstaller if needed...
python -m pip install pyinstaller

echo Creating executable with PyInstaller...
python -m PyInstaller ^
--clean ^
--onefile ^
--windowed ^
--name=ClawAI-Studio ^
--icon=frontend\src\assets\icon.ico ^
main.py

if %errorlevel% equ 0 (
    echo.
    echo ✓ Build completed successfully!
    echo Executable is in the 'dist' folder
) else (
    echo.
    echo ✗ Build failed with error level %errorlevel%
)

pause