from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from clawai.bridge import BridgeParticipantConfig, BridgeConsultResult, BridgeToolDecision, bridge_service

router = APIRouter()

COGNITION_ROOT = Path(__file__).resolve().parents[2] / ".clawai" / "cognition"
WORKSPACES_ROOT = COGNITION_ROOT / "workspaces"
LEARNING_FILE = COGNITION_ROOT / "learning.jsonl"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dirs() -> None:
    WORKSPACES_ROOT.mkdir(parents=True, exist_ok=True)
    COGNITION_ROOT.mkdir(parents=True, exist_ok=True)


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


def _tokenize(text: str) -> set[str]:
    return {token.lower() for token in text.replace("/", " ").replace("-", " ").split() if len(token) >= 3}


def _objective_id(text: str) -> str:
    return hashlib.sha1(text.strip().lower().encode("utf-8")).hexdigest()[:12]


@dataclass(slots=True, frozen=True)
class CognitionTaskClassification:
    category: str
    recommended_tool: str
    confidence: float
    rationale: str
    tags: list[str] = field(default_factory=list)
    parallel_roles: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class CognitionReasoningNode:
    node_id: str
    label: str
    kind: str
    score: float = 0.0
    details: str = ""
    children: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class CognitionWorkspace:
    workspace_id: str
    objective_id: str
    objective: str
    prompt: str
    created_at: str
    updated_at: str
    classification: CognitionTaskClassification
    decision: BridgeToolDecision
    debate_summary: str
    reasoning_graph: list[CognitionReasoningNode] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class CognitionLearningEntry:
    entry_id: str
    objective_id: str
    objective: str
    prompt: str
    timestamp: str
    category: str
    recommended_tool: str
    winner_role: str
    confidence: float
    summary: str
    notes: str = ""
    provider: str = ""
    judge_provider: str = ""


@dataclass(slots=True, frozen=True)
class CognitionSupervisionResult:
    objective: str
    prompt: str
    objective_id: str
    workspace_id: str
    classification: CognitionTaskClassification
    decision: BridgeToolDecision
    debate: BridgeConsultResult
    reasoning_graph: list[CognitionReasoningNode]
    learning_entry: CognitionLearningEntry
    workspace: CognitionWorkspace


class BridgeParticipantRequest(BaseModel):
    role: str = Field(default="planner")
    provider: str | None = None
    model: str = ""


class BridgeConsultRequest(BaseModel):
    prompt: str
    system_prompt: str | None = None
    participants: list[BridgeParticipantRequest] = Field(default_factory=list)
    judge_provider: str | None = None


class CognitionSuperviseRequest(BaseModel):
    prompt: str
    objective: str | None = None
    system_prompt: str | None = None
    participants: list[BridgeParticipantRequest] = Field(default_factory=list)
    judge_provider: str | None = None


class CognitionClassifyRequest(BaseModel):
    prompt: str


class CognitionLearningRequest(BaseModel):
    objective: str
    prompt: str
    category: str
    recommended_tool: str
    winner_role: str
    confidence: float = 0.0
    summary: str
    notes: str = ""
    provider: str = ""
    judge_provider: str = ""


class CognitionSupervisor:
    def classify(self, prompt: str) -> CognitionTaskClassification:
        text = prompt.lower()
        rules: list[tuple[str, str, tuple[str, ...], str]] = [
            ("implement", "implement", ("implementar", "feature", "funcionalidade", "codigo", "code", "refator", "refactor"), "O pedido parece exigir escrita de código."),
            ("verify", "verify", ("teste", "test", "verify", "falha", "bug", "erro", "valida"), "O pedido parece exigir validação ou diagnóstico."),
            ("git", "git", ("git", "commit", "merge", "branch", "rollback", "revert", "push", "pull"), "O pedido parece exigir operação de versionamento."),
            ("planning", "planning", ("plano", "planej", "roadmap", "prioridade", "subtarefa", "queue"), "O pedido parece exigir planejamento ou decomposição."),
            ("memory", "memory", ("memoria", "memória", "remember", "historico", "histórico", "reutil", "learn"), "O pedido parece exigir memória de engenharia."),
            ("filesystem", "filesystem", ("arquivo", "file", "path", "diretorio", "directory", "pasta"), "O pedido parece exigir arquivos ou diretórios."),
            ("search", "search", ("buscar", "search", "procurar", "find", "localizar", "scan"), "O pedido parece exigir busca de informação."),
            ("queue", "queue", ("fila", "queue", "sequencial", "pipeline"), "O pedido parece exigir processamento em fila."),
        ]
        for category, tool, keywords, reason in rules:
            if any(keyword in text for keyword in keywords):
                return CognitionTaskClassification(
                    category=category,
                    recommended_tool=tool,
                    confidence=0.78,
                    rationale=reason,
                    tags=sorted({category, tool}),
                    parallel_roles=["planner", "coder", "reviewer"],
                )
        return CognitionTaskClassification(
            category="chat",
            recommended_tool="chat",
            confidence=0.55,
            rationale="O pedido parece melhor atendido por conversa geral e síntese.",
            tags=["chat"],
            parallel_roles=["planner", "reviewer"],
        )

    def _workspace(self, objective: str, prompt: str, classification: CognitionTaskClassification, decision: BridgeToolDecision, debate_summary: str, reasoning_graph: list[CognitionReasoningNode]) -> CognitionWorkspace:
        _ensure_dirs()
        workspace_id = f"ws-{_objective_id(objective or prompt)}-{uuid.uuid4().hex[:8]}"
        workspace = CognitionWorkspace(
            workspace_id=workspace_id,
            objective_id=_objective_id(objective or prompt),
            objective=objective,
            prompt=prompt,
            created_at=_now(),
            updated_at=_now(),
            classification=classification,
            decision=decision,
            debate_summary=debate_summary,
            reasoning_graph=reasoning_graph,
        )
        self._save_workspace(workspace)
        return workspace

    def _save_workspace(self, workspace: CognitionWorkspace) -> None:
        _ensure_dirs()
        payload = asdict(workspace)
        _json_dump(WORKSPACES_ROOT / f"{workspace.workspace_id}.json", payload)
        index = _json_load(WORKSPACES_ROOT / "_index.json", {})
        index[workspace.workspace_id] = {
            "workspace_id": workspace.workspace_id,
            "objective_id": workspace.objective_id,
            "objective": workspace.objective,
            "updated_at": workspace.updated_at,
            "category": workspace.classification.category,
            "recommended_tool": workspace.classification.recommended_tool,
            "winner_role": workspace.decision.winner_role,
        }
        _json_dump(WORKSPACES_ROOT / "_index.json", index)

    def get_workspace(self, workspace_id: str) -> dict[str, Any] | None:
        path = WORKSPACES_ROOT / f"{workspace_id}.json"
        if not path.exists():
            return None
        return _json_load(path, None)

    def list_workspaces(self) -> list[dict[str, Any]]:
        index = _json_load(WORKSPACES_ROOT / "_index.json", {})
        if isinstance(index, dict):
            return [index[key] for key in sorted(index.keys(), key=lambda value: str(index[value].get("updated_at", "")), reverse=True)]
        return []

    def record_learning(self, entry: CognitionLearningEntry) -> None:
        _ensure_dirs()
        with LEARNING_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")

    def list_learning(self, limit: int = 20) -> list[dict[str, Any]]:
        if not LEARNING_FILE.exists():
            return []
        entries: list[dict[str, Any]] = []
        for line in LEARNING_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                if isinstance(payload, dict):
                    entries.append(payload)
            except Exception:
                continue
        entries.sort(key=lambda item: str(item.get("timestamp", "")), reverse=True)
        return entries[: max(0, limit)]

    def supervise(
        self,
        prompt: str,
        objective: str | None = None,
        system_prompt: str | None = None,
        participants: list[BridgeParticipantConfig] | None = None,
        judge_provider: str | None = None,
    ) -> CognitionSupervisionResult:
        prompt = prompt.strip()
        if not prompt:
            raise ValueError("prompt is required")

        objective_text = (objective or prompt).strip()
        classification = self.classify(prompt)
        debate = bridge_service.consult(
            prompt=prompt,
            system_prompt=system_prompt,
            participants=participants,
            judge_provider=judge_provider,
        )
        decision = debate.decision
        reasoning_graph = self._build_graph(prompt, objective_text, classification, debate)
        workspace = self._workspace(
            objective=objective_text,
            prompt=prompt,
            classification=classification,
            decision=decision,
            debate_summary=debate.final_answer,
            reasoning_graph=reasoning_graph,
        )
        learning_entry = CognitionLearningEntry(
            entry_id=uuid.uuid4().hex,
            objective_id=workspace.objective_id,
            objective=objective_text,
            prompt=prompt,
            timestamp=_now(),
            category=classification.category,
            recommended_tool=decision.recommended_tool,
            winner_role=decision.winner_role,
            confidence=decision.confidence,
            summary=debate.final_answer,
            notes=classification.rationale,
            provider=classification.recommended_tool,
            judge_provider=debate.judge_provider,
        )
        self.record_learning(learning_entry)
        return CognitionSupervisionResult(
            objective=objective_text,
            prompt=prompt,
            objective_id=workspace.objective_id,
            workspace_id=workspace.workspace_id,
            classification=classification,
            decision=decision,
            debate=debate,
            reasoning_graph=reasoning_graph,
            learning_entry=learning_entry,
            workspace=workspace,
        )

    def _build_graph(
        self,
        prompt: str,
        objective: str,
        classification: CognitionTaskClassification,
        debate: BridgeConsultResult,
    ) -> list[CognitionReasoningNode]:
        root_id = "root"
        nodes = [
            CognitionReasoningNode(
                node_id=root_id,
                label=objective,
                kind="objective",
                score=1.0,
                details=prompt,
                children=["classification", "debate", "decision"],
            ),
            CognitionReasoningNode(
                node_id="classification",
                label=classification.category,
                kind="classifier",
                score=classification.confidence,
                details=f"tool={classification.recommended_tool}; rationale={classification.rationale}",
                children=["debate"],
            ),
            CognitionReasoningNode(
                node_id="debate",
                label="Debate entre modelos",
                kind="debate",
                score=debate.decision.confidence,
                details=f"winner={debate.winner_role}; tool={debate.decision.recommended_tool}",
                children=["decision"],
            ),
            CognitionReasoningNode(
                node_id="decision",
                label=debate.decision.recommended_tool,
                kind="decision",
                score=debate.decision.confidence,
                details=debate.decision.reason,
                children=[],
            ),
        ]
        for participant in debate.participants:
            nodes.append(
                CognitionReasoningNode(
                    node_id=f"participant-{participant.role}",
                    label=f"{participant.role}:{participant.provider}",
                    kind="participant",
                    score=1.0 if participant.content.strip() else 0.0,
                    details=participant.content[:500] if participant.content else participant.error,
                    children=["debate"],
                )
            )
        return nodes


cognition_supervisor = CognitionSupervisor()


@router.get("/bridge/providers")
def bridge_providers():
    return {
        "providers": list(bridge_service.available_providers()),
        "tools": list(bridge_service.list_tools()),
        "default_roles": ["planner", "coder", "reviewer"],
    }


@router.post("/bridge/consult")
def bridge_consult(request: BridgeConsultRequest):
    try:
        participants = [
            BridgeParticipantConfig(
                role=item.role,
                provider=item.provider or bridge_service.default_provider_for_role(item.role),
                model=item.model,
            )
            for item in request.participants
        ]
        result = bridge_service.consult(
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            participants=participants or None,
            judge_provider=request.judge_provider,
        )
        return asdict(result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/bridge/recommend-tool")
def bridge_recommend_tool(request: BridgeConsultRequest):
    try:
        decision = bridge_service.recommend_tool(
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            judge_provider=request.judge_provider,
        )
        return asdict(decision)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/cognition/classify")
def cognition_classify(request: CognitionClassifyRequest):
    try:
        return asdict(cognition_supervisor.classify(request.prompt))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/cognition/supervise")
def cognition_supervise(request: CognitionSuperviseRequest):
    try:
        participants = [
            BridgeParticipantConfig(
                role=item.role,
                provider=item.provider or bridge_service.default_provider_for_role(item.role),
                model=item.model,
            )
            for item in request.participants
        ]
        result = cognition_supervisor.supervise(
            prompt=request.prompt,
            objective=request.objective,
            system_prompt=request.system_prompt,
            participants=participants or None,
            judge_provider=request.judge_provider,
        )
        return asdict(result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/cognition/workspaces")
def cognition_workspaces():
    return cognition_supervisor.list_workspaces()


@router.get("/cognition/workspaces/{workspace_id}")
def cognition_workspace(workspace_id: str):
    workspace = cognition_supervisor.get_workspace(workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


@router.get("/cognition/learning")
def cognition_learning(limit: int = 20):
    return cognition_supervisor.list_learning(limit=limit)
