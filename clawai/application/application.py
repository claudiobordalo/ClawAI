from clawai.ai import ModelRole
from clawai.ai import ModelRouter
from clawai.prompts import PromptEngine
from clawai.providers.factory import ProviderFactory
from clawai.providers.implementations.ollama_provider import OllamaProvider
from clawai.providers.implementations.openai_provider import OpenAIProvider


class Application:

    def __init__(
        self,
        model_router: ModelRouter | None = None,
    ) -> None:
        # ProviderFactory é a fonte única da disponibilidade de providers.
        # A registration acontece durante o bootstrap da Application, antes
        # de qualquer chamada a ModelRouter.provider_for().
        ProviderFactory.register_provider("ollama", OllamaProvider)
        ProviderFactory.register_provider("openai", OpenAIProvider)

        self._model_router = model_router or ModelRouter()

        self._prompt_engine = PromptEngine(
            self._model_router.provider_for(ModelRole.CODER)
        )

    @property
    def prompt_engine(
        self,
    ) -> PromptEngine:

        return self._prompt_engine

    @property
    def model_router(
        self,
    ) -> ModelRouter:

        return self._model_router
