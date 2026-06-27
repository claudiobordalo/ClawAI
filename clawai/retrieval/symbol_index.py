from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from clawai.codebase import ProjectSnapshot, ModuleInfo, ClassInfo, FunctionInfo


@dataclass(frozen=True)
class SymbolRef:
    kind: str  # module | class | function | method
    name: str  # symbol simple name (for method, method name)
    qualname: str  # for method: Class.method; for others: same as name
    module: str  # module name (stem)
    file: str  # relative path from project root


class SymbolIndex:
    """
    Índice determinístico de símbolos a partir de um ProjectSnapshot.
    Permite localizar módulos, classes, funções e métodos por nome simples.
    """

    def __init__(self, snapshot: ProjectSnapshot) -> None:
        self._root = Path(snapshot.root)
        self._by_module: Dict[str, Tuple[SymbolRef, ...]] = {}
        self._by_class: Dict[str, Tuple[SymbolRef, ...]] = {}
        self._by_function: Dict[str, Tuple[SymbolRef, ...]] = {}
        self._by_symbol: Dict[str, Tuple[SymbolRef, ...]] = {}

        # Build deterministic lists
        module_refs: List[SymbolRef] = []
        class_pairs: List[Tuple[str, SymbolRef]] = []
        func_pairs: List[Tuple[str, SymbolRef]] = []
        sym_pairs: List[Tuple[str, SymbolRef]] = []

        # Create module refs
        for m in snapshot.modules:
            rel = self._rel(m.file.path)
            ref = SymbolRef(kind="module", name=m.module_name, qualname=m.module_name, module=m.module_name, file=rel)
            module_refs.append(ref)

            # classes
            for c in m.classes:
                cref = SymbolRef(
                    kind="class",
                    name=c.name,
                    qualname=c.name,
                    module=m.module_name,
                    file=rel,
                )
                class_pairs.append((c.name, cref))
                sym_pairs.append((c.name, cref))
                # methods
                for meth in c.methods:
                    mref = SymbolRef(
                        kind="method",
                        name=meth.name,
                        qualname=f"{c.name}.{meth.name}",
                        module=m.module_name,
                        file=rel,
                    )
                    sym_pairs.append((meth.name, mref))

            # functions
            for fn in m.functions:
                fref = SymbolRef(
                    kind="function",
                    name=fn.name,
                    qualname=fn.name,
                    module=m.module_name,
                    file=rel,
                )
                func_pairs.append((fn.name, fref))
                sym_pairs.append((fn.name, fref))

        # Group deterministically
        def group_pairs(pairs: List[Tuple[str, SymbolRef]]) -> Dict[str, Tuple[SymbolRef, ...]]:
            out: Dict[str, Tuple[SymbolRef, ...]] = {}
            # Sort by key then by (file, qualname)
            pairs.sort(key=lambda x: (x[0], x[1].file, x[1].qualname))
            i = 0
            n = len(pairs)
            while i < n:
                key = pairs[i][0]
                same: List[SymbolRef] = []
                while i < n and pairs[i][0] == key:
                    same.append(pairs[i][1])
                    i += 1
                out[key] = tuple(same)
            return out

        # Modules grouped by name (unique usually)
        module_pairs = [(r.name, r) for r in module_refs]
        self._by_module = group_pairs(module_pairs)
        self._by_class = group_pairs(class_pairs)
        self._by_function = group_pairs(func_pairs)
        self._by_symbol = group_pairs(sym_pairs)

    def _rel(self, path: str) -> str:
        try:
            return str(Path(path).resolve().relative_to(self._root)).replace("\\", "/")
        except Exception:
            return str(path).replace("\\", "/")

    # API mínima
    def find_module(self, name: str) -> Tuple[SymbolRef, ...]:
        return self._by_module.get(name, ())

    def find_class(self, name: str) -> Tuple[SymbolRef, ...]:
        return self._by_class.get(name, ())

    def find_function(self, name: str) -> Tuple[SymbolRef, ...]:
        return self._by_function.get(name, ())

    def find_symbol(self, name: str) -> Tuple[SymbolRef, ...]:
        # Unificado: classes, functions e methods (e pode incluir modules)
        res = self._by_symbol.get(name, ())
        if res:
            return res
        return self._by_module.get(name, ())
