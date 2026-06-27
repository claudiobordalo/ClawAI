from __future__ import annotations

from typing import Dict, Optional, Type

from clawai.providers.base import BaseProvider


class ProviderFactory:
    _providers: Dict[str, Type[BaseProvider]] = {}

    @classmethod
    def register_provider(
        cls, name: str, provider_cls: Type[BaseProvider]
    ) -> None:
        cls._providers[name] = provider_cls

    @classmethod
    def unregister_provider(cls, name: str) -> None:
        cls._providers.pop(name, None)

    @classmethod
    def list_providers(cls) -> tuple[str, ...]:
        return tuple(sorted(cls._providers))

    @classmethod
    def get_provider(cls, name: str) -> Type[BaseProvider]:
        if name not in cls._providers:
            raise ValueError(
                f"Unknown provider: {name!r}. "
                f"Available: {list(cls._providers)}"
            )
        return cls._providers[name]

    @classmethod
    def create(
        cls,
        provider: str,
        **kwargs,
    ) -> BaseProvider:
        provider_cls = cls.get_provider(provider)
        return provider_cls(**kwargs)
