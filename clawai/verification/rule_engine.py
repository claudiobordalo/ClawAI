from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple

from clawai.diffing import Patch

from .verification_result import VerificationResult
from .verification_rule import VerificationRule


class RuleEngine:
    """Executes verification rules over patches.

    - Deterministic for same inputs.
    - No side effects on disk.
    - Stops on first error-level failure to avoid noisy outputs.
    """

    def __init__(self, rules: Sequence[VerificationRule] | None = None) -> None:
        self._rules: Tuple[VerificationRule, ...] = tuple(rules or ())

    def verify(self, patches: Iterable[Patch]) -> VerificationResult:
        checked = 0
        passed = 0
        failed = 0
        warnings: List[str] = []
        errors: List[str] = []

        for patch in patches:
            checked += 1
            for rule in self._rules:
                ok, message = rule.evaluator(patch)
                if ok:
                    passed += 1
                else:
                    if rule.severity.lower() == "error":
                        failed += 1
                        errors.append(f"{rule.name}: {message}")
                        # Stop on first critical failure
                        return VerificationResult.fail(checked, passed, failed, tuple(warnings), tuple(errors))
                    else:
                        warnings.append(f"{rule.name}: {message}")
                        failed += 1

        if errors:
            return VerificationResult.fail(checked, passed, failed, tuple(warnings), tuple(errors))
        return VerificationResult.ok(checked, passed, failed, tuple(warnings))

    def rules(self) -> Tuple[VerificationRule, ...]:
        return self._rules
