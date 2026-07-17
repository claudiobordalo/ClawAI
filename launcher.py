"""
ClawAI Launcher – Desktop Native Mode.

Este script é o ponto de entrada alternativo para a versão desktop.
Inicia backend + frontend em uma janela nativa (PyWebView).
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("CLAWAI_MODE", "desktop")


def main():
    """Inicia o ClawAI Studio no modo desktop nativo."""
    print("=" * 60)
    print("  ClawAI Studio")
    print("=" * 60)
    print()

    try:
        from clawai.desktop_server import start_desktop
        start_desktop()
    except ImportError as e:
        print(f"[ERROR] Falha ao importar: {e}")
        print("Instale: pip install pywebview httpx psutil")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
