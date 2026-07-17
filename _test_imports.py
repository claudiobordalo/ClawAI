import sys
sys.path.insert(0, r'D:\ClawAI')

# Test bootstrap imports
imports_to_test = [
    'clawai.ai.ai_manager',
    'clawai.ai.providers.ollama_provider',
    'clawai.core.container',
    'clawai.memory.chunker',
    'clawai.memory.memory_manager',
    'clawai.memory.providers.ollama_embedding_service',
    'clawai.memory.stores.chroma.chroma_vector_store',
    'clawai.projects.services.project_manager',
    'clawai.storage.providers.json_storage_provider',
    'clawai.storage.services.storage_manager',
    'clawai.workspace.workspace',
    'clawai.workspace.manager',
    'clawai.agents.registry.registry',
    'clawai.agents.factory.factory',
    'clawai.agents.agent',
    'clawai.agents.specialist_agent',
]

for imp in imports_to_test:
    try:
        __import__(imp)
        print(f"OK   {imp}")
    except Exception as e:
        print(f"FAIL {imp}: {type(e).__name__}: {e}")
