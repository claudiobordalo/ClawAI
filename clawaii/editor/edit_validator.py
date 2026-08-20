from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from .edit_operation import EditOperation


class EditValidator:
    """Validates an EditOperation prior to application.

    This component must not modify files.
    """

    def validate(self, operation: EditOperation) -> Tuple[bool, Optional[str]]:
        path = operation.file_path()
        try:
            if not path.exists() or not path.is_file():
                return False, "File does not exist"

            try:
                on_disk = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                return False, "Unable to read file as text"

            if operation.original_content != on_disk:
                return False, "Original content does not match file"

            if operation.new_content is None or operation.new_content == "":
                return False, "New content is empty"

            if operation.new_content == operation.original_content:
                return False, "New content is identical to original"

            return True, None
        except Exception as e:  # Defensive: never raise to the caller
            return False, f"Validation error: {e}"
