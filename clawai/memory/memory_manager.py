from __future__ import annotations

from clawai.memory.chunker import Chunker
from clawai.memory.embeddings.embedding_service import EmbeddingService
from clawai.memory.models.document import Document
from clawai.memory.stores.vector_store import VectorStore


class MemoryManager:
    """
    Coordinates long-term memory.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        chunker: Chunker | None = None,
    ) -> None:

        self._embedding_service = embedding_service
        self._vector_store = vector_store
        self._chunker = chunker or Chunker()

    def add_document(
        self,
        document: Document,
    ) -> None:

        chunks = self._chunker.split(document)

        for chunk in chunks:
            chunk.embedding = self._embedding_service.embed(
                chunk.content,
            )

            self._vector_store.add(chunk)

    def search(
        self,
        query: str,
        limit: int = 5,
    ):

        embedding = self._embedding_service.embed(query)

        return self._vector_store.search(
            embedding=embedding,
            limit=limit,
        )

    def clear(self) -> None:
        self._vector_store.clear()
