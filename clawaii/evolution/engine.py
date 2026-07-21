from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from clawai.autopilot import autonomy
from clawai.integrations.composio import composio_service
from clawai.intelligence.broker import cognition_broker, intelligence_orchestrator

ROOT = Path(__file__).resolve().parents[2]
STATE_ROOT = ROOT / ".clawai" / "evolution"
BACKLOG_FILE = STATE_ROOT / "backlog.json"
HISTORY_FILE = STATE_ROOT / "history.jsonl"
STATE_FILE = STATE_ROOT / "state.json"

IGNORED_DIRS = {".git", ".venv", "__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache", "node_modules", ".clawai"}
TEXT_EXTS = {".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".txt", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".css", ".html", ".sh", ".ps1"}
TODO_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b", re.IGNORECASE)
MERGE_RE = re.compile(r"^(<<<<<<<|=======|>>>>>>>)", re.MULTILINE)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dirs() -> None:
    STATE_ROOT.mkdir(parents=True, exist_ok=True)


def _json_load(path: Path, default: Any):
    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _stable_id(value: str) -> str:
    return hashlib.sha1(value.strip().lower().encode("utf-8")).hexdigest()[:12]


def _clean(text: str) -> str:
    return " ".join(text.strip().split())[:220]


@dataclass(slots=True)
class EvolutionBacklogItem:
    backlog_id: str
    objective_id: str
    title: str
    objective: str
    description: str
    category: str
    priority: int
    status: str = "pending"
    reasons: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    queue_id: str = ""
    run_id: str = ""
    attempts: int = 0
    last_error: str = ""
    result_summary: str = ""
    verify_success: bool | None = None
    auto_enqueued: bool = False
    test_command: str = "python verify.py"
    max_iterations: int = 3
    max_files: int = 15

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "EvolutionBacklogItem":
        objective = str(payload.get("objective") or payload.get("title") or "")
        return cls(
            backlog_id=str(payload.get("backlog_id") or uuid.uuid4().hex),
            objective_id=str(payload.get("objective_id") or _stable_id(objective)),
            title=str(payload.get("title") or objective or "Improvement"),
            objective=objective,
            description=str(payload.get("description") or ""),
            category=str(payload.get("category") or "general"),
            priority=int(payload.get("priority") or 50),
            status=str(payload.get("status") or "pending"),
            reasons=[str(item) for item in payload.get("reasons", [])] if isinstance(payload.get("reasons"), list) else [],
            tags=[str(item) for item in payload.get("tags", [])] if isinstance(payload.get("tags"), list) else [],
            created_at=str(payload.get("created_at") or _now()),
            updated_at=str(payload.get("updated_at") or _now()),
            queue_id=str(payload.get("queue_id") or ""),
            run_id=str(payload.get("run_id") or ""),
            attempts=int(payload.get("attempts") or 0),
            last_error=str(payload.get("last_error") or ""),
            result_summary=str(payload.get("result_summary") or ""),
            verify_success=payload.get("verify_success") if payload.get("verify_success") is None else bool(payload.get("verify_success")),
            auto_enqueued=bool(payload.get("auto_enqueued") or False),
            test_command=str(payload.get("test_command") or "python verify.py"),
            max_iterations=int(payload.get("max_iterations") or 3),
            max_files=int(payload.get("max_files") or 15),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EvolutionAnalysis:
    objective: str
    summary: str
    timestamp: str
    project_health: dict[str, Any] = field(default_factory=dict)
    signals: list[str] = field(default_factory=list)
    candidates: list[EvolutionBacklogItem] = field(default_factory=list)
    intelligence: dict[str, Any] = field(default_factory=dict)
    composio: dict[str, Any] = field(default_factory=dict)
    autonomy: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EvolutionCycleRecord:
    cycle_id: str
    started_at: str
    finished_at: str = ""
    status: str = "running"
    analysis_summary: str = ""
    backlog_created: int = 0
    backlog_queued: int = 0
    backlog_completed: int = 0
    queued_title: str = ""
    queued_objective_id: str = ""
    queued_queue_id: str = ""
    queued_run_id: str = ""
    active_queue_size: int = 0
    signals: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EvolutionState:
    enabled: bool = False
    running: bool = False
    interval_seconds: int = 900
    cycles_run: int = 0
    last_cycle_at: str = ""
    last_success_at: str = ""
    last_error: str = ""
    last_summary: str = ""
    backlog_size: int = 0
    pending_items: int = 0
    queued_items: int = 0
    running_items: int = 0
    completed_items: int = 0
    active_queue_size: int = 0
    next_cycle_at: str = ""
    last_queued_title: str = ""
    last_queued_objective_id: str = ""
    last_cycle_id: str = ""


class EvolutionEngine:
    def __init__(self, interval_seconds: int | None = None) -> None:
        _ensure_dirs()
        self.interval_seconds = max(60, int(interval_seconds or int(os.getenv("CLAWAI_EVOLUTION_INTERVAL_SECONDS", "900"))))
        self._lock = threading.Lock()
        self._worker_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._worker: threading.Thread | None = None
        self._state = self._load_state()
        self._state.interval_seconds = self.interval_seconds
        self._save_state(self._state)

    def _load_state(self) -> EvolutionState:
        payload = _json_load(STATE_FILE, {})
        if isinstance(payload, dict):
            try:
                return EvolutionState(
                    enabled=bool(payload.get("enabled", False)),
                    running=bool(payload.get("running", False)),
                    interval_seconds=int(payload.get("interval_seconds") or self.interval_seconds),
                    cycles_run=int(payload.get("cycles_run") or 0),
                    last_cycle_at=str(payload.get("last_cycle_at") or ""),
                    last_success_at=str(payload.get("last_success_at") or ""),
                    last_error=str(payload.get("last_error") or ""),
                    last_summary=str(payload.get("last_summary") or ""),
                    backlog_size=int(payload.get("backlog_size") or 0),
                    pending_items=int(payload.get("pending_items") or 0),
                    queued_items=int(payload.get("queued_items") or 0),
                    running_items=int(payload.get("running_items") or 0),
                    completed_items=int(payload.get("completed_items") or 0),
                    active_queue_size=int(payload.get("active_queue_size") or 0),
                    next_cycle_at=str(payload.get("next_cycle_at") or ""),
                    last_queued_title=str(payload.get("last_queued_title") or ""),
                    last_queued_objective_id=str(payload.get("last_queued_objective_id") or ""),
                    last_cycle_id=str(payload.get("last_cycle_id") or ""),
                )
            except Exception:
                pass
        return EvolutionState(interval_seconds=self.interval_seconds)

    def _save_state(self, state: EvolutionState) -> None:
        _json_dump(STATE_FILE, asdict(state))

    def _load_backlog(self) -> list[EvolutionBacklogItem]:
        payload = _json_load(BACKLOG_FILE, [])
        items: list[EvolutionBacklogItem] = []
        if isinstance(payload, list):
            for raw in payload:
                if isinstance(raw, dict):
                    try:
                        items.append(EvolutionBacklogItem.from_dict(raw))
                    except Exception:
                        continue
        return items

    def _save_backlog(self, items: list[EvolutionBacklogItem]) -> None:
        items.sort(key=lambda item: (-int(item.priority), item.created_at))
        _json_dump(BACKLOG_FILE, [item.to_dict() for item in items])

    def _append_history(self, record: EvolutionCycleRecord) -> None:
        with HISTORY_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")

    def _count_backlog(self, items: list[EvolutionBacklogItem]) -> dict[str, int]:
        return {
            "pending": sum(1 for item in items if item.status == "pending"),
            "queued": sum(1 for item in items if item.status == "queued"),
            "running": sum(1 for item in items if item.status == "running"),
            "completed": sum(1 for item in items if item.status in {"done", "failed", "skipped"}),
        }

    def _sync_backlog_with_queue(self, items: list[EvolutionBacklogItem]) -> None:
        try:
            queue_items = autonomy.list_queue()
        except Exception:
            queue_items = []

        queue_map = {item.objective_id: item for item in queue_items}
        for item in items:
            queued = queue_map.get(item.objective_id)
            if not queued:
                continue
            item.queue_id = queued.queue_id
            item.run_id = queued.run_id
            item.updated_at = _now()
            item.attempts = max(item.attempts, 1)
            item.result_summary = queued.summary or item.result_summary
            item.last_error = queued.error or item.last_error
            if queued.status in {"queued", "running"}:
                item.status = queued.status
                item.auto_enqueued = True
            elif queued.status == "done":
                item.status = "done"
                item.verify_success = bool(queued.result_success)
                item.auto_enqueued = True
            elif queued.status in {"failed", "cancelled", "cancel_requested"}:
                item.status = "failed"
                item.verify_success = False if queued.result_success is None else queued.result_success
                item.auto_enqueued = True

    def _scan_repository(self) -> dict[str, Any]:
        todo_hits: list[dict[str, Any]] = []
        conflict_hits: list[str] = []
        verify_duplicates: list[dict[str, Any]] = []
        identifier_counts: dict[str, int] = {}
        signals: set[str] = set()

        for path in ROOT.rglob("*"):
            if any(part in IGNORED_DIRS for part in path.parts):
                continue
            if not path.is_file() or path.suffix.lower() not in TEXT_EXTS:
                continue
            try:
                if path.stat().st_size > 700_000:
                    continue
            except Exception:
                continue

            text = _safe_read_text(path)
            if not text:
                continue

            if MERGE_RE.search(text):
                conflict_hits.append(str(path.relative_to(ROOT)).replace("\\", "/"))
                signals.add("merge_conflict")

            for match in TODO_RE.finditer(text):
                todo_hits.append(
                    {
                        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                        "marker": match.group(1).upper(),
                        "line": text[: match.start()].count("\n") + 1,
                    }
                )
                signals.add("todo")
                if len(todo_hits) >= 20:
                    break

            if path.name in {"api.ts", "ChatPanel.tsx", "OperationsHub.tsx", "App.tsx"}:
                count = text.count("runVerify") + text.count("verifyRoute")
                if count > 1:
                    verify_duplicates.append(
                        {
                            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                            "count": count,
                        }
                    )
                    signals.add("duplicate_verify")

            for ident in re.findall(r"\b[A-Za-z_][A-Za-z0-9_]{2,}\b", text):
                identifier_counts[ident] = identifier_counts.get(ident, 0) + 1

        frequent = sorted(
            [
                {"identifier": ident, "count": count}
                for ident, count in identifier_counts.items()
                if count >= 18 and len(ident) >= 5
            ],
            key=lambda item: (-item["count"], item["identifier"]),
        )[:15]

        return {
            "todo_hits": todo_hits,
            "conflict_hits": conflict_hits,
            "verify_duplicates": verify_duplicates,
            "frequent_identifiers": frequent,
            "signals": sorted(signals),
            "file_count": sum(1 for path in ROOT.rglob("*") if path.is_file() and not any(part in IGNORED_DIRS for part in path.parts)),
        }

    def _candidate(self, title: str, objective: str, description: str, category: str, priority: int, reasons: list[str], tags: list[str], test_command: str = "python verify.py", max_iterations: int = 3, max_files: int = 15) -> EvolutionBacklogItem:
        objective = _clean(objective)
        return EvolutionBacklogItem(
            backlog_id=uuid.uuid4().hex,
            objective_id=_stable_id(objective),
            title=title,
            objective=objective,
            description=description,
            category=category,
            priority=max(1, min(priority, 100)),
            reasons=reasons,
            tags=tags,
            test_command=test_command,
            max_iterations=max(1, min(max_iterations, 5)),
            max_files=max(1, min(max_files, 20)),
        )

    def _dedupe(self, candidates: list[EvolutionBacklogItem]) -> list[EvolutionBacklogItem]:
        out: dict[str, EvolutionBacklogItem] = {}
        for item in candidates:
            existing = out.get(item.objective_id)
            if existing is None or item.priority > existing.priority:
                if existing is not None:
                    item.backlog_id = existing.backlog_id
                    item.status = existing.status
                    item.queue_id = existing.queue_id
                    item.run_id = existing.run_id
                    item.attempts = existing.attempts
                    item.result_summary = existing.result_summary
                    item.last_error = existing.last_error
                    item.verify_success = existing.verify_success
                    item.auto_enqueued = existing.auto_enqueued
                    item.created_at = existing.created_at
                out[item.objective_id] = item
                continue
            existing.reasons = sorted(set(existing.reasons + item.reasons))
            existing.tags = sorted(set(existing.tags + item.tags))
            existing.priority = max(existing.priority, item.priority)
            out[item.objective_id] = existing
        return sorted(out.values(), key=lambda item: (-item.priority, item.created_at))

    def _generate_candidates(self, scan: dict[str, Any], intelligence_state: dict[str, Any], composio_state: dict[str, Any], autonomy_state: dict[str, Any]) -> list[EvolutionBacklogItem]:
        memory_total = int((intelligence_state.get("memory") or {}).get("total") or 0)
        candidates: list[EvolutionBacklogItem] = []

        if not composio_state.get("configured", False):
            candidates.append(self._candidate(
                title="Configurar integração Composio",
                objective="Implementar a configuração completa do Composio no ClawAI.",
                description="Ativar descoberta dinâmica de ferramentas e execução por provider.",
                category="integration",
                priority=94,
                reasons=["credenciais Composio não detectadas"],
                tags=["composio", "integration"],
            ))

        if len(composio_state.get("sample_tools", [])) < 5:
            candidates.append(self._candidate(
                title="Expandir descoberta de ferramentas",
                objective="Ampliar a descoberta automática de ferramentas e actions via Composio.",
                description="Registrar mais ferramentas no ToolRegistry e refletir conexões ativas.",
                category="integration",
                priority=88,
                reasons=["descoberta automática ainda está pequena"],
                tags=["composio", "tools", "registry"],
            ))

        if not os.getenv("MCP_SERVERS", "").strip():
            candidates.append(self._candidate(
                title="Adicionar suporte MCP",
                objective="Adicionar uma camada MCP para o ClawAI consumir ferramentas externas de forma padronizada.",
                description="Permitir servidores MCP como fonte adicional de capacidades.",
                category="integration",
                priority=82,
                reasons=["nenhum servidor MCP configurado"],
                tags=["mcp", "broker"],
            ))

        if memory_total < 50:
            candidates.append(self._candidate(
                title="Fortalecer memória semântica",
                objective="Fortalecer a memória semântica do ClawAI com recuperação mais rica e reutilização de soluções.",
                description="Adicionar melhor indexação e consulta por similaridade para decisões passadas.",
                category="memory",
                priority=78,
                reasons=[f"apenas {memory_total} memórias registradas"],
                tags=["memory", "learning", "rag"],
            ))

        if scan["conflict_hits"]:
            path = scan["conflict_hits"][0]
            candidates.append(self._candidate(
                title="Resolver conflitos de merge remanescentes",
                objective="Eliminar conflitos de merge e artefatos conflitantes que ainda existam no código.",
                description=f"Marcador de conflito encontrado em {path}.",
                category="stability",
                priority=100,
                reasons=[f"conflito detectado em {path}"],
                tags=["merge", "conflict"],
            ))

        if scan["todo_hits"]:
            first = scan["todo_hits"][0]
            candidates.append(self._candidate(
                title="Limpar TODOs e FIXMEs críticos",
                objective="Remover TODOs e FIXMEs críticos do código e transformá-los em melhorias implementadas.",
                description=f"Primeiro marcador em {first['path']} linha {first['line']}.",
                category="cleanup",
                priority=76,
                reasons=[f"{first['marker']} em {first['path']}:{first['line']}"],
                tags=["todo", "cleanup"],
            ))

        if scan["verify_duplicates"]:
            dup = scan["verify_duplicates"][0]
            candidates.append(self._candidate(
                title="Eliminar duplicação de helpers de verify",
                objective="Eliminar a duplicação de helpers e tipos relacionados a verify no frontend e backend.",
                description=f"Duplicação detectada em {dup['path']}.",
                category="refactor",
                priority=90,
                reasons=[f"duplicação em {dup['path']}"],
                tags=["verify", "frontend", "refactor"],
            ))

        if scan["frequent_identifiers"]:
            frequent = scan["frequent_identifiers"][0]
            if frequent["count"] > 40:
                candidates.append(self._candidate(
                    title="Reduzir acoplamento de identificadores muito frequentes",
                    objective="Reduzir acoplamento e melhorar modularização dos pontos de maior repetição no projeto.",
                    description=f"{frequent['identifier']} aparece {frequent['count']} vezes.",
                    category="refactor",
                    priority=62,
                    reasons=[f"identificador frequente: {frequent['identifier']}"],
                    tags=["architecture", "refactor"],
                ))

        if not autonomy_state.get("queue"):
            candidates.append(self._candidate(
                title="Criar cobertura de testes de integração para a camada cognitiva",
                objective="Criar e fortalecer testes de integração para o broker de inteligência, Composio e Evolution Engine.",
                description="Cobrir o ciclo de análise, backlog e enfileiramento automático.",
                category="testing",
                priority=84,
                reasons=["fila de autonomia vazia"],
                tags=["tests", "integration"],
            ))

        try:
            meta = cognition_broker.analyze(
                prompt="Analise o estado do ClawAI e sugira a próxima melhoria técnica mais importante.",
                objective="Evolution Engine",
            )
            if meta.decision.recommended_tool in {"filesystem", "git", "workflow", "memory", "planning", "search", "verify"}:
                candidates.append(self._candidate(
                    title=f"Aprimorar estratégia de {meta.decision.recommended_tool}",
                    objective=f"Aprimorar a estratégia de {meta.decision.recommended_tool} do ClawAI com base na análise cognitiva atual.",
                    description=meta.reasoning,
                    category="cognition",
                    priority=73,
                    reasons=[meta.reasoning],
                    tags=["cognition", meta.decision.recommended_tool],
                ))
        except Exception:
            pass

        if not candidates:
            candidates.append(self._candidate(
                title="Melhorar observabilidade do ciclo evolutivo",
                objective="Melhorar observabilidade do ciclo evolutivo com métricas, logs e eventos mais ricos.",
                description="Adicionar indicadores de execução, backlog e memória.",
                category="observability",
                priority=55,
                reasons=["nenhuma melhoria crítica detectada"],
                tags=["observability", "metrics"],
            ))

        return self._dedupe(candidates)

    def analyze_project(self) -> EvolutionAnalysis:
        intelligence_state = cognition_broker.state()
        composio_state = composio_service.summary()
        autonomy_state = autonomy.get_state()
        scan = self._scan_repository()
        candidates = self._generate_candidates(scan, intelligence_state, composio_state, autonomy_state)
        return EvolutionAnalysis(
            objective="Analisar o estado do ClawAI e propor a próxima melhoria para aumentar autonomia, integração e estabilidade.",
            summary=f"{len(candidates)} melhorias candidatas identificadas; {len(scan['todo_hits'])} TODO/FIXME; {len(scan['conflict_hits'])} conflitos; {len(scan['verify_duplicates'])} sinais de duplicação.",
            timestamp=_now(),
            project_health={
                "files_scanned": scan["file_count"],
                "todo_hits": len(scan["todo_hits"]),
                "merge_conflicts": len(scan["conflict_hits"]),
                "duplicate_hits": len(scan["verify_duplicates"]),
                "memory_total": int((intelligence_state.get("memory") or {}).get("total") or 0),
                "composio_tools": len(composio_state.get("sample_tools", [])),
                "queue_size": len(autonomy_state.get("queue", [])),
                "active_queue_size": sum(1 for item in autonomy_state.get("queue", []) if item.get("status") in {"queued", "running"}),
            },
            signals=scan["signals"],
            candidates=candidates,
            intelligence={"classification": cognition_broker.analyze("Analise o ClawAI", objective="Evolution Engine").classification},
            composio=composio_state,
            autonomy={"plans": len(autonomy_state.get("plans", [])), "queue": len(autonomy_state.get("queue", [])), "memory": len(autonomy_state.get("recent_memory", []))},
        )

    def _record_learning(self, analysis: EvolutionAnalysis, backlog: list[EvolutionBacklogItem], queued_item: EvolutionBacklogItem | None) -> None:
        try:
            intelligence_orchestrator.learn_from_execution(
                objective="Evolution Engine",
                prompt=analysis.objective,
                summary=f"{analysis.summary}{'; enfileirado: ' + queued_item.title if queued_item else ''}",
                tool=(queued_item.category if queued_item else (backlog[0].category if backlog else "analysis")),
                outcome="success" if queued_item else "analysis",
                artifacts=[item.title for item in backlog[:8]],
                tags=["evolution", "autonomy", "backlog"],
                metadata={
                    "signals": analysis.signals,
                    "project_health": analysis.project_health,
                    "queued_item": queued_item.to_dict() if queued_item else None,
                },
            )
        except Exception:
            pass

    def _update_state(self, backlog: list[EvolutionBacklogItem], analysis: EvolutionAnalysis | None = None, queued_item: EvolutionBacklogItem | None = None) -> None:
        counts = self._count_backlog(backlog)
        with self._lock:
            self._state.backlog_size = len(backlog)
            self._state.pending_items = counts["pending"]
            self._state.queued_items = counts["queued"]
            self._state.running_items = counts["running"]
            self._state.completed_items = counts["completed"]
            try:
                self._state.active_queue_size = autonomy.queue_size()
            except Exception:
                self._state.active_queue_size = counts["queued"] + counts["running"]
            if analysis:
                self._state.last_summary = analysis.summary
            if queued_item:
                self._state.last_queued_title = queued_item.title
                self._state.last_queued_objective_id = queued_item.objective_id
            self._state.next_cycle_at = datetime.fromtimestamp(time.time() + self.interval_seconds, tz=timezone.utc).isoformat()
            self._save_state(self._state)

    def _queue_next(self, backlog: list[EvolutionBacklogItem]) -> EvolutionBacklogItem | None:
        pending = sorted([item for item in backlog if item.status == "pending"], key=lambda item: (-item.priority, item.created_at))
        if not pending:
            return None
        active_queue = 0
        try:
            active_queue = autonomy.queue_size()
        except Exception:
            active_queue = sum(1 for item in backlog if item.status in {"queued", "running"})
        if active_queue > 0:
            return None
        item = pending[0]
        queued = autonomy.enqueue(
            objective=item.objective,
            test_command=item.test_command,
            max_iterations=item.max_iterations,
            max_files=item.max_files,
        )
        item.status = "queued"
        item.queue_id = queued.queue_id
        item.run_id = queued.run_id
        item.auto_enqueued = True
        item.attempts += 1
        item.updated_at = _now()
        return item

    def _record_cycle(self, record: EvolutionCycleRecord) -> None:
        with HISTORY_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")

    def run_once(self) -> EvolutionCycleRecord:
        record = EvolutionCycleRecord(cycle_id=uuid.uuid4().hex[:12], started_at=_now())
        with self._lock:
            self._state.running = True
            self._state.last_cycle_id = record.cycle_id
            self._state.last_cycle_at = record.started_at
            self._save_state(self._state)

        try:
            analysis = self.analyze_project()
            backlog = self._load_backlog()
            if backlog:
                by_id = {item.objective_id: item for item in backlog}
                for candidate in analysis.candidates:
                    previous = by_id.get(candidate.objective_id)
                    if previous is None:
                        by_id[candidate.objective_id] = candidate
                    else:
                        candidate.backlog_id = previous.backlog_id
                        candidate.status = previous.status
                        candidate.queue_id = previous.queue_id
                        candidate.run_id = previous.run_id
                        candidate.attempts = previous.attempts
                        candidate.result_summary = previous.result_summary
                        candidate.verify_success = previous.verify_success
                        candidate.auto_enqueued = previous.auto_enqueued
                        candidate.created_at = previous.created_at
                        by_id[candidate.objective_id] = candidate
                backlog = list(by_id.values())
            else:
                backlog = analysis.candidates

            self._sync_backlog_with_queue(backlog)
            backlog = self._prioritize(backlog)
            self._save_backlog(backlog)
            queued_item = self._queue_next(backlog)
            if queued_item:
                self._save_backlog(backlog)

            record.backlog_created = len(analysis.candidates)
            counts = self._count_backlog(backlog)
            record.backlog_queued = counts["queued"]
            record.backlog_completed = counts["completed"]
            record.queued_title = queued_item.title if queued_item else ""
            record.queued_objective_id = queued_item.objective_id if queued_item else ""
            record.queued_queue_id = queued_item.queue_id if queued_item else ""
            record.queued_run_id = queued_item.run_id if queued_item else ""
            record.active_queue_size = counts["queued"] + counts["running"]
            record.signals = analysis.signals
            record.analysis_summary = analysis.summary
            record.meta = {"project_health": analysis.project_health, "intelligence": analysis.intelligence, "composio": analysis.composio, "autonomy": analysis.autonomy}
            record.status = "ok"

            self._update_state(backlog, analysis=analysis, queued_item=queued_item)
            self._record_learning(analysis, backlog, queued_item)
            return record
        except Exception as exc:
            record.status = "failed"
            record.errors.append(str(exc))
            self._record_cycle_failure(str(exc), record)
            raise
        finally:
            record.finished_at = _now()
            self._record_cycle(record)
            with self._lock:
                self._state.running = False
                self._state.cycles_run += 1
                self._state.last_cycle_at = record.finished_at
                self._save_state(self._state)

    def _prioritize(self, backlog: list[EvolutionBacklogItem]) -> list[EvolutionBacklogItem]:
        for item in backlog:
            bonus = 0
            if item.category in {"integration", "stability"}:
                bonus += 8
            if item.category in {"refactor", "testing"}:
                bonus += 5
            if item.category == "memory":
                bonus += 4
            item.priority = min(100, item.priority + bonus)
        return sorted(backlog, key=lambda item: (-item.priority, item.created_at))

    def _record_cycle_failure(self, error: str, record: EvolutionCycleRecord) -> None:
        try:
            self._state.last_error = error
            self._save_state(self._state)
            self._record_cycle(record)
        except Exception:
            pass

    def start(self) -> EvolutionState:
        with self._worker_lock:
            self._state.enabled = True
            self._save_state(self._state)
            if self._worker and self._worker.is_alive():
                return self.get_state()
            self._stop_event.clear()
            self._worker = threading.Thread(target=self._worker_loop, daemon=True)
            self._worker.start()
        return self.get_state()

    def stop(self) -> EvolutionState:
        with self._worker_lock:
            self._state.enabled = False
            self._save_state(self._state)
            self._stop_event.set()
        return self.get_state()

    def _worker_loop(self) -> None:
        while not self._stop_event.is_set() and self._state.enabled:
            try:
                self.run_once()
            except Exception:
                pass
            if self._stop_event.wait(self.interval_seconds):
                break

    def list_backlog(self) -> list[EvolutionBacklogItem]:
        backlog = self._load_backlog()
        self._sync_backlog_with_queue(backlog)
        return self._prioritize(backlog)

    def list_history(self, limit: int = 20) -> list[dict[str, Any]]:
        payload = _json_load(HISTORY_FILE, [])
        if not isinstance(payload, list):
            lines: list[dict[str, Any]] = []
            if HISTORY_FILE.exists():
                for line in HISTORY_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
                    if not line.strip():
                        continue
                    try:
                        item = json.loads(line)
                        if isinstance(item, dict):
                            lines.append(item)
                    except Exception:
                        continue
            payload = lines
        payload.sort(key=lambda item: str(item.get("started_at", "")), reverse=True)
        return payload[: max(0, limit)]

    def get_state(self) -> EvolutionState:
        backlog = self.list_backlog()
        counts = self._count_backlog(backlog)
        with self._lock:
            self._state.backlog_size = len(backlog)
            self._state.pending_items = counts["pending"]
            self._state.queued_items = counts["queued"]
            self._state.running_items = counts["running"]
            self._state.completed_items = counts["completed"]
            try:
                self._state.active_queue_size = autonomy.queue_size()
            except Exception:
                self._state.active_queue_size = counts["queued"] + counts["running"]
            if self._state.enabled and not self._state.next_cycle_at:
                self._state.next_cycle_at = datetime.fromtimestamp(time.time() + self.interval_seconds, tz=timezone.utc).isoformat()
            return EvolutionState(**asdict(self._state))

    def initialize(self) -> EvolutionState:
        self.rebuild_backlog()
        return self.get_state()

    def summary(self) -> dict[str, Any]:
        return {
            "state": asdict(self.get_state()),
            "backlog": [item.to_dict() for item in self.list_backlog()],
            "history": self.list_history(limit=20),
        }

    def backlog_overview(self) -> dict[str, Any]:
        backlog = self.list_backlog()
        top = backlog[0] if backlog else None
        return {
            "counts": self._count_backlog(backlog),
            "top_item": top.to_dict() if top else None,
            "items": [item.to_dict() for item in backlog],
        }

    def rebuild_backlog(self) -> list[EvolutionBacklogItem]:
        analysis = self.analyze_project()
        backlog = analysis.candidates
        self._sync_backlog_with_queue(backlog)
        backlog = self._prioritize(backlog)
        self._save_backlog(backlog)
        self._update_state(backlog, analysis=analysis)
        self._record_learning(analysis, backlog, None)
        return backlog


evolution_engine = EvolutionEngine()
