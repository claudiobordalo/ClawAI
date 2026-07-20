#!/usr/bin/env python3

import sys
print("Python executable:", sys.executable)
print("Current working directory:", sys.path[0])

# Add project root to Python path  
project_root = 'D:\\\\ClawAI\\\\clawaii'
sys.path.insert(0, project_root)

try:
    print(f"Trying to import from: {project_root}")
    
    # Try importing the settings module directly
    import core.config.settings
    
    print("✓ Successfully imported core.config.settings")
    
    # Create an instance 
    from core.config.settings import Settings
    settings = Settings()
    
    print(f"✓ Created Settings successfully")  
    print(f"Application name: {settings.application_name}")
    print(f"Version: {settings.version}") 
    
except Exception as e:
    print("✗ Error:")
    import traceback
    traceback.print_exc()

print("\nDone.")