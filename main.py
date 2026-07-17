"""
ClawAI Studio – Entry Point (Desktop Native)

Este é o entry point principal do ClawAI.
- Inicia backend FastAPI + frontend React em uma janela nativa (PyWebView)
- Não depende de navegador externo
- Não depende de .bat ou .cmd
- Detecta automaticamente modelos (LM Studio / Ollama / OpenAI)
- Distribuível como único .exe via PyInstaller
"""

import os
import sys
from pathlib import Path

# Adiciona o diretório raiz ao Python path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Configura variáveis de ambiente
os.environ.setdefault("CLAWAI_MODE", "desktop")


def main():
    """Inicia o ClawAI Studio no modo desktop nativo."""
    print("=" * 60)
    print("  ClawAI Studio")
    print("  https://github.com/nicholasgn00/ClawAI")
    print("=" * 60)
    print()

    try:
        from clawai.desktop_server import start_desktop
        start_desktop()
    except ImportError as e:
        print(f"[ERROR] Falha ao importar módulo desktop: {e}")
        print()
        print("Instale as dependências necessárias:")
        print("  pip install pywebview httpx psutil")
        print()
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Erro ao iniciar: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
