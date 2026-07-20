import sys

# Add project root to path 
sys.path.insert(0, '.')

try:
    from core.config.settings import Settings
    
    s = Settings()
    
    print("SUCCESS!")
    print(f"App name: {s.application_name}")
    print(f"Version: {s.version}")  
    print(f"Default model: {s.default_model}")
    print(f"Ollama host: {s.ollama_host}")

except Exception as e:
    print(f"FAILED with error:")
    import traceback
    traceback.print_exc()