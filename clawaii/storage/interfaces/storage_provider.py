from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class StorageProvider(ABC):

    @abstractmethod
    def exists(self, key: str) -> bool:
        ...

    @abstractmethod
    def read(self, key: str) -> dict[str, Any] | list[Any]:
        ...

    @abstractmethod
    def write(
        self,
        key: str,
        data: dict[str, Any] | list[Any],
    ) -> None:
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        ...
