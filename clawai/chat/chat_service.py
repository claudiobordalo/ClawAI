from __future__ import annotations

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterator

from clawai.ai.router import AIRouter, ModelRole
from clawai.autonomy.agent_runtime import AgentRuntime
from clawai.documents.reader import documents
from clawai.memory.memory import memory
from clawai.cognition.pipeline import CognitionPipeline
from clawai.cognition.types import PipelineResult
from clawai.search.search_engine import SearchResult, SearchTimings, search
from clawai.workspaces.manager import workspace_manager

BASE_SYSTEM_PROMPT = "Você é o ClawAI, um agente de desenvolvimento dentro do próprio projeto. Responda como o ClawAI e seja direto."
SUPERVISOR_PROMPT = "Classifique a solicitação e responda em JSON puro com intent, primary_role, strategy, should_parallel, confidence e rationale."
PLANNER_PROMPT = "Produza um plano curto com objetivo, subtarefas numeradas, riscos e critério de pronto."
CODER_PROMPT = "Proponha a implementação concreta: arquivos prováveis, mudanças e próximos passos."
REVIEWER_PROMPT = "Revise a proposta, aponte lacunas, riscos e melhorias objetivas."
SYNTH_PROMPT = "Sintetize a melhor resposta final ao usuário em português, sem mencionar etapas internas."
CODER_HINTS = ("implemente", "corrija", "refatore", "ajuste", "arquivo", "frontend", "backend", "react", "tsx", "py", "python", "ui", "interface")
PLANNER_HINTS = ("planeje", "plano", "backlog", "roadmap", "arquitetura", "priorize", "organize")
REVIEWER_HINTS = ("revise", "review", "avaliar", "audite", "compare", "analisar")
VISION_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff", ".tif"}


@dataclass(slots=True, frozen=True)
class ChatTimings:
    # name: str
    # ms: float
    search: SearchTimings = field(default_factory=SearchTimings)
    model_ms: float = 0.0
    postprocess_ms: float = 0.0
    total_ms: float = 0.0

@dataclass(slots=True, frozen=True)
class ChatStageTiming:
    name: str
    ms: float

@dataclass(slots=True, frozen=True)
class ChatResponse:
    answer: str
    used_memory: bool
    used_knowledge: bool
    requires_web: bool
    provider: str
    model: str
    memory_saved: bool = False
    timings: ChatTimings = field(default_factory=ChatTimings)
    stage_timings: list[ChatStageTiming] = field(default_factory=list)

    @classmethod
    def from_pipeline(cls, result: PipelineResult) -> "ChatResponse":
        return cls(
            answer=result.answer,
            used_memory=result.used_memory,
            used_knowledge=result.used_knowledge,
            requires_web=result.requires_web,
            provider=result.provider,
            model=result.model,
            memory_saved=result.memory_saved,
            timings=ChatTimings(
                search=result.timings.search,
                model_ms=result.synthesis.duration_ms,
                postprocess_ms=result.timings.postprocess_ms,
                total_ms=result.timings.total_ms,
            ),
        )


class CognitionPipeline:
    def __init__(self, router: AIRouter, provider_name: str) -> None:
        self.router = router
        self.provider_name = provider_name

    def execute(self, prompt: str, file: str | None = None) -> ChatResponse:
        started = time.perf_counter()
        stages: list[ChatStageTiming] = []

        runtime = AgentRuntime(router=self.router, max_iterations=3)
        runtime_result = runtime.run(prompt, file=file)
        return ChatResponse(
            answer=runtime_result["answer"],
            used_memory=False,
            used_knowledge=False,
            requires_web=False,
            provider=self.provider_name,
            model=self.router.model_for(ModelRole.DEFAULT),
            timings=ChatTimings(
                search=SearchTimings(),
                model_ms=0.0,
                postprocess_ms=0.0,
                total_ms=(time.perf_counter() - started) * 1000,
            ),
            stage_timings=stages,
        )

        def mark(name: str, t0: float) -> None:
            stages.append(ChatStageTiming(name=name, ms=(time.perf_counter() - t0) * 1000))

        t0 = time.perf_counter()
        prepared = self._prepare_prompt(prompt, file)
        mark("prepare", t0)

        t0 = time.perf_counter()
        search_result = search.build_prompt(prepared)
        mark("search", t0)

        prompt_lower = prompt.lower().strip()
        engineering_request = any(
            word in prompt_lower
            for word in (
                "implemente",
                "corrija",
                "refatore",
                "analise",
                "backlog",
                "planeje",
                "arquitetura",
                "codigo",
                "arquivo",
                "python",
                "tsx",
                "react",
            )
        )

        simple_chat = file is None and not engineering_request

        if simple_chat:
            t0 = time.perf_counter()
            answer = self.router.ask(
                prompt=prepared,
                role=ModelRole.DEFAULT,
                system_prompt=BASE_SYSTEM_PROMPT,
            )
            mark("chat", t0)

            return ChatResponse(
                answer=answer,
                used_memory=False,
                used_knowledge=False,
                requires_web=False,
                provider=self.provider_name,
                model=self.router.model_for(ModelRole.DEFAULT),
                timings=ChatTimings(
                    search=search_result.timings,
                    model_ms=0.0,
                    postprocess_ms=0.0,
                    total_ms=(time.perf_counter() - started) * 1000,
                ),
                stage_timings=stages,
            )

        t0 = time.perf_counter()
        supervisor = self._supervise(prepared, file, search_result)
        mark("supervisor", t0)

        t0 = time.perf_counter()
        plan_text = self._plan(prepared, supervisor, search_result)
        mark("planner", t0)

        t0 = time.perf_counter()
        coder, reviewer = self._debate(prepared, supervisor, plan_text, search_result)
        mark("debate", t0)

        t0 = time.perf_counter()
        synthesis = self._synthesize(prepared, supervisor, plan_text, coder, reviewer, search_result)
        mark("synthesis", t0)

        t0 = time.perf_counter()
        answer, memory_saved = self._finalize_answer(synthesis)
        mark("postprocess", t0)

        return ChatResponse(
            answer=answer,
            used_memory=search_result.used_memory,
            used_knowledge=search_result.used_knowledge,
            requires_web=search_result.requires_web,
            provider=self.provider_name,
            model=self.router.model_for(ModelRole.DEFAULT),
            memory_saved=memory_saved,
            timings=ChatTimings(
                search=search_result.timings,
                model_ms=0.0,
                postprocess_ms=0.0,
                total_ms=(time.perf_counter() - started) * 1000,
            ),
            stage_timings=stages,
        )

    def stream(self, prompt: str, file: str | None = None, chunk_size: int = 120) -> Iterator[dict[str, object]]:
        result = self.execute(prompt, file)
        for start in range(0, len(result.answer), chunk_size):
            yield {"type": "delta", "text": result.answer[start:start + chunk_size]}
        yield {"type": "final", "reply": asdict(result)}

    def _prepare_prompt(self, prompt: str, file: str | None) -> str:
        if file:
            path = Path(file)
            content = documents.read(path)
            return f"Arquivo enviado:\n{path.name}\n\nConteúdo:\n{content}\n\nPergunta do usuário:\n{prompt}"

        workspace_context = self._build_workspace_context(prompt, file)
        if workspace_context:
            return f"Contexto do workspace:\n{workspace_context}\n\nPergunta do usuário:\n{prompt}"
        return prompt

    def _build_workspace_context(self, prompt: str, file: str | None) -> str | None:
        if file:
            return None

        try:
            workspace = workspace_manager.current()
        except Exception:
            return "Nenhum workspace está aberto."

        root = Path(getattr(workspace, "root", "")).expanduser().resolve()
        if not root.exists():
            return "Nenhum workspace está aberto."

        prompt_lower = (prompt or "").strip().lower()
        target = self._resolve_workspace_target(prompt_lower, root)
        if target is not None:
            rel_path = target.relative_to(root).as_posix() if target.is_relative_to(root) else target.as_posix()
            if target.is_dir():
                tree_text = self._build_tree_summary(target, workspace_id=getattr(workspace, "workspace_id", None))
                return (
                    f"Workspace ativo: {getattr(workspace, 'name', root.name)}\n"
                    f"Caminho: {root}\n"
                    f"Pasta relevante: {rel_path}\n\n"
                    f"Árvore resumida:\n{tree_text}"
                )
            if target.is_file() or target.suffix:
                try:
                    content = workspace_manager.read_file(rel_path, workspace_id=getattr(workspace, "workspace_id", None))
                    excerpt = "\n".join(content.splitlines()[:80])
                    return (
                        f"Workspace ativo: {getattr(workspace, 'name', root.name)}\n"
                        f"Caminho: {root}\n"
                        f"Arquivo relevante: {rel_path}\n\n"
                        f"Conteúdo:\n{excerpt}"
                    )
                except Exception:
                    pass

        tree_text = self._build_tree_summary(root, workspace_id=getattr(workspace, "workspace_id", None))
        return (
            f"Workspace ativo: {getattr(workspace, 'name', root.name)}\n"
            f"Caminho: {root}\n\n"
            f"Árvore resumida:\n{tree_text}"
        )

    def _build_tree_summary(self, root: Path, *, workspace_id: str | None = None, max_items: int = 40) -> str:
        try:
            relative = "" if root == Path(workspace_manager.current().root).resolve() else str(root.relative_to(Path(workspace_manager.current().root).resolve())).replace("\\", "/")
            items = workspace_manager.tree(relative, workspace_id=workspace_id)
        except Exception:
            items = []

        if items:
            lines = []
            for item in items[:max_items]:
                marker = "/" if item.get("directory") else ""
                lines.append(f"- {item.get('name', '')}{marker}")
            if len(items) > max_items:
                lines.append(f"- ... (+{len(items) - max_items} itens)")
            return "\n".join(lines) or "(vazio)"

        lines: list[str] = []
        try:
            for child in sorted(root.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
                if child.name.startswith("."):
                    continue
                if child.name in {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv", "node_modules"}:
                    continue
                marker = "/" if child.is_dir() else ""
                lines.append(f"- {child.name}{marker}")
                if len(lines) >= max_items:
                    break
        except Exception:
            return "(vazio)"

        return "\n".join(lines) or "(vazio)"

    def _resolve_workspace_target(self, prompt_lower: str, root: Path) -> Path | None:
        if not prompt_lower:
            return None

        matches = re.findall(r"[A-Za-z0-9._/-]+", prompt_lower)
        for token in matches:
            if token in {"o", "que", "existe", "nesse", "nesse", "projeto", "analise", "como", "funciona", "frontend", "backend", "api"}:
                continue
            candidate = root / token
            if candidate.exists():
                return candidate

        if "openai" in prompt_lower:
            for path in sorted(root.rglob("*")):
                if path.is_file() and path.suffix.lower() in {".py", ".md", ".json", ".yaml", ".yml", ".toml", ".txt", ".ts", ".tsx", ".js", ".jsx"}:
                    try:
                        content = path.read_text(encoding="utf-8", errors="ignore")
                    except Exception:
                        continue
                    if "openai" in content.lower():
                        return path

        if "frontend" in prompt_lower:
            candidate = root / "frontend"
            if candidate.exists():
                return candidate

        if prompt_lower.startswith("analise "):
            token = prompt_lower[len("analise "):].strip().split()[0]
            candidate = root / token
            if candidate.exists() or candidate.suffix:
                return candidate

        return None

    def _supervise(self, prompt: str, file: str | None, search_result: SearchResult) -> dict[str, object]:
        text = f"{prompt} {Path(file).name if file else ''}".lower()
        if file and Path(file).suffix.lower() in VISION_SUFFIXES:
            return {"intent": "vision", "primary_role": ModelRole.VISION, "parallel": False, "rationale": "arquivo visual"}
        if any(h in text for h in REVIEWER_HINTS):
            return {"intent": "review", "primary_role": ModelRole.REVIEWER, "parallel": True, "rationale": "pedido de revisão"}
        if any(h in text for h in PLANNER_HINTS):
            return {"intent": "plan", "primary_role": ModelRole.PLANNER, "parallel": True, "rationale": "pedido de planejamento"}
        if any(h in text for h in CODER_HINTS):
            return {"intent": "code", "primary_role": ModelRole.CODER, "parallel": True, "rationale": "pedido de implementação"}
        # raw = self._ask(ModelRole.PLANNER, SUPERVISOR_PROMPT, f"Solicitação:\n{prompt}\n\nContexto:\n{_limit_text(search_result.prompt, 5000)}")
        # data = _extract_json(raw)
        # if isinstance(data, dict):
        #     return {
        #         "intent": str(data.get("intent", "general")),
        #         "primary_role": _role_from_name(str(data.get("primary_role", "default"))),
        #         "parallel": bool(data.get("should_parallel", True)),
        #         "rationale": str(data.get("rationale", "")),
        #     }
        # return {"intent": "general", "primary_role": ModelRole.DEFAULT, "parallel": True, "rationale": "fluxo geral"}
        return {
            "intent": "general",
            "primary_role": ModelRole.DEFAULT,
            "parallel": True,
            "rationale": "fluxo geral",
        }

    def _plan(self, prompt: str, supervisor: dict[str, object], search_result: SearchResult) -> str:
        result = self._ask(
            ModelRole.PLANNER,
            PLANNER_PROMPT,
            f"Solicitação:\n{prompt}\n\nSupervisor:\n{supervisor}\n\nContexto:\n{_limit_text(search_result.prompt, 5000)}",
        )
        print("\n===== PLANNER =====")
        print(result)
        print("===================\n")
        return result

    def _debate(self, prompt: str, supervisor: dict[str, object], search_result: SearchResult) -> tuple[str, str]:
        ctx = f"""
        Solicitação:
        {prompt}
        Supervisor:
        {supervisor}
        Plano:
        {plan_text}
        Contexto:
        {_limit_text(search_result.prompt, 5000)}
        """
        with ThreadPoolExecutor(max_workers=2) as ex:
            future_coder = ex.submit(self._ask, ModelRole.CODER, CODER_PROMPT, ctx)
            future_reviewer = ex.submit(self._ask, ModelRole.REVIEWER, REVIEWER_PROMPT, ctx)

            coder = future_coder.result()
            reviewer = future_reviewer.result()
        print("\n===== CODER =====")
        print(coder)
        print("\n===== REVIEWER =====")
        print(reviewer)
        print("=====================\n")
        return coder, reviewer

    def _synthesize(self, prompt: str, supervisor: dict[str, object], coder: str, reviewer: str, search_result: SearchResult) -> str:
        ctx = f"Solicitação:\n{prompt}\n\nSupervisor:\n{supervisor}\n\nCoder:\n{coder}\n\nReviewer:\n{reviewer}\n\nContexto:\n{_limit_text(search_result.prompt, 5000)}"
        result = self._ask(
            ModelRole.DEFAULT,
            SYNTH_PROMPT,
            ctx,
        )
        print("\n===== SYNTHESIS =====")
        print(result)
        print("=====================\n")
        return result

    def _ask(
        self,
        role: ModelRole,
        system_prompt: str,
        prompt: str,
    ) -> str:
        return self.router.ask(
            prompt=prompt,
            role=role,
            system_prompt=system_prompt,
        )

    def _finalize_answer(self, answer: str) -> tuple[str, bool]:
        if "<MEMORY>" not in answer or "</MEMORY>" not in answer:
            return answer, False
        block = answer.split("<MEMORY>", 1)[1].split("</MEMORY>", 1)[0]
        title = content = ""
        for line in block.splitlines():
            lower = line.lower()
            if lower.startswith("titulo:"):
                title = line.split(":", 1)[1].strip()
            elif lower.startswith("conteudo:"):
                content = line.split(":", 1)[1].strip()
        if title and content:
            memory.add(category="general", title=title, content=content, source="chat")
        return answer.split("<MEMORY>", 1)[0].strip(), bool(title and content)


class ChatService:
    def __init__(self) -> None:
        self.router = AIRouter()
        self.provider_name = getattr(self.router, "_provider", "ollama")
        self.pipeline = CognitionPipeline(self.router, self.provider_name)

    def ask(self, prompt: str, file: str | None = None) -> ChatResponse:
        return self.pipeline.execute(prompt, file)

    def ask_stream(self, prompt: str, file: str | None = None) -> Iterator[dict[str, object]]:
        yield from self.pipeline.stream(prompt, file)



def _limit_text(text: str, limit: int = 6000) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[:limit] + "\n..."


def _extract_json(text: str) -> dict[str, object] | None:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE)
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    candidate = match.group(0) if match else cleaned
    try:
        data = json.loads(candidate)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _role_from_name(value: str) -> ModelRole:
    return {
        "planner": ModelRole.PLANNER,
        "coder": ModelRole.CODER,
        "reviewer": ModelRole.REVIEWER,
        "vision": ModelRole.VISION,
        "embedding": ModelRole.EMBEDDING,
    }.get(value.strip().lower(), ModelRole.DEFAULT)


chat = ChatService()
