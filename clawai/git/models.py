from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class GitSnapshot:
    branch: str
    commit: str
    dirty: bool = False


@dataclass(slots=True, frozen=True)
class GitOperationResult:
    success: bool
    return_code: int
    stdout: str
    stderr: str
    command: str
