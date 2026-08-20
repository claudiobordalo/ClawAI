#!/usr/bin/env python3

import sys
import os

# Add the project root to Python path 
project_root = 'D:\\\\ClawAI\\\\clawaii'
sys.path.insert(0, project_root)

print(f"Python Path updated with: {project_root}")
print("Current working directory:", os.getcwd())

try:
    # Try importing and creating settings
    from core.config.settings import Settings
    
    print("\n✓ Successfully imported Settings class")
    
    # Create an instance 
    settings = Settings()
    print("✓ Created Settings instance successfully")
    
    # Test properties  
    print(f"Application name: {settings.application_name}")
    print(f"Version: {settings.version}")  
    print(f"Debug mode: {settings.debug_mode}")
    print(f"Default model: {settings.default_model}")
    print(f"Ollama host: {settings.ollama_host}")
    
except Exception as e:
    print(f"\n✗ Error occurred:")
    import traceback
    traceback.print_exc()