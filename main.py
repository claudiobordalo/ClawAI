"""
ClawAI Main Entry Point - Integra backend e frontend para distribuição standalone.
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

# Configura variáveis de ambiente
os.environ.setdefault("CLAWAI_MODE", "standalone")


def ensure_frontend():
    """Garante que o frontend está buildado."""
    frontend_dist = ROOT / "frontend" / "dist"

    if not frontend_dist.exists():
        print("\n[INFO] Buildando frontend...")
        try:
            import subprocess

            frontend_dir = ROOT / "frontend"
            result = subprocess.run(
                ["npm", "run", "build"],
                cwd=frontend_dir,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"[WARN] Falha no build: {result.stderr[:200]}")
                return False
            print("[OK] Frontend buildado com sucesso.")
        except Exception as e:
            print(f"[WARN] Erro ao buildar: {e}")
            return False

    return True


def start_server():
    """Inicia o servidor FastAPI com frontend estático."""
    import uvicorn
    from api import app as backend_app

    print("\n" + "=" * 60)
    print("  ClawAI Desktop Iniciado")
    print("=" * 60)
    print("  Frontend: http://127.0.0.1:8000")
    print("  Backend:  http://127.0.0.1:8000/api")
    print("=" * 60 + "\n")

    uvicorn.run(backend_app, host="127.0.0.1", port=8000, log_level="info")


def main():
    """Função principal."""
    print("Iniciando ClawAI Desktop...")

    # Garante frontend
    ensure_frontend()

    # Inicia servidor
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Aguarda início
    time.sleep(2)

    # Abre navegador
    try:
        webbrowser.open("http://127.0.0.1:8000")
        print("[INFO] Navegador aberto em http://127.0.0.1:8000")
    except Exception:
        print("[INFO] Abra http://127.0.0.1:8000 no navegador")

    # Mantém rodando
    try:
        server_thread.join()
    except KeyboardInterrupt:
        print("\n[INFO] ClawAI Desktop encerrado.")


if __name__ == "__main__":
    main()
