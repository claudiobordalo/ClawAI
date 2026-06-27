from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from clawai.development.development_result import DevelopmentResult
from clawai.testing.test_suite_result import TestSuiteResult
from clawai.testing.test_diagnosis import DiagnosisResult


@dataclass(frozen=True)
class RepairIteration:
    iteration: int
    development_result: Optional[DevelopmentResult]
    test_result: Optional[TestSuiteResult]
    diagnosis: Optional[DiagnosisResult]
    success: bool
