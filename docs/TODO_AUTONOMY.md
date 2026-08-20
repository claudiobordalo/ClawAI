# ClawAI Autonomy Roadmap — Todo & Gap Analysis

> Generated from repository evidence. Identifies everything preventing ClawAI from becoming a fully autonomous software engineering agent. Only describes what actually exists (or doesn't exist) in the codebase.

---

## Critical Blockers

These are issues that must be resolved before any meaningful autonomous operation is possible.

### 1.0 Dual Cognition Pipelines — Neither Works End-to-End

**Priority**: Critical  
**Complexity**: Medium  
**Impacted modules**: `clawai/chat/chat_service.py`, `clawai/cognition/pipeline.py`, `clawai/chat/chat_service.py.CognitionPipeline`, `clawai/cognition/pipeline.py.CognitionPipeline`

**Evidence**:
- Two separate `CognitionPipeline` classes exist:
  1. `clawai/chat/chat_service.py` (line 66) — Simpler flow: intent classifier → agent or direct model call. This is the one actually used by `ChatService`.
  2. `clawai/cognition/pipeline.py` (line 21) — More complex multi-stage pipeline: supervisor → planner → debate → judge → synthesis. This one is **not used** by any production code path.
- `ChatService.__init__` (chat_service.py line 172-176) creates `CognitionPipeline` from `chat_service.py`, not from `cognition/pipeline.py`.
- The sophisticated pipeline in `cognition/pipeline.py` is orphaned code with no callers.

**Gap**: The multi-stage reasoning pipeline (supervisor, planner, debate, judge) exists but is disconnected from the actual chat flow. The simple pipeline lacks proper multi-step reasoning.

**Suggested order**: 1

### 2.0 Empty Agent Subpackages — Planned Refactoring Never Completed

**Priority**: Critical  
**Complexity**: Large  
**Impacted modules**: `clawai/agents/base/`, `clawai/agents/factory/`, `clawai/agents/implementations/`, `clawai/agents/manager/`, `clawai/agents/registry/`

**Evidence** (file sizes confirm emptiness):
```
clawai/agents/base/agent.py              → 0 bytes
clawai/agents/factory/factory.py          → 0 bytes
clawai/agents/implementations/coding.py   → 0 bytes
clawai/agents/implementations/memory.py   → 0 bytes
clawai/agents/implementations/planner.py  → 0 bytes
clawai/agents/implementations/review.py   → 0 bytes
clawai/agents/manager/manager.py          → 0 bytes
clawai/agents/registry/registry.py        → 0 bytes
```

**Gap**: Five subpackages were scaffolded but never implemented. Meanwhile, concrete agents (`agent.py`, `patch_agent.py`, `code_agent.py`, etc.) live directly in the `agents/` directory without a proper factory, registry, or base class hierarchy.

**Suggested order**: 2

### 3.0 Two Memory Systems — No Unified Strategy

**Priority**: Critical  
**Complexity**: Medium  
**Impacted modules**: `clawai/memory/memory.py`, `clawai/memory/memory_manager.py`, `clawai/bootstrap.py`, `clawai/agents/agent.py`, `clawai/chat/chat_service.py`

**Evidence**:
- `clawai/memory/memory.py` — JSON-file-based `Memory` singleton. Used by `Agent.ask()` (agents/agent.py line 43) and `ChatService._finalize_answer()` (chat/chat_service.py line 151). Stores data in `.clawai/memory/*.json`. Simple keyword search — no embeddings.
- `clawai/memory/memory_manager.py` — ChromaDB-based `MemoryManager`. Registered in the DI container in `bootstrap.py` (line 49) but never resolved/used by any actual agent code.
- `clawai/bootstrap.py` creates `MemoryManager` with `OllamaEmbeddingService` and `ChromaVectorStore`, registers it in `ServiceContainer` — but agents bypass the container entirely.

**Gap**: Two parallel memory implementations with no bridge between them. The JSON memory is actually used but is primitive (keyword search only). The ChromaDB memory is sophisticated (vectors, embeddings) but unused by any agent.

**Suggested order**: 3

### 4.0 Bootstrap vs Application — Inconsistent Initialization

**Priority**: Critical  
**Complexity**: Small  
**Impacted modules**: `clawai/bootstrap.py`, `clawai/application/application.py`, `main.py`, `api.py`

**Evidence**:
- `clawai/bootstrap.py` creates a `ServiceContainer` with `StorageManager`, `ProjectManager`, `Workspace`, `MemoryManager`, `AIManager`. This is called from `main.py` (CLI mode).
- `clawai/application/application.py` creates a completely different initialization: registers providers directly on `ProviderFactory`, creates `ModelRouter` and `PromptEngine` without using `ServiceContainer`. This is imported by `api.py` via `from clawai.application import Application`.
- `api.py` does NOT call `bootstrap.build_container()` — it creates its own `Application` instance that bypasses the DI container entirely.

**Gap**: Two separate initialization paths exist. `main.py` uses the DI container but `api.py` doesn't. Services registered in the container are never used by the API server.

**Suggested order**: 4

---

## Missing Infrastructure

### 5.0 No Proper Dependency Injection Usage

**Priority**: High  
**Complexity**: Medium  
**Impacted modules**: `clawai/core/container/service_container.py`, `clawai/bootstrap.py`, `clawai/application/application.py`, all service consumers

**Evidence**:
- `ServiceContainer` works (40 lines, stores `dict[type, instance]`) but **nothing resolves from it after bootstrap**.
- `Agent`, `ChatService`, `AgentRuntime`, `AutoImplementService`, `EvolutionEngine` all instantiate their dependencies directly with `self.router = AIRouter()` or similar constructors.
- No service is wired through the container end-to-end.

**Gap**: The DI container exists but is not actually used for dependency injection. Every major service creates its own dependencies internally.

**Suggested order**: 5

### 6.0 No Configuration System Actually Applied

**Priority**: High  
**Complexity**: Small  
**Impacted modules**: `clawai/core/config/settings.py`, `clawai/core/config/loader.py`, `configs/config.yaml`

**Evidence**:
- `Settings` dataclass (settings.py) has defaults for models, paths, resources.
- `apply_config()` method accepts a `dict[str, Any]` but is **never called** from any production code path.
- `configs/config.yaml` exists with model names (qwen2.5-coder, qwen3, deepseek-r1) but is never loaded at startup.
- `ModelRouter.__init__` creates `Settings()` with defaults only — config.yaml is ignored.

**Gap**: Configuration values exist in YAML but are never loaded. The system uses hardcoded Python defaults, making model configuration impossible without code changes.

**Suggested order**: 6

### 7.0 No Process Isolation or Sandboxing

**Priority**: High  
**Complexity**: Large  
**Impacted modules**: `clawai/autopilot/auto_implement_runtime.py`, `clawai/execution/action_executor.py`, `clawai/tools/implementations/terminal.py`

**Evidence**:
- `AutoImplementService._run_tests()` (auto_implement_runtime.py line 913) runs arbitrary shell commands with `subprocess.run(command, shell=True, cwd=ROOT, timeout=1800)` — no sandbox, no permission model, full filesystem access.
- `_apply_changes()` writes files directly to the repository with `target.write_text(content, encoding="utf-8")` — no review step before writing.
- No evidence of read-only mode, dry-run capability, or approval gates for file modifications.

**Gap**: An autonomous agent with write access to the filesystem and shell execution has no safety mechanisms. A single bad LLM response could corrupt the entire repository.

**Suggested order**: 7

---

## Missing Abstractions

### 8.0 No Unified Tool Abstraction

**Priority**: High  
**Complexity**: Medium  
**Impacted modules**: `clawai/tools/`, `clawai/tools/base/tool.py`, `clawai/tools/registry/`, `clawai/tools/manager/`

**Evidence**:
- Multiple overlapping tool abstractions exist:
  - `clawai/tools/base/tool.py` — `Tool` base class
  - `clawai/tools/registry.py` — `ToolRegistry` singleton (different from `clawai/tools/registry/`)
  - `clawai/tools/tool_registry.py` — Another registry class
  - `clawai/tools/manager/manager.py` — Yet another manager
  - `clawai/tools/registry/registry.py` — 0 bytes, empty
  - `clawai/tools/manager/manager.py` — 0 bytes, empty
- `AgentRuntime._build_default_tool_executor()` creates its own `ToolRegistry` with only `FilesystemTool` — ignoring other tool implementations.

**Gap**: 3+ tool registry/manager abstractions with no clear hierarchy. Two are empty. The one actually used by AgentRuntime only registers a single filesystem tool.

**Suggested order**: 8

### 9.0 No Agent Registry or Factory

**Priority**: High  
**Complexity**: Medium  
**Impacted modules**: `clawai/agents/registry/`, `clawai/agents/factory/`, `clawai/dispatcher/`

**Evidence**:
- Agent registry is empty (0 bytes).
- Agent factory is empty (0 bytes).
- `dispatcher/agent_registry.py` exists but the corresponding registry subpackage is empty.
- Individual agents (`CodeAgent`, `PatchAgent`, `ReflectionAgent`, etc.) are instantiated manually without any registry or factory.

**Gap**: No centralized way to discover, instantiate, or route between agent types. New agents cannot be registered without code changes.

**Suggested order**: 9

### 10.0 No Provider Abstraction for Embeddings

**Priority**: Medium  
**Complexity**: Small  
**Impacted modules**: `clawai/memory/embeddings/`, `clawai/memory/providers/ollama_embedding_service.py`

**Evidence**:
- `EmbeddingService` base class exists in `embeddings/embedding_service.py`.
- Only one implementation: `OllamaEmbeddingService` in `providers/ollama_embedding_service.py`.
- No factory or registry for embedding providers.
- The base `Memory` (JSON) doesn't use embeddings at all.

**Gap**: Embedding providers are not pluggable. Switching from Ollama embeddings to another provider requires code changes.

**Suggested order**: 10

---

## Missing Memory

### 11.0 No Cross-Session Memory Persistence

**Priority**: High  
**Complexity**: Medium  
**Impacted modules**: `clawai/memory/memory.py`, `clawai/memory/memory_manager.py`, `clawai/chat/chat_service.py`

**Evidence**:
- JSON memory stores by category (`general`, etc.) but has no cross-session retrieval mechanism beyond keyword matching.
- ChromaDB memory has vector search but is unused.
- `ChatService` only saves memories marked with `<MEMORY>` tags — no automatic learning from conversation patterns.
- No memory consolidation, deduplication, or importance scoring.

**Gap**: The agent cannot effectively recall past learnings across sessions. The JSON memory is too primitive (keyword-only), and the ChromaDB memory is unused.

**Suggested order**: 11

### 12.0 No Long-Term Learning from Execution Outcomes

**Priority**: High  
**Complexity**: Large  
**Impacted modules**: `clawai/evolution/engine.py`, `clawai/intelligence/memory.py`, `clawai/autopilot/auto_implement_runtime.py`

**Evidence**:
- `EvolutionEngine` scans for TODOs/conflicts but stores results in `semantic_memory` via `IntelligenceOrchestrator.learn_from_execution()` — however, this learning is **never read back** to influence future behavior.
- `AutoImplementService` does not consult past execution history when selecting files or generating plans.
- The `SemanticMemory` in `clawai/intelligence/memory.py` is used by `ToolBroker.search_memory()` but results only affect tool recommendation, not code generation quality.

**Gap**: Past successes and failures are recorded but never used to improve future code generation or task planning.

**Suggested order**: 12

### 13.0 No Conversation History Tracking

**Priority**: Medium  
**Complexity**: Small  
**Impacted modules**: `clawai/memory/conversation_memory.py`, `clawai/chat/chat_service.py`

**Evidence**:
- `clawai/memory/conversation_memory.py` exists but `ChatService` does not maintain conversation history between calls.
- Each `POST /api/chat` is stateless — no context from previous messages is carried forward.
- The chat endpoint has no notion of conversation ID or session.

**Gap**: Multi-turn conversations are not supported. Each chat request is isolated.

**Suggested order**: 13

---

## Missing Tooling

### 14.0 AgentRuntime Only Has Filesystem Tools

**Priority**: Critical  
**Complexity**: Small  
**Impacted modules**: `clawai/autonomy/agent_runtime.py`, `clawai/tools/implementations/`

**Evidence**:
- `AgentRuntime._build_default_tool_executor()` (agent_runtime.py line 267) creates a `ToolRegistry` and registers only `FilesystemTool`.
- Tool implementations exist for: `filesystem.py`, `git.py`, `python.py`, `search.py`, `terminal.py` — but none are registered in the runtime.
- `AgentRuntime._available_tools_summary()` would return only `[{"name": "filesystem", "provider": "local", "description": ""}]`.

**Gap**: The autonomous agent runtime has access to only one tool (filesystem read/write). No git, search, terminal, or code execution tools are available during autonomous operation.

**Suggested order**: 14

### 15.0 Composio Integration Not Wired to Agent Loop

**Priority**: High  
**Complexity**: Medium  
**Impacted modules**: `clawai/integrations/composio/`, `clawai/tools/registry.py`, `clawai/autonomy/agent_runtime.py`

**Evidence**:
- `ComposioService` exists (composio_service.py) and is registered in `ToolRegistry` as "composio".
- But `AgentRuntime` creates its own `ToolRegistry` in `_build_default_tool_executor()` — a **different instance** that does NOT include Composio tools.
- `ToolBroker.discover_tools()` (intelligence/broker.py line 42) merges native and Composio tools — but this is used for analysis/recommendation, not for actual execution.

**Gap**: Composio integration works at the registry level but is disconnected from the actual agent runtime. Tools are discovered but not available during execution.

**Suggested order**: 15

### 16.0 No Web Search or External Knowledge Access

**Priority**: Medium  
**Complexity**: Small  
**Impacted modules**: `clawai/web/web_search.py`, `clawai/search/search_engine.py`

**Evidence**:
- `clawai/web/web_search.py` exists but is never integrated into any agent flow.
- `ChatService` and `CognitionPipeline` do not call web search.
- The `IntentClassifier` never routes to web search.

**Gap**: The agent cannot access the internet for current information, documentation, or dependencies.

**Suggested order**: 16

---

## Missing Evaluation

### 17.0 No Integration Tests Exist

**Priority**: High  
**Complexity**: Large  
**Impacted modules**: `tests/integration/`

**Evidence**:
- `tests/integration/__init__.py` exists but contains only a blank line (2 bytes).
- No integration tests exist for any module.
- `clawai/api/test_dummy.py` exists but contains no meaningful tests.

**Gap**: There is no test coverage for how components interact. The agent loop, auto-implement pipeline, evolution engine, and cognition pipeline have zero integration tests.

**Suggested order**: 17

### 18.0 No End-to-End Tests

**Priority**: High  
**Complexity**: Large  
**Impacted modules**: `tests/e2e/`

**Evidence**:
- `tests/e2e/__init__.py` exists but contains only a blank line (2 bytes).
- No E2E tests exist.

**Gap**: The full system (API → agent → tools → verification) has never been tested as a whole.

**Suggested order**: 18

### 19.0 Verify Script Only Checks Compilation

**Priority**: Medium  
**Complexity**: Small  
**Impacted modules**: `verify.py`

**Evidence**:
- `verify.py` (613 lines) runs: Python compilation check, frontend build, pytest (unit tests only), and API endpoint tests.
- API tests use `TestClient` with `unittest.mock.patch` — no real LLM is called.
- No benchmark, no regression test suite, no performance measurement.

**Gap**: "Verification" only confirms the code compiles and unit tests pass. It does not verify actual agent behavior, response quality, or task completion.

**Suggested order**: 19

### 20.0 No Performance or Quality Benchmarks

**Priority**: Low  
**Complexity**: Medium  
**Impacted modules**: (nonexistent)

**Evidence**:
- No benchmark suite exists anywhere in the repository.
- No metrics for task completion rate, iteration count, token usage, or response quality.
- `LLMCallMetrics` exists (autonomy/llm_metrics.py) but records are only used within a single `AgentRuntime.run()` call — no persistent benchmarks.

**Gap**: There is no way to measure whether the agent is improving over time.

**Suggested order**: 20

---

## Missing Planning

### 21.0 No Hierarchical Task Decomposition

**Priority**: High  
**Complexity**: Large  
**Impacted modules**: `clawai/goals/`, `clawai/agent/agent_loop.py`

**Evidence**:
- `GoalManager` and `Goal` classes exist with backlog, priority, status — but goals are treated as flat lists.
- `GoalDecomposer` exists but is not integrated into the agent loop.
- `AgentLoop.run()` (agent_loop.py line 91) iterates goals sequentially — no parallel execution, no dependency resolution beyond ordering.
- `GoalDependencyGraph` exists but has no evidence of being used to resolve inter-goal dependencies.

**Gap**: Planning infrastructure exists but is not connected. Goals are executed sequentially without decomposition, parallelization, or dependency management.

**Suggested order**: 21

### 22.0 No Plan Verification Before Execution

**Priority**: High  
**Complexity**: Medium  
**Impacted modules**: `clawai/autonomy/planner.py`, `clawai/agent/agent_loop.py`, `clawai/goals/goal_planner.py`

**Evidence**:
- In `AgentLoop`, the planner generates a goal backlog, then each goal is immediately executed — no human approval step, no simulated dry-run, no cost estimation.
- `AutoImplementService._parse_plan()` parses JSON from the LLM and immediately applies changes — no intermediate verification.
- `GoalValidator` exists but validates goal structure (title/description required), not plan correctness.

**Gap**: Plans are generated and executed without any verification step between "what the LLM proposed" and "what gets applied to the filesystem."

**Suggested order**: 22

### 23.0 No Resource-Aware Scheduling

**Priority**: Medium  
**Complexity**: Small  
**Impacted modules**: `clawai/resources/manager.py`, `clawai/core/config/settings.py`

**Evidence**:
- `ResourceManager` exists but is not integrated with the agent loop or evolution engine.
- `Settings` has resource thresholds (cpu_busy_percent, ram_busy_percent, disk_busy_percent) and `critical_processes` (gta5.exe, dofus.exe, blender.exe, etc.) — but nothing reads or enforces these thresholds during execution.

**Gap**: The system can detect resource pressure but does not adapt scheduling or throttle execution based on it.

**Suggested order**: 23

---

## Missing Safety

### 24.0 No Approval Gates for File Changes

**Priority**: Critical  
**Complexity**: Small  
**Impacted modules**: `clawai/autopilot/auto_implement_runtime.py`, `clawai/agents/patch_applier.py`

**Evidence**:
- `AutoImplementService._apply_changes()` writes files directly with no confirmation step.
- No "dry-run" mode exists for any code path that modifies files.
- The frontend has no approval UI for pending changes.
- `BackupManager` exists (agents/backup_manager.py) but auto-implement creates its own backup system (iteration_backup_root) separate from it.

**Gap**: An autonomous agent can destroy the repository with a single bad LLM response. No human-in-the-loop is required.

**Suggested order**: 24

### 25.0 No Input Validation or Prompt Injection Protection

**Priority**: High  
**Complexity**: Medium  
**Impacted modules**: `clawai/chat/chat_service.py`, `api.py`, `clawai/autonomy/agent_runtime.py`

**Evidence**:
- Chat endpoint (`POST /api/chat`) accepts arbitrary prompt strings and passes them directly to the LLM with no sanitization.
- `AgentRuntime` passes user input directly to the planner, which controls tool execution.
- No prompt injection detection, no input length validation beyond LLM context limits, no role separation between user input and system prompts.

**Gap**: The system is vulnerable to prompt injection. A user could craft input that causes the agent to execute arbitrary tool commands.

**Suggested order**: 25

### 26.0 No Execution Timeouts or Budget Enforcement

**Priority**: High  
**Complexity**: Small  
**Impacted modules**: `clawai/autonomy/agent_runtime.py`, `clawai/autopilot/auto_implement_runtime.py`, `clawai/agent/agent_loop.py`

**Evidence**:
- `AgentRuntime` has `max_iterations=3` with `LLMCallMetrics(max_calls=10)` as soft limits, but no hard wall-clock timeout.
- `AutoImplementService` has `timeout=1800` for test commands but no overall execution budget.
- `AgentLoop` has no timeout — execution can run indefinitely if goals keep retrying.
- Evolution engine has `interval_seconds=900` but a single cycle could block the background thread indefinitely.

**Gap**: Without enforced budgets, a misbehaving LLM or runaway loop can consume unbounded resources.

**Suggested order**: 26

### 27.0 No Rollback for Agent Loop Operations

**Priority**: Medium  
**Complexity**: Small  
**Impacted modules**: `clawai/agent/agent_loop.py`, `clawai/agents/backup_manager.py`

**Evidence**:
- `AutoImplementService` has git rollback after failed iterations (auto_implement_runtime.py line 530).
- But `AgentLoop` and `AgentRuntime` have **no rollback mechanism**.
- `BackupManager` exists but is not referenced by any production code path.

**Gap**: Only the auto-implement service has rollback. Regular agent loop operations can leave the filesystem in an inconsistent state with no way to recover.

**Suggested order**: 27

---

## Missing Self-Improvement

### 28.0 Evolution Engine Does Not Improve the Agent

**Priority**: Critical  
**Complexity**: Large  
**Impacted modules**: `clawai/evolution/engine.py`, `clawai/autopilot/auto_implement_runtime.py`

**Evidence**:
- `EvolutionEngine` scans for TODOs, conflicts, duplicates — then enqueues them via `autonomy.enqueue()`.
- The enqueued items are executed by `AutoImplementService`, which generates code changes.
- But the evolution engine **never modifies the agent itself** — no prompt tuning, no tool registration, no memory optimization, no model parameter adjustment.
- `_record_learning()` stores results in semantic memory but nothing reads those results to improve the next evolution cycle.

**Gap**: The evolution engine improves the *project* but not the *agent*. The agent's own prompts, tools, memory, and behavior remain static.

**Suggested order**: 28

### 29.0 No Prompt Optimization or Self-Tuning

**Priority**: High  
**Complexity**: Large  
**Impacted modules**: `clawai/prompts/`, `clawai/prompt/`, `clawai/evolution/engine.py`

**Evidence**:
- System prompts are hardcoded strings in multiple files (`agents/agent.py`, `chat/chat_service.py`, `autonomy/agent_runtime.py`, `autopilot/auto_implement_runtime.py`, `cognition/pipeline.py`).
- `PromptEngine` exists in two places (`prompt/prompt_engine.py`, `prompts/prompt_engine.py`) but neither supports dynamic prompt optimization based on past results.
- No A/B testing framework, no prompt versioning, no automatic refinement.

**Gap**: Prompts are static. The agent cannot learn from failures to improve its own prompts.

**Suggested order**: 29

### 30.0 No Model Performance Tracking

**Priority**: Low  
**Complexity**: Small  
**Impacted modules**: (nonexistent)

**Evidence**:
- `LLMCallMetrics` tracks calls within a single run but data is not persisted.
- No historical record of which models work best for which tasks.
- `ModelRouter` routes by role (coder, planner, reviewer) with no feedback loop to adjust routing based on actual performance.

**Gap**: There is no way to know which model performs best for coding vs planning vs reviewing. Model selection is based on configuration only, not empirical results.

**Suggested order**: 30

---

## Missing Coding Capabilities

### 31.0 No Code Generation Pipeline — Only File Rewrites

**Priority**: High  
**Complexity**: Large  
**Impacted modules**: `clawai/autopilot/auto_implement_runtime.py`, `clawai/diffing/`, `clawai/patching/`

**Evidence**:
- `AutoImplementService` generates entire file contents — there is no diff/patch pipeline for surgical changes.
- `diffing/patch_generator.py` and `patching/patch_planner.py` exist but are **never called** from auto-implement.
- `PatchAgent` generates JSON patch operations (replace, insert_before, insert_after, delete) but is **not wired** into the auto-implement flow.
- The system prompt in `AutoImplementService._system_prompt()` says "Quando mudar um arquivo, forneça o conteúdo completo final do arquivo" — full file rewrites only.

**Gap**: The system can only rewrite entire files, not make surgical edits. The diffing/patching infrastructure exists but is disconnected from the auto-implement pipeline.

**Suggested order**: 31

### 32.0 No Multi-File Context Management

**Priority**: High  
**Complexity**: Medium  
**Impacted modules**: `clawai/autopilot/auto_implement_runtime.py`

**Evidence**:
- `_select_candidate_files()` selects up to `max_files` (default 15) files but concatenates all contents into a single prompt.
- `_read_file_snippet()` truncates files at `MAX_FILE_CONTEXT_CHARS = 4000` — large files are only partially visible.
- There is no mechanism to track which files have been read, which have been modified, or what the "current state" of the workspace is across iterations.

**Gap**: The LLM sees only a snapshot of selected files, with no awareness of the full project structure or the history of changes made in previous iterations.

**Suggested order**: 32

### 33.0 No Dependency Analysis for Change Impact

**Priority**: Medium  
**Complexity**: Medium  
**Impacted modules**: `clawai/codebase/dependency_graph.py`, `clawai/autopilot/auto_implement_runtime.py`

**Evidence**:
- `DependencyGraph` exists in `codebase/dependency_graph.py` but is never used by auto-implement.
- `AutoImplementService` selects files by keyword/token matching only — no import analysis, no symbol resolution, no type inference.
- After changing a file, there is no mechanism to detect which other files might need updates.

**Gap**: The agent cannot determine the impact of a code change. It may modify one file without updating imports, type definitions, or tests in dependent files.

**Suggested order**: 33

### 34.0 No Test Generation

**Priority**: Medium  
**Complexity**: Large  
**Impacted modules**: `clawai/testing/`, `clawai/autopilot/auto_implement_runtime.py`

**Evidence**:
- `testing/test_runner.py` exists but is not integrated with auto-implement.
- Auto-implement only runs existing tests (`pytest -q`) — it never generates new tests for the code it writes.
- `testing/test_generator`-like module does not exist.

**Gap**: The agent can modify code but cannot generate tests to validate its own changes.

**Suggested order**: 34

---

## Missing Reasoning Capabilities

### 35.0 Intent Classifier Is Heuristic-Only

**Priority**: High  
**Complexity**: Small  
**Impacted modules**: `clawai/chat/intent_classifier.py`

**Evidence**:
- `IntentClassifier.classify()` uses simple keyword matching against `ENGINEERING_HINTS` and `WORKSPACE_HINTS` tuples — no LLM-based classification.
- Keywords are hardcoded strings in Portuguese ("implemente", "corrija", "refatore", "ajuste", "analise", etc.).
- Classification is binary: agent vs direct. No nuance for task type, complexity, or required tools.

**Gap**: Intent classification is fragile keyword matching, not semantic understanding. Adding a new language or domain requires code changes.

**Suggested order**: 35

### 36.0 No Multi-Step Reasoning with State Persistence

**Priority**: High  
**Complexity**: Large  
**Impacted modules**: `clawai/autonomy/agent_runtime.py`, `clawai/cognition/`

**Evidence**:
- `AgentRuntime.run()` maintains state within a single `ExecutionState` object (max 10 LLM calls, 3 iterations).
- After the run completes, the state is discarded — no persistent reasoning trace.
- The sophisticated `cognition/pipeline.py` (supervisor → planner → debate → judge) is orphaned.
- `cognition/pipeline.py` also has no persistent state — each `execute()` call is independent.

**Gap**: Multi-step reasoning exists but leaves no trace. The agent cannot backtrack, review past decisions, or learn from previous reasoning chains.

**Suggested order**: 36

### 37.0 No Self-Reflection or Error Analysis Loop

**Priority**: High  
**Complexity**: Medium  
**Impacted modules**: `clawai/autonomy/reflector.py`, `clawai/selfrepair/`, `clawai/cognition/failure_analysis.py`

**Evidence**:
- `Reflector` exists (autonomy/reflector.py) and is called in `AgentRuntime` when tool results indicate failure.
- `SelfRepairEngine` exists (selfrepair/self_repair_engine.py) but is **not integrated** into any agent loop or auto-implement flow.
- `FailureAnalysis` exists (cognition/failure_analysis.py) but is never called from production code.
- `ReflectionAgent` exists (agents/reflection_agent.py) but is not wired into any pipeline.

**Gap**: Reflection, self-repair, and failure analysis infrastructure exists but is fragmented and disconnected from actual execution flows.

**Suggested order**: 37

---

## Implementation Roadmap

### Milestone 1 — Foundation (Weeks 1-3)

**Goal**: Make the existing infrastructure actually work together.

| Order | Item | Description |
|-------|------|-------------|
| 1 | 1.0 — Consolidate pipelines | Remove or merge the dual CognitionPipeline. Connect the multi-stage pipeline to ChatService. |
| 3 | 3.0 — Unify memory systems | Bridge JSON memory and ChromaDB memory. Make MemoryManager usable from agents. |
| 4 | 4.0 — Fix initialization | Make api.py use bootstrap or make bootstrap use application — single initialization path. |
| 6 | 6.0 — Load config.yaml | Wire config loading into startup. Make Settings.apply_config() actually called. |
| 5 | 5.0 — Use DI container | Wire at least the major services (ModelRouter, MemoryManager, WorkspaceManager) through ServiceContainer. |

### Milestone 2 — Safety (Weeks 4-5)

**Goal**: Enable autonomous operation without risk of repository destruction.

| Order | Item | Description |
|-------|------|-------------|
| 24 | 24.0 — Approval gates | Add dry-run mode and confirmation step before file writes. Frontend approval UI. |
| 25 | 25.0 — Prompt injection protection | Add input validation, role separation, injection detection. |
| 26 | 26.0 — Budget enforcement | Add wall-clock timeouts, max token budgets, cost tracking. |
| 7 | 7.0 — Sandboxing | Add optional sandboxed execution for test commands. Read-only mode. |
| 27 | 27.0 — Rollback for agent loop | Extend git/backup rollback beyond auto-implement to all agent operations. |

### Milestone 3 — Agent Architecture (Weeks 6-8)

**Goal**: Complete the planned agent refactoring.

| Order | Item | Description |
|-------|------|-------------|
| 2 | 2.0 — Implement agent subpackages | Build base, factory, implementations, manager, registry. Migrate existing agents. |
| 8 | 8.0 — Unify tool abstractions | Consolidate tool registries. Single ToolRegistry used everywhere. |
| 9 | 9.0 — Agent registry & factory | Implement agent discovery and instantiation through registry. |
| 14 | 14.0 — Wire all tools to runtime | Register git, search, terminal, python tools in AgentRuntime. |
| 15 | 15.0 — Connect Composio | Share ToolRegistry instance between ComposioService and AgentRuntime. |

### Milestone 4 — Reasoning & Planning (Weeks 9-11)

**Goal**: Give the agent actual reasoning and planning capabilities.

| Order | Item | Description |
|-------|------|-------------|
| 21 | 21.0 — Hierarchical planning | Connect GoalDecomposer, GoalDependencyGraph to agent loop. |
| 22 | 22.0 — Plan verification | Add plan review step before execution. LLM-as-judge for plan correctness. |
| 35 | 35.0 — Semantic intent classification | Replace keyword classifier with LLM-based classification. |
| 36 | 36.0 — Persistent reasoning traces | Save reasoning chains to memory. Enable backtracking and review. |
| 37 | 37.0 — Reflection loop | Connect SelfRepairEngine, FailureAnalysis, Reflector into a unified feedback loop. |

### Milestone 5 — Coding & Tools (Weeks 12-14)

**Goal**: Enable surgical code changes and broader tool access.

| Order | Item | Description |
|-------|------|-------------|
| 31 | 31.0 — Diff-based editing | Wire PatchAgent/patch_generator into auto-implement. Add surgical edits. |
| 33 | 33.0 — Dependency impact analysis | Use DependencyGraph to find affected files after changes. |
| 32 | 32.0 — Multi-file context | Add change history tracking. Show diff between iterations. |
| 34 | 34.0 — Test generation | Generate tests alongside code changes. |
| 16 | 16.0 — Web search integration | Connect web_search.py to chat flow for external knowledge. |

### Milestone 6 — Memory & Learning (Weeks 15-16)

**Goal**: Make the agent learn from experience.

| Order | Item | Description |
|-------|------|-------------|
| 11 | 11.0 — Cross-session memory | Implement vector-based memory retrieval for past learnings. |
| 12 | 12.0 — Learning from execution | Use semantic memory to influence file selection, plan generation, error avoidance. |
| 13 | 13.0 — Conversation history | Add session tracking to chat. Maintain multi-turn conversation context. |
| 29 | 29.0 — Prompt optimization | Add prompt versioning and automatic refinement from past results. |

### Milestone 7 — Self-Improvement (Weeks 17-18)

**Goal**: Make the evolution engine improve the agent itself.

| Order | Item | Description |
|-------|------|-------------|
| 28 | 28.0 — Evolve the agent | Evolution engine should tune prompts, register tools, optimize memory thresholds. |
| 30 | 30.0 — Model performance tracking | Track which model/role combinations work best. Use data for routing decisions. |
| 23 | 23.0 — Resource-aware scheduling | Integrate ResourceManager to throttle when system is busy. |

### Milestone 8 — Testing & Evaluation (Ongoing)

**Goal**: Measure and verify agent quality.

| Order | Item | Description |
|-------|------|-------------|
| 17 | 17.0 — Integration tests | Test component interactions: agent + tools, planner + executor, evolution + auto-implement. |
| 18 | 18.0 — E2E tests | Full pipeline tests: API → agent → code change → verify. |
| 19 | 19.0 — Meaningful verification | Add task completion benchmarks, response quality metrics to verify.py. |
| 20 | 20.0 — Performance benchmarks | Track iteration count, token usage, success rate across runs. |

---

## Summary Statistics

| Category | Count | Critical | High | Medium | Low |
|----------|-------|----------|------|--------|-----|
| Critical Blockers | 4 | 4 | 0 | 0 | 0 |
| Missing Infrastructure | 3 | 0 | 3 | 0 | 0 |
| Missing Abstractions | 3 | 0 | 2 | 1 | 0 |
| Missing Memory | 3 | 0 | 2 | 1 | 0 |
| Missing Tooling | 3 | 1 | 1 | 1 | 0 |
| Missing Evaluation | 4 | 0 | 2 | 1 | 1 |
| Missing Planning | 3 | 0 | 2 | 1 | 0 |
| Missing Safety | 4 | 1 | 2 | 1 | 0 |
| Missing Self-Improvement | 3 | 1 | 1 | 0 | 1 |
| Missing Coding Capabilities | 4 | 0 | 3 | 1 | 0 |
| Missing Reasoning Capabilities | 3 | 0 | 3 | 0 | 0 |
| **Total** | **37** | **7** | **21** | **7** | **2** |

**Key Insight**: 7 critical blockers and 21 high-priority items exist. The foundation (initialization, memory, configuration) needs to be fixed before meaningful progress can be made on autonomy. The agent has impressive infrastructure breadth but almost none of it is wired together end-to-end.