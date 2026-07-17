import sys
sys.path.insert(0, r'D:\ClawAI')
try:
    import clawai
    print("OK - clawai imported successfully")
except Exception as e:
    print(f"FAIL - {type(e).__name__}: {e}")
