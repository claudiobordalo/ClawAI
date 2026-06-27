from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from .project_snapshot import SourceFile, ModuleInfo, ClassInfo, FunctionInfo


class SymbolExtractor:
    """
    Extrai informações estruturadas exclusivamente via AST para arquivos Python.
    Não executa código nem importa módulos do projeto.
    """

    def extract(self, file_path: str | Path) -> ModuleInfo:
        path = Path(file_path)
        src: str
        try:
            src = path.read_text(encoding="utf-8")
        except Exception as ex:
            # Tratar como arquivo vazio com erro de leitura
            source = SourceFile(path=str(path), extension=path.suffix)
            return ModuleInfo(
                file=source,
                module_name=path.stem,
                imports=(),
                classes=(),
                functions=(),
                docstring=None,
                parse_error=f"read_error: {ex}",
            )

        try:
            tree = ast.parse(src)
        except SyntaxError as syn:
            source = SourceFile(path=str(path), extension=path.suffix)
            return ModuleInfo(
                file=source,
                module_name=path.stem,
                imports=(),
                classes=(),
                functions=(),
                docstring=None,
                parse_error=f"syntax_error: {syn.msg}",
            )

        module_doc = ast.get_docstring(tree)

        imports: list[str] = []
        classes: list[ClassInfo] = []
        functions: list[FunctionInfo] = []

        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.extend(self._extract_imports(node))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(self._extract_function(node, is_method=False))
            elif isinstance(node, ast.ClassDef):
                classes.append(self._extract_class(node))

        source = SourceFile(path=str(path), extension=path.suffix)
        return ModuleInfo(
            file=source,
            module_name=path.stem,
            imports=tuple(imports),
            classes=tuple(classes),
            functions=tuple(functions),
            docstring=module_doc,
            parse_error=None,
        )

    def _extract_imports(self, node: ast.AST) -> list[str]:
        res: list[str] = []
        if isinstance(node, ast.Import):
            for alias in node.names:
                res.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            # Representa imports relativos como "." * level + (module ou "")
            level = "." * (node.level or 0)
            mod = node.module or ""
            res.append(f"{level}{mod}")
        return res

    def _extract_function(self, node: ast.AST, *, is_method: bool) -> FunctionInfo:
        assert isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        decorators = tuple(ast.unparse(d).strip() for d in node.decorator_list) if node.decorator_list else ()
        doc = ast.get_docstring(node)
        return FunctionInfo(name=node.name, decorators=decorators, docstring=doc, is_method=is_method)

    def _extract_class(self, node: ast.ClassDef) -> ClassInfo:
        bases = tuple(ast.unparse(b).strip() for b in node.bases) if node.bases else ()
        decorators = tuple(ast.unparse(d).strip() for d in node.decorator_list) if node.decorator_list else ()
        doc = ast.get_docstring(node)
        methods: list[FunctionInfo] = []
        for body_node in node.body:
            if isinstance(body_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(self._extract_function(body_node, is_method=True))
        return ClassInfo(name=node.name, bases=bases, methods=tuple(methods), decorators=decorators, docstring=doc)
