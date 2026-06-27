from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple, Union, Sequence


@dataclass(frozen=True)
class TestRequest:
    """Immutable test execution request.

    Fields:
    - project_root: root directory where tests will be executed (as current working dir)
    - command: command to execute pytest or other test runner. Prefer tuple[str, ...].
    - timeout: timeout in seconds for the whole execution.
    """
    project_root: Path
    command: Tuple[str, ...]
    timeout: float

    def __post_init__(self) -> None:
        # Normalize project_root to absolute Path
        object.__setattr__(self, "project_root", Path(self.project_root))
        # Ensure command is a tuple for immutability
        cmd = self.command
        if isinstance(cmd, (list, tuple)):
            object.__setattr__(self, "command", tuple(str(x) for x in cmd))
        else:
            # Accept string (space-separated) but normalize to tuple
            parts = str(cmd).strip().split()
            object.__setattr__(self, "command", tuple(parts))
        # Validate timeout
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")
