#!/usr/bin/env python3

# Test to verify Settings module can be imported and instantiated correctly  

import sys
print("Python executable:", sys.executable)
sys.path.insert(0, '.')

try:
    print("\nTesting import of core.config.settings...")
    
    from core.config.settings import Settings
    
    # Create an instance 
    settings = Settings()
    
    print(f"✓ SUCCESS: Created {settings.application_name} v{settings.version}")
    print("Settings loaded successfully!")
    
except Exception as e:
    print(f"✗ FAILED to load settings module:")
    import traceback
    traceback.print_exc()

print("\nDone.")