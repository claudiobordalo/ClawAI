# Goal System — API Reference & Extension Guide

## 1. GoalManager — Public API

```python
class GoalManager:
    def __init__(
        self,
        repository: EngineeringMemory | GoalRepository,
        event_bus: Optional[GoalEventBus] = None,
    ) -> None
```

### Constructor

| Parameter | Type | Description |
|-----------|------|-------------|
| `repository` | `EngineeringMemory \| GoalRepository` | Persistence backend. If `EngineeringMemory` is passed, wraps it in `EngineeringMemoryGoalRepository`. |
| `event_bus` | `GoalEventBus \| None` | Optional event bus; a new one is created if omitted. |

### Methods

| Method | Return | Description |
|--------|--------|-------------|
| `create_backlog()` | `GoalBacklog` | Builds a deduplicated, prioritized snapshot from repository + engineering memory. |
| `next_goal()` | `Goal \| None` | Returns first `TODO` goal from the current backlog. |
| `add_goal(goal)` | `Goal` | Saves a goal; validates uniqueness. Emits `GOAL_CREATED`. |
| `complete_goal(goal_id)` | `Goal \| None` | Transitions to `DONE`. Emits `GOAL_COMPLETED`. |
| `fail_goal(goal_id)` | `Goal \| None` | Transitions to `BLOCKED`. Emits `GOAL_COMPLETED` with `status="blocked"`. |
| `reprioritize(goal_id, priority)` | `Goal \| None` | Updates priority. Accepts `GoalPriority` or compatible `int`. |
| `find_goal(goal_id)` | `Goal \| None` | Direct lookup. |
| `remove_goal(goal_id)` | `bool` | Deletes from repository. Emits `GOAL_CANCELLED`. |
| `update_progress(goal_id, completion)` | `GoalProgress \| None` | Records progress. Auto-completes at 100%. Emits `GOAL_PROGRESS_UPDATED`. |
| `progress()` | `GoalProgress` | Aggregate completion across the backlog. |

### Events

| Event String | Metadata |
|--------------|----------|
| `goal.created` | `title`, `priority` (int) |
| `goal.completed` | `title`, optional `status: "blocked"` |
| `goal.cancelled` | `title` |
| `goal.progress_updated` | `completion`, `title` |

All events include `event_type` and `goal_id` on the `GoalEvent` dataclass.

---

## 2. GoalPlanner — API

```python
class GoalPlanner:
    def __init__(self, strategy: str | PlanningStrategy = "rule_based") -> None
    def plan(self, objective: str, context: PlanningContext | None = None) -> GoalBacklog
    def plan_to_goals(self, objective: str) -> Tuple[Goal, ...]
```

Splits an objective string by newlines, deduplicates by title, and produces deterministic UUID-based goal IDs:

- **Empty / whitespace-only input** → `()`
- **Single line** → one `Goal` with `GoalPriority.MEDIUM`
- **Multiple lines** → one `Goal` per unique line

### Extension Points

To create a custom planner, implement `PlanningStrategy`:

```python
class LLMPlanningStrategy(PlanningStrategy):
    def plan(self, context: PlanningContext) -> GoalBacklog:
        # Use an LLM to decompose objective into goals
        ...
```

Register it:

```python
PlannerFactory.register("llm", LLMPlanningStrategy)
planner = GoalPlanner(strategy="llm")
```

---

## 3. GoalRepository — Interface

```python
class GoalRepository(ABC):
    def load(self, goal_id: str) -> Optional[Goal]: ...
    def save(self, goal: Goal) -> None: ...
    def update(self, goal: Goal) -> None: ...
    def delete(self, goal_id: str) -> None: ...
    def list(self) -> Tuple[Goal, ...]: ...
```

### Built-in Implementation

| Class | Backend | Notes |
|-------|---------|-------|
| `EngineeringMemoryGoalRepository` | `EngineeringMemory` in-memory dict | Volatile; used for testing and single-session workflows |

### Custom Repository

Implement `GoalRepository` for any backend:

```python
class PostgresGoalRepository(GoalRepository):
    def save(self, goal: Goal) -> None:
        db.execute("INSERT INTO goals ...", ...)
    # ... implement remaining methods
```

### Extension Point — Reviewer

A Reviewer is a class that evaluates goal state and suggests transitions. It is **not** part of the core system; plug it in at the orchestration layer:

```python
class GoalReviewer:
    def review(self, goal: Goal, context: dict) -> GoalStatus:
        # Analyze goal and return suggested status
        ...
```

Integrate by wrapping `GoalManager` or calling `review()` before transitions.

---

## 4. GoalDependencyGraph — API

```python
class GoalDependencyGraph:
    def __init__(self, goals: Tuple[Goal, ...]) -> None
    def has_cycle(self) -> bool
    def find_cycle(self) -> List[str]
    def topological_sort(self) -> Tuple[Goal, ...]
    def get_unblocked(self) -> Tuple[Goal, ...]
    def get_dependents(self, goal_id: str) -> Tuple[str, ...]
    def dependency_depth(self, goal_id: str) -> int
```

See [`docs/planner.md`](../planner.md) for details.

## 5. GoalPrioritizer — API

```python
class GoalPrioritizer:
    def __init__(self, graph: GoalDependencyGraph) -> None
    def prioritize(self, goals: Tuple[Goal, ...]) -> Tuple[Goal, ...]
```

Deterministic sort: priority → dependency depth → impact → risk → input order.

## 6. GoalDecomposer — API

```python
class GoalDecomposer:
    def decompose(self, objective: str, goal_id_prefix: str = "plan") -> Tuple[Goal, ...]
```

Splits by newlines, "and" conjunctions, bullet/numbered lists. Infers `estimated_complexity` and `tags`.

## 7. PlanningStrategy / RuleBasedPlanningStrategy — API

```python
class PlanningStrategy(ABC):
    @abstractmethod
    def plan(self, context: PlanningContext) -> GoalBacklog: ...

class RuleBasedPlanningStrategy(PlanningStrategy):
    def plan(self, context: PlanningContext) -> GoalBacklog: ...
```

## 8. PlannerFactory — API

```python
class PlannerFactory:
    @classmethod
    def create(cls, strategy_name: str = "rule_based") -> PlanningStrategy
    @classmethod
    def register(cls, name: str, strategy_cls: type[PlanningStrategy]) -> None
```

## 9. GoalEventBus — API

```python
class GoalEventBus:
    def subscribe(self, event_type: str, handler: Callable) -> None
    def publish(self, event: GoalEvent) -> None
    def emit(self, event_type: str, goal_id: str, **metadata) -> GoalEvent
    def history(self) -> Tuple[GoalEvent, ...]
    def clear(self) -> None
```

### Usage Example

```python
bus = GoalEventBus()

def on_completed(event: GoalEvent) -> None:
    print(f"Goal {event.goal_id} completed: {event.metadata}")

bus.subscribe("goal.completed", on_completed)
```

---

## 10. GoalValidator — API

```python
class ValidationError(Exception):
    errors: List[str]

def validate_goal(
    goal: Goal,
    existing_goals: Sequence[Goal] = (),
) -> None | raise ValidationError
```

Checks performed:
- Non-empty `id`, `title`, `success_criteria`
- `id` matches `^[a-zA-Z0-9_\-\.]{1,128}$`
- Priority is a valid `GoalPriority` or convertible int
- No duplicate titles among `existing_goals`

---

## 11. Data Classes

### GoalProgress

```python
@dataclass(frozen=True)
class GoalProgress:
    goal: Optional[Goal]
    completion: float              # 0.0 – 100.0
    completed_items: tuple[str, ...]
    remaining_items: tuple[str, ...]
    summary: str

    # Properties
    is_completed: bool             # completion >= 100.0
    remaining_percentage: float    # max(0, 100 - completion)
    completed_percentage: float    # completion
```

Validates: no NaN, no Inf, range [0, 100].

### GoalBacklog

```python
@dataclass(frozen=True)
class GoalBacklog:
    goals: Tuple[Goal, ...]
    created_at: Optional[datetime]
    summary: str
```

### GoalEvent

```python
@dataclass(frozen=True)
class GoalEvent:
    timestamp: datetime
    event_type: str
    goal_id: str
    metadata: Dict[str, Any]
```

---

## 12. Enums

### GoalStatus

| Member | Value | Legacy Alias |
|--------|-------|-------------|
| `TODO` | `"todo"` | `GOAL_STATUS_PENDING` |
| `IN_PROGRESS` | `"in_progress"` | `GOAL_STATUS_RUNNING` |
| `BLOCKED` | `"blocked"` | `GOAL_STATUS_FAILED` |
| `DONE` | `"done"` | `GOAL_STATUS_COMPLETED` |
| `CANCELLED` | `"cancelled"` | `GOAL_STATUS_CANCELLED` |

`normalize_status(raw)` accepts: `GoalStatus` → identity; legacy strings (`"pending"`, `"completed"`, etc.) → mapped; value strings (`"todo"`, `"done"`) → value lookup; uppercase names (`"TODO"`, `"DONE"`) → name lookup.

### GoalPriority

| Member | Value | Legacy Alias |
|--------|-------|-------------|
| `CRITICAL` | `0` | `GOAL_PRIORITY_CRITICAL` |
| `HIGH` | `1` | `GOAL_PRIORITY_HIGH` |
| `MEDIUM` | `2` | `GOAL_PRIORITY_MEDIUM` |
| `LOW` | `3` | `GOAL_PRIORITY_LOW` |
| `OPTIONAL` | `4` | `GOAL_PRIORITY_OPTIONAL` |

`str()` returns lowercase name: `"critical"`, `"high"`, etc.

---

## 13. Extension Point Summary

| Point | Mechanism | Example |
|-------|-----------|---------|
| Planner | Duck-typed `.plan()` method | `LLMGoalPlanner`, `GoalPlanner` subclass |
| Repository | Implement `GoalRepository` ABC | `PostgresGoalRepository`, `RedisGoalRepository` |
| Reviewer | Orchestration-layer wrapper | `GoalReviewer` class read before transitions |
| Event handlers | `GoalEventBus.subscribe()` | Logging, metrics, notifications |
| Backlog merge | Override `_merge_with_memory_goals()` | Custom memory → goal derivation logic |

---

## 14. Dependency Graph

```
GoalBacklog
    └── Goal
GoalProgress
    └── Goal
GoalPlanner
    └── Goal
GoalRepository (ABC)
    ├── EngineeringMemoryGoalRepository
    └── (custom)
GoalValidator
    └── Goal, GoalPriority
GoalEventBus
    └── GoalEvent
GoalManager
    ├── GoalRepository
    ├── GoalEventBus
    ├── Goal, GoalBacklog, GoalProgress
    └── EngineeringMemory (optional, for backlog merge)
AutonomousExecutor
    └── (no dependency on goal system)
```

## 15. Test Layout

| File | Tests | Scope |
|------|-------|-------|
| `test_goal.py` | 22 | Domain entity, enums, normalization, backward compat |
| `test_goal_progress.py` | 17 | NaN/Inf, range, derived properties |
| `test_goal_backlog.py` | 9 | Defaults, 1000 goals, unicode |
| `test_goal_manager.py` | 48 | CRUD, events, concurrency, 1000 goals, backward compat |
| `test_goal_planner.py` | 7 | Empty, multiline, dedup, determinism |
| `test_goal_repository.py` | 10 | CRUD, sorting, determinism, 1000 goals |
| `test_goal_events.py` | 11 | Publish/emit/history/clear/multiple subs |
| `test_goal_validator.py` | 8 | Duplicate title, validation error list |
| `test_goal_coverage.py` | 21 | Edge-case coverage boost |
| `test_autonomous_executor.py` | 13 | No goal_manager references |
