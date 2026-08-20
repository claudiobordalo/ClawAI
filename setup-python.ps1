# ClawAI Python Setup Script
# Run this script to install Python and required dependencies for ClawAI

Write-Host "ClawAI Python Setup" -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
$pythonPath = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonPath) {
    Write-Host "Python not found. Please install Python 3.12+ from https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host ""
    $install = Read-Host "Would you like to download the Python installer? (Y/N)"
    if ($install -eq "Y" -or $install -eq "y") {
        Start-Process "https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe"
        Write-Host ""
        Write-Host "After installation, run this script again." -ForegroundColor Yellow
        exit
    }
} else {
    $pythonVersion = & python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
}

Write-Host ""
Write-Host "Installing ClawAI dependencies..." -ForegroundColor Cyan

# Install dependencies
pip install -r "$PSScriptRoot\requirements.txt"

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "You can now run ClawAI with:" -ForegroundColor White
Write-Host "  cd frontend" -ForegroundColor Gray
Write-Host "  npm run electron:dev" -ForegroundColor Gray
Write-Host ""
