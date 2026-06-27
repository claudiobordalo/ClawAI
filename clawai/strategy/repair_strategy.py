from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .repair_context import RepairContext
from .repair_decision import RepairDecision


class RepairStrategy:
    """Deterministic strategy to refine instructions between repair iterations.

    - No dependencies
    - No randomness
    - No complex regex; only string composition
    """

    def decide(self, context: RepairContext) -> RepairDecision:
        prev = context.previous_diagnosis
        if prev is None:
            # No diagnosis yet: keep original instruction
            reason = "no diagnosis available; using original instruction"
            return RepairDecision(
                continue_execution=True,
                updated_instruction=context.original_instruction,
                reason=reason,
            )

        # Build a deterministic updated instruction combining:
        # - original objective
        # - previous failure summary
        # - probable causes (joined, unique order preserved)
        # - explicit constraints to avoid repeating error and preserve valid changes
        causes: List[str] = []
        for c in prev.probable_causes:
            s = str(c).strip()
            if s and s not in causes:
                causes.append(s)
        causes_text = ", ".join(causes) if causes else "unknown cause"
        prev_summary = (context.previous_summary or "previous attempt failed").strip()

        updated = (
            f"Objective: {context.objective}.\n"
            f"Previous: {prev_summary}.\n"
            f"Probable causes: {causes_text}.\n"
            f"Guidelines: Do not repeat the same error; preserve all valid changes from earlier attempts; "
            f"apply only minimal, targeted modifications to address the causes.\n"
            f"Base instruction: {context.original_instruction}"
        )
        reason = f"refined instruction from diagnosis: {causes_text}"
        return RepairDecision(continue_execution=True, updated_instruction=updated, reason=reason)
