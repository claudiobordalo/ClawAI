from __future__ import annotations

import os

from openai import OpenAI

from clawai.providers.base import BaseProvider
from clawai.providers.base import ProviderResponse


class OpenAIProvider(BaseProvider):

    def __init__(
        self,
        model: str = "gpt-5",
        **kwargs,
    ) -> None:


        self._model = model

        self._client = OpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
        )

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> ProviderResponse:

        messages = []

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
            content=response.output_text,
            model=self._model,
            provider="openai",
            prompt_tokens=getattr(usage, "input_tokens", 0),
            completion_tokens=getattr(usage, "output_tokens", 0),
            total_tokens=getattr(usage, "total_tokens", 0),
        )
