#!/usr/bin/env python3

import sys
sys.path.insert(0, 'D:\\\\ClawAI\\\\clawaii')

try:
    from core.config.settings import Settings
    
    print("✓ Successfully imported Settings")
    
    settings = Settings()
    print(f"✓ Created Settings instance: {settings.application_name}")
    print(f"  Version: {settings.version}")  
    print(f"  Debug mode: {settings.debug_mode}")
    print(f"  Default model: {settings.default_model}")
    
except Exception as e:
    print(f"✗ Error importing or creating settings: {e}")
    import traceback
    traceback.print_exc()