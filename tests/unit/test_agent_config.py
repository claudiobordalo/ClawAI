from __future__ import annotations

import pytest

from clawai.config.agent_config import AgentConfig
from clawai.agent.agent_loop import AgentLoop
from clawai.prompt.prompt_engine import PromptEngine
from clawai.agent.agent_engine import AgentEngine
from clawai.memory.conversation_memory import ConversationMemory
from clawai.mission.mission import Mission
from unittest.mock import MagicMock


def test_agent_config_defaults() -> None:
    config = AgentConfig()

    assert config.max_iterations == 10
    assert config.memory_messages_limit == 10
    assert config.provider_timeout == 30.0
    assert config.provider_temperature == 0.7
    assert config.provider_max_tokens == 1024
    assert config.enable_tools is True
    assert config.enable_memory is True
    assert config.enable_workspace is True
    assert config.enable_system_prompt is True
    assert config.enable_tool_discovery is True


def test_agent_config_custom_values() -> None:
    config = AgentConfig(
        max_iterations=5,
        memory_messages_limit=2,
        provider_timeout=60.0,
        provider_temperature=0.2,
        provider_max_tokens=512,
        enable_tools=False,
        enable_memory=False,
        enable_workspace=False,
        enable_system_prompt=False,
        enable_tool_discovery=False,
    )

    assert config.max_iterations == 5
    assert config.memory_messages_limit == 2
    assert config.provider_timeout == 60.0
    assert config.provider_temperature == 0.2
    assert config.provider_max_tokens == 512
    assert config.enable_tools is False
    assert config.enable_memory is False
    assert config.enable_workspace is False
    assert config.enable_system_prompt is False
    assert config.enable_tool_discovery is False


def test_agent_config_immutable() -> None:
    config = AgentConfig()

    with pytest.raises(Exception):
        config.max_iterations = 20  # type: ignore[assignment]


def test_agent_config_equality() -> None:
    config1 = AgentConfig()
    config2 = AgentConfig()

    assert config1 == config2
    assert hash(config1) == hash(config2)


def test_prompt_engine_accepts_agent_config_optionally() -> None:
    memory = ConversationMemory()
    memory.add(role="user", content="ola")
    config = AgentConfig(memory_messages_limit=2)

    engine = PromptEngine(conversation_memory=memory, config=config)
    prompt = engine.build(
        mission=Mission(id="mission-001", objective="Test"),
        context_builder_result=MagicMock(context="CTX"),
        workspace=MagicMock(is_open=True, get_tree=lambda: {}),
        user_instruction="USER",
    )

    assert "CONVERSATION HISTORY" in prompt
    assert "ola" in prompt


def test_prompt_engine_respects_agent_config_tool_discovery() -> None:
    memory = ConversationMemory()
    memory.add(role="user", content="ola")
    config = AgentConfig(enable_tool_discovery=False)

    engine = PromptEngine(
        conversation_memory=memory,
        tool_discovery=MagicMock(),
        config=config,
    )
    prompt = engine.build(
        mission=Mission(id="mission-002", objective="Test"),
        context_builder_result=MagicMock(context="CTX"),
        workspace=MagicMock(is_open=True, get_tree=lambda: {}),
        user_instruction="USER",
    )

    assert "AVAILABLE TOOLS" not in prompt


def test_agent_loop_accepts_agent_config_optionally() -> None:
    engine = MagicMock(spec=AgentEngine)
    engine.execute.return_value = MagicMock(success=True, llm_response="ok", action=None, execution_result=None, error=None)

    config = AgentConfig(max_iterations=3)
    loop = AgentLoop(agent_engine=engine)
    result = loop.run(
        mission=MagicMock(),
        workspace=MagicMock(),
        user_instruction="test",
        config=config,
    )

    assert result.iterations == 1
    assert result.success is True


def test_agent_loop_respects_explicit_max_iterations_over_config() -> None:
    engine = MagicMock(spec=AgentEngine)
    engine.execute.return_value = MagicMock(success=True, llm_response="ok", action=None, execution_result=None, error=None)

    config = AgentConfig(max_iterations=2)
    loop = AgentLoop(agent_engine=engine)
    result = loop.run(
        mission=MagicMock(),
        workspace=MagicMock(),
        user_instruction="test",
        max_iterations=4,
        config=config,
    )

    assert result.iterations == 1
    assert result.success is True


def test_agent_loop_compatible_with_explicit_max_iterations() -> None:
    engine = MagicMock(spec=AgentEngine)
    engine.execute.return_value = MagicMock(success=True, llm_response="ok", action=None, execution_result=None, error=None)

    loop = AgentLoop(agent_engine=engine)
    result = loop.run(
        mission=MagicMock(),
        workspace=MagicMock(),
        user_instruction="test",
        max_iterations=4,
    )

    assert result.iterations == 1
    assert result.success is True


def test_default_values_stability() -> None:
    config = AgentConfig()
    assert config == AgentConfig()
    assert config.max_iterations == 10
    assert config.memory_messages_limit == 10
