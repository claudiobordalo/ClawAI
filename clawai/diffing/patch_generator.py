from __future__ import annotations

import difflib
from pathlib import Path
from typing import List, Tuple

from clawai.editor import EditOperation

from .patch import Patch
from .patch_result import PatchResult


class PatchGenerator:
    """Generates localized patches from an EditOperation using stdlib diff algorithms.

    - Deterministic for same inputs.
    - Never writes to disk.
    - Returns PatchResult with one or more Patch, or an error if no changes could be localized.
    """

    def generate(self, operation: EditOperation) -> PatchResult:
        try:
            orig = operation.original_content
            new = operation.new_content

            if orig == new:
                return PatchResult.fail("Nenhuma alteração detectada entre original e novo conteúdo.")

            orig_lines = orig.splitlines()
            new_lines = new.splitlines()

            sm = difflib.SequenceMatcher(a=orig_lines, b=new_lines, autojunk=False)
            patches: List[Patch] = []

            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                if tag == "equal":
                    continue
                original_block = "\n".join(orig_lines[i1:i2])
                replacement_block = "\n".join(new_lines[j1:j2])

                # Compute 1-based lines
                if tag == "insert":
                    start_line = i1 + 1
                    end_line = i1  # insertion before start_line
                else:
                    start_line = i1 + 1
                    end_line = i2  # inclusive

                patch = Patch(
                    file=str(operation.file_path()),
                    original=original_block,
                    replacement=replacement_block,
                    start_line=start_line,
                    end_line=end_line,
                    reason=operation.reason,
                )
                patches.append(patch)

            if not patches:
                return PatchResult.fail("Não foi possível localizar alterações (opcodes vazios).")

            return PatchResult.ok(tuple(patches))
        except Exception as e:
            return PatchResult.fail(f"PatchGenerator erro inesperado: {e}")
