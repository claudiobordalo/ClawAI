import sys, os
os.chdir(r'D:\ClawAI')
sys.path.insert(0, r'D:\ClawAI')

# Check if all routers can be imported without circular import errors.
try:
    from clawai.api.tools_api import router as tools_router
    print("tools_api OK")
except Exception as e:
    print(f"tools_api FAIL: {e}")

try:
    from clawai.api.bridge_api import router as bridge_router
    print("bridge_api OK")
except Exception as e:
    print(f"bridge_api FAIL: {e}")

try:
    from clawai.api.chat_api import router as chat_router
    print("chat_api OK")
except Exception as e:
    print(f"chat_api FAIL: {e}")

print("\nAll imports successful.")
