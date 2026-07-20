#!/usr/bin/env python3

import sys
sys.path.insert(0, '.')

# Import our classes  
from clawaii.core.model_manager import ModelManager, ModelInfo

print("Testing model manager imports...")

try:
    # Test basic instantiation 
    print("Creating mock settings...")
    
    class MockSettings:
        def __init__(self):
            self.default_model = "test-model:latest"
            self.enabled_providers = ["ollama"]
            
    mock_settings = MockSettings()
    print("Mock settings created")
    
    model_manager = ModelManager(mock_settings)
    print("Model manager instantiated successfully!")
    
    # Test methods
    default_model = model_manager.get_default_model() 
    print(f"Default model: {default_model}")
    
    available_models = model_manager.get_available_models()
    print(f"Available models count: {len(available_models)}")
    
except Exception as e:
    import traceback
    print(f"Error during testing: {e}")  
    traceback.print_exc()

print("Test completed.")