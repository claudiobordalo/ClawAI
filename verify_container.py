from clawai.bootstrap import build_container
from clawai.chat.chat_service import ChatService
from clawai.autopilot.auto_implement import AutoImplementService
from clawai.workspace.manager import WorkspaceManager
import sys

try:
    container = build_container()
    chat = container.resolve(ChatService)
    auto_implement = container.resolve(AutoImplementService)
    wm = container.resolve(WorkspaceManager)

    print("✅ ChatService resolveu com sucesso.")
    print(f"✅ AutoImplementService resolveu com sucesso.")
    print(f"✅ WorkspaceManager resolveu com sucesso.")
    print("✅ Integração de Container: OK")
except Exception as e:
    print(f"❌ Falha na integração de container: {e}")
    sys.exit(1)
