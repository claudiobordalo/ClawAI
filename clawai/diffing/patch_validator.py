from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from .patch import Patch


class PatchValidator:
    """Validates a Patch without modifying files.

    Rules:
    - Lines valid (1-based; for insertions allow end_line == start_line - 1).
    - Original content consistent with on-disk content slice.
    - Replacement differs from original.
    - Patch is not empty (either original or replacement must be non-empty, and must differ).
    """

    def validate(self, patch: Patch) -> Tuple[bool, Optional[str]]:
        try:
            # Validate lines
            if patch.start_line < 1:
                return False, "start_line inválido (deve ser >= 1)"

            is_insertion = patch.original == ""
            if is_insertion:
                # For insertion, we allow end_line == start_line - 1
                if patch.end_line != patch.start_line - 1:
                    return False, "Para inserção (original vazio), end_line deve ser start_line - 1"
            else:
                if patch.end_line < patch.start_line:
                    return False, "end_line não pode ser menor que start_line"

            # Read file
            path = Path(patch.file)
            if not path.exists() or not path.is_file():
                return False, "Arquivo não existe"

            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                return False, "Não foi possível ler arquivo como texto"

            lines = text.splitlines()

            # Extract original slice from lines based on 1-based indices
            if is_insertion:
                i1 = patch.start_line - 1  # insertion before this index
                i2 = patch.start_line - 1  # exclusive
            else:
                i1 = patch.start_line - 1
                i2 = patch.end_line  # exclusive

            if i1 < 0 or i1 > len(lines) or i2 < 0 or i2 > len(lines):
                return False, "Intervalo de linhas fora do arquivo"

            extracted = "\n".join(lines[i1:i2])

            if extracted != patch.original:
                return False, "Conteúdo original não corresponde ao arquivo"

            # Patch must not be empty
            if not patch.original and not patch.replacement:
                return False, "Patch vazio"

            # Replacement must differ from original
            if patch.replacement == patch.original:
                return False, "Replacement é idêntico ao original"

            return True, None
        except Exception as e:
            return False, f"PatchValidator erro: {e}"
