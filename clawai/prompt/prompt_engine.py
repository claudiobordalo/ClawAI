from __future__ import annotations

import json
from typing import Any

from clawai.mission.mission import Mission


class PromptEngine:
    """
    Responsabilidade única:
    - transformar (Mission + ContextBuilder resultado + Workspace + instrução do usuário)
      em um prompt final determinístico para envio ao Provider.

    Regras:
    - não chama LLM
    - não conhece Provider/Dispatcher
    - não executa ferramentas
    - não modifica Workspace
    - não acessa ResourceManager
    """

    def build(
        self,
        *,
        mission: Mission,
        context_builder_result: Any,
        workspace: Any,
        user_instruction: str,
    ) -> str:
        if mission is None:
            raise ValueError("PromptEngine: 'mission' é obrigatório.")
        if context_builder_result is None:
            raise ValueError("PromptEngine: 'context_builder_result' é obrigatório.")
        if workspace is None:
            raise ValueError("PromptEngine: 'workspace' é obrigatório.")
        if user_instruction is None:
            raise ValueError("PromptEngine: 'user_instruction' é obrigatório.")

        context_text = getattr(context_builder_result, "context", None)
        if context_text is None:
            context_text = str(context_builder_result)

        mission_block = self._build_mission_block(mission)
        context_block = self._build_context_block(context_text)
        workspace_block = self._build_workspace_block(workspace)
        user_block = self._build_user_block(user_instruction)

        # Ordem determinística dos blocos
        return "\n".join(
            [
                "==================== MISSION ====================",
                mission_block,
                "==================== CONTEXT ====================",
                context_block,
                "================ WORKSPACE STATE ================",
                workspace_block,
                "================== USER REQUEST =================",
                user_block,
            ]
        )

    def _build_mission_block(self, mission: Mission) -> str:
        payload = {
            "id": getattr(mission, "id", None),
            "objective": getattr(mission, "objective", None),
            "priority": getattr(mission, "priority", None),
            "status": str(getattr(mission, "status", None)),
            "current_step": getattr(mission, "current_step", None),
            "history": getattr(mission, "history", []),
            "context": getattr(mission, "context", {}),
            "result": getattr(mission, "result", {}),
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)

    def _build_context_block(self, context_text: str) -> str:
        return context_text if isinstance(context_text, str) else str(context_text)

    def _build_workspace_block(self, workspace: Any) -> str:
        # Evita dependência de filesystem real: apenas índices/representações.
        # Se get_tree estiver disponível, usamos a representação retornada.
        is_open = getattr(workspace, "is_open", None)
        tree_repr = None
        get_tree = getattr(workspace, "get_tree", None)

        if callable(get_tree):
            try:
                tree = get_tree()
                tree_repr = repr(tree)
            except Exception:
                tree_repr = None

        payload = {"is_open": is_open, "tree": tree_repr}
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)

    def _build_user_block(self, user_instruction: str) -> str:
        return user_instruction
