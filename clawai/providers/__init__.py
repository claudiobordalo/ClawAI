from .factory import ProviderFactory

from .implementations.openai_provider import OpenAIProvider
try:
    from .implementations.ollama_provider import OllamaProvider
except ModuleNotFoundError:
    OllamaProvider = None

ProviderFactory.register_provider(
    "openai",
    OpenAIProvider,
)

ProviderFactory.register_provider(
    "ollama",
    OllamaProvider,
)

__all__ = [
    "ProviderFactory",
    "OpenAIProvider",
    "OllamaProvider",
]