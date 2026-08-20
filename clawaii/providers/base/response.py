from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ProviderResponse:
    content: str
    model: str
    provider: str

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    elapsed_ms: float = 0.0