from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MemoryQuery:
    """Immutable filters for querying engineering memory.

    All filters are optional and combined with AND semantics when provided.
    String filters use exact equality for determinism.
    success_only=True filters only successful records; None/False does not filter.
    """

    objective: Optional[str] = None
    target_query: Optional[str] = None
    diagnosis: Optional[str] = None
    success_only: Optional[bool] = None
