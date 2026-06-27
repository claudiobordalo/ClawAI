from __future__ import annotations

import os

from ollama import Client

from clawai.providers.base import BaseProvider
from clawai.providers.base import ProviderResponse


class OllamaProvider(BaseProvider):

    def __init__(
        self,
        model: str | None = None,
        host: str = "http://localhost:11434",
        **kwargs,
    ) -> None:


        self._model = (
            model
            or os.getenv("CLAWAI_MODEL")
            or "qwen3:8b"
        )

        self._client = Client(host=host)

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> ProviderResponse:

        messages = []

        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt,
            })

        messages.append({
            "role": "user",
            "content": prompt,
        })

        response = self._client.chat(
            model=self._model,
            messages=messages,
            options={
                "temperature": 0.0,
                "num_predict": 250,
                "num_ctx": 4096,
            },
        )

        return ProviderResponse(
            content=response["message"]["content"],
            provider="ollama",
            model=self._model,
        )
