#!/usr/bin/env python3

import sys
print("Testing import in clawaii directory")
sys.path.insert(0, '.')

try:
    from core.config.settings import Settings
    
    settings = Settings()
    
    print(f"SUCCESS: {settings.application_name} v{settings.version}")
    print(f"Default model: {settings.default_model}") 
    print(f"Ollama host: {settings.ollama_host}")

except Exception as e:
    print("FAILED:", str(e))
    import traceback
    traceback.print_exc()