"""
ClawAI Desktop - Entry Point

Inicia o backend, constrói/serva o frontend,
e lança a janela desktop via pywebview.
"""

import sys
import os
import asyncio
import threading
import webbrowser
from pathlib import Path
from contextlib import suppress

# Detecta se está empacotado pelo PyInstaller
IS_FROZEN = getattr(sys, "frozen", False)
EXECUTABLE_DIR = Path(sys.executable).parent if IS_FROZEN else Path.cwd()
APP_DIR = Path(__file__).parent.parent if not IS_FROZEN else EXECUTABLE_DIR

# Adiciona ao path para imports
if not IS_FROZEN:
    sys.path.insert(0, str(APP_DIR / "backend"))
    sys.path.insert(0, str(APP_DIR))


def find_resource(*paths: str) -> Path:
    """Encontra um recurso (funciona em dev e empacotado)."""
    if IS_FROZEN:
        base = Path(getattr(sys, "_MEIPASS", EXECUTABLE_DIR))
    else:
        base = APP_DIR
    return base / "frontend" / "dist" / Path(*paths)


def find_frontend_dir() -> Path:
    """Localiza o diretório do frontend."""
    if IS_FROZEN:
        return find_resource()
    # Modo desenvolvimento: usa o dist do Vite
    frontend_dist = APP_DIR / "frontend" / "dist"
    if frontend_dist.exists():
        return frontend_dist
    # Se não existe dist, tenta o src (para desenvolvimento com Vite dev server)
    frontend_src = APP_DIR / "frontend"
    if frontend_src.exists():
        return frontend_src
    raise FileNotFoundError(
        "Frontend não encontrado. Execute 'npm run build' no diretório frontend/."
    )


def start_backend() -> str:
    """Inicia o servidor backend e retorna a URL."""
    from desktop.server import get_server

    server = get_server(APP_DIR)
    try:
        url = server.start(timeout=20.0)
        print(f"[ClawAI] Backend iniciado: {url}")
        return url
    except Exception as e:
        print(f"[ClawAI] Erro ao iniciar backend: {e}", file=sys.stderr)
        raise


def build_frontend():
    """Constrói o frontend com Vite se necessário."""
    dist_dir = APP_DIR / "frontend" / "dist"
    if dist_dir.exists():
        # Verifica se o build é recente (menos de 1 hora)
        import time
        age = time.time() - dist_dir.stat().st_mtime
        if age < 3600:
            return True
    # Constrói
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "node", "-v"],
            capture_output=True,
            timeout=5,
        )
        # Se node não está disponível, tenta npm/npx direto
        result = subprocess.run(
            ["npx", "vite", "build"],
            cwd=str(APP_DIR / "frontend"),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            print("[ClawAI] Frontend construído com sucesso.")
            return True
        else:
            print(f"[ClawAI] Aviso: build do frontend falhou: {result.stderr[:200]}", file=sys.stderr)
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        print(f"[ClawAI] Aviso: não foi possível construir o frontend: {e}", file=sys.stderr)
        return False


def create_splash_window():
    """Cria uma janela de splash durante o carregamento."""
    import webview

    splash_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                background: #0a0a0f;
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100vh;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                overflow: hidden;
            }
            .container {
                text-align: center;
            }
            .logo {
                width: 80px;
                height: 80px;
                margin: 0 auto 24px;
                background: linear-gradient(135deg, #6366f1, #8b5cf6, #a78bfa);
                border-radius: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 40px;
                animation: pulse 2s ease-in-out infinite;
            }
            @keyframes pulse {
                0%, 100% { transform: scale(1); opacity: 1; }
                50% { transform: scale(1.05); opacity: 0.8; }
            }
            .title {
                color: #e2e8f0;
                font-size: 24px;
                font-weight: 600;
                margin-bottom: 8px;
            }
            .subtitle {
                color: #64748b;
                font-size: 14px;
                margin-bottom: 32px;
            }
            .spinner {
                width: 40px;
                height: 40px;
                margin: 0 auto;
                border: 3px solid #1e293b;
                border-top-color: #6366f1;
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
            }
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            .status {
                color: #475569;
                font-size: 12px;
                margin-top: 16px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">🤖</div>
            <div class="title">ClawAI</div>
            <div class="subtitle">Inteligência Artificial Desktop</div>
            <div class="spinner"></div>
            <div class="status" id="status">Inicializando...</div>
        </div>
    </body>
    </html>
    """
    return splash_html


def on_api_ready(window, api):
    """Callback quando a API do pywebview está pronta."""
    print("[ClawAI] Janela principal criada, carregando frontend...")


def on_window_closing(window):
    """Callback quando a janela está sendo fechada."""
    from desktop.server import get_server
    server = get_server(APP_DIR)
    print("[ClawAI] Parando servidor backend...")
    server.stop()
    print("[ClawAI] ClawAI Desktop encerrado.")


def main():
    """Função principal do ClawAI Desktop."""
    print("=" * 50)
    print("  ClawAI Desktop")
    print("=" * 50)

    # 1. Inicia o backend
    try:
        api_url = start_backend()
    except Exception as e:
        print(f"ERRO CRÍTICO: {e}", file=sys.stderr)
        input("Pressione Enter para sair...")
        sys.exit(1)

    # 2. Tenta construir o frontend
    build_frontend()

    # 3. Localiza o frontend
    try:
        frontend_dir = find_frontend_dir()
    except FileNotFoundError as e:
        print(f"ERRO: {e}", file=sys.stderr)
        print("Dica: Execute 'npm install && npm run build' no diretório frontend/", file=sys.stderr)
        input("Pressione Enter para sair...")
        sys.exit(1)

    # 4. Verifica se é dev server ou build
    is_dev = not (frontend_dir / "index.html").exists()

    # 5. Carrega a janela
    try:
        import webview

        if is_dev:
            # Modo desenvolvimento: conecta ao Vite dev server
            dev_url = "http://localhost:5173"
            print(f"[ClawAI] Modo desenvolvimento: {dev_url}")

            # Inicia o Vite dev server em background
            vite_process = None
            try:
                import subprocess
                vite_process = subprocess.Popen(
                    ["npx", "vite", "--port", "5173"],
                    cwd=str(APP_DIR / "frontend"),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                # Espera o dev server subir
                import time
                for _ in range(30):
                    time.sleep(0.5)
                    try:
                        import urllib.request
                        urllib.request.urlopen(dev_url, timeout=1)
                        break
                    except Exception:
                        pass
                else:
                    print("[ClawAI] Aviso: Vite dev server pode não estar pronto.", file=sys.stderr)
            except FileNotFoundError:
                print("[ClawAI] Aviso: npx não encontrado. Usando fallback.", file=sys.stderr)
        else:
            # Modo produção: serve do build
            index_path = str(frontend_dir / "index.html")
            dev_url = None
            vite_process = None

        # Cria a janela
        window_kwargs = {
            "title": "ClawAI",
            "width": 1280,
            "height": 800,
            "min_size": (900, 600),
            "resizable": True,
            "fullscreen": False,
            "frameless": IS_FROZEN,
            "shadow": True,
            "text_selection": True,
            "js_api": None,
        }

        if is_dev and dev_url:
            window_kwargs["url"] = dev_url
        else:
            window_kwargs["html"] = open(index_path, encoding="utf-8").read()

        # Cria e inicia a janela
        window = webview.create_window(**window_kwargs)
        window.events.closing += on_window_closing

        webview.start(
            debug=False,
            **window_kwargs,
        )

    except ImportError:
        print("[ClawAI] pywebview não instalado. Instalando...", file=sys.stderr)
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pywebview"])
        # Tenta novamente
        main()

    except Exception as e:
        print(f"[ClawAI] Erro ao iniciar janela: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        # Fallback: abre no navegador
        if is_dev and dev_url:
            print(f"[ClawAI] Abrindo no navegador: {dev_url}")
            webbrowser.open(dev_url)
        elif not is_dev:
            index_path = str(frontend_dir / "index.html")
            file_url = f"file://{os.path.abspath(index_path)}"
            print(f"[ClawAI] Abrindo no navegador: {file_url}")
            webbrowser.open(file_url)
        input("Pressione Enter para sair...")
        sys.exit(1)


if __name__ == "__main__":
    main()
