"""
Script de build para criar o executável standalone da ClawAI Desktop.
Gera um arquivo .exe (Windows) ou executável (Linux/macOS) com tudo embutido.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def build():
    print("="*60)
    print("  Buildando ClawAI Desktop Standalone")
    print("="*60)
    
    # 1. Build do frontend
    print("\n[1/3] Buildando frontend...")
    frontend_dir = ROOT / "frontend"
    # Try common npm paths if npm is not in PATH
    npm_cmd = "npm"
    import shutil
    if not shutil.which("npm"):
        npm_cmd = r"C:\Program Files\nodejs\npm.cmd"
    
    result = subprocess.run(
        [npm_cmd, "run", "build"],
        cwd=frontend_dir,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"[ERRO] Falha no build do frontend:\n{result.stderr}")
        return False
    print("[OK] Frontend buildado.")
    
    # 2. Instalar dependências do Python
    print("\n[2/3] Verificando dependências...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", ".", "--quiet"],
        cwd=ROOT,
        check=True
    )
    print("[OK] Dependências instaladas.")
    
    # 3. Criar executável com PyInstaller
    print("\n[3/3] Criando executável...")
    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",  # Arquivo único
        "--name", "ClawAI",
        "--windowed",  # Sem janela de console (modo app)
        "--add-data", f"{ROOT / 'frontend' / 'dist'};frontend/dist",  # Inclui frontend
        "--add-data", f"{ROOT / 'clawai'};clawai",  # Inclui módulo clawai
        "--hidden-import", "uvicorn",
        "--hidden-import", "fastapi",
        "--hidden-import", "clawai",
        "main.py"
    ]
    
    result = subprocess.run(pyinstaller_cmd, cwd=ROOT)
    if result.returncode != 0:
        print("[ERRO] Falha no build do PyInstaller.")
        return False
    
    print("\n" + "="*60)
    print("  Build Concluído!")
    print("="*60)
    print(f"  Executável: {ROOT / 'dist' / 'ClawAI.exe'}")
    print("="*60)
    
    return True

if __name__ == "__main__":
    build()
