from __future__ import annotations

import json 
import time  
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, asdict  
from datetime import datetime


@dataclass
class LearningEntry:
    """Data class to represent a single learning entry in the system."""
    
    # Core identification and metadata
    id: str  # Unique identifier for this specific learning item 
    goal_id: str  # Reference to associated task or objective
    
    # Content and context  
    content_type: str   # Type of information stored (e.g., 'plan_improvement', 'error_resolution')
    title: str          # Short descriptive title
    body: str           # Detailed learning content 
    
    # Contextual metadata 
    tags: List[str]     # Categorization labels for easy retrieval  
    context_info: Dict[str, Any]   # Execution environment or situation details
    
    timestamp: str = None  # ISO formatted datetime when entry was created 

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class LearningEngine:
    """Learning engine for capturing and analyzing insights from task execution."""
    
    def __init__(self, *, max_entries: int = 100) -> None:
        """
        Initialize the learning engine.
        
        Args:
            max_entries (int): Maximum number of entries to keep in memory
        """ 
        self.entries: List[LearningEntry] = []
        self.max_entries = max_entries
        
    def store(self, entry: LearningEntry) -> None:
        """
        Store a new learning entry. 
        
        This method adds the provided entry and automatically manages size by removing oldest entries.
        
        Args:
            entry (LearningEntry): The entry to be stored
        """ 
        # Add the new entry  
        self.entries.append(entry)
        
        # Maintain max_entries limit by dropping old ones if needed  
        while len(self.entries) > self.max_entries:  
            self.entries.pop(0)  # Remove oldest
            
    def retrieve_by_tag(self, tag: str, count: int = 5) -> List[LearningEntry]:
        """
        Retrieve recent entries that have a specific tag.
        
        Args:
            tag (str): The tag to search for
            count (int): Maximum number of results to return
            
        Returns:
            list[LearningEntry]: Entries matching this tag, sorted by recency  
        """ 
        # Filter and sort by timestamp in descending order (most recent first)
        filtered = [e for e in self.entries if tag.lower() in [t.lower() for t in e.tags]]
        
        return sorted(filtered, key=lambda x: datetime.fromisoformat(x.timestamp), reverse=True)[:count] 
    
    def retrieve_by_content_pattern(self, pattern: str) -> List[LearningEntry]:
        """
        Find all entries where content contains a specific text pattern.
        
        Args:
            pattern (str): Pattern to search for in title or body
            
        Returns:
            list[LearningEntry]: Entries with matching content  
        """ 
        # Filter by checking if any of the failed messages contain the pattern
        return [e for e in self.entries if pattern.lower() in str(e.title).lower() or pattern.lower() in str(e.body).lower()]
    
    def retrieve_by_context(self, context_key: str, 
                            context_value: Union[str, int]) -> List[LearningEntry]:
        """
        Find all learning entries where a specific piece of contextual information matches.
        
        Args:
            context_key (str): The key in the `context_info` dict to filter on
            context_value (str | int): Value that should match
            
        Returns: 
            list[LearningEntry]: Entries with matching context values  
        """ 
        # Filter entries by specified contextual value 
        return [e for e in self.entries if str(e.context_info.get(context_key, "")) == str(context_value)]
        
    def get_learning_summary(self) -> dict[str, Any]:
        """
        Generate a summary of all stored learning insights.
        
        Returns:
            dict: Summary including entry counts and key metrics  
        """ 
        total = len(self.entries)
        if not self.entries:
            return {"total_entries": 0}
            
        # Get frequency count for each tag
        tag_counts = {}
        for entry in self.entries:
            for tag in entry.tags:
                key = str(tag).lower()
                tag_counts[key] = tag_counts.get(key, 0) + 1
                
        content_types = {}  
        for entry in self.entries:
            ct = entry.content_type
            if isinstance(ct, str):
                key = ct.lower() 
                content_types[key] = content_types.get(key, 0) + 1
        
        # Calculate success/failure metrics based on content analysis (simplified)
        
        return {
            "total_entries": total,
            "tags_distribution": tag_counts,
            "content_types": content_types  
        }
    
    def get_entry_by_id(self, entry_id: str) -> Optional[LearningEntry]:
        """
        Find a specific learning entry by its unique ID (if it exists).
        
        Args:
            entry_id (str): The identifier for the desired entry
            
        Returns:
            LearningEntry or None if not found
        """ 
        # In practice this would be more efficient with an index, but since we're keeping in memory,
        # just iterate through all entries to find match.
        for e in self.entries:  
            if str(e.id) == entry_id:
                return e
                
        return None
        
    def clear(self) -> None:
        """
        Clear all stored learning data. 
        """   
        self.entries.clear()
        
    def export_to_json(self, filepath: str = "learning_data.json") -> None:
        """
        Export the entire set of entries to a JSON file.
         
        Args:
            filepath (str): Path where the exported JSON should be saved
        """  
        # Convert each entry into serializable dict form 
        serialized_entries = [asdict(entry) for entry in self.entries] 
        
        with open(filepath, 'w', encoding='utf-8') as f:   
            json.dump(serialized_entries, f, ensure_ascii=False, indent=2)
            
    def import_from_json(self, filepath: str) -> None:
        """
        Import entries from a JSON file into this learning engine.
        
        Args:
            filepath (str): Path to the source JSON file
        """  
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Convert back to LearningEntry objects 
        self.entries.clear()  # Start fresh
        
        for entry_data in data:   
            try:
                # Create the learning object from serialized form  
                obj = LearningEntry(**entry_data)  
                self.entries.append(obj)
                
            except Exception as e:
                print(f"Warning: Failed to import an entry due to {e}")
                continue
                
    def get_entries_since(self, timestamp: str) -> List[LearningEntry]:
        """
        Get all entries that occurred after a specific datetime.
        
        Args:
            timestamp (str): ISO formatted date string 
            
        Returns:
            list[LearningEntry]: Entries newer than the specified time
        """  
        try:
            filter_time = datetime.fromisoformat(timestamp)
            
            # Filter by comparing timestamps 
            return [e for e in self.entries if datetime.fromisoformat(e.timestamp) > filter_time]
        
        except Exception as ex:   
            print(f"Warning: Invalid timestamp provided. {ex}")
            return []
    
    def get_entries_by_type(self, content_type: str, limit: int = None) -> List[LearningEntry]:
        """
        Get all entries of a specific type.
         
        Args:
            content_type (str): The type to filter by
            limit (int): Maximum number of results to return
            
        Returns:
            list[LearningEntry]: Entries matching the specified type  
        """ 
        typed_entries = [e for e in self.entries if str(e.content_type).lower() == content_type.lower()] 
        
        # Sort by recency
        sorted_typed = sorted(typed_entries, key=lambda x: datetime.fromisoformat(x.timestamp), reverse=True)
        
        if limit is not None:
            return sorted_typed[:limit]
            
        return sorted_typed


# Example usage and test functions  
def demo_learning_engine():
    """Demonstrate how to use the learning engine."""
    
    # Create a new instance 
    engine = LearningEngine(max_entries=10)
    
    print("=== Demo: Learning Engine ===")
    
    # Test data
    entry1 = LearningEntry(
        id="learn_001",
        goal_id="task_001",  
        content_type="plan_improvement",
        title="Batch Processing Strategy Improvement", 
        body="By implementing exponential backoff and increasing buffer size, we reduced timeouts by 85%.",
        tags=["planning", "batch_processing"],
        context_info={"environment": "staging"}
    )
    
    entry2 = LearningEntry(
        id="learn_002",
        goal_id="task_001",  
        content_type="error_resolution",
        title="Staging Timeout Fix Applied", 
        body="Timeouts were resolved by adjusting retry logic and adding timeout exceptions to the configuration.",
        tags=["errors", "timeout_fix"],
        context_info={"environment": "staging"}
    )
    
    entry3 = LearningEntry(
        id="learn_003",
        goal_id="task_002",  
        content_type="network_insight",
        title="Development Network Configuration Issue Resolved", 
        body="Adding firewall exception for port 8443 resolved connection refused errors.",
        tags=["network_issues"],
        context_info={"environment": "development"}
    )
    
    # Store entries
    engine.store(entry1)  
    engine.store(entry2)
    engine.store(entry3)

    print("\n--- Learning Summary ---")
    summary = engine.get_learning_summary()
    for key, value in summary.items():
        if isinstance(value, dict):
            print(f"{key}: {json.dumps(value, indent=2)}") 
        else:
            print(f"{key}: {value}")

    print("\n--- Entries tagged with 'errors' ---")
    error_entries = engine.retrieve_by_tag("errors", count=5)
    for entry in error_entries:  
        print(f"ID: {entry.id} | Title: '{entry.title}'")

    print("\n--- Learning entries mentioning 'timeout' ---") 
    timeout_entries = engine.retrieve_by_content_pattern("timeout")
    for entry in timeout_entries:
        print(f"ID: {entry.id} | Content Type: {entry.content_type}")


if __name__ == "__main__":
    demo_learning_engine()