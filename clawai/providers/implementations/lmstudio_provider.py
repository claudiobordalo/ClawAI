from __future__ import annotations

import os
from typing import Any

from openai import OpenAI

from clawai.providers.base import BaseProvider
from clawai.providers.base import ProviderResponse
from clawai.providers.factory.factory import ProviderFactory


class LMStudioProvider(BaseProvider):
    def __init__(
        self,
        model: str = "local-model",
        base_url: str | None = None,
        api_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        settings = kwargs.get("settings")
        if settings is not None:
            base_url = base_url or getattr(settings, "lmstudio_base_url", None)
            api_key = api_key or getattr(settings, "lmstudio_api_key", None)
            model = model or getattr(settings, "lmstudio_default_model", model)

        self._model = model
        self._base_url = (
            base_url
            or os.getenv("LMSTUDIO_BASE_URL")
            or "http://127.0.0.1:1234/v1"
        ).rstrip("/")
        self._api_key = api_key or os.getenv("LMSTUDIO_API_KEY") or "lm-studio"
        self._client = OpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
        )

    def available_models(self) -> list[str]:
        try:
            response = self._client.models.list()
        except Exception:
            return []

        data = getattr(response, "data", response)
        models: list[str] = []

        for item in data or []:
            if isinstance(item, dict):
                model_id = item.get("id") or item.get("name")
            else:
                model_id = getattr(item, "id", None) or getattr(item, "name", None)

            if model_id:
                models.append(str(model_id))

        return sorted(set(models))

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
            provider="lmstudio",
            prompt_tokens=int(getattr(usage, "input_tokens", 0) or 0),
            completion_tokens=int(getattr(usage, "output_tokens", 0) or 0),
            total_tokens=int(getattr(usage, "total_tokens", 0) or 0),
            elapsed_ms=0.0,
        )


ProviderFactory.register_provider("lmstudio", LMStudioProvider)
