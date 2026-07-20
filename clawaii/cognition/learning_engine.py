"""
Learning Engine for Claw AI - stores insights and patterns learned from processing.
"""

from dataclasses import dataclass, field  
import json 
from typing import Dict, List, Optional, Set
from collections import defaultdict

@dataclass 
class LearningEntry:
    """Represents a single learning entry."""
    
    id: str  # Unique identifier for the insight (e.g., 'learn_001')
    title: str   # Title or summary of what was learned  
    content_type: str  # Type of information stored ('insight', 'pattern') 
    tags: List[str] = field(default_factory=list)  # Tags to categorize the learning
    created_at: Optional[float] = None  # Timestamp when entry was added (optional)
    
    def __post_init__(self):
        if not self.tags:
            self.tags = [] 

class LearningEngine:
    """Manages a collection of learned insights and patterns with search capabilities."""
    
    def __init__(self): 
        self._learnings: Dict[str, LearningEntry] = {}  # Store by ID
        self._tags_index: Dict[str, Set[str]] = defaultdict(set)  # Index learning IDs by tag  
        self._content_type_index: Dict[str, Set[str]] = defaultdict(set)
    
    def add_learning(self, entry: LearningEntry):
        """Add a new learning to the system."""
        
        if not isinstance(entry, LearningEntry): 
            raise TypeError("entry must be of type 'LearningEntry'")
            
        # Add to main storage
        self._learnings[entry.id] = entry
        
        # Update indices  
        for tag in entry.tags:
            self._tags_index[tag].add(entry.id)
        
        self._content_type_index[entry.content_type].add(entry.id) 
    
    def get_learning(self, learning_id: str) -> Optional[LearningEntry]:
        """Retrieve a specific learning by its ID."""
        return self._learnings.get(learning_id)
    
    def search_by_tag(self, tag: str) -> List[LearningEntry]: 
        """Find all learnings associated with the given tag.""" 
        
        entry_ids = self._tags_index.get(tag, set())  
        
        # Return actual entries
        return [self._learnings[mid] for mid in entry_ids if mid in self._learnings]
    
    def search_by_content_type(self, content_type: str) -> List[LearningEntry]:
        """Find all learnings of a specific type."""
        
        entry_ids = self._content_type_index.get(content_type, set())
        
        return [self._learnings[mid] for mid in entry_ids if mid in self._learnings]
    
    def search_by_text(self, query: str) -> List[LearningEntry]:
        """Search learnings by text content (title or tags)."""
        
        results = []
        query_lower = query.lower()
        
        # Iterate through all entries
        for learning_entry in self._learnings.values():
            if (query_lower in learning_entry.title.lower() 
                or any(query_lower in tag.lower() for tag in learning_entry.tags)):
                
                results.append(learning_entry)
            
        return results
    
    def get_summary(self) -> Dict:
        """Get a summary of all learnings."""
        
        total_entries = len(self._learnings)
        
        # Count tags distribution
        tags_distribution: Dict[str, int] = defaultdict(int)
        for entry in self._learnings.values():
            for tag in entry.tags:
                tags_distribution[tag] += 1
                
        content_types: Dict[str, int] = defaultdict(int) 
        for entry in self._learnings.values():  
            content_types[entry.content_type] += 1
            
        return {
            "total_entries": total_entries,
            "tags_distribution": dict(tags_distribution),
            "content_types": dict(content_types)
        }
    
    def export_to_json(self, filepath: str):
        """Export all learnings to a JSON file."""
        
        data = []
        for entry in self._learnings.values():
            # Convert LearningEntry to dictionary
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
        """Import learnings from a JSON file."""
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            # Clear existing learning
            self._learnings.clear()
            
            for entry_dict in data:
                entry = LearningEntry(
                    id=entry_dict['id'],
                    title=entry_dict['title'], 
                    content_type=entry_dict['content_type'],
                    tags=entry_dict.get('tags', []),
                    created_at=entry_dict.get('created_at')
                )
                
                self.add_learning(entry)
        except FileNotFoundError:
            print(f"File {filepath} not found.")
            
    def demo():
        """Demonstration of the Learning Engine."""
        
        # Create a learning engine instance
        learner = LearningEngine()
    
        # Add some sample learnings  
        entry1 = LearningEntry(
            id="learn_001",
            title="Chunked Processing Efficiency", 
            content_type="insight",
            tags=["performance_optimization"]
        )
        
        entry2 = LearningEntry( 
            id="learn_002",
            title="Retry Logic Pattern for Network Failures",
            content_type="pattern",
            tags=["retry_strategy"]  
        )
    
        entry3 = LearningEntry(
            id="learn_003", 
            title="Handling Temporary Network Issues in Batch Processing",
            content_type="insight",
            tags=["network_issues"]
        )

        learner.add_learning(entry1)
        learner.add_learning(entry2)   
        learner.add_learning(entry3)

        print("=== Demo: Learning Engine ===\n")
        
        # Show summary
        summary = learner.get_summary()
        print("--- Learning Summary ---")  
        for key, value in summary.items():
            if isinstance(value, dict):
                print(f"{key}: {value}")
            else:
                print(f"{key}: {value}")

        print() 
        
        # Search by tag 
        perf_entries = learner.search_by_tag("performance_optimization")
        print("--- Entries tagged with 'performance_optimization' ---")  
        
        for entry in perf_entries: 
            print(f"ID: {entry.id} | Title: '{entry.title}'")

        print()
            
        # Search by text
        retry_insights = learner.search_by_text("retry")
        print("--- Insights mentioning 'retry' ---")
        
        for entry in retry_insights:
            print(f"ID: {entry.id} | Content Type: {entry.content_type}")
    
if __name__ == "__main__":
    LearningEngine.demo()