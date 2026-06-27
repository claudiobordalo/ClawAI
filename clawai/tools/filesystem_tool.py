from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from clawai.workspace.ignore import IgnoreEngine

RuntimeResult = dict[str, Any]


def _runtime_result(*, success: bool, result: Any, error: str | None, duration_ms: float) -> RuntimeResult:
    return {
        "success": success,
        "result": result,
        "error": error,
        "duration_ms": float(duration_ms),
    }


class FilesystemTool:
    """
    Tool de filesystem com contrato de runtime_result e sem lançar exceções.

    Observações:
    - Não depende de Workspace/ContextBuilder/Mission.
    - IgnoreEngine é aplicado somente em search() (requisito).
    """

    @property
    def name(self) -> str:
        return "filesystem"

    @property
    def description(self) -> str:
        return "Filesystem operations with runtime result contract."

    def describe(self) -> ToolDescriptor:
        from clawai.tools.tool_descriptor import ArgumentDescriptor, ToolDescriptor

        return ToolDescriptor(
            name=self.name,
            description=self.description,
            arguments=(
                ArgumentDescriptor(
                    name="action",
                    type="string",
                    description="Ação a ser executada: read_file, write_file, append_file, delete_file, exists, mkdir, list_dir, copy, move, search, read_text",
                    required=True,
                ),
                ArgumentDescriptor(
                    name="path",
                    type="string",
                    description="Caminho do arquivo ou diretório",
                    required=False,
                ),
                ArgumentDescriptor(
                    name="content",
                    type="string",
                    description="Conteúdo para escrita (write_file / append_file)",
                    required=False,
                ),
                ArgumentDescriptor(
                    name="src",
                    type="string",
                    description="Caminho de origem (copy / move)",
                    required=False,
                ),
                ArgumentDescriptor(
                    name="dst",
                    type="string",
                    description="Caminho de destino (copy / move)",
                    required=False,
                ),
                ArgumentDescriptor(
                    name="pattern",
                    type="string",
                    description="Padrão glob para busca (search)",
                    required=False,
                ),
                ArgumentDescriptor(
                    name="max_chars",
                    type="integer",
                    description="Máximo de caracteres para leitura (read_text)",
                    required=False,
                ),
                ArgumentDescriptor(
                    name="root",
                    type="string",
                    description="Diretório raiz para busca (search)",
                    required=False,
                ),
            ),
            examples=(
                '{"action":"read_file","path":"README.md"}',
                '{"action":"write_file","path":"test.txt","content":"Hello"}',
                '{"action":"search","root":".","pattern":"*.py"}',
            ),
            version="1.0.0",
        )

    def __init__(self, *, ignore_engine: IgnoreEngine | None = None) -> None:
        self._ignore_engine = ignore_engine

    def health(self) -> RuntimeResult:
        start = time.perf_counter()
        try:
            return _runtime_result(
                success=True,
                result={"name": self.name},
                error=None,
                duration_ms=(time.perf_counter() - start) * 1000,
            )
        except Exception as e:
            return _runtime_result(
                success=False,
                result=None,
                error=str(e),
                duration_ms=(time.perf_counter() - start) * 1000,
            )

    def execute(self, **kwargs: Any) -> RuntimeResult:
        start = time.perf_counter()
        action = kwargs.get("action")
        try:
            actions = {
                "read_file": self.read_file,
                "write_file": self.write_file,
                "append_file": self.append_file,
                "delete_file": self.delete_file,
                "exists": self.exists,
                "mkdir": self.mkdir,
                "list_dir": self.list_dir,
                "copy": self.copy,
                "move": self.move,
                "search": self.search,
                "read_text": self.read_text,
            }
            if action not in actions:
                return _runtime_result(
                    success=False,
                    result=None,
                    error=f"Unknown action: {action}",
                    duration_ms=(time.perf_counter() - start) * 1000,
                )

            # Passa kwargs sem "action"
            fn_kwargs = {k: v for k, v in kwargs.items() if k != "action"}
            res = actions[action](**fn_kwargs)
            # O método já retorna o contrato, então preserva o duration_ms dele.
            return res
        except Exception as e:
            return _runtime_result(
                success=False,
                result=None,
                error=str(e),
                duration_ms=(time.perf_counter() - start) * 1000,
            )

    def read_file(self, path: str) -> RuntimeResult:
        start = time.perf_counter()
        try:
            data = Path(path).read_bytes()
            return _runtime_result(
                success=True,
                result=data,
                error=None,
                duration_ms=(time.perf_counter() - start) * 1000,
            )
        except FileNotFoundError:
            return _runtime_result(
                success=False,
                result=None,
                error=f"File not found: {path}",
                duration_ms=(time.perf_counter() - start) * 1000,
            )
        except Exception as e:
            return _runtime_result(
                success=False,
                result=None,
                error=str(e),
                duration_ms=(time.perf_counter() - start) * 1000,
            )

    def write_file(self, path: str, content: bytes | str) -> RuntimeResult:
        start = time.perf_counter()
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, str):
                p.write_text(content, encoding="utf-8")
            else:
                p.write_bytes(content)
            return _runtime_result(
                success=True,
                result=None,
                error=None,
                duration_ms=(time.perf_counter() - start) * 1000,
            )
        except Exception as e:
            return _runtime_result(
                success=False,
                result=None,
                error=str(e),
                duration_ms=(time.perf_counter() - start) * 1000,
            )

    def append_file(self, path: str, content: bytes | str) -> RuntimeResult:
        start = time.perf_counter()
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, str):
                p.open("a", encoding="utf-8").write(content)
            else:
                with p.open("ab") as f:
                    f.write(content)
            return _runtime_result(
                success=True,
                result=None,
                error=None,
                duration_ms=(time.perf_counter() - start) * 1000,
            )
        except Exception as e:
            return _runtime_result(
                success=False,
                result=None,
                error=str(e),
                duration_ms=(time.perf_counter() - start) * 1000,
            )

    def delete_file(self, path: str) -> RuntimeResult:
        start = time.perf_counter()
        try:
            p = Path(path)
            if not p.exists():
                return _runtime_result(
                    success=False,
                    result=None,
                    error=f"File not found: {path}",
                    duration_ms=(time.perf_counter() - start) * 1000,
                )
            p.unlink()
            return _runtime_result(
                success=True,
                result=None,
                error=None,
                duration_ms=(time.perf_counter() - start) * 1000,
            )
        except Exception as e:
            return _runtime_result(
                success=False,
                result=None,
                error=str(e),
                duration_ms=(time.perf_counter() - start) * 1000,
            )

    def exists(self, path: str) -> RuntimeResult:
        start = time.perf_counter()
        try:
            return _runtime_result(
                success=True,
                result=Path(path).exists(),
                error=None,
                duration_ms=(time.perf_counter() - start) * 1000,
            )
        except Exception as e:
            return _runtime_result(
                success=False,
                result=None,
                error=str(e),
                duration_ms=(time.perf_counter() - start) * 1000,
            )

    def mkdir(self, path: str) -> RuntimeResult:
        start = time.perf_counter()
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return _runtime_result(
                success=True,
                result=None,
                error=None,
                duration_ms=(time.perf_counter() - start) * 1000,
            )
        except Exception as e:
            return _runtime_result(
                success=False,
                result=None,
                error=str(e),
                duration_ms=(time.perf_counter() - start) * 1000,
            )

    def list_dir(self, path: str) -> RuntimeResult:
        start = time.perf_counter()
        try:
            p = Path(path)
            if not p.exists() or not p.is_dir():
                return _runtime_result(
                    success=False,
                    result=None,
                    error=f"Not a directory: {path}",
                    duration_ms=(time.perf_counter() - start) * 1000,
                )
            items = [str(child) for child in p.iterdir()]
            return _runtime_result(
                success=True,
                result=sorted(items),
                error=None,
                duration_ms=(time.perf_counter() - start) * 1000,
            )
        except Exception as e:
            return _runtime_result(
                success=False,
                result=None,
                error=str(e),
                duration_ms=(time.perf_counter() - start) * 1000,
            )

    def copy(self, src: str, dst: str) -> RuntimeResult:
        start = time.perf_counter()
        try:
            from shutil import copy2

            dst_path = Path(dst)
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            copy2(src, str(dst_path))
            return _runtime_result(
                success=True,
                result=None,
                error=None,
                duration_ms=(time.perf_counter() - start) * 1000,
            )
        except Exception as e:
            return _runtime_result(
                success=False,
                result=None,
                error=str(e),
                duration_ms=(time.perf_counter() - start) * 1000,
            )

    def move(self, src: str, dst: str) -> RuntimeResult:
        start = time.perf_counter()
        try:
            dst_path = Path(dst)
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            Path(src).rename(str(dst_path))
            return _runtime_result(
                success=True,
                result=None,
                error=None,
                duration_ms=(time.perf_counter() - start) * 1000,
            )
        except Exception as e:
            return _runtime_result(
                success=False,
                result=None,
                error=str(e),
                duration_ms=(time.perf_counter() - start) * 1000,
            )

    def read_text(self, path: str, max_chars: int | None = None) -> RuntimeResult:
        start = time.perf_counter()
        try:
            p = Path(path)
            text = p.read_text(encoding="utf-8")
            if max_chars is not None:
                text = text[:max_chars]
            return _runtime_result(
                success=True,
                result=text,
                error=None,
                duration_ms=(time.perf_counter() - start) * 1000,
            )
        except FileNotFoundError:
            return _runtime_result(
                success=False,
                result=None,
                error=f"File not found: {path}",
                duration_ms=(time.perf_counter() - start) * 1000,
            )
        except Exception as e:
            return _runtime_result(
                success=False,
                result=None,
                error=str(e),
                duration_ms=(time.perf_counter() - start) * 1000,
            )

    def search(self, root: str, pattern: str) -> RuntimeResult:
        start = time.perf_counter()
        try:
            root_path = Path(root)
            if not root_path.exists() or not root_path.is_dir():
                return _runtime_result(
                    success=False,
                    result=[],
                    error=f"Not a directory: {root}",
                    duration_ms=(time.perf_counter() - start) * 1000,
                )

            matches: list[str] = []
            # Requisito: usar pathlib.Path.rglob()
            for p in root_path.rglob(pattern):
                if p.is_dir():
                    continue

                if self._ignore_engine is not None:
                    if self._ignore_engine.is_ignored(p, is_dir=False, is_binary=False):
                        continue

                matches.append(str(p))

            return _runtime_result(
                success=True,
                result=sorted(matches),
                error=None,
                duration_ms=(time.perf_counter() - start) * 1000,
            )
        except Exception as e:
            return _runtime_result(
                success=False,
                result=[],
                error=str(e),
                duration_ms=(time.perf_counter() - start) * 1000,
            )
