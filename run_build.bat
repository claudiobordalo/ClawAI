@echo off
REM Simple build script for ClawAI

cd /d "D:\ClawAI"

echo Building ClawAI executable...
echo.

pyinstaller --clean --onefile --windowed --name="ClawAI-Studio" main.py

if %errorlevel% equ 0 (
    echo.
    echo ✓ Build completed successfully!
    echo Executable is in the 'dist' folder
) else (
    echo.
    echo ✗ Build failed with error level %errorlevel%
)

pause