from core.config.settings import Settings

s = Settings()
print(f'Success: {s.application_name} v{s.version}')
print(f'Default model: {s.default_model}')  
print(f'Ollama host: {s.ollama_host}')