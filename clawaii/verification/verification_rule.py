from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from clawai.diffing import Patch


Evaluator = Callable[[Patch], tuple[bool, str]]


@dataclass(frozen=True)
class VerificationRule:
    name: str
    description: str
    severity: str  # e.g., "error", "warning", "info"
    evaluator: Evaluator
