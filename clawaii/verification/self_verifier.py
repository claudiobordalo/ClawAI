from __future__ import annotations

from typing import Iterable, List, Optional, Sequence

from clawai.diffing import Patch
from clawai.diffing import PatchValidator
from clawai.tracing.execution_trace import ExecutionTraceManager

from .rule_engine import RuleEngine
from .verification_result import VerificationResult
from .verification_rule import VerificationRule


class SelfVerifier:
    """Main entry point for self-verification of patches.

    Flow: PatchValidator -> RuleEngine -> VerificationResult
    """

    def __init__(
        self,
        *,
        patch_validator: PatchValidator,
        rule_engine: RuleEngine,
        trace: Optional[ExecutionTraceManager] = None,
    ) -> None:
        self._validator = patch_validator
        self._engine = rule_engine
        self._trace = trace

    def verify(self, patches: Iterable[Patch]) -> VerificationResult:
        patches_list = list(patches)

        # Trace: validation phase
        tkn = self._trace.start("SelfVerifier", "validate_patches") if self._trace else None
        # Validate all patches; stop on first critical failure
        checked = 0
        for p in patches_list:
            ok, err = self._validator.validate(p)
            checked += 1
            if not ok:
                if tkn:
                    self._trace.finish(tkn, status="failure", metadata={"error": err or "validation failed", "checked": checked})
                return VerificationResult.fail(checked_patches=checked, passed=0, failed=0, warnings=tuple(), errors=(err or "validation failed",))
        if tkn:
            self._trace.finish(tkn, status="success", metadata={"checked": checked})

        # Trace: rules phase
        tkn2 = self._trace.start("SelfVerifier", "run_rules") if self._trace else None
        result = self._engine.verify(patches_list)
        if tkn2:
            self._trace.finish(tkn2, status="success" if result.success else "failure", metadata={
                "checked": result.checked_patches,
                "passed": result.passed_rules,
                "failed": result.failed_rules,
                "errors": len(result.errors),
                "warnings": len(result.warnings),
            })
        return result

    @staticmethod
    def default_rules() -> Sequence[VerificationRule]:
        """Provide a minimal set of default rules, easily extensible."""
        from pathlib import Path

        def rule_patch_valido(p: Patch) -> tuple[bool, str]:
            if p.start_line < 1:
                return False, "start_line inválido"
            if p.original == "":
                if p.end_line != p.start_line - 1:
                    return False, "inserção deve ter end_line == start_line - 1"
            else:
                if p.end_line < p.start_line:
                    return False, "end_line menor que start_line"
            return True, "ok"

        def rule_replacement_diferente(p: Patch) -> tuple[bool, str]:
            if p.replacement == p.original:
                return False, "replacement idêntico ao original"
            return True, "ok"

        def rule_intervalo_valido(p: Patch) -> tuple[bool, str]:
            # Same checks as rule_patch_valido but kept separate for clarity/extensibility
            return rule_patch_valido(p)

        def rule_conteudo_original_consistente(p: Patch) -> tuple[bool, str]:
            path = Path(p.file)
            if not path.exists() or not path.is_file():
                return False, "arquivo não existe"
            try:
                text = path.read_text(encoding="utf-8")
            except Exception:
                return False, "não foi possível ler arquivo"
            lines = text.splitlines()
            if p.original == "":
                i1 = p.start_line - 1
                i2 = p.start_line - 1
            else:
                i1 = p.start_line - 1
                i2 = p.end_line
            if i1 < 0 or i2 > len(lines):
                return False, "intervalo fora do arquivo"
            extracted = "\n".join(lines[i1:i2])
            if extracted != p.original:
                return False, "conteúdo original divergente do arquivo"
            return True, "ok"

        return (
            VerificationRule("Patch válido", "Estrutura básica do patch é válida", "error", rule_patch_valido),
            VerificationRule("Replacement diferente", "Replacement não pode ser igual ao original", "error", rule_replacement_diferente),
            VerificationRule("Intervalo de linhas válido", "Intervalo deve ser válido", "warning", rule_intervalo_valido),
            VerificationRule("Conteúdo original consistente", "Original deve coincidir com arquivo", "error", rule_conteudo_original_consistente),
        )
