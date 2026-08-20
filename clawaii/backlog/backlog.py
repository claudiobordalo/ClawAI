from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
BACKLOG_PATH = ROOT / "backlog" / "state.json"


@dataclass
class BacklogItem:
    id: str
    type: str  # 'tech_debt' or 'roadmap'
    title: str
    description: str
    status: str  # 'open', 'in_progress', 'done', 'cancelled'
    priority: int  # 1 (high) to 5 (low)
    created_at: str
    updated_at: str
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BacklogItem":
        return cls(**data)


class BacklogManager:
    def __init__(self, path: Path | None = None):
        self.path = path or BACKLOG_PATH
        self.items: list[BacklogItem] = []
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                self.items = [BacklogItem.from_dict(item) for item in data.get("items", [])]
            except Exception:
                self.items = []
        else:
            self.items = []

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {"items": [item.to_dict() for item in self.items]}
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def add_item(
        self,
        type: str,
        title: str,
        description: str = "",
        priority: int = 3,
        tags: list[str] | None = None,
    ) -> BacklogItem:
        item_id = f"{type[:3]}-{int(time.time())}"
        now = datetime.now(timezone.utc).isoformat()
        item = BacklogItem(
            id=item_id,
            type=type,
            title=title,
            description=description,
            status="open",
            priority=priority,
            created_at=now,
            updated_at=now,
            tags=tags or [],
        )
        self.items.append(item)
        self._save()
        return item

    def update_item_status(self, item_id: str, status: str) -> bool:
        for item in self.items:
            if item.id == item_id:
                item.status = status
                item.updated_at = datetime.now(timezone.utc).isoformat()
                self._save()
                return True
        return False

    def add_tag(self, item_id: str, tag: str) -> bool:
        for item in self.items:
            if item.id == item_id:
                if tag not in item.tags:
                    item.tags.append(tag)
                    item.updated_at = datetime.now(timezone.utc).isoformat()
                    self._save()
                    return True
        return False

    def remove_item(self, item_id: str) -> bool:
        initial_len = len(self.items)
        self.items = [item for item in self.items if item.id != item_id]
        if len(self.items) < initial_len:
            self._save()
            return True
        return False

    def get_items_by_type(self, item_type: str) -> list[BacklogItem]:
        return [item for item in self.items if item.type == item_type]

    def get_open_items(self, item_type: str | None = None) -> list[BacklogItem]:
        items = [item for item in self.items if item.status == "open"]
        if item_type:
            items = [item for item in items if item.type == item_type]
        return sorted(items, key=lambda x: x.priority)

    def get_stats(self) -> dict[str, int]:
        stats = {"total": len(self.items), "open": 0, "in_progress": 0, "done": 0, "cancelled": 0}
        for item in self.items:
            if item.status in stats:
                stats[item.status] += 1
        return stats

    def __repr__(self) -> str:
        return f"BacklogManager(items={len(self.items)}, path={self.path})"
