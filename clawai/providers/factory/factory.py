from __future__ import annotations

import os

from clawai.core.config.settings import Settings
from clawai.providers.base import BaseProvider
from clawai.providers.implementations.ollama_provider import OllamaProvider


class ProviderFactory:

    @staticmethod
    def create(
        settings: Settings | None = None,
        model: str | None = None,
    ) -> BaseProvider:

        resolved_settings = settings or Settings()
        resolved_model = (
            model
            or os.getenv("CLAWAI_MODEL")
            or resolved_settings.default_model
        )

        return OllamaProvider(
            model=resolved_model,
            host=resolved_settings.ollama_host,
        )
