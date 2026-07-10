from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ProcessedResponse:
    """Structured output from post-processing a raw model response."""

    answer: str  # cleaned answer with extracted blocks removed
    memories: list[dict] = field(default_factory=list)
    tasks: list[str] = field(default_factory=list)
    reflections: dict = field(default_factory=dict)
    patches: list[dict] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)

    @property
    def memory_saved(self) -> bool:
        return len(self.memories) > 0


class ResponsePostProcessor:
    """
    Unified component for extracting structured data from model responses.

    Day-1 responsibility (replaces current _finalize_answer):
      - MEMORY block extraction and persistence

    Future responsibilities (add extract_* methods without touching existing code):
      - TASK, REFLECTION, PATCH block extraction
      - Metrics generation from response artifacts
    """

    def __init__(self, memory) -> None:
        self._memory = memory

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self, raw_response: str) -> ProcessedResponse:
        """Main entry point — runs all extractors on a raw model response."""
        result = ProcessedResponse(answer=raw_response)

        self._extract_memories(raw_response, result)

        answer_text = raw_response
        if "<MEMORY>" in answer_text and "</MEMORY>" in answer_text:
            answer_text = answer_text.split("<MEMORY>", 1)[0].strip()
        result.answer = answer_text

        return result

    # ------------------------------------------------------------------
    # Extractors (add new ones here)
    # ------------------------------------------------------------------

    def _extract_memories(self, raw: str, out: ProcessedResponse) -> None:
        if "<MEMORY>" not in raw or "</MEMORY>" not in raw:
            return

        block = raw.split("<MEMORY>", 1)[1].split("</MEMORY>", 1)[0]
        title = ""
        content = ""

        for line in block.splitlines():
            lower = line.lower()
            if lower.startswith("titulo:"):
                title = line.split(":", 1)[1].strip()
            elif lower.startswith("conteudo:"):
                content = line.split(":", 1)[1].strip()

        if title and content:
            self._memory.add(
                category="general",
                title=title,
                content=content,
                source="chat",
            )
            out.memories.append({
                "category": "general",
                "title": title,
                "content": content,
            })
