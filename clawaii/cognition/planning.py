"""
Planning Engine for Claw AI - generates and manages execution plans.
"""

from dataclasses import dataclass, field  
import json 
from typing import Dict, List, Optional, Set
from collections import defaultdict

@dataclass 
class PlanningEntry:
    """Represents a single planning entry."""
    
    id: str  # Unique identifier for the plan (e.g., 'plan_001')
    title: str   # Title or summary of what this plan represents  
    content_type: str  # Type of information stored ('initial_plan', 'refined_plan') 
    tags: List[str] = field(default_factory=list)  # Tags to categorize the plan
    created_at: Optional[float] = None  # Timestamp when entry was added (optional)
    
    def __post_init__(self):
        if not self.tags:
            self.tags = [] 

class PlanningEngine:
    """Manages a collection of plans with search and retrieval capabilities."""
    
    def __init__(self): 
        self._plans: Dict[str, PlanningEntry] = {}  # Store by ID
        self._tags_index: Dict[str, Set[str]] = defaultdict(set)  # Index plan IDs by tag  
        self._content_type_index: Dict[str, Set[str]] = defaultdict(set)
    
    def add_plan(self, entry: PlanningEntry):
        """Add a new plan to the system."""
        
        if not isinstance(entry, PlanningEntry): 
            raise TypeError("entry must be of type 'PlanningEntry'")
            
        # Add to main storage
        self._plans[entry.id] = entry
        
        # Update indices  
        for tag in entry.tags:
            self._tags_index[tag].add(entry.id)
        
        self._content_type_index[entry.content_type].add(entry.id) 
    
    def get_plan(self, plan_id: str) -> Optional[PlanningEntry]:
        """Retrieve a specific plan by its ID."""
        return self._plans.get(plan_id)
    
    def search_by_tag(self, tag: str) -> List[PlanningEntry]: 
        """Find all plans associated with the given tag.""" 
        
        entry_ids = self._tags_index.get(tag, set())  
        
        # Return actual entries
        return [self._plans[mid] for mid in entry_ids if mid in self._plans]
    
    def search_by_content_type(self, content_type: str) -> List[PlanningEntry]:
        """Find all plans of a specific type."""
        
        entry_ids = self._content_type_index.get(content_type, set())
        
        return [self._plans[mid] for mid in entry_ids if mid in self._plans]
    
    def search_by_text(self, query: str) -> List[PlanningEntry]:
        """Search plans by text content (title or tags)."""
        
        results = []
        query_lower = query.lower()
        
        # Iterate through all entries
        for plan_entry in self._plans.values():
            if (query_lower in plan_entry.title.lower() 
                or any(query_lower in tag.lower() for tag in plan_entry.tags)):
                
                results.append(plan_entry)
            
        return results
    
    def get_summary(self) -> Dict:
        """Get a summary of all plans."""
        
        total_entries = len(self._plans)
        
        # Count tags distribution
        tags_distribution: Dict[str, int] = defaultdict(int)
        for entry in self._plans.values():
            for tag in entry.tags:
                tags_distribution[tag] += 1
                
        content_types: Dict[str, int] = defaultdict(int) 
        for entry in self._plans.values():  
            content_types[entry.content_type] += 1
            
        return {
            "total_entries": total_entries,
            "tags_distribution": dict(tags_distribution),
            "content_types": dict(content_types)
        }
    
    def export_to_json(self, filepath: str):
        """Export all plans to a JSON file."""
        
        data = []
        for entry in self._plans.values():
            # Convert PlanningEntry to dictionary
            entry_dict = {
                'id': entry.id,
                'title': entry.title,
                'content_type': entry.content_type, 
                'tags': entry.tags,
                'created_at': entry.created_at  
            }
            
            data.append(entry_dict)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def import_from_json(self, filepath: str):
        """Import plans from a JSON file."""
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            # Clear existing plan
            self._plans.clear()
            
            for entry_dict in data:
                entry = PlanningEntry(
                    id=entry_dict['id'],
                    title=entry_dict['title'], 
                    content_type=entry_dict['content_type'],
                    tags=entry_dict.get('tags', []),
                    created_at=entry_dict.get('created_at')
                )
                
                self.add_plan(entry)
        except FileNotFoundError:
            print(f"File {filepath} not found.")
            
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