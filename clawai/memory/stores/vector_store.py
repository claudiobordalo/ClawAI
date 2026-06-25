from __future__ import annotations

from abc import ABC, abstractmethod

from clawai.memory.models.chunk import Chunk


class VectorStore(ABC):
    """
    Base interface for vector databases.
    """

    @abstractmethod
    def add(self, chunk: Chunk) -> None:
        raise NotImplementedError

    @abstractmethod
    def search(
        self,
        embedding: list[float],
        limit: int = 5,
    ) -> list[Chunk]:
        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        chunk_id: str,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        raise NotImplementedError