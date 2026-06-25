from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Document:
    """
    Represents a document stored in long-term memory.
    """

    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)