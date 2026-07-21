import sys
sys.path.insert(0, '.')

try:
    from core.config.settings import Settings
    print("Settings imported successfully")
    
    settings = Settings()
    print(f"Application: {settings.application_name}")
    print(f"Version: {settings.version}")
    print(f"Debug mode: {settings.debug_mode}")
    
except Exception as e:
    print(f"Error importing Settings: {e}")
    import traceback
    traceback.print_exc()

try:
    from core.model_manager import ModelManager 
    print("ModelManager imported successfully")
except Exception as e:
    print(f"Error importing ModelManager: {e}")