from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RepairDecision:
    continue_execution: bool
    updated_instruction: str
    reason: str
