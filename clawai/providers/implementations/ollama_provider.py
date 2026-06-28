from __future__ import annotations

import os
from typing import Any, Iterator

from ollama import Client

from clawai.providers.base import BaseProvider
from clawai.providers.base import ProviderResponse


class OllamaProvider(BaseProvider):
    def __init__(
        self,
        model: str | None = None,
        settings: Any | None = None,
        host: str | None = None,
        **kwargs,
    ) -> None:
        self._model = (
            model
            or os.getenv("CLAWAI_MODEL")
            or "qwen3:8b"
        )

        if host is None and settings is not None:
            host = getattr(settings, "ollama_host", None)

        self._client = Client(host=host or "http://localhost:11434")

    def _build_messages(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []

        if system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        return messages

    def _chat_options(self) -> dict[str, object]:
        return {
            "temperature": 0.0,
            "num_predict": 250,
            "num_ctx": 4096,
        }

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> ProviderResponse:
        response = self._client.chat(
            model=self._model,
            messages=self._build_messages(prompt, system_prompt),
            options=self._chat_options(),
        )

        return ProviderResponse(
            content=response["message"]["content"],
            provider="ollama",
            model=self._model,
        )

    def stream_generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> Iterator[str]:
        stream = self._client.chat(
            model=self._model,
            messages=self._build_messages(prompt, system_prompt),
            options=self._chat_options(),
            stream=True,
        )

        for chunk in stream:
            content = ""

            if isinstance(chunk, dict):
                content = (
                    chunk.get("message", {})
                    .get("content", "")
                    or chunk.get("response", "")
                )
            else:
                message = getattr(chunk, "message", None)
                if message is not None:
                    content = getattr(message, "content", "") or ""
                if not content:
                    content = getattr(chunk, "response", "") or ""

            if content:
                yield content