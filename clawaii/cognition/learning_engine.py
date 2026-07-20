"""
Learning Engine for Claw AI - captures insights and patterns learned from processing.
"""

import datetime
from .base_memory_system import BaseMemoryEntry, BaseMemorySystem

class LearningEntry(BaseMemoryEntry):
    """Represents a single learning entry about performance or behavior."""
    
    def __init__(self, id: str, title: str, content_type: str, tags=None, created_at=None,
                 insights: list = None, improvement_suggestions: list = None):
        super().__init__(id=id, title=title, content_type=content_type, tags=tags or [], created_at=created_at)
        
        # Learning-specific fields
        self.insights = insights or []              # Key learning points  
        self.improvement_suggestions = improvement_suggestions or []  # Suggestions for better performance

class LearningEngine(BaseMemorySystem):
    """Manages learned knowledge and patterns from AI processing."""
    
    def __init__(self): 
        super().__init__()
        
    def add_learning(self, entry: LearningEntry):
        """Add a new learning to the system."""  
        self.add_entry(entry)
        
    def get_learning(self, learning_id: str) -> LearningEntry:
        """Retrieve a specific learning by its ID."""
        return self.get_entry(learning_id)

    def receive_execution_result(self, task_id: str, result: dict, success: bool):
        """
        Automatically receives results from executed tasks and converts them to insights.
        
        Args:
            task_id (str): Identifier for the executed task
            result (dict): Result details from execution  
            success (bool): Whether execution was successful 
        """ 
        
        # Create an insight based on whether it succeeded or failed
        if success:  
            title = f"Success Pattern: {task_id}"
            insights = [f"Task '{task_id}' completed successfully"]
            
            # Extract performance metrics from result for further analysis
            perf_metrics = []
            if 'duration_seconds' in result:
                perf_metrics.append(f"Duration: {result['duration_seconds']}s")
                
            if 'processed_records' in result:
                perf_metrics.append(f"Records processed: {result['processed_records']}")
            
            insights.extend(perf_metrics)
        else:
            title = f"Failure Pattern: {task_id}" 
            insights = [f"Task '{task_id}' failed with error"]
            
            # Extract failure details
            if 'error' in result and isinstance(result['error'], str):
                insights.append(f"Error type: {result['error']}")
                
        learning_entry = LearningEntry(
            id=f"learn_{len(self._entries) + 1:03d}",
            title=title,
            content_type="execution_insight",
            tags=["learning", "performance"],
            insights=insights, 
            improvement_suggestions=[]
        )
        
        self.add_learning(learning_entry)
    
    def get_recent_learnings(self) -> list:
        """Get most recent learnings that might be relevant for planning."""
        # Return entries sorted by creation time (most recent first)
        def sort_key(entry):
            created_at = getattr(entry, 'created_at', None)
            if created_at is None:
                return 0
            return created_at
        
        return sorted(
            [entry for entry in self._entries.values() if isinstance(entry, LearningEntry)],
            key=sort_key,
            reverse=True
        )

    def demo():
        """Demonstration of the Learning Engine."""
        
        # Create a learning engine instance  
        learner = LearningEngine()
    
        # Add some sample learnings 
        insight_entry_1 = LearningEntry(
            id="learn_perf_opt",
            title="Performance Optimization Insight", 
            content_type="execution_insight",
            tags=["learning", "performance"],
            insights=[
                "Chunked processing improves memory usage by 40%",
                "Batching requests reduces network overhead"
            ],
            improvement_suggestions=[  
                "Implement automatic chunk size adjustment",
                "Add connection pooling for better resource reuse" 
            ]
        )
        
        insight_entry_2 = LearningEntry(
            id="learn_error_handling", 
            title="Error Handling Pattern",
            content_type="execution_insight", 
            tags=["learning", "error_management"],
            insights=[
                "Retry mechanism with exponential backoff prevents timeout failures"
            ],
            improvement_suggestions=[]
        )

        learner.add_learning(insight_entry_1)
        learner.add_learning(insight_entry_2)

        print("=== Demo: Learning Engine ===\n")
        
        # Show summary 
        summary = learner.get_summary()
        print("--- Learning Summary ---")  
        for key, value in summary.items():
            if isinstance(value, dict):
                print(f"{key}: {value}")
            else:
                print(f"{key}: {value}")

if __name__ == "__main__":
    LearningEngine.demo()