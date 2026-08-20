#!/usr/bin/env python3

# Direct test of settings import from project root 
import sys
print("Testing Settings module...")

try:
    # Add the clawaii directory to Python path  
    project_root = 'D:\\\\ClawAI\\\\clawaii'
    
    print(f"Adding {project_root} to sys.path")
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        
    import os
    config_path = f'{project_root}/core/config/settings.py' 
    print(f"Checking file: {config_path}")
    print(f"File exists: {os.path.exists(config_path)}")
    
    # Try the actual import  
    from core.config.settings import Settings
    
    settings = Settings()
    
    print("SUCCESS!")
    print(f"Application name: {settings.application_name}") 
    print(f"Version: {settings.version}")
    print(f"Default model: {settings.default_model}")
    print(f"Ollama host: {settings.ollama_host}")

except Exception as e:
    import traceback
    print("ERROR:")
    traceback.print_exc()