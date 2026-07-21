from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingService(ABC):
    """
    Generates vector embeddings from text.
    """

    @abstractmethod
    def embed(
        self,
        text: str,
    ) -> list[float]:
        raise NotImplementedError