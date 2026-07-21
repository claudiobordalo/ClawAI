from __future__ import annotations

from pathlib import Path

from .edit_operation import EditOperation
from .edit_result import EditResult


class EditApplier:
    """Applies a single EditOperation to disk.

    Characteristics:
    - Writes exactly one file.
    - Returns EditResult.
    - Never raises exceptions to the caller.
    - Prepared for future transactional behavior.
    """

    def apply(self, operation: EditOperation) -> EditResult:
        path: Path = operation.file_path()

        # Read previous content first (if this fails, we cannot proceed)
        try:
            previous = path.read_text(encoding="utf-8")
        except Exception as e:
            return EditResult.fail(path, None, None, f"Read error: {e}")

        # Attempt to write new content
        try:
            # Simple direct write; future sprints may replace with atomic/transactional writes
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(operation.new_content)
        except Exception as e:
            # On write failure, best-effort read current state to report deterministically
            try:
                current = path.read_text(encoding="utf-8")
            except Exception:
                current = None
            return EditResult.fail(path, previous, current, f"Write error: {e}")

        # Read current content after write, for reporting
        try:
            current = path.read_text(encoding="utf-8")
        except Exception:
            current = None

        return EditResult.ok(path, previous, current)
