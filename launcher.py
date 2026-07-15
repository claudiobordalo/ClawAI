"""
ClawAI Launcher - Inicia o backend e serve o frontend como um aplicativo standalone.
Este script é o ponto de entrada para a versão "desktop" da ClawAI.
"""

import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

# Adiciona o diretório raiz ao Python path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

def start_server():
    """Inicia o servidor FastAPI."""
    import uvicorn
    from api import app
    
    print("\n" + "="*60)
    print("  ClawAI Desktop - Backend Iniciado")
    print("="*60)
    print(f"  Acesse: http://127.0.0.1:8000")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

def serve_frontend():
    """
    Verifica se o frontend está buildado e serve os arquivos estáticos.
    Se não estiver, tenta buildar automaticamente.
    """
    frontend_dist = ROOT / "frontend" / "dist"
    
    if not frontend_dist.exists():
        print("\n[INFO] Frontend não encontrado. Buildando...")
        try:
            import subprocess
            frontend_dir = ROOT / "frontend"
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-e", "."],
                cwd=ROOT,
                check=True
            )
            result = subprocess.run(
                ["npm", "run", "build"],
                cwd=frontend_dir,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"[WARN] Falha no build do frontend: {result.stderr}")
                return False
        except Exception as e:
            print(f"[WARN] Erro ao buildar frontend: {e}")
            return False
    
    return True

def main():
    """Função principal do launcher."""
    print("Iniciando ClawAI Desktop...")
    
    # Verifica e serve o frontend
    if not serve_frontend():
        print("[AVISO] O frontend não está disponível. Iniciando apenas o backend.")
    
    # Inicia o servidor em uma thread separada
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Aguarda o servidor iniciar
    time.sleep(2)
    
    # Abre o navegador automaticamente
    try:
        webbrowser.open("http://127.0.0.1:8000")
        print("[INFO] Navegador aberto em http://127.0.0.1:8000")
    except Exception:
        print("[INFO] Abra http://127.0.0.1:8000 no navegador")
    
    # Mantém o programa rodando
    try:
        server_thread.join()
    except KeyboardInterrupt:
        print("\n[INFO] ClawAI Desktop encerrado.")

if __name__ == "__main__":
    main()
