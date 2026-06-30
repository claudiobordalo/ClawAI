from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
STATE_FILE = ROOT / ".clawai" / "workspaces.json"
IGNORED_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "node_modules",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_id(path: Path) -> str:
    return hashlib.sha1(str(path).encode("utf-8", errors="ignore")).hexdigest()[:12]


def _load_json(path: Path, default: Any):
    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


@dataclass(slots=True)
class WorkspaceInfo:
    workspace_id: str
    name: str
    root: str
    active: bool = False
    created_at: str = field(default_factory=_now)
    last_opened_at: str = field(default_factory=_now)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "WorkspaceInfo":
        return cls(
            workspace_id=str(payload.get("workspace_id") or payload.get("id") or uuid.uuid4().hex[:12]),
            name=str(payload.get("name") or Path(str(payload.get("root") or ROOT)).name),
            root=str(payload.get("root") or ROOT),
            active=bool(payload.get("active") or False),
            created_at=str(payload.get("created_at") or _now()),
            last_opened_at=str(payload.get("last_opened_at") or _now()),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class WorkspaceManager:
    def __init__(self) -> None:
        self._lock = Lock()
        self._workspaces = self._load()
        if not self._workspaces:
            self._workspaces = [
                WorkspaceInfo(
                    workspace_id="default",
                    name=ROOT.name,
                    root=str(ROOT),
                    active=True,
                )
            ]
            self._save()
        if not any(workspace.active for workspace in self._workspaces):
            self._workspaces[0].active = True
            self._save()

    def _load(self) -> list[WorkspaceInfo]:
        payload = _load_json(STATE_FILE, [])
        if not isinstance(payload, list):
            return []
        items: list[WorkspaceInfo] = []
        for raw in payload:
            if isinstance(raw, dict):
                try:
                    items.append(WorkspaceInfo.from_dict(raw))
                except Exception:
                    continue
        return items

    def _save(self) -> None:
        _dump_json(STATE_FILE, [workspace.to_dict() for workspace in self._workspaces])

    def list_workspaces(self) -> list[WorkspaceInfo]:
        with self._lock:
            self._workspaces.sort(key=lambda item: (not item.active, item.last_opened_at), reverse=False)
            return [WorkspaceInfo.from_dict(workspace.to_dict()) for workspace in self._workspaces]

    def current(self) -> WorkspaceInfo:
        with self._lock:
            for workspace in self._workspaces:
                if workspace.active:
                    return WorkspaceInfo.from_dict(workspace.to_dict())
            return WorkspaceInfo.from_dict(self._workspaces[0].to_dict())

    def get(self, workspace_id: str) -> WorkspaceInfo:
        with self._lock:
            for workspace in self._workspaces:
                if workspace.workspace_id == workspace_id:
                    return WorkspaceInfo.from_dict(workspace.to_dict())
        raise KeyError(workspace_id)

    def _find_by_root(self, root: Path) -> WorkspaceInfo | None:
        root_str = str(root)
        for workspace in self._workspaces:
            if Path(workspace.root) == root or workspace.root == root_str:
                return workspace
        return None

    def open_workspace(self, path: str, name: str | None = None) -> WorkspaceInfo:
        target = Path(path).expanduser().resolve()
        if not target.exists():
            raise FileNotFoundError(f"Workspace folder not found: {path}")
        if not target.is_dir():
            raise NotADirectoryError(f"Workspace path is not a directory: {path}")

        with self._lock:
            existing = self._find_by_root(target)
            if existing:
                self._activate(existing.workspace_id)
                existing.name = name or existing.name or target.name
                existing.last_opened_at = _now()
                self._save()
                return WorkspaceInfo.from_dict(existing.to_dict())

            workspace = WorkspaceInfo(
                workspace_id=_stable_id(target),
                name=name or target.name,
                root=str(target),
                active=True,
            )

            for item in self._workspaces:
                item.active = False
            self._workspaces.append(workspace)
            self._save()
            return WorkspaceInfo.from_dict(workspace.to_dict())

    def set_active(self, workspace_id: str) -> WorkspaceInfo:
        with self._lock:
            workspace = self._activate(workspace_id)
            workspace.last_opened_at = _now()
            self._save()
            return WorkspaceInfo.from_dict(workspace.to_dict())

    def close_workspace(self, workspace_id: str) -> list[WorkspaceInfo]:
        with self._lock:
            if len(self._workspaces) == 1:
                return [WorkspaceInfo.from_dict(self._workspaces[0].to_dict())]

            next_workspaces = [workspace for workspace in self._workspaces if workspace.workspace_id != workspace_id]
            if len(next_workspaces) == len(self._workspaces):
                return [WorkspaceInfo.from_dict(workspace.to_dict()) for workspace in self._workspaces]

            if not any(workspace.active for workspace in next_workspaces):
                next_workspaces[0].active = True

            self._workspaces = next_workspaces
            self._save()
            return [WorkspaceInfo.from_dict(workspace.to_dict()) for workspace in self._workspaces]

    def _activate(self, workspace_id: str) -> WorkspaceInfo:
        found: WorkspaceInfo | None = None
        for workspace in self._workspaces:
            workspace.active = workspace.workspace_id == workspace_id
            if workspace.active:
                found = workspace
        if found is None:
            raise KeyError(workspace_id)
        return found

    def active_root(self, workspace_id: str | None = None) -> Path:
        if workspace_id:
            workspace = self.get(workspace_id)
            return Path(workspace.root)
        return Path(self.current().root)

    def resolve_path(self, path: str, workspace_id: str | None = None) -> Path:
        root = self.active_root(workspace_id)
        target = root if not path else (root / path).resolve()
        if target != root and root not in target.parents:
            raise PermissionError("Invalid path")
        return target

    def tree(self, path: str = "", workspace_id: str | None = None) -> list[dict[str, Any]]:
        directory = self.resolve_path(path, workspace_id=workspace_id)
        if not directory.exists():
            raise FileNotFoundError("Folder not found")
        if not directory.is_dir():
            raise NotADirectoryError("Path is not a folder")

        items: list[dict[str, Any]] = []
        for child in sorted(directory.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            if child.name in IGNORED_NAMES:
                continue
            items.append(
                {
                    "name": child.name,
                    "path": str(child.relative_to(self.active_root(workspace_id))).replace("\\", "/"),
                    "directory": child.is_dir(),
                    "children": [],
                }
            )
        return items

    def read_file(self, path: str, workspace_id: str | None = None) -> str:
        target = self.resolve_path(path, workspace_id=workspace_id)
        if not target.exists() or not target.is_file():
            raise FileNotFoundError("File not found")
        return target.read_text(encoding="utf-8", errors="ignore")

    def save_file(self, path: str, content: str, workspace_id: str | None = None) -> dict[str, Any]:
        target = self.resolve_path(path, workspace_id=workspace_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {
            "success": True,
            "path": str(target.relative_to(self.active_root(workspace_id))).replace("\\", "/"),
            "workspace_id": workspace_id or self.current().workspace_id,
        }

    def summary(self) -> dict[str, Any]:
        current = self.current()
        workspaces = self.list_workspaces()
        return {
            "current": current.to_dict(),
            "workspaces": [workspace.to_dict() for workspace in workspaces],
            "active_count": sum(1 for workspace in workspaces if workspace.active),
        }


workspace_manager = WorkspaceManager()
