from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
CACHE_FILE = ROOT / ".clawai" / "composio" / "cache.json"


@dataclass(slots=True)
class ComposioCache:
    path: Path = CACHE_FILE
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)

    def load(self) -> dict[str, Any]:
        with self._lock:
            if not self.path.exists():
                return {}

            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                return {}

    def save(self, payload: dict[str, Any]) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def get(self, key: str, default: Any = None) -> Any:
        payload = self.load()
        return payload.get(key, default)

    def set(self, key: str, value: Any) -> None:
        payload = self.load()
        payload[key] = value
        self.save(payload)

    def clear(self) -> None:
        with self._lock:
            if self.path.exists():
                self.path.unlink()


composio_cache = ComposioCache()
