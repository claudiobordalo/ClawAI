from clawai.providers.base import BaseProvider
from .prompt_manager import PromptManager


class PromptEngine:

    def __init__(
        self,
        provider: BaseProvider,
    ) -> None:

        self._provider = provider
        self._prompts = PromptManager()

    def execute(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:

        system = self._prompts.load(system_prompt)

        response = self._provider.generate(
            prompt=user_prompt,
            system_prompt=system,
        )

        return response.content
