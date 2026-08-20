from __future__ import annotations

import os
from typing import Any

from ollama import Client

from clawai.providers.base import BaseProvider
from clawai.providers.base import ProviderResponse
from clawai.providers.factory.factory import ProviderFactory


class OllamaProvider(BaseProvider):
    def __init__(
        self,
        model: str = "gemma4:latest",
        host: str | None = None,
        **kwargs: Any,
    ) -> None:
        self._model = model
        self._host = (host or os.getenv("OLLAMA_HOST") or "http://127.0.0.1:11434").rstrip("/")
        self._client = Client(host=self._host)

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> ProviderResponse:
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

        response = self._client.chat(
            model=self._model,
            messages=messages,
            options={
                "temperature": 0.2,
            },
        )

        content = ""
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0

        if isinstance(response, dict):
            content = (
                response.get("message", {}).get("content", "")
                or response.get("response", "")
                or ""
            )
            usage = response.get("usage") or {}
            prompt_tokens = int(usage.get("prompt_eval_count", 0) or 0)
            completion_tokens = int(usage.get("eval_count", 0) or 0)
            total_tokens = prompt_tokens + completion_tokens
        else:
            message = getattr(response, "message", None)
            content = getattr(message, "content", "") or ""
            prompt_tokens = int(getattr(response, "prompt_eval_count", 0) or 0)
            completion_tokens = int(getattr(response, "eval_count", 0) or 0)
            total_tokens = prompt_tokens + completion_tokens

        return ProviderResponse(
            content=content,
            model=self._model,
            provider="ollama",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            elapsed_ms=0.0,
        )


ProviderFactory.register_provider("ollama", OllamaProvider)