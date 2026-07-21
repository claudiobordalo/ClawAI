#!/usr/bin/env python3

# Simple direct test 
import sys  
print("Testing settings import...")

try:
    # Add project root to path directly in code
    sys.path.insert(0, '.')
    
    print(f"Python paths: {sys.path[:3]}")
    
    from core.config.settings import Settings
    
    s = Settings()
    
    print("SUCCESS!")
    print(f"App name: {s.application_name}")
    print(f"Version: {s.version}")  
    print(f"Default model: {s.default_model}")

except Exception as e:
    print(f"FAILED with error:")
    import traceback
    traceback.print_exc()

print("\nDone.")