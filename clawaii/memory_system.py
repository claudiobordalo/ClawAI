from __future__ import annotations

import json 
import time  
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, asdict  
from datetime import datetime


@dataclass
class MemoryEntry:
    """Data class to represent a single memory entry in the system."""
    
    # Core identification and metadata
    id: str  # Unique identifier for this specific memory item 
    goal_id: str  # Reference to associated task or objective
    
    # Content and context  
    content_type: str   # Type of information stored (e.g., 'plan', 'learning', 'observation')
    title: str          # Short descriptive title
    body: str           # Detailed memory content 
    
    # Contextual metadata 
    tags: List[str]     # Categorization labels for easy retrieval  
    context_info: Dict[str, Any]   # Execution environment or situation details
    
    timestamp: str = None  # ISO formatted datetime when entry was created 

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class MemorySystem:
    """Memory system for storing and retrieving contextual information."""
    
    def __init__(self, *, max_entries: int = 100) -> None:
        """
        Initialize the memory system.
        
        Args:
            max_entries (int): Maximum number of entries to keep in memory
        """ 
        self.entries: List[MemoryEntry] = []
        self.max_entries = max_entries
        
    def store(self, entry: MemoryEntry) -> None:
        """
        Store a new memory entry. 
        
        This method adds the provided entry and automatically manages size by removing oldest entries.
        
        Args:
            entry (MemoryEntry): The entry to be stored
        """ 
        # Add the new entry  
        self.entries.append(entry)
        
        # Maintain max_entries limit by dropping old ones if needed  
        while len(self.entries) > self.max_entries:  
            self.entries.pop(0)  # Remove oldest
            
    def retrieve_by_tag(self, tag: str, count: int = 5) -> List[MemoryEntry]:
        """
        Retrieve recent entries that have a specific tag.
        
        Args:
            tag (str): The tag to search for
            count (int): Maximum number of results to return
            
        Returns:
            list[MemoryEntry]: Entries matching this tag, sorted by recency  
        """ 
        # Filter and sort by timestamp in descending order (most recent first)
        filtered = [e for e in self.entries if tag.lower() in [t.lower() for t in e.tags]]
        
        return sorted(filtered, key=lambda x: datetime.fromisoformat(x.timestamp), reverse=True)[:count] 
    
    def retrieve_by_content_pattern(self, pattern: str) -> List[MemoryEntry]:
        """
        Find all entries where content contains a specific text pattern.
        
        Args:
            pattern (str): Pattern to search for in title or body
            
        Returns:
            list[MemoryEntry]: Entries with matching content  
        """ 
        # Filter by checking if any of the failed messages contain the pattern
        return [e for e in self.entries if pattern.lower() in str(e.title).lower() or pattern.lower() in str(e.body).lower()]
    
    def retrieve_by_context(self, context_key: str, 
                            context_value: Union[str, int]) -> List[MemoryEntry]:
        """
        Find all memory entries where a specific piece of contextual information matches.
        
        Args:
            context_key (str): The key in the `context_info` dict to filter on
            context_value (str | int): Value that should match
            
        Returns: 
            list[MemoryEntry]: Entries with matching context values  
        """ 
        # Filter entries by specified contextual value 
        return [e for e in self.entries if str(e.context_info.get(context_key, "")) == str(context_value)]
        
    def get_memory_summary(self) -> dict[str, Any]:
        """
        Generate a summary of all stored memory.
        
        Returns:
            dict: Summary including entry counts and tag distribution  
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
        
        return {
            "total_entries": total,
            "tags_distribution": tag_counts,
            "content_types": content_types  
        }
    
    def get_entry_by_id(self, entry_id: str) -> Optional[MemoryEntry]:
        """
        Find a specific memory entry by its unique ID (if it exists).
        
        Args:
            entry_id (str): The identifier for the desired entry
            
        Returns:
            MemoryEntry or None if not found
        """ 
        # In practice this would be more efficient with an index, but since we're keeping in memory,
        # just iterate through all entries to find match.
        for e in self.entries:  
            if str(e.id) == entry_id:
                return e
                
        return None
        
    def clear(self) -> None:
        """
        Clear all stored memory data. 
        """   
        self.entries.clear()
        
    def export_to_json(self, filepath: str = "memory_data.json") -> None:
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
        Import entries from a JSON file into this memory system.
        
        Args:
            filepath (str): Path to the source JSON file
        """  
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Convert back to MemoryEntry objects 
        self.entries.clear()  # Start fresh
        
        for entry_data in data:   
            try:
                # Create the memory object from serialized form  
                obj = MemoryEntry(**entry_data)  
                self.entries.append(obj)
                
            except Exception as e:
                print(f"Warning: Failed to import an entry due to {e}")
                continue
                
    def get_entries_since(self, timestamp: str) -> List[MemoryEntry]:
        """
        Get all entries that occurred after a specific datetime.
        
        Args:
            timestamp (str): ISO formatted date string 
            
        Returns:
            list[MemoryEntry]: Entries newer than the specified time
        """  
        try:
            filter_time = datetime.fromisoformat(timestamp)
            
            # Filter by comparing timestamps 
            return [e for e in self.entries if datetime.fromisoformat(e.timestamp) > filter_time]
        
        except Exception as ex:   
            print(f"Warning: Invalid timestamp provided. {ex}")
            return []
    
    def get_entries_by_type(self, content_type: str, limit: int = None) -> List[MemoryEntry]:
        """
        Get all entries of a specific type.
         
        Args:
            content_type (str): The type to filter by
            limit (int): Maximum number of results to return
            
        Returns:
            list[MemoryEntry]: Entries matching the specified type  
        """ 
        typed_entries = [e for e in self.entries if str(e.content_type).lower() == content_type.lower()] 
        
        # Sort by recency
        sorted_typed = sorted(typed_entries, key=lambda x: datetime.fromisoformat(x.timestamp), reverse=True)
        
        if limit is not None:
            return sorted_typed[:limit]
            
        return sorted_typed


# Example usage and test functions  
def demo_memory_system():
    """Demonstrate how to use the memory system."""
    
    # Create a new instance 
    engine = MemorySystem(max_entries=10)
    
    print("=== Demo: Memory System ===")
    
    # Test data
    entry1 = MemoryEntry(
        id="mem_001",
        goal_id="task_001",  
        content_type="plan",
        title="Batch Processing Strategy", 
        body="Process large files in chunks with retry logic.",
        tags=["planning", "batch_processing"],
        context_info={"environment": "production"}
    )
    
    entry2 = MemoryEntry(
        id="mem_002",
        goal_id="task_001",  
        content_type="learning",
        title="Improved Chunked Processing Strategy", 
        body="By implementing exponential backoff and increasing buffer size, we reduced timeouts by 85%.",
        tags=["planning", "batch_processing"],
        context_info={"environment": "staging"}
    )
    
    entry3 = MemoryEntry(
        id="mem_003",
        goal_id="task_002",  
        content_type="observation",
        title="Development Network Configuration Issue", 
        body="Adding firewall exception for port 8443 resolved connection refused errors.",
        tags=["network_issues"],
        context_info={"environment": "development"}
    )
    
    # Store entries
    engine.store(entry1)  
    engine.store(entry2)
    engine.store(entry3)

    print("\n--- Memory Summary ---")
    summary = engine.get_memory_summary()
    for key, value in summary.items():
        if isinstance(value, dict):
            print(f"{key}: {json.dumps(value, indent=2)}") 
        else:
            print(f"{key}: {value}")

    print("\n--- Entries tagged with 'planning' ---")
    planning_entries = engine.retrieve_by_tag("planning", count=5)
    for entry in planning_entries:  
        print(f"ID: {entry.id} | Title: '{entry.title}'")

    print("\n--- Memory entries mentioning 'batch processing' ---") 
    batch_entries = engine.retrieve_by_content_pattern("batch processing")
    for entry in batch_entries:
        print(f"ID: {entry.id} | Content Type: {entry.content_type}")


if __name__ == "__main__":
    demo_memory_system()