"""
Memory System for Claw AI - stores contextual information and states.
"""

from .base_memory_system import BaseMemoryEntry, BaseMemorySystem

class MemoryEntry(BaseMemoryEntry):
    """Represents a single memory entry."""
    
    def __init__(self, id: str, title: str, content_type: str, tags=None, created_at=None):
        super().__init__(id=id, title=title, content_type=content_type, tags=tags or [], created_at=created_at)

class MemorySystem(BaseMemorySystem):
    """Manages a collection of memories with search and retrieval capabilities."""
    
    def __init__(self): 
        super().__init__()
        
    def add_memory(self, entry: MemoryEntry):
        """Add a new memory to the system."""
        self.add_entry(entry)
        
    def get_memory(self, memory_id: str) -> MemoryEntry:
        """Retrieve a specific memory by its ID."""
        return self.get_entry(memory_id)
    
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