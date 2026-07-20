"""
Memory System for Claw AI - stores contextual information and states.
"""

from dataclasses import dataclass, field  
import json 
from typing import Dict, List, Optional, Set
from collections import defaultdict

@dataclass 
class MemoryEntry:
    """Represents a single memory entry."""
    
    id: str  # Unique identifier for the memory entry (e.g., 'mem_001')
    title: str   # Title or summary of what this memory represents  
    content_type: str  # Type of information stored ('context', 'state') 
    tags: List[str] = field(default_factory=list)  # Tags to categorize the memory
    created_at: Optional[float] = None  # Timestamp when entry was added (optional)
    
    def __post_init__(self):
        if not self.tags:
            self.tags = [] 

class MemorySystem:
    """Manages a collection of memories with search and retrieval capabilities."""
    
    def __init__(self): 
        self._memories: Dict[str, MemoryEntry] = {}  # Store by ID
        self._tags_index: Dict[str, Set[str]] = defaultdict(set)  # Index memory IDs by tag  
        self._content_type_index: Dict[str, Set[str]] = defaultdict(set)
    
    def add_memory(self, entry: MemoryEntry):
        """Add a new memory to the system."""
        
        if not isinstance(entry, MemoryEntry): 
            raise TypeError("entry must be of type 'MemoryEntry'")
            
        # Add to main storage
        self._memories[entry.id] = entry
        
        # Update indices  
        for tag in entry.tags:
            self._tags_index[tag].add(entry.id)
        
        self._content_type_index[entry.content_type].add(entry.id) 
    
    def get_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """Retrieve a specific memory by its ID."""
        return self._memories.get(memory_id)
    
    def search_by_tag(self, tag: str) -> List[MemoryEntry]: 
        """Find all memories associated with the given tag.""" 
        
        entry_ids = self._tags_index.get(tag, set())  
        
        # Return actual entries
        return [self._memories[mid] for mid in entry_ids if mid in self._memories]
    
    def search_by_content_type(self, content_type: str) -> List[MemoryEntry]:
        """Find all memories of a specific type."""
        
        entry_ids = self._content_type_index.get(content_type, set())
        
        return [self._memories[mid] for mid in entry_ids if mid in self._memories]
    
    def search_by_text(self, query: str) -> List[MemoryEntry]:
        """Search memories by text content (title or tags)."""
        
        results = []
        query_lower = query.lower()
        
        # Iterate through all entries
        for mem_entry in self._memories.values():
            if (query_lower in mem_entry.title.lower() 
                or any(query_lower in tag.lower() for tag in mem_entry.tags)):
                
                results.append(mem_entry)
            
        return results
    
    def get_summary(self) -> Dict:
        """Get a summary of all memories."""
        
        total_entries = len(self._memories)
        
        # Count tags distribution
        tags_distribution: Dict[str, int] = defaultdict(int)
        for entry in self._memories.values():
            for tag in entry.tags:
                tags_distribution[tag] += 1
                
        content_types: Dict[str, int] = defaultdict(int) 
        for entry in self._memories.values():  
            content_types[entry.content_type] += 1
            
        return {
            "total_entries": total_entries,
            "tags_distribution": dict(tags_distribution),
            "content_types": dict(content_types)
        }
    
    def export_to_json(self, filepath: str):
        """Export all memories to a JSON file."""
        
        data = []
        for entry in self._memories.values():
            # Convert MemoryEntry to dictionary
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
        """Import memories from a JSON file."""
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            # Clear existing memory
            self._memories.clear()
            
            for entry_dict in data:
                entry = MemoryEntry(
                    id=entry_dict['id'],
                    title=entry_dict['title'], 
                    content_type=entry_dict['content_type'],
                    tags=entry_dict.get('tags', []),
                    created_at=entry_dict.get('created_at')
                )
                
                self.add_memory(entry)
        except FileNotFoundError:
            print(f"File {filepath} not found.")
            
    def demo():
        """Demonstration of the Memory System."""
        
        # Create a memory system instance
        mem_system = MemorySystem()
    
        # Add some sample memories  
        entry1 = MemoryEntry(
            id="mem_001",
            title="Staging Environment State", 
            content_type="context",
            tags=["environment_context", "staging"]
        )
        
        entry2 = MemoryEntry( 
            id="mem_002",
            title="Production Deployment Status",
            content_type="state",
            tags=["processing_state"]  
        )
    
        entry3 = MemoryEntry(
            id="mem_003", 
            title="Development Environment State",
            content_type="context", 
            tags=["environment_context", "development"]
        )

        mem_system.add_memory(entry1)
        mem_system.add_memory(entry2)   
        mem_system.add_memory(entry3)

        print("=== Demo: Memory System ===\n")
        
        # Show summary
        summary = mem_system.get_summary()
        print("--- Memory Summary ---")  
        for key, value in summary.items():
            if isinstance(value, dict):
                print(f"{key}: {value}")
            else:
                print(f"{key}: {value}")

        print() 
        
        # Search by tag 
        env_entries = mem_system.search_by_tag("environment_context")
        print("--- Entries tagged with 'environment_context' ---")  
        
        for entry in env_entries: 
            print(f"ID: {entry.id} | Title: '{entry.title}'")

        print()
            
        # Search by text
        staging_memories = mem_system.search_by_text("staging")
        print("--- Memories mentioning 'staging' ---")
        
        for entry in staging_memories:
            print(f"ID: {entry.id} | Content Type: {entry.content_type}")
    
if __name__ == "__main__":
    MemorySystem.demo()