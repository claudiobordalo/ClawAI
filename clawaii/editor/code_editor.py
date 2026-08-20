from __future__ import annotations

from typing import Iterable, List, Optional

from .edit_applier import EditApplier
from .edit_operation import EditOperation
from .edit_result import EditResult
from .edit_validator import EditValidator


class CodeEditor:
    """Main entry point to validate and apply edit operations.

    Flow: EditValidator -> EditApplier
    """

    def __init__(
        self,
        validator: Optional[EditValidator] = None,
        applier: Optional[EditApplier] = None,
    ) -> None:
        self.validator = validator or EditValidator()
        self.applier = applier or EditApplier()

    def apply(self, operation: EditOperation) -> EditResult:
        valid, error = self.validator.validate(operation)
        if not valid:
            # Do not modify files on validation failure.
            # Provide a deterministic result including the current on-disk content when possible.
            try:
                current = operation.file_path().read_text(encoding="utf-8")
            except Exception:
                current = None
            return EditResult.fail(operation.file_path(), current, current, error or "Validation failed")

        return self.applier.apply(operation)

    def apply_many(self, operations: Iterable[EditOperation]) -> List[EditResult]:
        results: List[EditResult] = []
        for op in operations:
            res = self.apply(op)
            results.append(res)
            if not res.success:
                break  # Interrupt on first failure; no rollback in this sprint.
        return results
