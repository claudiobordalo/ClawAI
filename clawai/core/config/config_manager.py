from __future__ import annotations

from typing import Any

from clawai.core.config.loader import ConfigLoader
from clawai.core.config.settings import Settings
from clawai.core.config.validator import ConfigValidator


class ConfigManager:
    """
    Centraliza o carregamento e acesso às configurações da aplicação.
    """

    def __init__(
        self,
        loader: ConfigLoader,
        validator: ConfigValidator | None = None,
    ) -> None:
        self._loader = loader
        self._validator = validator

        self._config: dict[str, Any] = {}
        self._settings = Settings()

    def load(self) -> None:
        self._config = self._loader.load()

        if self._validator is not None:
            self._validator.validate(self._config)

    def reload(self) -> None:
        self.load()

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def has(self, key: str) -> bool:
        return key in self._config

    def all(self) -> dict[str, Any]:
        return self._config.copy()

    @property
    def settings(self) -> Settings:
        return self._settings