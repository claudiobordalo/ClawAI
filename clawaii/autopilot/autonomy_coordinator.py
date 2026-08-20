from __future__ import annotations

import hashlib
import json
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from clawai.autopilot.auto_implement_runtime import auto_implement

ROOT = Path(__file__).resolve().parents[2]
STATE_ROOT = ROOT / ".clawai" / "autonomy"
PLANS_DIR = STATE_ROOT / "plans"
MEMORY_FILE = STATE_ROOT / "memory.jsonl"
QUEUE_FILE = STATE_ROOT / "queue.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_state_dirs() -> None:
    PLANS_DIR.mkdir(parents=True, exist_ok=True)
    STATE_ROOT.mkdir(parents=True, exist_ok=True)


def _slugify(text: str) -> str:
    normalized = "".join(ch.lower() if ch.isalnum() else "-" for ch in text.strip())
    normalized = "-".join(part for part in normalized.split("-") if part)
    return normalized[:60] or "objective"


def _objective_id(objective: str) -> str:
    return hashlib.sha1(objective.strip().lower().encode("utf-8")).hexdigest()[:12]


def _json_load(path: Path, default: Any):
    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _json_dump(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


@dataclass(slots=True)
class PlanningSubtask:
    title: str
    status: str = "pending"
    progress: float = 0.0
    note: str = ""


@dataclass(slots=True)
class PlanningState:
    objective_id: str
    objective: str
    plan_id: str
    created_at: str
    updated_at: str
    status: str = "active"
    subtasks: list[PlanningSubtask] = field(default_factory=list)
    current_index: int = 0
    progress: float = 0.0
    last_run_id: str = ""
    last_summary: str = ""


@dataclass(slots=True)
class EngineeringMemoryEntry:
    memory_id: str
    objective_id: str
    objective: str
    timestamp: str
    outcome: str
    summary: str
    decisions: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    solutions: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    git_commit: str = ""
    verify_success: bool | None = None
    notes: str = ""


@dataclass(slots=True)
class QueueItem:
    queue_id: str
    objective_id: str
    objective: str
    test_command: str
    max_iterations: int
    max_files: int
    enqueued_at: str
    status: str = "queued"
    run_id: str = ""
    order: int = 0
    summary: str = ""
    error: str = ""
    result_success: bool | None = None


def _plan_seed(objective: str, memory_hits: list[EngineeringMemoryEntry]) -> list[str]:
    tokens = objective.lower()
    subtasks = [
        "Entender o objetivo e localizar os arquivos centrais",
        "Aplicar a implementação principal com mudanças mínimas",
        "Executar testes e verify para validar a alteração",
        "Registrar a solução e preparar commit/rollback automático",
    ]

    if "git" in tokens:
        subtasks.insert(0, "Preparar branch, commit e merge automáticos")
    if "fila" in tokens or "queue" in tokens:
        subtasks.insert(0, "Garantir processamento sequencial da fila")
    if "memória" in tokens or "memory" in tokens:
        subtasks.insert(0, "Persistir decisões e reutilizar contexto anterior")
    if "planej" in tokens or "plan" in tokens:
        subtasks.insert(0, "Persistir plano e acompanhar progresso entre execuções")

    if memory_hits:
        subtasks.append(f"Reaproveitar {len(memory_hits)} memórias relevantes já registradas")

    deduped: list[str] = []
    for item in subtasks:
        if item not in deduped:
            deduped.append(item)
    return deduped


def _score_memory(objective: str, entry: EngineeringMemoryEntry) -> int:
    objective_tokens = {t for t in objective.lower().replace("/", " ").replace("-", " ").split() if len(t) >= 3}
    haystack = " ".join(
        [
            entry.objective.lower(),
            entry.summary.lower(),
            " ".join(entry.decisions).lower(),
            " ".join(entry.errors).lower(),
            " ".join(entry.solutions).lower(),
            " ".join(entry.files).lower(),
        ]
    )
    score = 0
    for token in objective_tokens:
        if token in haystack:
            score += 2
    if entry.objective_id == _objective_id(objective):
        score += 10
    return score


class AutonomyCoordinator:
    def __init__(self) -> None:
        _ensure_state_dirs()
        self._lock = threading.Lock()
        self._worker_lock = threading.Lock()
        self._worker: threading.Thread | None = None

    def _load_plans(self) -> dict[str, PlanningState]:
        raw = _json_load(PLANS_DIR / "_index.json", {})
        plans: dict[str, PlanningState] = {}
        for objective_id, payload in raw.items():
            try:
                subtasks = [PlanningSubtask(**item) for item in payload.get("subtasks", [])]
                plans[objective_id] = PlanningState(
                    objective_id=payload["objective_id"],
                    objective=payload["objective"],
                    plan_id=payload["plan_id"],
                    created_at=payload["created_at"],
                    updated_at=payload["updated_at"],
                    status=payload.get("status", "active"),
                    subtasks=subtasks,
                    current_index=int(payload.get("current_index", 0)),
                    progress=float(payload.get("progress", 0.0)),
                    last_run_id=payload.get("last_run_id", ""),
                    last_summary=payload.get("last_summary", ""),
                )
            except Exception:
                continue
        return plans

    def _save_plan(self, plan: PlanningState) -> None:
        _ensure_state_dirs()
        raw = _json_load(PLANS_DIR / "_index.json", {})
        raw[plan.objective_id] = asdict(plan)
        _json_dump(PLANS_DIR / "_index.json", raw)
        _json_dump(PLANS_DIR / f"{plan.objective_id}.json", asdict(plan))

    def _load_or_create_plan(self, objective: str) -> PlanningState:
        objective_id = _objective_id(objective)
        index = self._load_plans()
        existing = index.get(objective_id)
        if existing:
            return existing

        memory_hits = self.list_memory(objective, limit=5)
        subtasks = [PlanningSubtask(title=item) for item in _plan_seed(objective, memory_hits)]
        plan = PlanningState(
            objective_id=objective_id,
            objective=objective.strip(),
            plan_id=uuid.uuid4().hex,
            created_at=_now(),
            updated_at=_now(),
            subtasks=subtasks,
        )
        self._save_plan(plan)
        return plan

    def get_plan(self, objective_id: str) -> PlanningState | None:
        return self._load_plans().get(objective_id)

    def list_plans(self) -> list[PlanningState]:
        return list(self._load_plans().values())

    def _load_memory(self) -> list[EngineeringMemoryEntry]:
        entries: list[EngineeringMemoryEntry] = []
        if not MEMORY_FILE.exists():
            return entries
        for line in MEMORY_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                entries.append(EngineeringMemoryEntry(**payload))
            except Exception:
                continue
        return entries

    def list_memory(self, objective: str | None = None, limit: int = 20) -> list[EngineeringMemoryEntry]:
        entries = self._load_memory()
        if objective:
            entries.sort(key=lambda entry: _score_memory(objective, entry), reverse=True)
        else:
            entries.sort(key=lambda entry: entry.timestamp, reverse=True)
        return entries[: max(0, limit)]

    def record_memory(self, entry: EngineeringMemoryEntry) -> None:
        _ensure_state_dirs()
        with MEMORY_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")

    def _load_queue(self) -> list[QueueItem]:
        payload = _json_load(QUEUE_FILE, [])
        items: list[QueueItem] = []
        if isinstance(payload, list):
            for raw in payload:
                try:
                    items.append(QueueItem(**raw))
                except Exception:
                    continue
        return items

    def _save_queue(self, items: list[QueueItem]) -> None:
        _ensure_state_dirs()
        _json_dump(QUEUE_FILE, [asdict(item) for item in items])

    def list_queue(self) -> list[QueueItem]:
        items = self._load_queue()
        items.sort(key=lambda item: (item.order, item.enqueued_at))
        return items

    def queue_size(self) -> int:
        return len([item for item in self._load_queue() if item.status in {"queued", "running"}])

    def enqueue(
        self,
        objective: str,
        test_command: str = "uv run python -m pytest -q",
        max_iterations: int = 3,
        max_files: int = 15,
    ) -> QueueItem:
        objective = objective.strip()
        if not objective:
            raise ValueError("objective is required")

        with self._lock:
            items = self._load_queue()
            next_order = (max((item.order for item in items), default=0) + 1) if items else 1
            item = QueueItem(
                queue_id=uuid.uuid4().hex,
                objective_id=_objective_id(objective),
                objective=objective,
                test_command=test_command,
                max_iterations=max(1, min(int(max_iterations), 5)),
                max_files=max(1, min(int(max_files), 20)),
                enqueued_at=_now(),
                order=next_order,
            )
            items.append(item)
            self._save_queue(items)
            self._ensure_worker()
            return item

    def _ensure_worker(self) -> None:
        with self._worker_lock:
            if self._worker and self._worker.is_alive():
                return
            self._worker = threading.Thread(target=self._worker_loop, daemon=True)
            self._worker.start()

    def _worker_loop(self) -> None:
        while True:
            with self._lock:
                items = self._load_queue()
                next_item = next((item for item in items if item.status == "queued"), None)
                if next_item is None:
                    self._save_queue(items)
                    return
                next_item.status = "running"
                next_item.run_id = uuid.uuid4().hex[:12]
                self._save_queue(items)

            try:
                result = auto_implement.implement(
                    objective=next_item.objective,
                    test_command=next_item.test_command,
                    max_iterations=next_item.max_iterations,
                    max_files=next_item.max_files,
                )
                next_item.status = "done" if result.success else "failed"
                next_item.result_success = result.success
                next_item.summary = result.summary
                next_item.error = ""
                self._record_from_result(next_item, result)
            except Exception as exc:
                next_item.status = "failed"
                next_item.error = str(exc)
                next_item.result_success = False

            with self._lock:
                items = self._load_queue()
                for idx, item in enumerate(items):
                    if item.queue_id == next_item.queue_id:
                        items[idx] = next_item
                        break
                self._save_queue(items)

    def _record_from_result(self, item: QueueItem, result: Any) -> None:
        objective_id = item.objective_id
        plan = self._load_or_create_plan(item.objective)
        plan.updated_at = _now()
        plan.last_run_id = item.run_id
        plan.last_summary = getattr(result, "summary", "")
        plan.status = "completed" if getattr(result, "success", False) else "failed"
        if plan.subtasks:
            completed = min(len(plan.subtasks), max(1, len(getattr(result, "iterations", []))))
            for idx, subtask in enumerate(plan.subtasks):
                if idx < completed and getattr(result, "success", False):
                    subtask.status = "done"
                    subtask.progress = 1.0
            plan.current_index = min(completed, len(plan.subtasks))
            plan.progress = plan.current_index / max(len(plan.subtasks), 1)
        self._save_plan(plan)

        memory_entry = EngineeringMemoryEntry(
            memory_id=uuid.uuid4().hex,
            objective_id=objective_id,
            objective=item.objective,
            timestamp=_now(),
            outcome="success" if getattr(result, "success", False) else "failed",
            summary=getattr(result, "summary", ""),
            decisions=[
                f"branch={getattr(result, 'git_branch', '')}",
                f"commit={getattr(result, 'git_commit', '')}",
                f"verify={'pass' if getattr(result, 'verify_success', False) else 'fail'}",
            ],
            errors=[
                getattr(result, "git_rollback_reason", "") or "",
            ],
            solutions=[
                getattr(result, "verify_summary", "") or "",
            ],
            files=list(getattr(result, "candidate_files", []) or []),
            git_commit=getattr(result, "git_commit", "") or "",
            verify_success=getattr(result, "verify_success", None),
        )
        self.record_memory(memory_entry)

    def get_state(self) -> dict[str, Any]:
        plans = self.list_plans()
        queue = self.list_queue()
        memory = self.list_memory(limit=20)
        return {
            "plans": [asdict(plan) for plan in plans],
            "queue": [asdict(item) for item in queue],
            "recent_memory": [asdict(entry) for entry in memory],
        }


autonomy = AutonomyCoordinator()
