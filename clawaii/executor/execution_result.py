from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from clawai.editor.edit_result import EditResult
from clawai.selfrepair.repair_result import RepairResult


@dataclass(frozen=True)
class ExecutionResult:
    success: bool
    repair_result: RepairResult
    applied_results: Tuple[EditResult, ...]
    summary: str
    error: Optional[str] = None
