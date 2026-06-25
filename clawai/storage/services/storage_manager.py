from __future__ import annotations

from typing import Any

from clawai.storage.interfaces.storage_provider import StorageProvider


class StorageManager:

    def __init__(
        self,
        provider: StorageProvider,
    ) -> None:

        self._provider = provider

    def exists(
        self,
        key: str,
    ) -> bool:

        return self._provider.exists(key)

    def load(
        self,
        key: str,
    ) -> dict[str, Any] | list[Any]:

        return self._provider.read(key)

    def save(
        self,
        key: str,
        data: dict[str, Any] | list[Any],
    ) -> None:

        self._provider.write(
            key,
            data,
        )

    def delete(
        self,
        key: str,
    ) -> None:

        self._provider.delete(key)
