from __future__ import annotations

import os
from typing import Any

from openai import OpenAI

from clawai.providers.base import BaseProvider
from clawai.providers.base import ProviderResponse
from clawai.providers.factory.factory import ProviderFactory


class OpenAIProvider(BaseProvider):
    def __init__(
        self,
        model: str = "gpt-5",
        api_key: str | None = None,
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        self._model = model

        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY não configurada.")

        self._client = OpenAI(
            api_key=key,
            base_url=base_url or os.getenv("OPENAI_BASE_URL") or None,
        )

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

        response = self._client.responses.create(
            model=self._model,
            input=messages,
        )

        usage = getattr(response, "usage", None)

        return ProviderResponse(
            content=getattr(response, "output_text", "") or "",
            model=self._model,
            provider="openai",
            prompt_tokens=int(getattr(usage, "input_tokens", 0) or 0),
            completion_tokens=int(getattr(usage, "output_tokens", 0) or 0),
            total_tokens=int(getattr(usage, "total_tokens", 0) or 0),
            elapsed_ms=0.0,
        )


ProviderFactory.register_provider("openai", OpenAIProvider)