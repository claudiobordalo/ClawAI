from clawai.ai import ModelRole
from clawai.ai import ModelRouter
from clawai.prompts import PromptEngine


class Application:

    def __init__(
        self,
        model_router: ModelRouter | None = None,
    ) -> None:

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
