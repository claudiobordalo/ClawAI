
from __future__ import annotations
import subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"

steps = [
    ("Compile api.py",[sys.executable,"-m","py_compile","api.py"],ROOT),
    ("Compile package",[sys.executable,"-m","compileall","clawai"],ROOT),
    ("Frontend build",["npm","run","build"],FRONTEND),
    ("Pytest",["pytest","-q"],ROOT),
]

ok=0
print("="*70)
print("ClawAI Verify")
print("="*70)
start=time.perf_counter()

for name,cmd,cwd in steps:
    print(f"\n[{name}]")
    r=subprocess.run(cmd,cwd=cwd,text=True,capture_output=True)
    if r.returncode==0:
        ok+=1
        print("OK")
    else:
        print("FAILED")
    if r.stdout:
        print(r.stdout[-4000:])
    if r.stderr:
        print(r.stderr[-4000:])

print("\n"+"="*70)
print(f"Passed {ok}/{len(steps)} checks")
print(f"Elapsed {(time.perf_counter()-start):.2f}s")
