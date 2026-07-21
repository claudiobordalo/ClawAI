from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from threading import Lock
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MEMORY_FILE = ROOT / ".clawai" / "intelligence" / "memory.jsonl"

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+", flags=re.UNICODE)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tokenize(text: str) -> set[str]:
    return {token.lower() for token in _TOKEN_RE.findall(text) if len(token) >= 2}


@dataclass(slots=True)
class SemanticMemoryEntry:
    memory_id: str
    objective: str
    prompt: str
    summary: str
    timestamp: str
    tool: str = ""
    outcome: str = ""
    tags: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    source: str = "manual"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class MemorySearchResult:
    entry: SemanticMemoryEntry
    score: float


class SemanticMemoryStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or MEMORY_FILE
        self._lock = Lock()

    def remember(self, payload: dict[str, Any] | SemanticMemoryEntry) -> SemanticMemoryEntry:
        entry = payload if isinstance(payload, SemanticMemoryEntry) else self._entry_from_payload(payload)
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
        return entry

    def search(self, query: str, limit: int = 10) -> list[SemanticMemoryEntry]:
        if not self.path.exists():
            return []

        q_tokens = _tokenize(query)
        q_text = query.strip().lower()
        scored: list[MemorySearchResult] = []
        for entry in self._load_all():
            score = self._score(query=q_text, query_tokens=q_tokens, entry=entry)
            if score > 0:
                scored.append(MemorySearchResult(entry=entry, score=score))

        scored.sort(key=lambda item: (-item.score, item.entry.timestamp), reverse=False)
        scored = sorted(scored, key=lambda item: (-item.score, item.entry.timestamp), reverse=False)
        return [item.entry for item in scored[: max(0, limit)]]

    def recent(self, limit: int = 10) -> list[SemanticMemoryEntry]:
        entries = self._load_all()
        entries.sort(key=lambda item: item.timestamp, reverse=True)
        return entries[: max(0, limit)]

    def stats(self) -> dict[str, Any]:
        entries = self._load_all()
        outcomes: dict[str, int] = {}
        tools: dict[str, int] = {}
        for item in entries:
            outcomes[item.outcome or "unknown"] = outcomes.get(item.outcome or "unknown", 0) + 1
            tools[item.tool or "unknown"] = tools.get(item.tool or "unknown", 0) + 1
        return {
            "total": len(entries),
            "outcomes": outcomes,
            "tools": tools,
            "recent": [entry.to_dict() for entry in self.recent(limit=5)],
        }

    def _entry_from_payload(self, payload: dict[str, Any]) -> SemanticMemoryEntry:
        return SemanticMemoryEntry(
            memory_id=str(payload.get("memory_id") or uuid.uuid4().hex),
            objective=str(payload.get("objective") or payload.get("title") or ""),
            prompt=str(payload.get("prompt") or payload.get("objective") or ""),
            summary=str(payload.get("summary") or payload.get("result") or ""),
            timestamp=str(payload.get("timestamp") or _now()),
            tool=str(payload.get("tool") or payload.get("recommended_tool") or ""),
            outcome=str(payload.get("outcome") or payload.get("status") or ""),
            tags=[str(item) for item in payload.get("tags", []) if isinstance(payload.get("tags"), list)],
            artifacts=[str(item) for item in payload.get("artifacts", []) if isinstance(payload.get("artifacts"), list)],
            source=str(payload.get("source") or "manual"),
            metadata={k: v for k, v in payload.items() if k not in {"memory_id", "objective", "title", "prompt", "summary", "result", "timestamp", "tool", "recommended_tool", "outcome", "status", "tags", "artifacts", "source"}},
        )

    def _load_all(self) -> list[SemanticMemoryEntry]:
        entries: list[SemanticMemoryEntry] = []
        if not self.path.exists():
            return entries

        for line in self.path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                if isinstance(payload, dict):
                    entries.append(self._entry_from_payload(payload))
            except Exception:
                continue
        return entries

    def _score(self, query: str, query_tokens: set[str], entry: SemanticMemoryEntry) -> float:
        haystack = " ".join([
            entry.objective,
            entry.prompt,
            entry.summary,
            entry.tool,
            entry.outcome,
            " ".join(entry.tags),
            " ".join(entry.artifacts),
            json.dumps(entry.metadata, ensure_ascii=False),
        ]).lower()
        entry_tokens = _tokenize(haystack)
        if not entry_tokens:
            return 0.0

        overlap = len(query_tokens & entry_tokens)
        union = len(query_tokens | entry_tokens) or 1
        jaccard = overlap / union
        seq = SequenceMatcher(None, query, haystack).ratio() if query else 0.0
        bonus = 0.0
        if query and query in haystack:
            bonus += 0.3
        if entry.objective and query and query in entry.objective.lower():
            bonus += 0.25
        if entry.summary and query and query in entry.summary.lower():
            bonus += 0.15
        return (jaccard * 0.7) + (seq * 0.3) + bonus


semantic_memory = SemanticMemoryStore()
