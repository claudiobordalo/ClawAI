from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from clawai.executor import ExecutionRequest
from clawai.goals import Goal, PlanningContext

from .agent_context import AgentContext
from .execution_events import (
    COGNITIVE_DECISION,
    COGNITIVE_REVIEW,
    EXECUTOR_FINISHED,
    EXECUTOR_STARTED,
    GOAL_FAILED,
    GOAL_FINISHED,
    GOAL_RETRIED,
    GOAL_STARTED,
    PLANNER_FINISHED,
    PLANNER_STARTED,
    REPLAN_COMPLETED,
    REPLAN_STARTED,
    SESSION_CANCELLED,
    SESSION_FINISHED,
    SESSION_STARTED,
)
from .execution_session import ExecutionSession
from .abstract_agent_loop import AbstractAgentLoop
from .execution_state import ExecutionState
from .goal_execution_result import GoalExecutionResult
from .metrics import AgentMetrics

logger = logging.getLogger("clawai.agent")


@dataclass(frozen=True, slots=True)
class IterationRecord:
    iteration: int
    llm_response: str | None = None
    action: dict[str, Any] | None = None
    execution_result: dict[str, Any] | None = None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class LoopResult:
    success: bool
    iterations: int = 0
    final_response: str | None = None
    last_action: dict[str, Any] | None = None
    history: tuple[IterationRecord, ...] = ()
    error: str | None = None


class AgentLoop(AbstractAgentLoop):
    def __init__(self, context: AgentContext) -> None:
        self._context = context
        self._paused = False
        self._cancelled = False
        self._metrics = AgentMetrics()

    @property
    def context(self) -> AgentContext:
        return self._context

    @property
    def metrics(self) -> AgentMetrics:
        return self._metrics

    def cancel(self) -> None:
        self._cancelled = True

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def stop(self) -> None:
        self._cancelled = True

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled

    def run(self, objective: str) -> ExecutionSession:
        session_id = str(uuid.uuid4())
        session = ExecutionSession(id=session_id, objective=objective)
        self._context.session = session
        bus = self._context.event_bus
        gm = self._context.goal_manager
        planner = self._context.planner
        memory = self._context.memory
        checkpoint = self._context.checkpoint_manager

        session.state = ExecutionState.RUNNING
        session.started_at = datetime.now(timezone.utc)
        bus.emit(SESSION_STARTED, session_id, objective=objective)

        try:
            bus.emit(PLANNER_STARTED, session_id, objective=objective)
            ctx = PlanningContext(
                objective=objective,
                engineering_memory=memory,
                previous_attempts=0,
            )
            backlog = planner.plan(objective, context=ctx)
            bus.emit(PLANNER_FINISHED, session_id, goal_count=len(backlog.goals))

            if not backlog.goals:
                session.state = ExecutionState.COMPLETED
                session.finished_at = datetime.now(timezone.utc)
                bus.emit(SESSION_FINISHED, session_id, state="completed")
                return session

            for goal in backlog.goals:
                if self._cancelled:
                    session.state = ExecutionState.CANCELLED
                    bus.emit(SESSION_CANCELLED, session_id)
                    break

                while self._paused and not self._cancelled:
                    time.sleep(0.1)

                if self._cancelled:
                    session.state = ExecutionState.CANCELLED
                    bus.emit(SESSION_CANCELLED, session_id)
                    break

                if (
                    self._context.config.max_goals > 0
                    and len(session.completed_goals) + len(session.failed_goals)
                    >= self._context.config.max_goals
                ):
                    logger.info(
                        "Max goals reached, stopping loop",
                        extra={"max": self._context.config.max_goals},
                    )
                    break

                gm.add_goal(goal)
                gm.create_backlog()

                result = self._execute_goal(goal, session)

                if result is None:
                    continue

                session.results.append(result)

                if checkpoint:
                    checkpoint.save(session, backlog)

                if result.requires_replan and self._context.config.auto_replan:
                    self._metrics.replan_count += 1
                    session.state = ExecutionState.REPLANNING
                    bus.emit(PLANNER_STARTED, session_id, reason="replan")
                    bus.emit(
                        REPLAN_STARTED,
                        objective,
                        previous_attempts=self._metrics.replan_count,
                    )
                    ctx = PlanningContext(
                        objective=objective,
                        engineering_memory=memory,
                        repository_state=list(backlog.goals),
                        previous_attempts=self._metrics.replan_count,
                    )
                    backlog = planner.plan(objective, context=ctx)
                    bus.emit(
                        PLANNER_FINISHED,
                        session_id,
                        goal_count=len(backlog.goals),
                    )
                    bus.emit(
                        REPLAN_COMPLETED,
                        objective,
                        goal_count=len(backlog.goals),
                    )

            if not self._cancelled:
                session.state = ExecutionState.COMPLETED
        except Exception as e:
            logger.error("Agent loop failed", extra={"error": str(e)})
            session.state = ExecutionState.FAILED

        session.finished_at = datetime.now(timezone.utc)
        bus.emit(
            SESSION_FINISHED,
            session_id,
            state=session.state.value,
            duration=session.metadata.get("total_duration", 0),
        )
        self._context.session = session
        return session

    def _execute_goal(
        self,
        goal: Goal,
        session: ExecutionSession,
    ) -> Optional[GoalExecutionResult]:
        ctx = self._context
        bus = ctx.event_bus
        gm = ctx.goal_manager
        executor = ctx.executor
        retry = ctx.retry_policy
        reasoning_engine = ctx.reasoning_engine

        session.current_goal = goal.id
        bus.emit(GOAL_STARTED, goal.id, title=goal.title)
        logger.info("Executing goal", extra={"goal_id": goal.id, "title": goal.title})

        start_time = time.perf_counter()
        attempt = 0
        max_retries = retry.max_retries

        def attempt_execution() -> Any:
            bus.emit(EXECUTOR_STARTED, goal.id, title=goal.title)
            req = ExecutionRequest(
                project_root=Path("."),
                objective=goal.title,
                target_query=goal.title,
                instructions=goal.description,
                max_iterations=3,
            )
            exec_result: Any = executor.run(req)
            bus.emit(
                EXECUTOR_FINISHED,
                goal.id,
                success=getattr(exec_result, "success", False),
                title=goal.title,
            )
            return exec_result

        def _emit_cognitive_events(cognitive_result: Any) -> None:
            bus.emit(
                COGNITIVE_REVIEW,
                goal.id,
                review_result=cognitive_result.assessment.value,
            )
            bus.emit(
                COGNITIVE_DECISION,
                goal.id,
                next_action=cognitive_result.next_action,
            )

        def _build_cognitive_result(
            success: bool,
            errors: list,
            output: str,
            duration: float,
        ) -> Any:
            import time as _time

            t0 = _time.perf_counter()
            reasoning = reasoning_engine.analyze(
                goal_id=goal.id,
                goal_title=goal.title,
                success=success,
                errors=errors or None,
                output=output,
                duration=duration,
                retry_count=attempt,
            )
            t1 = _time.perf_counter()
            latency = t1 - t0
            self._metrics.cognitive_latency += latency
            self._metrics.cognitive_latencies.append(latency)
            if reasoning.confidence is not None:
                bucket = str(round(reasoning.confidence * 10) * 10)
                self._metrics.confidence_distribution[bucket] = (
                    self._metrics.confidence_distribution.get(bucket, 0) + 1
                )
            return reasoning

        while attempt <= max_retries:
            if self._cancelled:
                return None

            try:
                exec_result = attempt_execution()
                duration = time.perf_counter() - start_time
                self._metrics.execution_durations.append(duration)
                self._metrics.total_duration += duration

                exec_success = bool(getattr(exec_result, "success", False))
                exec_errors: list = []
                if not exec_success:
                    err = getattr(exec_result, "error", None)
                    if err:
                        exec_errors = [str(err)]
                    else:
                        exec_errors = ["execution_failed"]

                reasoning = _build_cognitive_result(
                    success=exec_success,
                    errors=exec_errors,
                    output=str(getattr(exec_result, "summary", "")),
                    duration=duration,
                )

                _emit_cognitive_events(reasoning)

                if reasoning.next_action == "continue":
                    gm.complete_goal(goal.id)
                    session.completed_goals.append(goal.id)
                    bus.emit(GOAL_FINISHED, goal.id, title=goal.title, duration=duration)
                    logger.info(
                        "Goal completed",
                        extra={
                            "goal_id": goal.id,
                            "title": goal.title,
                            "duration": duration,
                        },
                    )
                    self._metrics.goals_completed += 1
                    return GoalExecutionResult(
                        goal=goal,
                        success=True,
                        output=str(getattr(exec_result, "summary", "")),
                        duration=duration,
                        errors=[],
                        warnings=[],
                        requires_replan=False,
                        attempts=attempt + 1,
                        review_result=reasoning.assessment.value,
                        failure_category=reasoning.failure_category,
                        confidence=reasoning.confidence,
                        reasoning=reasoning.reason,
                        decision=reasoning.recommendation,
                        next_action=reasoning.next_action,
                    )

                if reasoning.should_retry and attempt < max_retries:
                    self._metrics.goals_retried += 1
                    bus.emit(
                        GOAL_RETRIED,
                        goal.id,
                        title=goal.title,
                        attempt=attempt + 1,
                        error="; ".join(exec_errors) if exec_errors else "unknown",
                    )
                    delay = retry.compute_delay(attempt)
                    time.sleep(delay)
                    attempt += 1
                    continue

                gm.fail_goal(goal.id)
                session.failed_goals.append(goal.id)
                error_str = "; ".join(exec_errors) if exec_errors else "execution_failed"
                bus.emit(GOAL_FAILED, goal.id, title=goal.title, error=error_str)
                logger.warning(
                    "Goal failed",
                    extra={
                        "goal_id": goal.id,
                        "title": goal.title,
                        "error": error_str,
                    },
                )
                self._metrics.goals_failed += 1
                return GoalExecutionResult(
                    goal=goal,
                    success=False,
                    output=str(getattr(exec_result, "summary", "")),
                    duration=duration,
                    errors=exec_errors,
                    warnings=[],
                    requires_replan=True,
                    attempts=attempt + 1,
                    review_result=reasoning.assessment.value,
                    failure_category=reasoning.failure_category,
                    confidence=reasoning.confidence,
                    reasoning=reasoning.reason,
                    decision=reasoning.recommendation,
                    next_action=reasoning.next_action,
                )

            except Exception as e:
                duration = time.perf_counter() - start_time
                self._metrics.execution_durations.append(duration)
                self._metrics.total_duration += duration
                error_str = str(e)

                reasoning = _build_cognitive_result(
                    success=False,
                    errors=[error_str],
                    output="",
                    duration=duration,
                )

                _emit_cognitive_events(reasoning)

                if (
                    reasoning.should_retry
                    and attempt < max_retries
                    and retry.is_retryable(e)
                ):
                    self._metrics.goals_retried += 1
                    bus.emit(
                        GOAL_RETRIED,
                        goal.id,
                        title=goal.title,
                        attempt=attempt + 1,
                        error=error_str,
                    )
                    delay = retry.compute_delay(attempt)
                    time.sleep(delay)
                    attempt += 1
                    continue

                gm.fail_goal(goal.id)
                session.failed_goals.append(goal.id)
                bus.emit(GOAL_FAILED, goal.id, title=goal.title, error=error_str)
                self._metrics.goals_failed += 1
                logger.error(
                    "Goal failed after exception",
                    extra={
                        "goal_id": goal.id,
                        "title": goal.title,
                        "error": error_str,
                    },
                )
                return GoalExecutionResult(
                    goal=goal,
                    success=False,
                    output="",
                    duration=duration,
                    errors=[error_str],
                    requires_replan=True,
                    attempts=attempt + 1,
                    review_result=reasoning.assessment.value,
                    failure_category=reasoning.failure_category,
                    confidence=reasoning.confidence,
                    reasoning=reasoning.reason,
                    decision=reasoning.recommendation,
                    next_action=reasoning.next_action,
                )

        raise RuntimeError("_execute_goal: unreachable")
