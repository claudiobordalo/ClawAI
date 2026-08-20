from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Patch:
    """Represents a localized change in a file.

    Conventions:
    - Lines are 1-based.
    - For replacements/deletions: [start_line, end_line] inclusive defines the slice in the original file.
    - For insertions: original is empty, and end_line should be exactly start_line - 1, indicating an insertion
      occurring immediately before start_line (or at EOF if start_line == last_line + 1).
    """

    file: str | Path
    original: str
    replacement: str
    start_line: int
    end_line: int
    reason: str

    def file_path(self) -> Path:
        return Path(self.file)
