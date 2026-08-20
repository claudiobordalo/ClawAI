from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EditOperation:
    """Immutable representation of a single code edit operation.

    Attributes:
        file: Target file path (absolute or relative).
        original_content: Expected current content of the file before applying the edit.
        new_content: Content to write to the file.
        reason: Human-readable reason describing why the change is needed.
    """

    file: str | Path
    original_content: str
    new_content: str
    reason: str

    def file_path(self) -> Path:
        """Return the path object for the target file."""
        return Path(self.file)
