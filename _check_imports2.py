import sys, os
os.chdir(r'D:\ClawAI')
sys.path.insert(0, r'D:\ClawAI')

# Check if the full application factory works.
try:
    from clawai.api.application import create_app
    app = create_app()
    print(f"create_app OK - {len(app.routes)} routes")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"\nFAIL: {e}")
