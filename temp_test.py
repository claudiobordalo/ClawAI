import sys

# Test if we can import the model manager module directly 
try:
    from clawaii.core.model_manager import ModelManager, ModelInfo
    
    print("SUCCESS: Imported ModelManager and ModelInfo")
    
    # Create a simple mock settings class to test instantiation  
    class MockSettings:
        def __init__(self):
            self.default_model = "test-model:latest"
            self.enabled_providers = ["ollama"]
            
    try:
        mock_settings = MockSettings()
        model_manager = ModelManager(mock_settings)
        print("SUCCESS: Created ModelManager instance")
        
        # Test basic methods
        default_model = model_manager.get_default_model() 
        print(f"Default model test passed: {default_model}")
        
        available_models = model_manager.get_available_models()
        print(f"Available models count test passed: {len(available_models)}") 
        
    except Exception as e:
        import traceback  
        print(f"ERROR creating instance or calling methods: {e}")
        traceback.print_exc()

except ImportError as ie:
    print(f"Import error occurred: {ie}") 
    # Let's try to understand what files exist in the expected location
    import os
    clawaii_path = "clawaii"
    if os.path.exists(clawaii_path):
        print("Contents of clawaii directory:")
        for root, dirs, files in os.walk(clawaii_path):  
            level = root.replace(clawaii_path, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")
    else: 
        print("clawaii directory does not exist")

except Exception as e:
    import traceback
    print(f"Unexpected error during test: {e}")  
    traceback.print_exc()