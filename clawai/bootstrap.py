from __future__ import annotations

from clawai.ai.ai_manager import AIManager
from clawai.ai.providers.ollama_provider import OllamaProvider
from clawai.core.container import ServiceContainer
from clawai.memory.chunker import Chunker
from clawai.memory.memory_manager import MemoryManager
from clawai.memory.providers.ollama_embedding_service import OllamaEmbeddingService
from clawai.memory.stores.chroma.chroma_vector_store import ChromaVectorStore
from clawai.projects.services.project_manager import ProjectManager
from clawai.storage.providers.json_storage_provider import JsonStorageProvider
from clawai.storage.services.storage_manager import StorageManager
from clawai.workspace.workspace import Workspace


def build_container() -> ServiceContainer:

    container = ServiceContainer()

    storage = StorageManager(
        JsonStorageProvider(),
    )

    workspace = Workspace()

    embedding = OllamaEmbeddingService()

    vector_store = ChromaVectorStore()

    memory = MemoryManager(
        embedding_service=embedding,
        vector_store=vector_store,
        chunker=Chunker(),
    )

    ai = AIManager()

    ai.register(
        OllamaProvider(
            model="qwen2.5-coder:14b",
        )
    )

    projects = ProjectManager(storage)

    container.register(StorageManager, storage)
    container.register(ProjectManager, projects)
    container.register(Workspace, workspace)
    container.register(MemoryManager, memory)
    container.register(AIManager, ai)

    return container
