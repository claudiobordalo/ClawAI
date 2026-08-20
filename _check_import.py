import sys; sys.path.insert(0, r'D:\ClawAI')
try:
    from clawai.api import app as backend_app
    print("Import OK")
except Exception as e:
    print(f"ERROR: {e}")
