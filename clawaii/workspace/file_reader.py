from __future__ import annotations

from pathlib import Path

from .ignore import is_probably_binary


class FileReader:
    """
    FileReader:
    - leitura sob demanda
    - nunca cachear arquivo inteiro
    """

    def read_text(
        self,
        path: str | Path,
        *,
        encoding: str = "utf-8",
        errors: str = "ignore",
        max_chars: int | None = None,
    ) -> str:
        p = Path(path)

        if is_probably_binary(p):
            return ""

        if max_chars is None:
            # leitura sob demanda
            return p.read_text(encoding=encoding, errors=errors)

        # leitura incremental por caracteres
        # (evita carregar arquivo completo)
        out_parts: list[str] = []
        used = 0

        # lê em blocos em bytes e decodifica como texto (simplificado)
        # para manter compatibilidade, usamos stream text com read().
        with p.open("r", encoding=encoding, errors=errors) as f:
            while True:
                remaining = max_chars - used
                if remaining <= 0:
                    break
                chunk = f.read(min(8192, remaining))
                if not chunk:
                    break
                out_parts.append(chunk)
                used += len(chunk)

        return "".join(out_parts)
