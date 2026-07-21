from __future__ import annotations

import os
from typing import Any

import google.generativeai as genai

from clawai.providers.base import BaseProvider
from clawai.providers.base import ProviderResponse
from clawai.providers.factory.factory import ProviderFactory


class GoogleProvider(BaseProvider):
    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        api_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        self._model = model

        key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("GOOGLE_API_KEY não configurada.")

        genai.configure(api_key=key)

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> ProviderResponse:
        model = genai.GenerativeModel(
            model_name=self._model,
            system_instruction=system_prompt if system_prompt else None,
        )

        response = model.generate_content(prompt)

        usage = getattr(response, "usage_metadata", None)

        return ProviderResponse(
            content=getattr(response, "text", "") or "",
            model=self._model,
            provider="google",
            prompt_tokens=int(getattr(usage, "prompt_token_count", 0) or 0),
            completion_tokens=int(getattr(usage, "candidates_token_count", 0) or 0),
            total_tokens=int(getattr(usage, "total_token_count", 0) or 0),
            elapsed_ms=0.0,
        )


ProviderFactory.register_provider("google", GoogleProvider)