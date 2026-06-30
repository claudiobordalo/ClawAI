from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, fields
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
STATE_FILE = ROOT / ".clawai" / "workspaces.json"
IGNORED = {".git", ".venv", "__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache", "node_modules"}

_ALLOWED_FIELDS = {f.name for f in fields(Workspace)}
def _workspace_from_dict(data: dict) -> Workspace:
    return Workspace(
        **{
            k: v
            for k, v in data.items()
            if k in _ALLOWED_FIELDS
        }
    )

def _stable_id(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8", errors="ignore")).hexdigest()[:12]


def _load() -> list[dict[str, Any]]:
    if not STATE_FILE.exists():
        return []
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(items: list[dict[str, Any]]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


@dataclass
class Workspace:
    workspace_id: str
    name: str
    root: str
    active: bool = False
    created_at: str | None = None

class WorkspaceState:
    def __init__(self) -> None:
        self._lock = Lock()
        self._items = [
            _workspace_from_dict(item)
            for item in _load()
            if isinstance(item, dict)
        ]
        if not self._items:
            self._items = [Workspace("default", ROOT.name, str(ROOT), True)]
            self._persist()
        if not any(item.active for item in self._items):
            self._items[0].active = True
            self._persist()

    def _persist(self) -> None:
        _save([asdict(item) for item in self._items])

    def current(self) -> Workspace:
        for item in self._items:
            if item.active:
                return item
        return self._items[0]

    def list(self) -> list[Workspace]:
        return list(self._items)

    def open(self, path: str, name: str | None = None) -> Workspace:
        target = Path(path).expanduser().resolve()
        if not target.exists() or not target.is_dir():
            raise FileNotFoundError(path)
        with self._lock:
            for item in self._items:
                if Path(item.root) == target:
                    self.select(item.workspace_id)
                    return item
            for item in self._items:
                item.active = False
            workspace = Workspace(_stable_id(str(target)), name or target.name, str(target), True)
            self._items.append(workspace)
            self._persist()
            return workspace

    def select(self, workspace_id: str) -> Workspace:
        with self._lock:
            selected = None
            for item in self._items:
                item.active = item.workspace_id == workspace_id
                if item.active:
                    selected = item
            if selected is None:
                raise KeyError(workspace_id)
            self._persist()
            return selected

    def close(self, workspace_id: str) -> list[Workspace]:
        with self._lock:
            if len(self._items) == 1:
                return self._items
            self._items = [item for item in self._items if item.workspace_id != workspace_id]
            if not any(item.active for item in self._items):
                self._items[0].active = True
            self._persist()
            return self._items

    def root(self, workspace_id: str | None = None) -> Path:
        ws = self.current() if workspace_id is None else next(item for item in self._items if item.workspace_id == workspace_id)
        return Path(ws.root)

    def resolve(self, path: str, workspace_id: str | None = None) -> Path:
        base = self.root(workspace_id)
        target = base if not path else (base / path).resolve()
        if target != base and base not in target.parents:
            raise PermissionError("Invalid path")
        return target

    def tree(self, path: str = "", workspace_id: str | None = None) -> list[dict[str, Any]]:
        directory = self.resolve(path, workspace_id)
        if not directory.exists() or not directory.is_dir():
            raise FileNotFoundError(path)
        items = []
        for child in sorted(directory.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            if child.name in IGNORED:
                continue
            items.append({"name": child.name, "path": str(child.relative_to(self.root(workspace_id))).replace("\\", "/"), "directory": child.is_dir(), "children": []})
        return items

    def read(self, path: str, workspace_id: str | None = None) -> str:
        file = self.resolve(path, workspace_id)
        if not file.exists() or not file.is_file():
            raise FileNotFoundError(path)
        return file.read_text(encoding="utf-8", errors="ignore")

    def write(self, path: str, content: str, workspace_id: str | None = None) -> dict[str, Any]:
        file = self.resolve(path, workspace_id)
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding="utf-8")
        return {"success": True, "workspace_id": self.current().workspace_id, "path": str(file.relative_to(self.root(workspace_id))).replace("\\", "/")}

    def summary(self) -> dict[str, Any]:
        return {"current": asdict(self.current()), "workspaces": [asdict(item) for item in self._items]}


workspace_state = WorkspaceState()
