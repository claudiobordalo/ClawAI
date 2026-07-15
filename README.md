# ClawAI

Autonomous coding agent with self-repair, goal-driven planning, and engineering memory.

## Architecture

```
clawai/
├── agent/           # Autonomous agent orchestration (Sprint 4)
│   ├── autonomous_agent.py
│   ├── agent_loop.py
│   ├── agent_context.py
│   ├── execution_session.py
│   ├── execution_state.py
│   ├── execution_events.py
│   ├── goal_execution_result.py
│   ├── retry_policy.py
│   ├── checkpoint_manager.py
│   └── metrics.py
├── goals/           # Goal subsystem — deterministic planning & tracking
│   ├── goal.py
│   ├── goal_manager.py
│   ├── goal_planner.py
│   ├── goal_events.py
│   ├── goal_validator.py
│   ├── goal_status.py
│   ├── goal_priority.py
│   ├── goal_complexity.py
│   ├── goal_progress.py
│   ├── goal_backlog.py
│   ├── goal_repository.py
│   ├── goal_dependency_graph.py
│   ├── goal_prioritizer.py
│   ├── goal_decomposer.py
│   ├── planning_context.py
│   ├── planning_strategy.py
│   ├── planner_factory.py
│   └── engineering_memory_goal_repository.py
├── executor/        # Task execution engine
├── editor/          # Code editing operations
├── engineering/     # Engineering memory & records
├── tracing/         # Execution trace & observability
├── testing/         # Test runner & result tracking
├── selfrepair/      # Self-repair engine
├── verification/    # Self-verification
└── development/     # Development pipeline orchestration
```

## Local providers

ClawAI can run against local OpenAI-compatible servers.

To use LM Studio, set:

```bash
CLAWAI_DEFAULT_PROVIDER=lmstudio
LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1
LMSTUDIO_API_KEY=lm-studio
LMSTUDIO_MODEL=<your-loaded-model>
```

The provider can also list available local models through the backend router when the server supports `/v1/models`.

## Goal System

The Goal subsystem provides an LLM-free, event-driven framework for defining, planning, tracking, and completing goals. See:

- [`docs/architecture/goals.md`](docs/architecture/goals.md) — Architecture overview & Mermaid diagrams
- [`docs/architecture/goal_system.md`](docs/architecture/goal_system.md) — Full API reference & extension guide
- [`docs/planner.md`](docs/planner.md) — Sprint 3: Planner system, decomposition, dependency graph, prioritization
- [`docs/agent.md`](docs/agent.md) — Sprint 4: Autonomous agent loop, sessions, retry, checkpoints

### Quick Start

```python
from clawai.goals import (
    GoalManager, GoalPlanner, GoalBacklog,
    GoalStatus, GoalPriority, Goal,
    PlanningContext,
)

# Plan using the new strategy architecture
planner = GoalPlanner(strategy="rule_based")
ctx = PlanningContext(objective="Fix auth bug\nAdd tests\nDeploy")
backlog = planner.plan("Fix auth bug\nAdd tests\nDeploy", context=ctx)

# Orchestrate
mgr = GoalManager(repository=EngineeringMemory())
for g in backlog.goals:
    mgr.add_goal(g)

# Track
mgr.create_backlog()
goal = mgr.next_goal()
mgr.complete_goal(goal.id)

# Aggregate
progress = mgr.progress()
print(progress.summary)
```

## Tests

```bash
pytest                            # Full suite (573+ tests)
pytest tests/unit/test_goal*.py   # Goal subsystem (168 tests)
pytest --cov=clawai.goals         # Coverage > 95%
```

## Validation

```bash
ruff check .
mypy clawai/
```

## Technical Backlog

See [`docs/technical_backlog.md`](docs/technical_backlog.md) for the roadmap.
