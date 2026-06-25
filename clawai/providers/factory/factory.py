from __future__ import annotations

import os

from clawai.providers.base import BaseProvider
from clawai.providers.implementations.ollama_provider import OllamaProvider


class ProviderFactory:

    @staticmethod
    def create() -> BaseProvider:

        model = os.getenv(
            "CLAWAI_MODEL",
            "qwen2.5-coder:14b",
        )

        return OllamaProvider(
            model=model,
        )