from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChangeRequest:
    """Represents a requested code change objective.

    Attributes:
        objective: High-level goal for the change.
        target_query: Query used to locate relevant files/symbols.
        instructions: Concrete instructions to guide the change.
    """

    objective: str
    target_query: str
    instructions: str
