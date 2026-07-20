from __future__ import annotations

import json 
from typing import List, Dict, Any, Optional  
from dataclasses import dataclass, asdict 

@dataclass  
class PlanStep:
    """Represents a single step in the execution plan."""
    
    # Core information about this task
    id: str  # Unique identifier for this step
    description: str  # What needs to be done 
    tool_name: Optional[str] = None  # Which tool/function should perform it (if applicable)
    parameters: Dict[str, Any] = None   # Parameters needed by the tool
    
    # Execution context and metadata  
    priority: int = 0  # Priority level for execution order
    depends_on: List[str] = None  # IDs of steps that must complete before this one 
    max_attempts: int = 1  # Maximum number of times to retry if it fails 
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
            
        if self.depends_on is None:
            self.depends_on = []
            

class Planner:
    """Enhanced planner that creates and manages execution plans for objectives."""
    
    def __init__(self, *, max_steps: int = 50) -> None:
        """
        Initialize the planner.
        
        Args:
            max_steps (int): Maximum number of steps allowed in a plan  
        """
        self.max_steps = max_steps
        self.steps: List[PlanStep] = []
    
    def create_plan(self, objective: str, context: str) -> Dict[str, Any]:
        """
        Create an execution plan for the given objective.
        
        Args:
            objective (str): The main goal to achieve  
            context (str): Background information about constraints or requirements
            
        Returns:
            dict: Plan structure containing steps and metadata
        """ 
        # This is a simplified version - in practice this would be more sophisticated,
        # perhaps using LLMs for planning, but here we'll demonstrate the concept
        
        plan = {
            "objective": objective,
            "context": context,  
            "steps": [],
            "created_at": self._get_timestamp(),
            "total_steps": 0
        }
        
        if not objective:
            return plan
            
        # Simple heuristic-based planning - in a real system this would be more intelligent 
        steps = []
        
        # Basic step generation based on common patterns  
        if context and ("file" in context.lower() or "read" in context.lower()):
            steps.append(PlanStep(
                id="step_01",
                description="Read input file",   
                tool_name="read_file",
                parameters={"path": "/input/data.txt"},
                priority=1,
                max_attempts=3
            ))
            
        if objective and ("search" in objective.lower() or "find" in objective.lower()):
            steps.append(PlanStep(
                id="step_02", 
                description="Search for relevant information",
                tool_name="web_search",
                parameters={"query": objective},
                priority=1,
                max_attempts=3
            ))
            
        if context and ("format" in context.lower() or "output" in context.lower()):
            steps.append(PlanStep(
                id="step_03", 
                description="Format results into structured output",
                tool_name="format_output",
                parameters={"style": "json"},
                priority=2,
                max_attempts=1
            ))
            
        # Add a final step to validate completion  
        if steps:
            last_priority = max(step.priority for step in steps) + 1
            
            steps.append(PlanStep(
                id="step_final", 
                description="Validate that objective was achieved",
                tool_name="validate_completion", 
                parameters={"objective": objective},
                priority=last_priority,
                depends_on=[s.id for s in steps],
                max_attempts=2
            ))
        
        # Limit to maximum allowed steps  
        plan["steps"] = [asdict(step) for step in steps[:self.max_steps]]
        plan["total_steps"] = len(plan["steps"])
        
        self.steps.clear()
        self.steps.extend(steps)
            
        return plan
    
    def get_next_step(self, executed_ids: List[str]) -> Optional[PlanStep]:
        """
        Get the next executable step based on dependencies and execution history.
        
        Args:
            executed_ids (list): IDs of steps that have already been completed
            
        Returns:
            PlanStep or None if no more steps are available  
        """ 
        # Find all unexecuted steps
        pending = [step for step in self.steps if step.id not in executed_ids]
        
        # Filter by dependencies - only return those where all deps are done
        ready_to_execute = []
        for step in pending:
            # If no dependencies or all required ones completed, it's eligible 
            has_all_deps = True  
            
            for dep_id in step.depends_on:   
                if dep_id not in executed_ids:
                    has_all_deps = False
                    break
                    
            if has_all_deps and len(step.id) > 0: # Ensure valid ID exists
                ready_to_execute.append((step.priority, step)) 
                
        # Return the highest priority eligible step (lowest number)
        if ready_to_execute:
            return min(ready_to_execute)[1]
            
        return None
    
    def get_step_by_id(self, step_id: str) -> Optional[PlanStep]:
        """
        Find a specific plan step by its ID.
        
        Args:
            step_id (str): The unique identifier for the desired step
            
        Returns:
            PlanStep or None if not found
        """ 
        for step in self.steps:
            if step.id == step_id:  
                return step
                
        return None
        
    def get_all_steps(self) -> List[PlanStep]:
        """
        Get a copy of all defined steps.
        
        Returns:
            list[PlanStep]: All plan steps
        """ 
        # Return defensive copy to prevent modification from outside
        return self.steps.copy()
    
    def validate_plan_completeness(self, executed_ids: List[str]) -> bool:
        """
        Check if the current execution has completed all required tasks.
        
        Args:
            executed_ids (list): IDs of steps that have been executed
            
        Returns:
            bool: True if plan is complete or no more executable steps remain
        """ 
        # Get any remaining unexecuted steps  
        pending = [step for step in self.steps if step.id not in executed_ids]
        
        return len(pending) == 0
    
    def get_plan_summary(self, executed_ids: List[str] = None) -> Dict[str, Any]:
        """
        Generate a summary of the current plan state.
         
        Args:
            executed_ids (list): IDs that have already been completed
            
        Returns:
            dict: Summary information about steps and execution status
        """ 
        if executed_ids is None:
            executed_ids = []
            
        all_steps = self.get_all_steps()  
        
        # Categorize by completion state  
        pending_count = 0
        executed_count = len(executed_ids)
        
        for step in all_steps:   
            if step.id not in executed_ids and len(step.id) > 0:
                pending_count += 1
                
        return {
            "total_steps": len(all_steps),
            "executed_steps": executed_count,
            "pending_steps": pending_count, 
            "completed_percentage": (executed_count / max(len(all_steps), 1)) * 100
        }
        
    def _get_timestamp(self) -> str:
        """
        Get current timestamp in ISO format.
        
        Returns:  
            str: Current datetime as an ISO string
        """ 
        from datetime import datetime
        return datetime.now().isoformat()
    
    @classmethod  
    def load_from_json(cls, data_str_or_file: str) -> Planner:
        """
        Create a planner instance by loading plan structure.
        
        Args:
            data_str_or_file (str): Either JSON string or path to file containing the plan
            
        Returns:
            Planner: New planner with loaded steps
        """ 
        try:
            # Try parsing as direct JSON first  
            if isinstance(data_str_or_file, str):
                import json
                
                parsed = json.loads(data_str_or_file)   
                
                # Create new planner and populate it with the data
                plan_steps = []
                for step_data in parsed.get("steps", []): 
                    try:
                        step_obj = PlanStep(**step_data)
                        plan_steps.append(step_obj)
                        
                    except Exception as e:  
                        print(f"Warning: Could not create Step from {step_data}: {e}")
                
                planner = cls()
                planner.steps.extend(plan_steps) 
                return planner
                
        except json.JSONDecodeError:
            pass
            
        # If it fails, try treating input as file path
        with open(data_str_or_file, 'r') as f:  
            data = json.load(f)
            
        plan_steps = []    
        for step_data in data.get("steps", []):
            try:
                step_obj = PlanStep(**step_data) 
                plan_steps.append(step_obj)
                
            except Exception as e:
                print(f"Warning: Could not create Step from {step_data}: {e}")
        
        planner = cls()
        planner.steps.extend(plan_steps)
        return planner
        
    def save_to_json(self, filepath: str) -> None:
        """
        Save current plan to a JSON file.
         
        Args:
            filepath (str): Path where the file should be saved
        """ 
        # Convert all steps into serializable form  
        serialized = [asdict(step) for step in self.steps]
        
        with open(filepath, 'w', encoding='utf-8') as f:   
            json.dump({"steps": serialized}, f, ensure_ascii=False, indent=2)


# Example usage and test functions
def demo_planner():
    """Demonstrate how to use the planner."""
    
    print("=== Demo: Planner ===")
    
    # Create a new plan  
    planner = Planner(max_steps=10)
    
    objective = "Process user data files"
    context = "Need to read input file, search for related info, then format output" 
    
    plan = planner.create_plan(objective, context) 
    print(f"\nCreated Plan: {plan['objective']}")
    print(f"Steps: {plan['total_steps']}")  
    
    # Display steps
    if plan["steps"]:
        print("\nPlan Steps:")
        for i, step in enumerate(plan["steps"]):  
            tool_info = f" using {step.get('tool_name', 'N/A')}" if step.get("tool_name") else ""
            depends_str = " (depends on: {})".format(", ".join(step.get("depends_on", []))) \
                         if step.get("depends_on") and len(step["depends_on"]) > 0 else ""  
            
            print(f"   {i+1}. {step['description']}{tool_info} - Priority:{step['priority']} {depends_str}")
    
    # Simulate execution
    executed = []
    while True:
        next_step = planner.get_next_step(executed) 
        if not next_step:  
            break
            
        print(f"\nExecuting step '{next_step.description}'")
        
        # Mark as done for simulation purposes
        executed.append(next_step.id)
    
    summary = planner.get_plan_summary(executed)
    print("\nPlan Summary:")
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.1f}%")
        else:
            print(f"  {key}: {value}")
            

if __name__ == "__main__":
    demo_planner()