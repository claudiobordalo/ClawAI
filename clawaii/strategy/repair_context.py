from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from clawai.testing.test_diagnosis import DiagnosisResult


@dataclass(frozen=True)
class RepairContext:
    objective: str
    original_instruction: str
    current_instruction: str
    iteration: int
    previous_diagnosis: Optional[DiagnosisResult]
    previous_summary: Optional[str]
