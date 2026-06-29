from __future__ import annotations

import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from typing import Sequence

from clawai.ai.router import AIRouter, ModelRole
from clawai.bridge.models import (
    BridgeConsultResult,
    BridgeParticipantConfig,
    BridgeParticipantResult,
    BridgeToolDecision,
)
from clawai.core.config.settings import Settings
from clawai.providers.factory import ProviderFactory

AVAILABLE_TOOLS: tuple[str, ...] = (
    "chat",
    "verify",
    "implement",
    "queue",
    "memory",
    "planning",
    "git",
    "filesystem",
    "search",
)

ROLE_HINTS: dict[str, str] = {
    "planner": "Concentre-se em decompor a solicitação em passos e em escolher a melhor direção de solução.",
    "coder": "Concentre-se em implementação, consistência de código e detalhes técnicos.",
    "reviewer": "Concentre-se em revisar criticamente, apontar falhas e sugerir a melhor resposta final.",
    "default": "Responda com foco técnico, sem floreios desnecessários.",
}

ROLE_TO_MODEL_ROLE: dict[str, ModelRole] = {
    "planner": ModelRole.PLANNER,
    "coder": ModelRole.CODER,
    "reviewer": ModelRole.REVIEWER,
    "default": ModelRole.DEFAULT,
}


class BridgeService:
    def __init__(
        self,
        settings: Settings | None = None,
        default_provider: str = "ollama",
    ) -> None:
        self.settings = settings or Settings()
        self.default_provider = default_provider

    def available_providers(self) -> tuple[str, ...]:
        return ProviderFactory.list_providers()

    def default_provider_for_role(self, role: str) -> str:
        providers = set(self.available_providers())
        if role == "reviewer" and "openai" in providers and os.getenv("OPENAI_API_KEY"):
            return "openai"
        if self.default_provider in providers:
            return self.default_provider
        if "ollama" in providers:
            return "ollama"
        if providers:
            return sorted(providers)[0]
        return self.default_provider

    def default_participants(self) -> list[BridgeParticipantConfig]:
        return [
            BridgeParticipantConfig(role="planner", provider=self.default_provider_for_role("planner")),
            BridgeParticipantConfig(role="coder", provider=self.default_provider_for_role("coder")),
            BridgeParticipantConfig(role="reviewer", provider=self.default_provider_for_role("reviewer")),
        ]

    def list_tools(self) -> tuple[str, ...]:
        return AVAILABLE_TOOLS

    def consult(
        self,
        prompt: str,
        system_prompt: str | None = None,
        participants: Sequence[BridgeParticipantConfig] | None = None,
        judge_provider: str | None = None,
    ) -> BridgeConsultResult:
        prompt = prompt.strip()
        if not prompt:
            raise ValueError("prompt is required")

        resolved_participants = list(participants or self.default_participants())
        if not resolved_participants:
            resolved_participants = self.default_participants()

        started_at = time.perf_counter()
        results: list[BridgeParticipantResult] = []

        with ThreadPoolExecutor(max_workers=max(1, len(resolved_participants))) as executor:
            future_map = {
                executor.submit(self._run_participant, participant, prompt, system_prompt): index
                for index, participant in enumerate(resolved_participants)
            }
            ordered: dict[int, BridgeParticipantResult] = {}
            for future in as_completed(future_map):
                index = future_map[future]
                ordered[index] = future.result()

        results = [ordered[index] for index in sorted(ordered)]

        heuristic_tool, heuristic_reason = self._heuristic_tool(prompt)
        judge_provider_name = judge_provider or self._judge_provider(resolved_participants)
        judge_model = self._judge_model(judge_provider_name)
        judge_result = self._judge(
            prompt=prompt,
            system_prompt=system_prompt or "",
            participants=results,
            heuristic_tool=heuristic_tool,
            heuristic_reason=heuristic_reason,
            judge_provider=judge_provider_name,
            judge_model=judge_model,
        )

        elapsed_ms = (time.perf_counter() - started_at) * 1000
        final_answer = judge_result.get("final_answer") or self._fallback_answer(results, prompt)
        winner_role = str(judge_result.get("winner_role") or self._best_role(results))
        decision = BridgeToolDecision(
            recommended_tool=self._normalize_tool(
                str(judge_result.get("recommended_tool") or heuristic_tool)
            ),
            reason=str(judge_result.get("tool_reason") or heuristic_reason),
            confidence=self._coerce_confidence(judge_result.get("confidence")),
            winner_role=winner_role,
            source="judge" if judge_result else "heuristic",
        )

        return BridgeConsultResult(
            prompt=prompt,
            system_prompt=system_prompt or "",
            heuristic_tool=heuristic_tool,
            heuristic_reason=heuristic_reason,
            decision=decision,
            winner_role=winner_role,
            final_answer=final_answer,
            participants=results,
            elapsed_ms=elapsed_ms,
            parallel_roles=[participant.role for participant in resolved_participants],
            judge_model=judge_model,
            judge_provider=judge_provider_name,
            judge_raw=str(judge_result.get("raw") or ""),
        )

    def recommend_tool(
        self,
        prompt: str,
        system_prompt: str | None = None,
        judge_provider: str | None = None,
    ) -> BridgeToolDecision:
        result = self.consult(
            prompt=prompt,
            system_prompt=system_prompt,
            participants=[
                BridgeParticipantConfig(role="planner", provider=self.default_provider_for_role("planner")),
                BridgeParticipantConfig(role="reviewer", provider=self.default_provider_for_role("reviewer")),
            ],
            judge_provider=judge_provider,
        )
        return result.decision

    def _router(self, provider: str) -> AIRouter:
        return AIRouter(settings=self.settings, provider=provider)

    def _run_participant(
        self,
        participant: BridgeParticipantConfig,
        prompt: str,
        system_prompt: str | None,
    ) -> BridgeParticipantResult:
        role_key = self._normalize_role_name(participant.role)
        provider_name = participant.provider or self.default_provider_for_role(role_key)
        router = self._router(provider_name)
        model_role = ROLE_TO_MODEL_ROLE.get(role_key, ModelRole.DEFAULT)
        composed_prompt = self._compose_prompt(role_key, prompt)
        composed_system_prompt = self._compose_system_prompt(role_key, system_prompt)
        started_at = time.perf_counter()

        try:
            provider = router.provider_for(model_role)
            response = provider.generate(
                prompt=composed_prompt,
                system_prompt=composed_system_prompt,
            )
            elapsed_ms = (time.perf_counter() - started_at) * 1000
            return BridgeParticipantResult(
                role=role_key,
                provider=response.provider or provider_name,
                model=response.model,
                content=response.content,
                elapsed_ms=elapsed_ms,
                prompt_tokens=getattr(response, "prompt_tokens", 0),
                completion_tokens=getattr(response, "completion_tokens", 0),
                total_tokens=getattr(response, "total_tokens", 0),
            )
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - started_at) * 1000
            return BridgeParticipantResult(
                role=role_key,
                provider=provider_name,
                model=self._fallback_model(role_key),
                content="",
                elapsed_ms=elapsed_ms,
                error=str(exc),
            )

    def _judge_provider(self, participants: Sequence[BridgeParticipantConfig]) -> str:
        for participant in participants:
            if self._normalize_role_name(participant.role) == "reviewer" and participant.provider:
                return participant.provider
        return self.default_provider_for_role("reviewer")

    def _judge_model(self, provider_name: str) -> str:
        router = self._router(provider_name)
        try:
            return router.model_for(ModelRole.REVIEWER)
        except Exception:
            return self.settings.reviewer_model

    def _judge(
        self,
        *,
        prompt: str,
        system_prompt: str,
        participants: Sequence[BridgeParticipantResult],
        heuristic_tool: str,
        heuristic_reason: str,
        judge_provider: str,
        judge_model: str,
    ) -> dict[str, object]:
        router = self._router(judge_provider)
        participant_block = []
        for item in participants:
            participant_block.append(
                {
                    "role": item.role,
                    "provider": item.provider,
                    "model": item.model,
                    "content": item.content,
                    "error": item.error,
                    "elapsed_ms": round(item.elapsed_ms, 2),
                }
            )

        judge_prompt = (
            "Analise as respostas abaixo de múltiplos modelos e produza uma decisão final.\n\n"
            f"Pedido do usuário:\n{prompt}\n\n"
            f"Contexto adicional:\n{system_prompt or '-'}\n\n"
            f"Ferramenta sugerida pelo heurístico: {heuristic_tool}\n"
            f"Motivo heurístico: {heuristic_reason}\n\n"
            f"Ferramentas disponíveis: {', '.join(AVAILABLE_TOOLS)}\n\n"
            f"Respostas dos participantes:\n{json.dumps(participant_block, ensure_ascii=False, indent=2)}\n\n"
            "Retorne apenas JSON válido com as chaves:\n"
            "{\n"
            '  "winner_role": "planner|coder|reviewer|default",\n'
            '  "recommended_tool": "uma das ferramentas disponíveis",\n'
            '  "tool_reason": "justificativa curta",\n'
            '  "confidence": 0.0,\n'
            '  "final_answer": "resposta final em português"\n'
            "}\n"
        )

        try:
            provider = router.provider_for(ModelRole.REVIEWER)
            response = provider.generate(prompt=judge_prompt, system_prompt=self._judge_system_prompt())
            parsed = self._extract_json_object(response.content)
            parsed["raw"] = response.content
            if "winner_role" not in parsed:
                parsed["winner_role"] = self._best_role(participants)
            if "recommended_tool" not in parsed:
                parsed["recommended_tool"] = heuristic_tool
            if "tool_reason" not in parsed:
                parsed["tool_reason"] = heuristic_reason
            if "confidence" not in parsed:
                parsed["confidence"] = 0.5
            if "final_answer" not in parsed:
                parsed["final_answer"] = self._fallback_answer(participants, prompt)
            return parsed
        except Exception:
            return {
                "winner_role": self._best_role(participants),
                "recommended_tool": heuristic_tool,
                "tool_reason": heuristic_reason,
                "confidence": 0.5,
                "final_answer": self._fallback_answer(participants, prompt),
                "raw": "",
            }

    def _judge_system_prompt(self) -> str:
        return (
            "Você é o juiz da ponte de modelos do ClawAI. "
            "Escolha a melhor resposta, selecione a ferramenta mais apropriada e mantenha a resposta final objetiva. "
            "Sempre retorne JSON válido."
        )

    def _compose_prompt(self, role: str, prompt: str) -> str:
        return (
            f"Função: {role}\n"
            f"Tarefa do usuário:\n{prompt}\n\n"
            "Responda apenas com o conteúdo útil para sua função."
        )

    def _compose_system_prompt(self, role: str, system_prompt: str | None) -> str:
        hint = ROLE_HINTS.get(role, ROLE_HINTS["default"])
        if system_prompt and system_prompt.strip():
            return f"{hint}\n\nContexto adicional do usuário:\n{system_prompt.strip()}"
        return hint

    def _normalize_role_name(self, role: str) -> str:
        key = role.strip().lower()
        return key if key in ROLE_HINTS else "default"

    def _normalize_tool(self, tool: str) -> str:
        normalized = tool.strip().lower()
        return normalized if normalized in AVAILABLE_TOOLS else self._heuristic_tool(normalized)[0]

    def _fallback_model(self, role: str) -> str:
        if role == "planner":
            return self.settings.planner_model
        if role == "coder":
            return self.settings.coder_model
        if role == "reviewer":
            return self.settings.reviewer_model
        return self.settings.default_model

    def _best_role(self, participants: Sequence[BridgeParticipantResult]) -> str:
        available = [item for item in participants if item.content.strip()]
        if not available:
            return "default"
        reviewer = next((item for item in available if item.role == "reviewer"), None)
        if reviewer:
            return reviewer.role
        return max(available, key=lambda item: len(item.content.strip())).role

    def _fallback_answer(
        self,
        participants: Sequence[BridgeParticipantResult],
        prompt: str,
    ) -> str:
        reviewed = [item.content.strip() for item in participants if item.content.strip()]
        if reviewed:
            return reviewed[-1]
        return f"Não consegui produzir uma resposta modelada para: {prompt}"

    def _coerce_confidence(self, value: object) -> float:
        try:
            confidence = float(value)
        except Exception:
            return 0.5
        if confidence < 0.0:
            return 0.0
        if confidence > 1.0:
            return 1.0
        return confidence

    def _heuristic_tool(self, prompt: str) -> tuple[str, str]:
        text = prompt.lower()
        rules: list[tuple[str, tuple[str, ...], str]] = [
            (
                "implement",
                ("implementar", "implement", "feature", "funcionalidade", "codigo", "code", "refator", "refactor"),
                "O pedido parece exigir mudanças de código ou criação de funcionalidade.",
            ),
            (
                "verify",
                ("teste", "test", "verify", "valida", "falha", "erro", "bug"),
                "O pedido parece exigir validação, testes ou diagnóstico.",
            ),
            (
                "git",
                ("git", "commit", "merge", "branch", "rollback", "revert", "push", "pull"),
                "O pedido parece exigir operação de versionamento.",
            ),
            (
                "planning",
                ("plano", "planej", "roadmap", "prioridade", "subtarefa", "queue"),
                "O pedido parece exigir planejamento ou decomposição em subtarefas.",
            ),
            (
                "memory",
                ("memoria", "memória", "remember", "historico", "histórico", "reutil", "learn"),
                "O pedido parece exigir consulta ou registro de memória de engenharia.",
            ),
            (
                "filesystem",
                ("arquivo", "file", "path", "diretorio", "directory", "pasta"),
                "O pedido parece exigir navegação ou manipulação de arquivos.",
            ),
            (
                "search",
                ("buscar", "search", "procurar", "find", "localizar", "scan"),
                "O pedido parece exigir busca ou descoberta de informação.",
            ),
            (
                "queue",
                ("fila", "queue", "sequencial", "sequência", "pipeline"),
                "O pedido parece exigir execução em fila ou processamento sequencial.",
            ),
        ]
        for tool, keywords, reason in rules:
            if any(keyword in text for keyword in keywords):
                return tool, reason
        return "chat", "O pedido parece melhor atendido por conversa geral e síntese de modelos."

    def _extract_json_object(self, text: str) -> dict[str, object]:
        cleaned = text.strip()
        fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", cleaned, flags=re.DOTALL | re.IGNORECASE)
        if fence:
            cleaned = fence.group(1).strip()
        else:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                cleaned = cleaned[start : end + 1]

        data = json.loads(cleaned)
        if not isinstance(data, dict):
            raise ValueError("Judge output must be a JSON object")
        return data


bridge_service = BridgeService()
