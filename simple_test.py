#!/usr/bin/env python3

# Test script to check if we can import the settings module directly 
import sys
print("Python executable:", sys.executable)

try:
    # Add project root directory to path - using forward slashes for compatibility  
    sys.path.insert(0, 'D:/ClawAI/clawaii')
    
    print("\nTrying direct import of Settings...")
    
    from core.config.settings import Settings
    
    settings = Settings()
    
    print("✓ SUCCESS: Successfully imported and instantiated Settings!")
    print(f"  Application name: {settings.application_name}")
    print(f"  Version: {settings.version}") 
    print(f"  Default model: {settings.default_model}")
    print(f"  Ollama host: {settings.ollama_host}")
    
except Exception as e:
    print("✗ FAILED to import:")
    import traceback
    traceback.print_exc()