from __future__ import annotations

import json
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


@dataclass(slots=True)
class RuntimeTraceEvent:
    stage: str
    timestamp: str
    data: Any


@dataclass(slots=True)
class RuntimeTrace:
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    events: list[RuntimeTraceEvent] = field(default_factory=list)

    def add(self, stage: str, data: Any) -> None:
        self.events.append(
            RuntimeTraceEvent(
                stage=stage,
                timestamp=datetime.now(timezone.utc).isoformat(),
                data=data,
            )
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "created_at": self.created_at,
            "events": [
                {
                    "stage": event.stage,
                    "timestamp": event.timestamp,
                    "data": event.data,
                }
                for event in self.events
            ],
        }

    def save(self, root: str | Path | None = None) -> Path:
        target_root = Path(root) if root is not None else Path.cwd() / ".clawai" / "traces"
        target_root.mkdir(parents=True, exist_ok=True)
        target = target_root / f"trace_{self.run_id}.json"
        target.write_text(json.dumps(self.snapshot(), ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return target


@dataclass(slots=True)
class RuntimeProfileEntry:
    label: str
    elapsed_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RuntimeProfiler:
    entries: list[RuntimeProfileEntry] = field(default_factory=list)

    @contextmanager
    def measure(self, label: str, *, metadata: dict[str, Any] | None = None) -> Iterator[RuntimeProfileEntry]:
        entry = RuntimeProfileEntry(label=label, metadata=metadata or {})
        start = time.perf_counter()
        try:
            yield entry
        finally:
            entry.elapsed_ms = (time.perf_counter() - start) * 1000
            self.entries.append(entry)

    def snapshot(self) -> dict[str, Any]:
        return {
            "entries": [
                {
                    "label": entry.label,
                    "elapsed_ms": entry.elapsed_ms,
                    "metadata": entry.metadata,
                }
                for entry in self.entries
            ],
            "total_ms": sum(entry.elapsed_ms for entry in self.entries),
        }


@dataclass(slots=True)
class LLMCallMetrics:
    max_calls: int = 10
    calls: list[dict[str, Any]] = field(default_factory=list)

    @property
    def should_abort(self) -> bool:
        return len(self.calls) > self.max_calls

    def record(self, role: str, *, metadata: dict[str, Any] | None = None) -> None:
        self.calls.append({"role": role, "metadata": metadata or {}})

    def snapshot(self) -> dict[str, Any]:
        return {
            "max_calls": self.max_calls,
            "total_calls": len(self.calls),
            "should_abort": self.should_abort,
            "calls": list(self.calls),
        }
