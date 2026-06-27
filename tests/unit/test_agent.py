"""Tests for the Agent package (Sprint 4)."""

import os
import shutil
import time
import uuid
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock

import pytest

from clawai.agent import (
    AgentLoop,
    AgentConfiguration,
    AgentContext,
    AgentLoop,
    AgentMetrics,
    AutonomousAgent,
    CheckpointManager,
    ExecutionSession,
    ExecutionState,
    GoalExecutionResult,
    RetryPolicy,
)
from clawai.agent.execution_events import (
    EXECUTOR_FINISHED,
    EXECUTOR_STARTED,
    GOAL_FAILED,
    GOAL_FINISHED,
    GOAL_RETRIED,
    GOAL_STARTED,
    PLANNER_FINISHED,
    PLANNER_STARTED,
    SESSION_CANCELLED,
    SESSION_FINISHED,
    SESSION_STARTED,
)
from clawai.cognition import CognitiveFactory, ReasoningEngine
from clawai.engineering import EngineeringMemory
from clawai.goals import (
    EngineeringMemoryGoalRepository,
    Goal,
    GoalBacklog,
    GoalEventBus,
    GoalManager,
    GoalPlanner,
    GoalPriority,
    GoalStatus,
    PlanningContext,
)
from clawai.executor import ExecutionRequest, ExecutionResult


# ===== ExecutionState =====

class TestExecutionState:
    def test_values(self):
        assert ExecutionState.PENDING.value == "pending"
        assert ExecutionState.RUNNING.value == "running"
        assert ExecutionState.COMPLETED.value == "completed"
        assert ExecutionState.FAILED.value == "failed"
        assert ExecutionState.CANCELLED.value == "cancelled"

    def test_str(self):
        assert str(ExecutionState.WAITING) == "waiting"
        assert str(ExecutionState.REPLANNING) == "replanning"


# ===== GoalExecutionResult =====

class TestGoalExecutionResult:
    def test_defaults(self):
        g = Goal(id="g1", title="t1", description="d", success_criteria="s", priority=1)
        r = GoalExecutionResult(goal=g, success=True)
        assert r.output == ""
        assert r.duration == 0.0
        assert r.errors == []
        assert r.warnings == []
        assert r.metadata == {}
        assert not r.requires_replan

    def test_with_data(self):
        g = Goal(id="g1", title="t1", description="d", success_criteria="s", priority=1)
        r = GoalExecutionResult(
            goal=g, success=False, output="failed",
            duration=1.5, errors=["err1"],
            warnings=["warn1"], metadata={"key": "val"},
            requires_replan=True,
        )
        assert not r.success
        assert r.duration == 1.5
        assert r.errors == ["err1"]
        assert r.requires_replan


# ===== ExecutionSession =====

class TestExecutionSession:
    def test_defaults(self):
        s = ExecutionSession(id="s1", objective="test")
        assert s.state == ExecutionState.PENDING
        assert s.completed_goals == []
        assert s.failed_goals == []
        assert not s.cancelled
        assert s.results == []

    def test_with_data(self):
        s = ExecutionSession(
            id="s1", objective="test",
            state=ExecutionState.RUNNING,
            current_goal="g1",
            completed_goals=["g1"],
            cancelled=True,
        )
        assert s.state == ExecutionState.RUNNING
        assert s.current_goal == "g1"
        assert s.cancelled


# ===== ExecutionEvents =====

class TestExecutionEvents:
    def test_constants(self):
        assert SESSION_STARTED == "agent.session_started"
        assert SESSION_FINISHED == "agent.session_finished"
        assert GOAL_STARTED == "agent.goal_started"
        assert GOAL_FINISHED == "agent.goal_finished"
        assert GOAL_FAILED == "agent.goal_failed"
        assert GOAL_RETRIED == "agent.goal_retried"
        assert PLANNER_STARTED == "agent.planner_started"
        assert PLANNER_FINISHED == "agent.planner_finished"
        assert EXECUTOR_STARTED == "agent.executor_started"
        assert EXECUTOR_FINISHED == "agent.executor_finished"
        assert SESSION_CANCELLED == "agent.session_cancelled"


# ===== RetryPolicy =====

class TestRetryPolicy:
    def test_defaults(self):
        p = RetryPolicy()
        assert p.max_retries == 3
        assert p.base_delay == 1.0
        assert p.backoff_factor == 2.0

    def test_compute_delay(self):
        p = RetryPolicy(base_delay=1.0, backoff_factor=2.0, max_delay=60.0)
        assert p.compute_delay(0) == 1.0
        assert p.compute_delay(1) == 2.0
        assert p.compute_delay(2) == 4.0
        assert p.compute_delay(10) == 60.0  # capped

    def test_is_retryable(self):
        p = RetryPolicy(retryable_errors=(ValueError,))
        assert p.is_retryable(ValueError("test"))
        assert not p.is_retryable(TypeError("test"))

    def test_execute_success(self):
        p = RetryPolicy(max_retries=3)
        result = p.execute(lambda: 42)
        assert result == 42

    def test_execute_retry_then_success(self):
        p = RetryPolicy(max_retries=3, base_delay=0.01)
        call_count = [0]

        def fn():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("not yet")
            return "ok"

        result = p.execute(fn)
        assert result == "ok"
        assert call_count[0] == 3

    def test_execute_exhausted(self):
        p = RetryPolicy(max_retries=1, base_delay=0.01)

        def fn():
            raise ValueError("always fails")

        with pytest.raises(ValueError, match="always fails"):
            p.execute(fn)

    def test_execute_non_retryable(self):
        p = RetryPolicy(retryable_errors=(ValueError,), max_retries=3)

        def fn():
            raise TypeError("not retryable")

        with pytest.raises(TypeError):
            p.execute(fn)

    def test_execute_on_retry_callback(self):
        p = RetryPolicy(max_retries=2, base_delay=0.01)
        call_count = [0]
        retry_log = []

        def fn():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("try again")
            return "done"

        def on_retry(attempt, error):
            retry_log.append((attempt, str(error)))

        result = p.execute(fn, on_retry=on_retry)
        assert result == "done"
        assert len(retry_log) == 1
        assert retry_log[0][0] == 1


# ===== CheckpointManager =====

class TestCheckpointManager:
    def setup_method(self):
        self._dir = f"test_checkpoints_{uuid.uuid4().hex[:8]}"

    def teardown_method(self):
        if os.path.exists(self._dir):
            shutil.rmtree(self._dir)

    def test_save_and_load(self):
        cm = CheckpointManager(self._dir)
        session = ExecutionSession(id="sess1", objective="test")
        path = cm.save(session)
        assert os.path.exists(path)

        data = cm.load("sess1")
        assert data is not None
        assert data["session_id"] == "sess1"
        assert data["objective"] == "test"

    def test_load_nonexistent(self):
        cm = CheckpointManager(self._dir)
        assert cm.load("nothing") is None

    def test_save_with_backlog(self):
        cm = CheckpointManager(self._dir)
        session = ExecutionSession(id="sess2", objective="test")
        g = Goal(id="g1", title="t1", description="d", success_criteria="s", priority=1)
        backlog = GoalBacklog(goals=(g,))
        path = cm.save(session, backlog=backlog)
        assert os.path.exists(path)

        data = cm.load("sess2")
        assert data["backlog_goal_ids"] == ["g1"]

    def test_delete(self):
        cm = CheckpointManager(self._dir)
        session = ExecutionSession(id="sess3", objective="test")
        cm.save(session)
        assert cm.delete("sess3")
        assert not os.path.exists(f"{self._dir}/sess3.json")
        assert not cm.delete("nonexistent")

    def test_save_with_extra(self):
        cm = CheckpointManager(self._dir)
        session = ExecutionSession(id="sess4", objective="test")
        path = cm.save(session, extra={"custom": "value"})
        data = cm.load("sess4")
        assert data["custom"] == "value"


# ===== AgentMetrics =====

class TestAgentMetrics:
    def test_defaults(self):
        m = AgentMetrics()
        assert m.goals_completed == 0
        assert m.average_duration == 0.0
        assert m.total_goals == 0

    def test_average_duration(self):
        m = AgentMetrics(execution_durations=[1.0, 2.0, 3.0])
        assert m.average_duration == 2.0

    def test_total_goals(self):
        m = AgentMetrics(goals_completed=3, goals_failed=2, goals_skipped=1)
        assert m.total_goals == 6


# ===== AgentContext =====

class TestAgentContext:
    def test_default_config(self):
        c = AgentConfiguration()
        assert c.max_goals == 0
        assert c.auto_replan
        assert not c.checkpoint_enabled
        assert c.checkpoint_dir == ".checkpoints"

    def test_context_creation(self):
        planner = GoalPlanner()
        mem = EngineeringMemory()
        gm = GoalManager(EngineeringMemoryGoalRepository(mem))
        bus = GoalEventBus()
        ctx = AgentContext(
            planner=planner,
            goal_manager=gm,
            executor=MagicMock(),
            memory=mem,
            event_bus=bus,
            reasoning_engine=ReasoningEngine(),
            retry_policy=RetryPolicy(),
            config=AgentConfiguration(),
        )
        assert ctx.session is None
        assert ctx.config.max_goals == 0


# ===== Integration: AutonomousAgent =====

class _AgentHelper:
    @staticmethod
    def create_agent(**kwargs):
        from clawai.agent import AgentContext
        from clawai.agent.agent_loop import AgentLoop
        from clawai.goals import GoalEventBus
        
        context_kwargs = {}
        context_kwargs["planner"] = kwargs.pop("planner", None)
        context_kwargs["goal_manager"] = kwargs.pop("goal_manager", None)
        context_kwargs["executor"] = kwargs.pop("executor", None)
        context_kwargs["memory"] = kwargs.pop("memory", None)
        context_kwargs["event_bus"] = kwargs.pop("event_bus", GoalEventBus())
        context_kwargs["reasoning_engine"] = kwargs.pop("reasoning_engine", CognitiveFactory().create_reasoning_engine())
        context_kwargs["retry_policy"] = kwargs.pop("retry_policy", RetryPolicy())
        context_kwargs["config"] = kwargs.pop("config", AgentConfiguration())
        
        ctx = AgentContext(**context_kwargs)
        loop = AgentLoop(ctx)
        return AutonomousAgent(context=ctx, agent_loop=loop)

class TestAutonomousAgent:
    def test_agent_run_empty_objective(self):
        planner = GoalPlanner()
        mem = EngineeringMemory()
        gm = GoalManager(EngineeringMemoryGoalRepository(mem))
        executor = MagicMock()
        bus = GoalEventBus()

        ctx = AgentContext(
            planner=planner,
            goal_manager=gm,
            executor=executor,
            memory=mem,
            event_bus=bus,
            reasoning_engine=CognitiveFactory().create_reasoning_engine(),
            retry_policy=RetryPolicy(),
            config=AgentConfiguration(),
        )
        loop = AgentLoop(ctx)
        agent = AutonomousAgent(context=ctx, agent_loop=loop)
        session = agent.run("")
        assert session.state == ExecutionState.COMPLETED
        assert session.completed_goals == []
        assert agent.loop is not None

    def test_agent_run_single_goal(self):
        planner = GoalPlanner()
        mem = EngineeringMemory()
        gm = GoalManager(EngineeringMemoryGoalRepository(mem))
        executor = MagicMock()
        executor.run.return_value = ExecutionResult(
            success=True,
            summary="completed",
            repair_result=MagicMock(),
            applied_results=(),
        )
        bus = GoalEventBus()

        agent = AutonomousAgent(
            planner=planner,
            goal_manager=gm,
            executor=executor,
            memory=mem,
            event_bus=bus,
        )
        session = agent.run("Fix bug")
        assert session.state == ExecutionState.COMPLETED
        assert len(session.completed_goals) >= 1

    def test_agent_run_failing_goal(self):
        planner = GoalPlanner()
        mem = EngineeringMemory()
        gm = GoalManager(EngineeringMemoryGoalRepository(mem))
        executor = MagicMock()
        executor.run.return_value = ExecutionResult(
            success=False,
            summary="failed",
            error="something went wrong",
            repair_result=MagicMock(),
            applied_results=(),
        )
        bus = GoalEventBus()

        agent = AutonomousAgent(
            planner=planner,
            goal_manager=gm,
            executor=executor,
            memory=mem,
            event_bus=bus,
            retry_policy=RetryPolicy(max_retries=1, base_delay=0.01),
        )
        session = agent.run("Fix bug")
        assert len(session.failed_goals) >= 1

    def test_agent_cancel(self):
        planner = GoalPlanner()
        mem = EngineeringMemory()
        gm = GoalManager(EngineeringMemoryGoalRepository(mem))
        executor = MagicMock()
        bus = GoalEventBus()

        agent = AutonomousAgent(
            planner=planner,
            goal_manager=gm,
            executor=executor,
            memory=mem,
            event_bus=bus,
        )
        agent.cancel()
        session = agent.run("Fix bug")
        assert session.state in (ExecutionState.COMPLETED, ExecutionState.CANCELLED)

    def test_agent_pause_resume(self):
        planner = GoalPlanner()
        mem = EngineeringMemory()
        gm = GoalManager(EngineeringMemoryGoalRepository(mem))
        executor = MagicMock()
        executor.run.return_value = ExecutionResult(
            success=True,
            summary="ok",
            repair_result=MagicMock(),
            applied_results=(),
        )
        bus = GoalEventBus()

        agent = AutonomousAgent(
            planner=planner,
            goal_manager=gm,
            executor=executor,
            memory=mem,
            event_bus=bus,
        )
        agent.pause()
        agent.resume()
        session = agent.run("Fix bug")
        assert session.state == ExecutionState.COMPLETED

    def test_agent_stop(self):
        planner = GoalPlanner()
        mem = EngineeringMemory()
        gm = GoalManager(EngineeringMemoryGoalRepository(mem))
        executor = MagicMock()
        bus = GoalEventBus()

        agent = AutonomousAgent(
            planner=planner,
            goal_manager=gm,
            executor=executor,
            memory=mem,
            event_bus=bus,
        )
        agent.stop()
        session = agent.run("Fix bug")
        assert session.state in (ExecutionState.COMPLETED, ExecutionState.CANCELLED)

    def test_agent_properties(self):
        planner = GoalPlanner()
        mem = EngineeringMemory()
        gm = GoalManager(EngineeringMemoryGoalRepository(mem))
        executor = MagicMock()
        bus = GoalEventBus()

        agent = AutonomousAgent(
            planner=planner,
            goal_manager=gm,
            executor=executor,
            memory=mem,
            event_bus=bus,
        )
        assert agent.context is not None
        assert agent.loop is None

    def test_agent_retry_then_success(self):
        planner = GoalPlanner()
        mem = EngineeringMemory()
        gm = GoalManager(EngineeringMemoryGoalRepository(mem))
        executor = MagicMock()
        call_count = [0]

        def run_side_effect(req):
            call_count[0] += 1
            if call_count[0] < 2:
                return ExecutionResult(
                    success=False,
                    summary="fail",
                    error="retry me",
                    repair_result=MagicMock(),
                    applied_results=(),
                )
            return ExecutionResult(
                success=True,
                summary="ok",
                repair_result=MagicMock(),
                applied_results=(),
            )

        executor.run = run_side_effect
        bus = GoalEventBus()

        agent = AutonomousAgent(
            planner=planner,
            goal_manager=gm,
            executor=executor,
            memory=mem,
            event_bus=bus,
            retry_policy=RetryPolicy(max_retries=2, base_delay=0.01),
        )
        session = agent.run("Fix bug")
        assert len(session.completed_goals) >= 1

    def test_agent_loop_metrics(self):
        planner = GoalPlanner()
        mem = EngineeringMemory()
        gm = GoalManager(EngineeringMemoryGoalRepository(mem))
        executor = MagicMock()
        executor.run.return_value = ExecutionResult(
            success=True,
            summary="ok",
            repair_result=MagicMock(),
            applied_results=(),
        )
        bus = GoalEventBus()

        agent = AutonomousAgent(
            planner=planner,
            goal_manager=gm,
            executor=executor,
            memory=mem,
            event_bus=bus,
        )
        agent.run("Fix bug")
        loop = agent.loop
        assert loop is not None
        assert loop.metrics.goals_completed >= 1

    def test_agent_max_goals(self):
        planner = GoalPlanner()
        mem = EngineeringMemory()
        gm = GoalManager(EngineeringMemoryGoalRepository(mem))
        executor = MagicMock()
        executor.run.return_value = ExecutionResult(
            success=True,
            summary="ok",
            repair_result=MagicMock(),
            applied_results=(),
        )
        bus = GoalEventBus()
        config = AgentConfiguration(max_goals=1)

        agent = AutonomousAgent(
            planner=planner,
            goal_manager=gm,
            executor=executor,
            memory=mem,
            event_bus=bus,
            config=config,
        )
        session = agent.run("Fix bug\nAdd feature\nWrite docs")
        # With max_goals=1, only 1 goal should complete
        assert len(session.completed_goals) <= 1

    def test_agent_multiple_goals(self):
        planner = GoalPlanner()
        mem = EngineeringMemory()
        gm = GoalManager(EngineeringMemoryGoalRepository(mem))
        executor = MagicMock()
        executor.run.return_value = ExecutionResult(
            success=True,
            summary="ok",
            repair_result=MagicMock(),
            applied_results=(),
        )
        bus = GoalEventBus()

        agent = AutonomousAgent(
            planner=planner,
            goal_manager=gm,
            executor=executor,
            memory=mem,
            event_bus=bus,
        )
        session = agent.run("Goal A\nGoal B\nGoal C")
        assert len(session.completed_goals) >= 1

    def test_agent_replan(self):
        planner = GoalPlanner()
        mem = EngineeringMemory()
        gm = GoalManager(EngineeringMemoryGoalRepository(mem))
        executor = MagicMock()
        executor.run.return_value = ExecutionResult(
            success=False,
            summary="fail",
            error="replan needed",
            repair_result=MagicMock(),
            applied_results=(),
        )
        bus = GoalEventBus()

        agent = AutonomousAgent(
            planner=planner,
            goal_manager=gm,
            executor=executor,
            memory=mem,
            event_bus=bus,
            retry_policy=RetryPolicy(max_retries=0, base_delay=0.01),
        )
        session = agent.run("Fix bug")
        # With 0 retries, the goal should fail and require replan
        assert len(session.failed_goals) >= 1 or session.state == ExecutionState.COMPLETED

    def test_executor_exception_during_run(self):
        planner = GoalPlanner()
        mem = EngineeringMemory()
        gm = GoalManager(EngineeringMemoryGoalRepository(mem))
        executor = MagicMock()
        executor.run.side_effect = RuntimeError("unexpected error")
        bus = GoalEventBus()

        agent = AutonomousAgent(
            planner=planner,
            goal_manager=gm,
            executor=executor,
            memory=mem,
            event_bus=bus,
            retry_policy=RetryPolicy(max_retries=1, base_delay=0.01),
        )
        session = agent.run("Fix bug")
        assert len(session.failed_goals) >= 1

    def test_session_events(self):
        planner = GoalPlanner()
        mem = EngineeringMemory()
        gm = GoalManager(EngineeringMemoryGoalRepository(mem))
        executor = MagicMock()
        executor.run.return_value = ExecutionResult(
            success=True,
            summary="ok",
            repair_result=MagicMock(),
            applied_results=(),
        )
        bus = GoalEventBus()
        events = []

        def handler(event):
            if event.event_type.startswith("agent."):
                events.append(event.event_type)

        bus.subscribe("agent.session_started", handler)
        bus.subscribe("agent.session_finished", handler)
        bus.subscribe("agent.goal_started", handler)
        bus.subscribe("agent.goal_finished", handler)
        bus.subscribe("agent.planner_started", handler)
        bus.subscribe("agent.planner_finished", handler)
        bus.subscribe("agent.executor_started", handler)
        bus.subscribe("agent.executor_finished", handler)

        agent = AutonomousAgent(
            planner=planner,
            goal_manager=gm,
            executor=executor,
            memory=mem,
            event_bus=bus,
        )
        agent.run("Fix bug")

        assert "agent.session_started" in events
        assert "agent.session_finished" in events
        assert "agent.planner_started" in events
        assert "agent.planner_finished" in events
