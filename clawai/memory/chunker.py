from __future__ import annotations

from typing import Iterable

from clawai.memory.models.chunk import Chunk
from clawai.memory.models.document import Document


class Chunker:
    """
    Splits documents into semantic chunks.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        overlap: int = 200,
    ) -> None:

        self._chunk_size = chunk_size
        self._overlap = overlap

    def split(
        self,
        document: Document,
    ) -> list[Chunk]:

        text = document.content

        chunks: list[Chunk] = []

        start = 0
        index = 0

        while start < len(text):

            end = start + self._chunk_size

            content = text[start:end]

            chunks.append(
                Chunk(
                    id=f"{document.id}_{index}",
                    document_id=document.id,
                    content=content,
                    metadata=document.metadata.copy(),
                )
            )

            start += self._chunk_size - self._overlap
            index += 1

        return chunks
