from __future__ import annotations

import json
from typing import Any

from clawai.config.agent_config import AgentConfig
from clawai.mission.mission import Mission
from clawai.memory.conversation_memory import ConversationMemory, ConversationMessage
from clawai.tools.tool_discovery import ToolDiscovery
from clawai.tools.tool_descriptor import ToolDescriptor
from clawai.tools.tool_selection_policy import ToolSelectionPolicy
from clawai.prompt.system_prompt import SystemPrompt


class PromptEngine:
    """
    Responsabilidade única:
    - transformar (Mission + ContextBuilder resultado + Workspace + instrução do usuário)
      em um prompt final determinístico para envio ao Provider.

    Agora também incorpora uma seção de ferramentas quando um ToolDiscovery
    é fornecido via injeção de dependência opcional.

    Regras:
    - não chama LLM
    - não conhece Provider/Dispatcher
    - não executa ferramentas
    - não modifica Workspace
    - não acessa ResourceManager
    - não acessa ToolRegistry diretamente (apenas via ToolDiscovery)
    """

    def __init__(
        self,
        *,
        tool_discovery: ToolDiscovery | None = None,
        tool_selection_policy: ToolSelectionPolicy | None = None,
        conversation_memory: ConversationMemory | None = None,
        memory_messages_limit: int = 10,
        system_prompt: SystemPrompt | None = None,
        config: AgentConfig | None = None,
    ) -> None:
        """
        Args:
            tool_discovery: Discovery opcional de ferramentas.
                Se fornecido, uma seção de ferramentas será incluída no prompt.
            tool_selection_policy: Política opcional para selecionar quais ferramentas
                serão exibidas ao LLM.
            config: Configuração opcional do agente.
        """
        self._tool_discovery = (
            tool_discovery if config is None or config.enable_tool_discovery else None
        )
        self._tool_selection_policy = tool_selection_policy
        self._conversation_memory = (
            conversation_memory if config is None or config.enable_memory else None
        )
        self._memory_messages_limit = self._resolve_memory_messages_limit(
            config=config,
            memory_messages_limit=memory_messages_limit,
        )
        self._system_prompt = (
            system_prompt if config is None or config.enable_system_prompt else None
        )

    @staticmethod
    def _resolve_memory_messages_limit(
        *,
        config: AgentConfig | None,
        memory_messages_limit: int,
    ) -> int:
        if memory_messages_limit > 0 and (config is None or memory_messages_limit != 10):
            return memory_messages_limit

        if config is not None:
            return config.memory_messages_limit

        return 10

    @property
    def tool_discovery(self) -> ToolDiscovery | None:
        return self._tool_discovery

    @property
    def conversation_memory(self) -> ConversationMemory | None:
        return self._conversation_memory

    @property
    def memory_messages_limit(self) -> int:
        return self._memory_messages_limit

    @property
    def system_prompt(self) -> SystemPrompt | None:
        return self._system_prompt

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

        # Blocos base (ordem determinística)
        blocks: list[str] = []

        # 1) SYSTEM (se existir)
        if self._system_prompt is not None:
            sys_text = self._system_prompt.build()
            if sys_text:
                blocks.append("=============== SYSTEM ===============")
                blocks.append("")
                blocks.append(sys_text)

        # 2) MISSION (mantendo compatibilidade com estrutura existente)
        blocks.extend([
            "==================== MISSION ====================",
            mission_block,
        ])

        # 3) CONTEXT
        blocks.extend([
            "==================== CONTEXT ====================",
            context_block,
        ])

        # 4) WORKSPACE STATE
        blocks.extend([
            "================ WORKSPACE STATE ================",
            workspace_block,
        ])

        # Se houver memória de conversação, inclui o histórico antes do USER REQUEST
        if self._conversation_memory is not None:
            history_block = self._build_history_block()
            if history_block:
                blocks.append("=============== CONVERSATION HISTORY ==============")
                blocks.append("")
                blocks.append(history_block)

        # USER REQUEST sempre vem após (compatibilidade com estrutura existente)
        blocks.extend([
            "================== USER REQUEST =================",
            user_block,
        ])

        # Se ToolDiscovery estiver disponível, adiciona seção de ferramentas
        if self._tool_discovery is not None:
            tools_block = self._build_tools_block(
                mission=mission,
                workspace=workspace,
            )
            if tools_block:
                blocks.append("=============== AVAILABLE TOOLS ===============")
                blocks.append(tools_block)

        return "\n".join(blocks)

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

    def _build_history_block(self) -> str:
        """Monta bloco do histórico de conversas a partir da ConversationMemory.

        Regras:
        - Ordem cronológica preservada.
        - Respeita o limite configurado.
        - Histórico vazio -> retorna string vazia.
        - Nunca modifica a memória.
        """
        if self._conversation_memory is None:
            return ""

        try:
            last_msgs = self._conversation_memory.last(self._memory_messages_limit)
        except Exception:
            return ""

        if not last_msgs:
            return ""

        lines: list[str] = []
        for msg in last_msgs:
            role = getattr(msg, "role", "").upper() if hasattr(msg, "role") else ""
            content = getattr(msg, "content", "")

            lines.append(f"{role}:")
            lines.append(str(content))
            lines.append("")

        return "\n".join(lines).rstrip("\n")

    def _build_tools_block(self, *, mission: Mission, workspace: Any) -> str:
        """Constrói a seção de ferramentas do prompt usando ToolDiscovery."""
        if self._tool_discovery is None:
            return ""

        try:
            descriptors = self._tool_discovery.discover_all()
        except Exception:
            return ""

        if self._tool_selection_policy is not None:
            descriptors = self._tool_selection_policy.select(
                tools=descriptors,
                mission=mission,
                workspace=workspace,
            )

        if not descriptors:
            return ""

        lines: list[str] = []

        for desc in descriptors:
            lines.append(f"{desc.name}")
            lines.append("")

            if desc.description:
                lines.append(f"Description:")
                lines.append(f"{desc.description}")
                lines.append("")

            if desc.arguments:
                lines.append("Arguments:")
                for arg in desc.arguments:
                    required_str = "required" if arg.required else "optional"
                    default_str = f", default={arg.default}" if arg.default is not None else ""
                    desc_str = f" - {arg.name} ({arg.type}, {required_str}{default_str})"
                    if arg.description:
                        desc_str += f"\n   {arg.description}"
                    lines.append(desc_str)
                lines.append("")

            if desc.examples:
                lines.append("Examples:")
                for example in desc.examples:
                    lines.append(f" - {example}")
                lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines).rstrip("\n")
