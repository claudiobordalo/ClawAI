"""
Reflection Engine for Claw AI - reflects on execution outcomes and stores results.
"""

from datetime import datetime
from .base_memory_system import BaseMemoryEntry, BaseMemorySystem

class ReflectionEntry(BaseMemoryEntry):
    """Represents a single reflection about an executed task."""
    
    def __init__(self, id: str, title: str, content_type: str, tags=None, created_at=None,
                 task_id: str = None, result: dict = None, success: bool = False):
        super().__init__(id=id, title=title, content_type=content_type, tags=tags or [], created_at=created_at)
        
        # Reflection-specific fields
        self.task_id = task_id          # Identifier for the executed task 
        self.result = result            # Result details from execution  
        self.success = success          # Whether execution was successful

class ReflectionEngine(BaseMemorySystem):
    """Manages reflections on AI processing outcomes."""
    
    def __init__(self): 
        super().__init__()
        
    def add_reflection(self, entry: ReflectionEntry):
        """Add a new reflection to the system."""  
        self.add_entry(entry)
        
    def get_reflection(self, reflection_id: str) -> ReflectionEntry:
        """Retrieve a specific reflection by its ID."""
        return self.get_entry(reflection_id)

    def add_execution_result(self, task_id: str, result: dict, success: bool):
        """
        Add an execution outcome as a reflection.
        
        Args:
            task_id (str): Identifier for the executed task
            result (dict): Result details from execution  
            success (bool): Whether execution was successful 
        """ 
        
        # Create timestamp if not provided
        created_at = datetime.now()
        
        title = f"Reflection: {task_id}"
        
        reflection_entry = ReflectionEntry(
            id=f"ref_{len(self._entries) + 1:03d}",
            title=title,
            content_type="execution_outcome",
            tags=["reflection", "outcome"],
            task_id=task_id, 
            result=result,
            success=success,
            created_at=created_at
        )
        
        self.add_reflection(reflection_entry)
    
    def get_successful_executions(self) -> list:
        """Get all successful executions."""
        return [entry for entry in self._entries.values() 
                if isinstance(entry, ReflectionEntry) and entry.success]
                
    def get_failed_executions(self) -> list:  
        """Get all failed executions.""" 
        return [entry for entry in self._entries.values()
                if isinstance(entry, ReflectionEntry) and not entry.success]

    def demo():
        """Demonstration of the Reflection Engine."""
        
        # Create a reflection engine instance  
        reflector = ReflectionEngine() 
    
        # Add sample reflections
        success_entry = ReflectionEntry(
            id="ref_001", 
            title="Success: ProcessBatchData",
            content_type="execution_outcome",
            tags=["reflection", "outcome"],
            task_id="ProcessBatchData",
            result={"processed_records": 1500, "duration_seconds": 42},
            success=True
        )

        fail_entry = ReflectionEntry(
            id="ref_002", 
            title="Failure: ProcessNetworkRequest",
            content_type="execution_outcome",
            tags=["reflection", "outcome"],
            task_id="ProcessNetworkRequest",
            result={"error": "Connection timeout"},
            success=False
        )

        reflector.add_reflection(success_entry)
        reflector.add_reflection(fail_entry)

        print("=== Demo: Reflection Engine ===\n")
        
        # Show summary 
        summary = reflector.get_summary()
        print("--- Reflection Summary ---")  
        for key, value in summary.items():
            if isinstance(value, dict):
                print(f"{key}: {value}")
            else:
                print(f"{key}: {value}")

if __name__ == "__main__":
    ReflectionEngine.demo()