from __future__ import annotations

import chromadb

from clawai.memory.models.chunk import Chunk
from clawai.memory.stores.vector_store import VectorStore


class ChromaVectorStore(VectorStore):

    def __init__(
        self,
        path: str = "data/memory/chroma",
        collection_name: str = "default",
    ) -> None:

        self._client = chromadb.PersistentClient(path=path)

        self._collection = self._client.get_or_create_collection(
            collection_name,
        )

    def add(
        self,
        chunk: Chunk,
    ) -> None:

        self._collection.add(
            ids=[chunk.id],
            documents=[chunk.content],
            embeddings=[chunk.embedding],
            metadatas=[chunk.metadata],
        )

    def search(
        self,
        embedding: list[float],
        limit: int = 5,
    ) -> list[Chunk]:

        result = self._collection.query(
            query_embeddings=[embedding],
            n_results=limit,
        )

        chunks: list[Chunk] = []

        ids = result["ids"][0]
        documents = result["documents"][0]
        embeddings = result["embeddings"][0]
        metadatas = result["metadatas"][0]

        for i in range(len(ids)):
            chunks.append(
                Chunk(
                    id=ids[i],
                    document_id=metadatas[i].get("document_id", ""),
                    content=documents[i],
                    embedding=embeddings[i],
                    metadata=metadatas[i],
                )
            )

        return chunks

    def delete(
        self,
        chunk_id: str,
    ) -> None:
        self._collection.delete(ids=[chunk_id])

    def clear(self) -> None:
        self._client.delete_collection(self._collection.name)

        self._collection = self._client.get_or_create_collection(
            self._collection.name
        )