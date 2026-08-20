"""Quick test: does the backend import and start correctly?"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test imports
from main import app
print("OK: main.app imported successfully")

# Check routers
routes = [r for r in app.routes]
print(f"OK: {len(routes)} routes registered")

# Check key routers exist
route_paths = [str(r.path) if hasattr(r, 'path') else '' for r in routes]
for expected in ['/health', '/api/chat', '/api/tree', '/api/file']:
    found = any(expected in p for p in route_paths)
    status = "OK" if found else "MISSING"
    print(f"  {status}: {expected}")

print("\nBackend validation complete.")
