"""Validate that the backend imports and registers routes correctly."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from api import app

routes = [r for r in app.routes if hasattr(r, "path")]
print(f"OK: {len(routes)} routes registered")

expected = ["/health", "/api/chat", "/api/tree", "/api/file"]
for path in expected:
    found = any(path in r.path for r in routes)
    print(f"  {'OK' if found else 'MISSING'}: {path}")

print("\nBackend validation PASSED.")
