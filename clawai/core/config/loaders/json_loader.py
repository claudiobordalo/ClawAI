from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from clawai.core.config.loader import ConfigLoader
from clawai.core.config.exceptions import ConfigurationLoadError


class JsonLoader(ConfigLoader):
    """
    Loader responsável por carregar arquivos JSON.
    """

    def __init__(self, file_path: str | Path) -> None:
        self._file_path = Path(file_path)

    def load(self) -> dict[str, Any]:
        if not self._file_path.exists():
            raise ConfigurationLoadError(
                f"Configuration file '{self._file_path}' was not found."
            )

        try:
            with self._file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, dict):
                raise ConfigurationLoadError(
                    "Root element of configuration must be a dictionary."
                )

            return data

        except json.JSONDecodeError as exc:
            raise ConfigurationLoadError(
                f"Invalid JSON file: {exc}"
            ) from exc