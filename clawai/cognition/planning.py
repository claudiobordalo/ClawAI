"""
Planning Engine for Claw AI - generates and manages execution plans.
"""

from .base_memory_system import BaseMemoryEntry, BaseMemorySystem

class PlanningEntry(BaseMemoryEntry):
    """Represents a single planning entry."""
    
    def __init__(self, id: str, title: str, content_type: str, tags=None, created_at=None):
        super().__init__(id=id, title=title, content_type=content_type, tags=tags or [], created_at=created_at)

class PlanningEngine(BaseMemorySystem):
    """Manages a collection of plans with search and retrieval capabilities."""
    
    def __init__(self): 
        super().__init__()
        
    def add_plan(self, entry: PlanningEntry):
        """Add a new plan to the system."""
        self.add_entry(entry)
        
    def get_plan(self, plan_id: str) -> PlanningEntry:
        """Retrieve a specific plan by its ID."""
        return self.get_entry(plan_id)
    
    def demo():
        """Demonstration of the Planning Engine."""
        
        # Create a planning engine instance
        planner = PlanningEngine()
    
        # Add some sample plans  
        entry1 = PlanningEntry(
            id="plan_001",
            title="Batch Processing Strategy", 
            content_type="initial_plan",
            tags=["planning", "batch_processing"]
        )
        
        entry2 = PlanningEntry( 
            id="plan_002",
            title="Improved Chunked Processing Strategy",
            content_type="refined_plan",
            tags=["planning", "chunking"]  
        )
    
        entry3 = PlanningEntry(
            id="plan_003", 
            title="Network Retry Logic Implementation",
            content_type="initial_plan",
            tags=["network_issues", "retry_strategy"]
        )

        planner.add_plan(entry1)
        planner.add_plan(entry2)   
        planner.add_plan(entry3)

        print("=== Demo: Planning Engine ===\n")
        
        # Show summary
        summary = planner.get_summary()
        print("--- Plan Summary ---")  
        for key, value in summary.items():
            if isinstance(value, dict):
                print(f"{key}: {value}")
            else:
                print(f"{key}: {value}")

        print() 
        
        
        # Search by tag 
        planning_entries = planner.search_by_tag("planning")
        print("--- Entries tagged with 'planning' ---")  
        
        for entry in planning_entries: 
            print(f"ID: {entry.id} | Title: '{entry.title}'")

        print()
            
        # Search by text
        batch_plans = planner.search_by_text("batch processing")
        print("--- Plans mentioning 'batch processing' ---")
        
        for entry in batch_plans:
            print(f"ID: {entry.id} | Content Type: {entry.content_type}")
    
if __name__ == "__main__":
    PlanningEngine.demo()