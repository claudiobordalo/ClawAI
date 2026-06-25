from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from clawai.core.config.loader import ConfigLoader
from clawai.core.config.exceptions import ConfigurationLoadError


class YamlLoader(ConfigLoader):
    """
    Loader responsável por carregar arquivos YAML.
    """

    def __init__(self, file_path: str | Path) -> None:
        self._file_path = Path(file_path)

    def load(self) -> dict[str, Any]:
        """
        Carrega um arquivo YAML.

        Returns:
            dict[str, Any]
        """
        if not self._file_path.exists():
            raise ConfigurationLoadError(
                f"Configuration file '{self._file_path}' was not found."
            )

        try:
            with self._file_path.open("r", encoding="utf-8") as file:
                data = yaml.safe_load(file) or {}

            if not isinstance(data, dict):
                raise ConfigurationLoadError(
                    "Root element of configuration must be a dictionary."
                )

            return data

        except yaml.YAMLError as exc:
            raise ConfigurationLoadError(
                f"Invalid YAML file: {exc}"
            ) from exc