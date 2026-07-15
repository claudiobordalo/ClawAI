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
from clawai.workspace.manager import WorkspaceManager
from clawai.ai.router import AIRouter
from clawai.chat.chat_service import ChatService
from clawai.cognition.pipeline import CognitionPipeline
from clawai.search.search_engine import SearchEngine
from clawai.agents.registry.registry import registry
from clawai.agents.factory.factory import factory
from clawai.agents.agent import GeneralAgent
from clawai.agents.specialist_agent import SpecialistAgent

def build_container() -> ServiceContainer:

    container = ServiceContainer()

    # Storage & Workspace
    storage = StorageManager(JsonStorageProvider())
    workspace = Workspace()
    
    # Memory (ChromaDB)
    embedding = OllamaEmbeddingService()
    vector_store = ChromaVectorStore()
    memory_manager = MemoryManager(
        embedding_service=embedding,
        vector_store=vector_store,
        chunker=Chunker(),
    )

    # AI & Router
    ai = AIManager()
    ai.register(OllamaProvider(model="gemma4:latest"))
    
    router = AIRouter()
    container.register(AIRouter, router)

    # Search Engine
    # Note: SearchEngine currently uses JSON memory globals. 
    # In a full refactor, we would inject MemoryManager here.
    search_engine = SearchEngine()

    # Cognition Pipeline
    # Wires together Supervisor, Planner, Debate, Judge
    pipeline = CognitionPipeline(
        router=router,
        provider_name="ollama",
        memory_manager=memory_manager,
        search_engine=search_engine,
    )

    # Chat Service
    chat_service = ChatService(router=router, pipeline=pipeline)
    container.register(ChatService, chat_service)

    # Auto Implement
    from clawai.autopilot.auto_implement import AutoImplementService
    auto_implement = AutoImplementService(router=router)
    container.register(AutoImplementService, auto_implement)

    # Workspace Manager
    wm = WorkspaceManager()
    container.register(WorkspaceManager, wm)

    # Projects
    projects = ProjectManager(storage)
    container.register(ProjectManager, projects)

    # Register Agents
    registry.register("general", GeneralAgent)
    registry.register("specialist", SpecialistAgent)
    
    # Register Container
    container.register(ServiceContainer, container)

    return container
