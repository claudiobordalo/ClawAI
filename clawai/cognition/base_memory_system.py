"""
Base Memory System for Claw AI - provides common infrastructure 
for memory management across different cognitive components.
"""

from dataclasses import dataclass, field  
import json 
from typing import Dict, List, Optional, Set
from collections import defaultdict

@dataclass
class BaseMemoryEntry:
    """Represents a single memory entry with basic metadata."""
    
    id: str  # Unique identifier for the entry (e.g., 'mem_001')
    title: str   # Title or summary of what this entry represents  
    content_type: str  # Type of information stored ('context', 'state', etc.) 
    tags: List[str] = field(default_factory=list)  # Tags to categorize the entry
    created_at: Optional[float] = None  # Timestamp when entry was added (optional)
    
    def __post_init__(self):
        if not self.tags:
            self.tags = [] 

class BaseMemorySystem:
    """Base class that provides common memory management infrastructure."""
    
    def __init__(self): 
        self._entries: Dict[str, BaseMemoryEntry] = {}  # Store by ID
        self._tags_index: Dict[str, Set[str]] = defaultdict(set)  # Index entry IDs by tag  
        self._content_type_index: Dict[str, Set[str]] = defaultdict(set)
    
    def add_entry(self, entry):
        """Add a new entry to the system."""
        
        if not isinstance(entry, BaseMemoryEntry): 
            raise TypeError("entry must be of type 'BaseMemoryEntry'")
            
        # Add to main storage
        self._entries[entry.id] = entry
        
        # Update indices  
        for tag in entry.tags:
            self._tags_index[tag].add(entry.id)
        
        self._content_type_index[entry.content_type].add(entry.id) 
    
    def get_entry(self, entry_id: str) -> Optional[BaseMemoryEntry]:
        """Retrieve a specific entry by its ID."""
        return self._entries.get(entry_id)
    
    def search_by_tag(self, tag: str) -> List[BaseMemoryEntry]: 
        """Find all entries associated with the given tag.""" 
        
        entry_ids = self._tags_index.get(tag, set())  
        
        # Return actual entries
        return [self._entries[mid] for mid in entry_ids if mid in self._entries]
    
    def search_by_content_type(self, content_type: str) -> List[BaseMemoryEntry]:
        """Find all entries of a specific type."""
        
        entry_ids = self._content_type_index.get(content_type, set())
        
        return [self._entries[mid] for mid in entry_ids if mid in self._entries]
    
    def search_by_text(self, query: str) -> List[BaseMemoryEntry]:
        """Search entries by text content (title or tags)."""
        
        results = []
        query_lower = query.lower()
        
        # Iterate through all entries
        for mem_entry in self._entries.values():
            if (query_lower in mem_entry.title.lower() 
                or any(query_lower in tag.lower() for tag in mem_entry.tags)):
                
                results.append(mem_entry)
            
        return results
    
    def get_summary(self) -> Dict:
        """Get a summary of all entries."""
        
        total_entries = len(self._entries)
        
        # Count tags distribution
        tags_distribution: Dict[str, int] = defaultdict(int)
        for entry in self._entries.values():
            for tag in entry.tags:
                tags_distribution[tag] += 1
                
        content_types: Dict[str, int] = defaultdict(int) 
        for entry in self._entries.values():  
            content_types[entry.content_type] += 1
            
        return {
            "total_entries": total_entries,
            "tags_distribution": dict(tags_distribution),
            "content_types": dict(content_types)
        }
    
    def export_to_json(self, filepath: str):
        """Export all entries to a JSON file."""
        
        data = []
        for entry in self._entries.values():
            # Convert BaseMemoryEntry to dictionary
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
        """Import entries from a JSON file."""
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            # Clear existing memory
            self._entries.clear()
            
            for entry_dict in data:
                entry = BaseMemoryEntry(
                    id=entry_dict['id'],
                    title=entry_dict['title'], 
                    content_type=entry_dict['content_type'],
                    tags=entry_dict.get('tags', []),
                    created_at=entry_dict.get('created_at')
                )
                
                self.add_entry(entry)
        except FileNotFoundError:
            print(f"File {filepath} not found.")