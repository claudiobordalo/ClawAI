import ast, sys, os

files = [
    r'D:\ClawAI\clawai\main.py',
    r'D:\ClawAI\clawai\desktop_server.py',
]
ok = True
for f in files:
    try:
        with open(f) as fh:
            ast.parse(fh.read())
        print(f"OK  {f}")
    except SyntaxError as e:
        print(f"SX  {f}: {e}")
        ok = False

sys.exit(0 if ok else 1)
