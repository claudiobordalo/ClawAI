from __future__ import annotations

import json
import re
from typing import Any, Optional

from clawaii.cognition.reflection_engine import ReflectionEngine, ReflectionEntry
from clawaii.cognition.failure_analysis import FailureAnalysis


class Reflector:
    def __init__(self, *, router: Any, reflection_engine: Optional[ReflectionEngine] = None) -> None:
        self.router = router
        self.reflection_engine = reflection_engine

    def reflect(
        self,
        *,
        objective: str,
        context: str,
        decision: dict[str, Any],
        tool_results: list[dict[str, Any]],
        iteration: int,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        system_prompt = (
            "Você é o agente de reflexão. Sua função principal é analisar os resultados das ações e decidir se o processo deve continuar ou parar."
            "Responda apenas com JSON válido contendo reflection, should_continue, error_type, needs_retry e strategy."
        )
        
        # Enhanced analysis of tool results
        error_details = self._analyze_tool_results(tool_results)
        error_type = "none"
        if error_details["has_errors"]:
            last_error_msg = next((r.get("error") for r in tool_results if r.get("error")), None)
            if last_error_msg:
                # Use enhanced classification
                try:
                    classified_category = FailureAnalysis.classify(last_error_msg)
                    error_type = str(classified_category) 
                except Exception:
                    error_type = "unknown"
        else:
            # If no direct errors but tool results exist, check for anomalies
            if tool_results and len(tool_results) > 0:
                all_empty_results = all(r.get("result") is None or (isinstance(r.get("result"), str) and r.get("result").strip() == "") 
                                       for r in tool_results)
                if all_empty_results:
                    error_type = "empty_result"

        # Get repeated errors from engine
        repeated_errors_str = ""
        strategy_suggestion = "default"
        
        if self.reflection_engine:
            repeated = self.reflection_engine.repeated_errors(min_count=2)
            if repeated:
                repeated_errors_str = f"\nERROS REPETIDOS DETECTADOS:\n{json.dumps(repeated, ensure_ascii=False)}"
                # Suggest strategy based on patterns
                if any("timeout" in str(err).lower() for err in repeated):
                    strategy_suggestion = "retry_with_timeout_increase"
                elif any("tool_failure" in str(err) or "execution_failed" in str(err).lower() 
                        for err in repeated):
                    strategy_suggestion = "fallback_to_alternative_approach"
                elif any("validation" in str(err).lower() for err in repeated):
                    strategy_suggestion = "refine_input_and_retry"

        # Enhanced payload with more context and history analysis
        payload = (
            f"Objetivo: {objective}\n\n"
            f"Contexto: {context}\n\n"
            f"Decisão anterior: {json.dumps(decision, ensure_ascii=False, default=str)}\n\n"
            f"Resultados das ferramentas:\n{self._format_tool_results(tool_results)}\n\n"
            f"Estado resumido: {json.dumps(state, ensure_ascii=False, default=str)}\n\n"
            f"Iteração atual: {iteration}\n"
            f"Detalhes de erro detectados:\n{json.dumps(error_details, ensure_ascii=False)}\n"
            f"{repeated_errors_str}\n"
        )
        
        try:
            raw = self.router.ask(
                prompt=payload,
                role="reviewer",
                system_prompt=system_prompt,
            )
        except Exception as e:
            return {
                "reflection": f"Reflection unavailable ({e}).",
                "should_continue": False,
                "error_type": "provider_error",
                "needs_retry": False,
                "strategy": strategy_suggestion
            }
        
        parsed = self._parse_json(
            raw,
            default={
                "reflection": "Análise de reflexão não disponível.",
                "should_continue": True,  # Default to continue for better autonomy
                "error_type": error_type,
                "needs_retry": False,
                "strategy": strategy_suggestion
            },
        )
        
        result = {
            "reflection": str(parsed.get("reflection") or ""),
            "should_continue": bool(parsed.get("should_continue", True)),  # Default to true for better autonomy
            "error_type": str(parsed.get("error_type") or error_type),
            "needs_retry": bool(parsed.get("needs_retry", False)),
            "strategy": str(parsed.get("strategy") or strategy_suggestion)
        }

        # Record the entry in the engine with enhanced information
        if self.reflection_engine:
            try:
                from datetime import datetime, timezone
                
                failed_msgs = [r.get("error") for r in tool_results if r.get("error")]
                success_flag = result["should_continue"] or result["needs_retry"]
                
                # Extract more meaningful information from decision reasoning
                decisions_list = []
                if isinstance(decision, dict) and "reasoning" in decision:
                    decisions_list.append(str(decision.get("reasoning", "")))
                elif isinstance(decision, str):
                    decisions_list.append(decision)
                
                entry = ReflectionEntry(
                    goal_id=objective,
                    goal_title=objective[:100],  # Truncate for ID
                    success=success_flag,
                    what_failed=failed_msgs if failed_msgs else [],
                    risks=[],
                    opportunities=[],
                    decisions=decisions_list,
                    duration=0.0, 
                    metadata={"iteration": iteration, "strategy_used": result["strategy"]}
                )
                self.reflection_engine.record(entry)
            except Exception as e:
                # Silent failure to not break the system
                pass

        return result

    def _analyze_tool_results(self, tool_results: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Analyze tool results for patterns and anomalies.
        Returns detailed error information that can guide decision making.
        """
        analysis = {
            "has_errors": False,
            "error_count": 0,
            "successful_tools": [],
            "failed_tools": [],
            "empty_results": [],
            "tool_details": []
        }
        
        if not tool_results:
            return analysis
        
        for result in tool_results:
            success = result.get("success")
            tool_name = result.get("tool", "unknown_tool")
            error_msg = result.get("error")
            
            detail_info = {
                "tool": tool_name,
                "success": bool(success),
                "has_error": bool(error_msg)
            }
            analysis["tool_details"].append(detail_info)
            
            if success is False or error_msg:
                analysis["has_errors"] = True
                analysis["error_count"] += 1
                analysis["failed_tools"].append(tool_name)
            elif success is True:
                analysis["successful_tools"].append(tool_name)
                
            # Check for empty results that might be problematic
            result_content = result.get("result")
            if (result_content is None or 
                (isinstance(result_content, str) and not result_content.strip())):
                analysis["empty_results"].append(tool_name)
        
        return analysis
    
    def _format_tool_results(self, tool_results: list[dict[str, Any]]) -> str:
        """
        Format tool results for better readability in reflection prompt.
        """
        if not tool_results:
            return "Nenhum resultado de ferramenta disponível."
        
        formatted = []
        for i, result in enumerate(tool_results):
            success_status = "✅ Sucesso" if result.get("success") is True else "❌ Falha" if result.get("success") is False else "❓ Indeterminado"
            tool_name = result.get("tool", "unknown_tool")
            error_msg = result.get("error")
            
            formatted.append(f"{i+1}. {tool_name} - {success_status}")
            if error_msg:
                formatted.append(f"   Erro: {str(error_msg)[:200]}...")  # Truncate long errors
        return "\n".join(formatted)
    
    def _parse_json(self, raw: str, *, default: dict[str, Any]) -> dict[str, Any]:
        try:
            text = raw.strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else default
        except Exception as e:
            # Log error but don't crash the system
            print(f"[REFLECTOR] Failed to parse JSON: {e}")
            return default

    def get_strategy_recommendation(self, repeated_errors: list[str]) -> str:
        """
        Provide strategy recommendations based on patterns of errors.
        This is used for automated decision making when direct reflection fails.
        """
        if not repeated_errors:
            return "default"
            
        # Analyze error types and suggest strategies
        combined_error_text = " ".join([str(err) for err in repeated_errors]).lower()
        
        if any(keyword in combined_error_text for keyword in ["timeout", "deadline"]):
            return "retry_with_timeout_increase"
        elif any(keyword in combined_error_text for keyword in ["tool_failure", "execution_failed", "invalid tool"]):
            return "fallback_to_alternative_approach" 
        elif any(keyword in combined_error_text for keyword in ["validation", "schema", "type error"]):
            return "refine_input_and_retry"
        else:
            # Default strategy
            return "default"

    def should_continue_autonomously(self, result: dict[str, Any]) -> bool:
        """
        Make autonomous decisions about whether to continue based on reflection results.
        This adds an extra layer of autonomy beyond what the LLM decides directly.
        """
        if not isinstance(result, dict):
            return True  # Default to continuing
            
        should_continue = result.get("should_continue", True)
        
        # If we're in a retry scenario or have been told to continue,
        # be more confident about proceeding
        needs_retry = result.get("needs_retry", False)
        error_type = str(result.get("error_type") or "none")
        
        if needs_retry:
            return True
            
        # For certain types of errors, we might want to automatically retry rather than stop
        auto_continue_errors = ["timeout", "empty_result"]
        if any(auto in error_type for auto in auto_continue_errors):
            return True
            
        return should_continue

# Additional utility functions that can be used by other components
def analyze_decision_quality(decision: dict[str, Any]) -> str:
    """
    Analyze the quality of a decision to provide feedback.
    
    Returns one of several assessment types based on decision content analysis.
    """
    if not isinstance(decision, dict):
        return "poor"
        
    reasoning = str(decision.get("reasoning", "")).lower()
    tool_usage = str(decision.get("tool_usage", "")).lower() 
    
    # Quality indicators
    quality_indicators = {
        "good": ["clear", "logical", "well-structured"],
        "fair": ["some", "partially", "limited"], 
        "poor": ["unclear", "confusing", "missing"]
    }
    
    score = 0
    
    for indicator in quality_indicators["good"]:
        if indicator in reasoning:
            score += 1
            
    for indicator in quality_indicators["fair"]:
        if indicator in reasoning:
            score -= 0.5
            
    for indicator in quality_indicators["poor"]:
        if indicator in reasoning:
            score -= 2
    
    # Consider tool usage as well
    if "tool" in tool_usage or "tools" in tool_usage:
        score += 1
        
    if score >= 1:
        return "good"
    elif score > -0.5: 
        return "fair"
    else:
        return "poor"

def get_error_context(error_type: str) -> dict[str, Any]:
    """
    Provide context and guidance for different error types.
    
    Returns a dictionary with information about the type of error,
    possible causes, and suggested actions to take when this occurs. 
    """
    contexts = {
        "timeout": {
            "description": "Timeout occurred while waiting for response",
            "causes": ["Network issues", "Slow processing", "Resource constraints"],
            "suggestions": [
                "Increase timeout duration",
                "Retry with exponential backoff"
            ]
        },
        "tool_failure": {
            "description": "Tool execution failed unexpectedly",
            "causes": ["Invalid tool configuration", "Missing dependencies", "API errors"], 
            "suggestions": [
                "Check tool setup and permissions",
                "Verify required libraries are installed"
            ]  
        },   
        "validation_failure": {
            "description": "Input validation error occurred",
            "causes": ["Incorrect data format", "Schema mismatch"],
            "suggestions": [
                "Refine input parameters",
                "Validate against schema before execution" 
            ]
        },
        "empty_result": {
            "description": "Tool returned empty or null result",
            "causes": ["No results found", "Incomplete processing"],  
            "suggestions": [
                "Check tool configuration",
                "Verify inputs are appropriate"
            ]   
        }
    }
    
    return contexts.get(error_type, {"description": f"Unknown error type: {error_type}"})