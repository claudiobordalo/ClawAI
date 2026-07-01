from __future__ import annotations

import os
from typing import Any

from anthropic import Anthropic

from clawai.providers.base import BaseProvider
from clawai.providers.base import ProviderResponse
from clawai.providers.factory.factory import ProviderFactory


class AnthropicProvider(BaseProvider):
    def __init__(
        self,
        model: str = "claude-3-5-sonnet-latest",
        api_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        self._model = model

        key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError("ANTHROPIC_API_KEY não configurada.")

        self._client = Anthropic(api_key=key)

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> ProviderResponse:
        messages: list[dict[str, str]] = [
            {
                "role": "user",
                "content": prompt,
            }
        ]

        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": 1024,
            "messages": messages,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        response = self._client.messages.create(**kwargs)

        content = ""
        for block in getattr(response, "content", []):
            if getattr(block, "type", "") == "text":
                content += getattr(block, "text", "")

        usage = getattr(response, "usage", None)

        return ProviderResponse(
            content=content.strip(),
            model=self._model,
            provider="anthropic",
            prompt_tokens=int(getattr(usage, "input_tokens", 0) or 0),
            completion_tokens=int(getattr(usage, "output_tokens", 0) or 0),
            total_tokens=int(getattr(usage, "input_tokens", 0) or 0) + int(getattr(usage, "output_tokens", 0) or 0),
            elapsed_ms=0.0,
        )


ProviderFactory.register_provider("anthropic", AnthropicProvider)