from __future__ import annotations

import ollama

from clawai.memory.embeddings.embedding_service import EmbeddingService


class OllamaEmbeddingService(EmbeddingService):
    """
    Embedding service backed by Ollama.
    """

    def __init__(
        self,
        model: str = "nomic-embed-text",
        host: str = "http://localhost:11434",
    ) -> None:
        self._model = model
        self._client = ollama.Client(host=host)

    def embed(
        self,
        text: str,
    ) -> list[float]:

        response = self._client.embeddings(
            model=self._model,
            prompt=text,
        )

        return response["embedding"]