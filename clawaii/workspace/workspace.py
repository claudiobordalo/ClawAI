from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .file_reader import FileReader
from .ignore import IgnoreEngine
from .project_tree import ProjectNode, ProjectTree
from .scanner import Scanner


@dataclass(frozen=True, slots=True)
class FileContext:
    path: str
    language: str
    content: str


class Workspace:
    """
    Workspace:
    - abrir projeto / fechar projeto
    - retornar árvore (ProjectTree)
    - fornecer wrappers retrocompatíveis load_project/build_context

    Política desta sprint:
    - Scanner descobre sem ler conteúdo
    - FileReader lê sob demanda e sem cachear arquivos inteiros
    - build_context usa leitura incremental controlada por max_chars
    """

    EXTENSIONS = {
        ".py": "python",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".cs": "csharp",
        ".java": "java",
        ".sql": "sql",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".md": "markdown",
        ".html": "html",
        ".css": "css",
        ".toml": "toml",
        ".txt": "text",
    }

    def __init__(self) -> None:
        self._open_root: Path | None = None
        self._ignore: IgnoreEngine | None = None
        self._scanner: Scanner | None = None
        self._reader = FileReader()

    def open_project(self, root: str | Path) -> None:
        root_path = Path(root)
        self.close_project()
        self._open_root = root_path
        self._ignore = IgnoreEngine(root_path)
        self._scanner = Scanner(root_path, ignore_engine=self._ignore)

    def close_project(self) -> None:
        self._open_root = None
        self._ignore = None
        self._scanner = None

    @property
    def is_open(self) -> bool:
        return self._open_root is not None

    def get_tree(self) -> ProjectTree:
        if self._open_root is None or self._scanner is None:
            raise RuntimeError("Workspace: nenhum projeto aberto")

        root = self._open_root

        def build_node(dir_path: Path) -> ProjectNode:
            children: list[ProjectNode] = []
            try:
                for p in dir_path.iterdir():
                    if p.name.startswith("."):
                        continue
                    if self._ignore and self._ignore.is_ignored(p, is_dir=p.is_dir()):
                        continue

                    if p.is_dir():
                        children.append(build_node(p))
                    else:
                        children.append(ProjectNode(name=p.name, is_dir=False))
            except Exception:
                # árvore leve: se falhar, retorna nó vazio para esta pasta
                pass
            return ProjectNode(name=dir_path.name, is_dir=True, children=tuple(children))

        root_node = build_node(root)
        return ProjectTree(root=root, root_node=root_node)

    # -----------------------------
    # Retrocompatibilidade
    # -----------------------------
    def load_project(self, root: str | Path) -> list[FileContext]:
        """
        Mantém assinatura pública existente.
        Ainda assim, a leitura é sob demanda (FileReader) e ocorre apenas para arquivos indexáveis.
        """
        root_path = Path(root)
        ignore = IgnoreEngine(root_path)
        ignore.load()
        scanner = Scanner(root_path, ignore_engine=ignore)

        files: list[FileContext] = []

        # indexa por extensão (descoberta via Scanner)
        for p in scanner.list_files():
            language = self.EXTENSIONS.get(p.suffix.lower())
            if language is None:
                continue

            content = self._reader.read_text(p, max_chars=None)
            rel = str(p.relative_to(root_path)).replace("\\", "/")
            files.append(FileContext(path=rel, language=language, content=content))

        return files

    def build_context(self, root: str | Path, max_chars: int = 120000) -> str:
        """
        build_context vira um uso leve: descobre arquivos via Scanner e lê incrementalmente sob demanda.
        """
        root_path = Path(root)
        ignore = IgnoreEngine(root_path)
        ignore.load()
        scanner = Scanner(root_path, ignore_engine=ignore)

        used = 0
        blocks: list[str] = []

        # varre em ordem determinística por path string
        candidates: Iterable[Path] = sorted(scanner.list_files(), key=lambda p: str(p))

        for p in candidates:
            language = self.EXTENSIONS.get(p.suffix.lower())
            if language is None:
                continue

            # lê apenas o necessário
            remaining = max_chars - used
            if remaining <= 0:
                break

            content = self._reader.read_text(p, max_chars=remaining)

            block = f"""
========================
Arquivo: {str(p.relative_to(root_path)).replace("\\", "/")}
Linguagem: {language}
========================

{content}

"""
            if used + len(block) > max_chars:
                blocks.append(block[:remaining])
                used += remaining
                break

            blocks.append(block)
            used += len(block)

        return "\n".join(blocks)


workspace = Workspace()
