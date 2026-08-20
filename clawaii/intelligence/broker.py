from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from clawai.bridge import bridge_service
from clawai.core.config.settings import Settings
from clawai.integrations.composio import composio_service
from clawai.integrations.composio.models import ToolBrokerDecision, ToolDescriptor

from .memory import SemanticMemoryEntry, semantic_memory

NATIVE_TOOL_DESCRIPTORS: tuple[ToolDescriptor, ...] = (
    ToolDescriptor(name="chat", provider="native", category="conversation", description="Model chat and synthesis", connected=True, actions=["ask"]),
    ToolDescriptor(name="verify", provider="native", category="testing", description="Project verification pipeline", connected=True, actions=["run"]),
    ToolDescriptor(name="git", provider="native", category="devops", description="Git workspace automation", connected=True, actions=["status", "branch", "commit", "merge_ff_only"]),
    ToolDescriptor(name="filesystem", provider="native", category="filesystem", description="Repository file access", connected=True, actions=["read", "tree", "write"]),
    ToolDescriptor(name="search", provider="native", category="search", description="Repository search and retrieval", connected=True, actions=["query", "files"]),
    ToolDescriptor(name="memory", provider="native", category="memory", description="Semantic memory store", connected=True, actions=["search", "remember", "stats"]),
    ToolDescriptor(name="planning", provider="native", category="planning", description="Planning and task decomposition", connected=True, actions=["analyze", "plan"]),
    ToolDescriptor(name="workflow", provider="native", category="orchestration", description="Queue and workflow management", connected=True, actions=["enqueue", "status", "next"]),
)


@dataclass(slots=True, frozen=True)
class IntelligenceAnalysis:
    prompt: str
    objective: str
    classification: dict[str, Any]
    decision: ToolBrokerDecision
    memory_hits: list[dict[str, Any]] = field(default_factory=list)
    discovered_tools: list[dict[str, Any]] = field(default_factory=list)
    parallel_agents: list[str] = field(default_factory=list)
    reasoning: str = ""
    model_strategy: dict[str, Any] = field(default_factory=dict)


class ToolBroker:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()

    def discover_tools(self, force_refresh: bool = False) -> list[ToolDescriptor]:
        composio_tools = [
            ToolDescriptor(
                name=tool.name,
                provider=tool.provider,
                category=tool.category,
                description=tool.description,
                connected=tool.connected,
                actions=tool.actions,
                source="composio",
                metadata=tool.metadata,
            )
            for tool in composio_service.discover_tools(force_refresh=force_refresh)
        ]
        discovered: dict[str, ToolDescriptor] = {tool.name: tool for tool in NATIVE_TOOL_DESCRIPTORS}
        for tool in composio_tools:
            discovered[tool.name] = tool
        return sorted(discovered.values(), key=lambda item: (item.provider, item.name))

    def search_memory(self, query: str, limit: int = 10) -> list[SemanticMemoryEntry]:
        return semantic_memory.search(query, limit=limit)

    def remember(self, payload: dict[str, Any]) -> SemanticMemoryEntry:
        return semantic_memory.remember(payload)

    def memory_stats(self) -> dict[str, Any]:
        return semantic_memory.stats()

    def recommend_tool(self, prompt: str, objective: str | None = None) -> ToolBrokerDecision:
        prompt = prompt.strip()
        objective_text = (objective or prompt).strip()
        memory_hits = self.search_memory(prompt, limit=5)
        decision = None
        try:
            decision = bridge_service.recommend_tool(prompt=prompt, system_prompt=objective_text or None)
        except Exception:
            decision = None

        heuristic_tool, heuristic_reason = self._heuristic_tool(prompt)
        chosen_tool = decision.recommended_tool if decision else heuristic_tool
        provider = self._tool_provider(chosen_tool)
        if provider == "unknown":
            provider = self._fallback_provider(chosen_tool)

        return ToolBrokerDecision(
            recommended_tool=chosen_tool,
            provider=provider,
            reason=(decision.reason if decision else heuristic_reason) + self._memory_suffix(memory_hits),
            confidence=decision.confidence if decision else self._heuristic_confidence(prompt),
            parallel_agents=self._parallel_agents(prompt, memory_hits),
            memory_hits=len(memory_hits),
            source="bridge" if decision else "heuristic",
        )

    def analyze(self, prompt: str, objective: str | None = None) -> IntelligenceAnalysis:
        objective_text = (objective or prompt).strip()
        classification = self._classify(prompt)
        memory_hits = self.search_memory(prompt, limit=5)
        decision = self.recommend_tool(prompt=prompt, objective=objective_text)
        return IntelligenceAnalysis(
            prompt=prompt,
            objective=objective_text,
            classification=classification,
            decision=decision,
            memory_hits=[entry.to_dict() for entry in memory_hits],
            discovered_tools=[asdict(tool) for tool in self.discover_tools()],
            parallel_agents=decision.parallel_agents,
            reasoning=self._reasoning_text(classification, decision, memory_hits),
            model_strategy=self._model_strategy(prompt, memory_hits, classification),
        )

    def state(self) -> dict[str, Any]:
        return {
            "tools": [asdict(tool) for tool in self.discover_tools()],
            "memory": self.memory_stats(),
            "providers": list(bridge_service.available_providers()),
            "bridge_tools": list(bridge_service.list_tools()),
        }

    def _classify(self, prompt: str) -> dict[str, Any]:
        text = prompt.lower()
        if any(token in text for token in ("implement", "feature", "refator", "code", "codigo")):
            return {"category": "implement", "recommended_tool": "filesystem", "confidence": 0.78, "rationale": "Mudança de código ou funcionalidade."}
        if any(token in text for token in ("git", "commit", "merge", "branch", "rollback")):
            return {"category": "git", "recommended_tool": "git", "confidence": 0.82, "rationale": "Operação de versionamento."}
        if any(token in text for token in ("teste", "test", "verify", "bug", "erro", "falha")):
            return {"category": "verify", "recommended_tool": "verify", "confidence": 0.8, "rationale": "Validação ou diagnóstico."}
        if any(token in text for token in ("memoria", "memory", "remember", "learn")):
            return {"category": "memory", "recommended_tool": "memory", "confidence": 0.76, "rationale": "Consulta ou gravação de memória."}
        if any(token in text for token in ("buscar", "search", "find", "localizar")):
            return {"category": "search", "recommended_tool": "search", "confidence": 0.74, "rationale": "Busca de informações."}
        if any(token in text for token in ("fila", "queue", "workflow", "pipeline")):
            return {"category": "workflow", "recommended_tool": "workflow", "confidence": 0.72, "rationale": "Orquestração ou fila."}
        return {"category": "chat", "recommended_tool": "chat", "confidence": 0.6, "rationale": "Conversa geral ou síntese."}

    def _heuristic_tool(self, prompt: str) -> tuple[str, str]:
        classification = self._classify(prompt)
        return str(classification["recommended_tool"]), str(classification["rationale"])

    def _heuristic_confidence(self, prompt: str) -> float:
        return float(self._classify(prompt)["confidence"])

    def _tool_provider(self, tool_name: str) -> str:
        for item in self.discover_tools():
            if item.name == tool_name:
                return item.provider
        return "unknown"

    def _fallback_provider(self, tool_name: str) -> str:
        if tool_name in {"filesystem", "git", "search", "memory", "planning", "workflow", "verify"}:
            return "native"
        return "composio"

    def _parallel_agents(self, prompt: str, memory_hits: list[SemanticMemoryEntry]) -> list[str]:
        tokens = len(prompt.split())
        if tokens < 12 and not memory_hits:
            return ["planner", "reviewer"]
        if tokens < 30:
            return ["planner", "coder", "reviewer"]
        return ["planner", "coder", "reviewer", "judge"]

    def _memory_suffix(self, memory_hits: list[SemanticMemoryEntry]) -> str:
        if not memory_hits:
            return ""
        return f"; {len(memory_hits)} memórias semelhantes recuperadas"

    def _model_strategy(self, prompt: str, memory_hits: list[SemanticMemoryEntry], classification: dict[str, Any]) -> dict[str, Any]:
        return {
            "parallel_agents": self._parallel_agents(prompt, memory_hits),
            "use_memory": bool(memory_hits),
            "tool": classification.get("recommended_tool", "chat"),
            "confidence": classification.get("confidence", 0.5),
            "provider_preference": ["ollama", "openai"],
        }

    def _reasoning_text(self, classification: dict[str, Any], decision: ToolBrokerDecision, memory_hits: list[SemanticMemoryEntry]) -> str:
        pieces = [
            f"Categoria: {classification.get('category', 'chat')}",
            f"Ferramenta: {decision.recommended_tool} ({decision.provider})",
            f"Confiança: {decision.confidence:.2f}",
        ]
        if memory_hits:
            pieces.append(f"Memórias: {len(memory_hits)} correspondências")
        return " | ".join(pieces)


class IntelligenceOrchestrator:
    def __init__(self, broker: ToolBroker | None = None) -> None:
        self.broker = broker or ToolBroker()

    def analyze(self, prompt: str, objective: str | None = None) -> IntelligenceAnalysis:
        return self.broker.analyze(prompt=prompt, objective=objective)

    def learn_from_execution(self, *, objective: str, prompt: str, summary: str, tool: str, outcome: str, artifacts: list[str] | None = None, tags: list[str] | None = None, metadata: dict[str, Any] | None = None) -> SemanticMemoryEntry:
        payload = {
            "objective": objective,
            "prompt": prompt,
            "summary": summary,
            "tool": tool,
            "outcome": outcome,
            "artifacts": artifacts or [],
            "tags": tags or [],
            "metadata": metadata or {},
            "source": "orchestrator",
        }
        return self.broker.remember(payload)

    def state(self) -> dict[str, Any]:
        return self.broker.state()


cognition_broker = ToolBroker()
intelligence_orchestrator = IntelligenceOrchestrator(cognition_broker)
