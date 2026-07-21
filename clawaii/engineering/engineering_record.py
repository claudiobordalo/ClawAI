from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Tuple


@dataclass(frozen=True)
class EngineeringRecord:
    """Immutable engineering execution record.

    Fields:
        timestamp: When the execution completed (UTC recommended).
        objective: High-level goal for the execution.
        target_query: Target selection or scope string.
        instructions: Instructions provided to the development pipeline (as seen by the executor request).
        diagnosis: Final diagnosis summary, if any.
        strategy: Strategy identifier used by the self-repair engine (e.g., class name).
        summary: High-level summary of the self-repair result.
        success: Overall success of the autonomous execution (self-repair + edits).
        modified_files: Files successfully modified during the execution, in application order.
        failed_tests: Names of failing tests from the final diagnosis (if available).
        duration: Total execution duration in seconds.
    """

    timestamp: datetime
    objective: str
    target_query: str
    instructions: str
    diagnosis: str
    strategy: str
    summary: str
    success: bool
    modified_files: Tuple[str, ...]
    failed_tests: Tuple[str, ...]
    duration: float
