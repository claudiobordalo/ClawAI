# Build script for ClawAI executable

Write-Host "Building ClawAI executable..." -ForegroundColor Green

# Change to project directory 
Set-Location "D:\ClawAI"

# Install dependencies if needed (uncomment the line below if you need it)
# pip install -r requirements.txt

try {
    # Run PyInstaller with proper escaping
    & pyinstaller --clean --onefile --windowed --name="ClawAI-Studio" "main.py"
    
    Write-Host "`n✅ Build completed successfully!" -ForegroundColor Green
    
    if (Test-Path "dist\ClawAI-Studio.exe") {
        Write-Host "Executable location: dist\ClawAI-Studio.exe" -ForegroundColor Yellow
    }
} catch {
    Write-Host "`n❌ Build failed with error:" -ForegroundColor Red
    Write-Error $_.Exception.Message 
}

Write-Host "`nPress any key to continue..."  
$null = $host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")