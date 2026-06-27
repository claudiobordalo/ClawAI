from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class CognitiveConfiguration:
    provider: str = "rule_based"
    model: Optional[str] = None
    temperature: float = 0.0
    max_tokens: int = 1024
    timeout: float = 30.0
    retry: int = 3
    reasoning_mode: str = "rule_based"
    review_mode: str = "rule_based"
