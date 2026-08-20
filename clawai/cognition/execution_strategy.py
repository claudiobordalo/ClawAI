from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List
import time

@dataclass(frozen=True)
class ExecutionResult:
    answer: str
    success: bool
    execution_path: str  # "agent", "dev", or "direct"
    tools_used: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    execution_time_ms: float = 0.0
    raw_output: Dict[str, Any] = field(default_factory=dict)

class ExecutionStrategy:
    def __init__(self, router: Any):
        self.router = router

    def execute(
        self,
        goal: str,
        prepared_prompt: Any,
        context: Dict[str, Any],
        router: Any,
    ) -> ExecutionResult:
        # Decision logic
        goal_lower = goal.lower()
        if any(word in goal_lower for word in ["code", "implement", "fix", "develop", "patch", "git"]):
            return self._execute_development_path(goal, prepared_prompt, context, router)
        
        if any(word in goal_lower for word in ["agent", "search", "web", "browse"]):
            return self._execute_agent_path(goal, prepared_prompt, context, router)
        
        return self._execute_direct_path(goal, prepared_prompt, context, router)

    def _execute_agent_path(self, goal: str, prepared_prompt: Any, context: Dict[str, Any], router: Any) -> ExecutionResult:
        from clawai.autonomy.agent_runtime import AgentRuntime
        runtime = AgentRuntime(router=router)
        start = time.perf_counter()
        
        prompt_text = prepared_prompt.text if hasattr(prepared_prompt, 'text') else str(prepared_prompt)
        runtime_result = runtime.run(prompt_text)
        
        duration = (time.perf_counter() - start) * 1000
        answer = str(runtime_result.get("answer") or "")
        
        return ExecutionResult(
            answer=answer,
            success=True,
            execution_path="agent",
            tools_used=runtime_result.get("tools", []),
            execution_time_ms=duration,
            raw_output=runtime_result
        )

    def _execute_development_path(self, goal: str, prepared_prompt: Any, context: Dict[str, Any], router: Any) -> ExecutionResult:
        from clawai.development.development_pipeline import DevelopmentPipeline
        dev_pipeline = DevelopmentPipeline()
        start = time.perf_counter()
        
        prompt_text = prepared_prompt.text if hasattr(prepared_prompt, 'text') else str(prepared_prompt)
        dev_result = dev_pipeline.execute(prompt_text)
        
        duration = (time.perf_counter() - start) * 1000
        
        if hasattr(dev_result, "answer"):
            answer = dev_result.answer
            success = getattr(dev_result, "success", True)
            files_modified = getattr(dev_result, "files_modified", [])
        else:
            answer = dev_result.get("answer", "")
            success = dev_result.get("success", True)
            files_modified = dev_result.get("files_modified", [])
            
        return ExecutionResult(
            answer=answer,
            success=success,
            execution_path="dev",
            files_modified=files_modified,
            execution_time_ms=duration,
            raw_output=vars(dev_result) if hasattr(dev_result, "__dict__") else dev_result
        )

    def _execute_direct_path(self, goal: str, prepared_prompt: Any, context: Dict[str, Any], router: Any) -> ExecutionResult:
        import time
        start = time.perf_counter()
        
        prompt_text = prepared_prompt.text if hasattr(prepared_prompt, 'text') else str(prepared_prompt)
        answer = router.ask(
            prompt=prompt_text,
            role="user",
            system_prompt="Responda de forma direta e concisa.",
        )
        
        duration = (time.perf_counter() - start) * 1000
        return ExecutionResult(
            answer=answer,
            success=True,
            execution_path="direct",
            execution_time_ms=duration
        )
