from pathlib import Path

from clawai.ai import (
    LLMClient,
    MockProvider,
)
from clawai.prompts import PromptEngine


class Application:

    def __init__(self) -> None:

        self._client = LLMClient(
            MockProvider()
        )

        self._prompt_engine = PromptEngine(
            self._client
        )

    @property
    def prompt_engine(
        self,
    ) -> PromptEngine:

        return self._prompt_engine
