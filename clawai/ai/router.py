from __future__ import annotations

from enum import Enum
from typing import Iterator

import clawai.providers  # noqa: F401

from clawai.core.config.settings import Settings
from clawai.providers.base import BaseProvider
from clawai.providers.factory import ProviderFactory


class ModelRole(str, Enum):
    DEFAULT = "default"
    PLANNER = "planner"
    CODER = "coder"
    REVIEWER = "reviewer"
    VISION = "vision"
    EMBEDDING = "embedding"


class ModelRouter:
    def __init__(
        self,
        settings: Settings | None = None,
        provider_factory: type[ProviderFactory] = ProviderFactory,
        provider: str = "ollama",
    ) -> None:
        self._settings = settings or Settings()
        self._provider_factory = provider_factory
        self._provider = provider

    def model_for(
        self,
        role: ModelRole | str,
    ) -> str:
        resolved_role = ModelRole(role)

        models = {
            ModelRole.DEFAULT: self._settings.default_model,
            ModelRole.PLANNER: self._settings.planner_model,
            ModelRole.CODER: self._settings.coder_model,
            ModelRole.REVIEWER: self._settings.reviewer_model,
            ModelRole.VISION: self._settings.vision_model,
            ModelRole.EMBEDDING: self._settings.embedding_model,
        }

        return models[resolved_role]

    def provider_for(
        self,
        role: ModelRole | str,
    ) -> BaseProvider:
        return self._provider_factory.create(
            provider=self._provider,
            settings=self._settings,
            model=self.model_for(role),
        )

    def ask(
        self,
        prompt: str,
        role: ModelRole | str = ModelRole.DEFAULT,
        system_prompt: str | None = None,
    ) -> str:
        provider = self.provider_for(role)
        response = provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
        )
        return response.content or ""

    def stream(
        self,
        prompt: str,
        role: ModelRole | str = ModelRole.DEFAULT,
        system_prompt: str | None = None,
    ) -> Iterator[str]:
        provider = self.provider_for(role)

        stream_generate = getattr(provider, "stream_generate", None)
        if callable(stream_generate):
            yield from stream_generate(
                prompt=prompt,
                system_prompt=system_prompt,
            )
            return

        response = provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
        )
        yield response.content or ""


AIRouter = ModelRouter
Model = ModelRole
