from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from clawai.storage.interfaces.storage_provider import StorageProvider


class JsonStorageProvider(StorageProvider):

    def __init__(
        self,
        root: Path = Path("data"),
    ) -> None:

        self._root = root
        self._root.mkdir(
            parents=True,
            exist_ok=True,
        )

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def read(
        self,
        key: str,
    ) -> dict[str, Any] | list[Any]:

        path = self._path(key)

        if not path.exists():
            return {}

        return json.loads(
            path.read_text(
                encoding="utf-8",
            )
        )

    def write(
        self,
        key: str,
        data: dict[str, Any] | list[Any],
    ) -> None:

        path = self._path(key)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            json.dumps(
                data,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def delete(
        self,
        key: str,
    ) -> None:

        path = self._path(key)

        if path.exists():
            path.unlink()

    def _path(
        self,
        key: str,
    ) -> Path:

        return self._root / f"{key}.json"
