from __future__ import annotations

import json 
import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict  
from datetime import datetime


@dataclass
class ReflectionEntry:
    """Data class to represent a single reflection entry in the engine."""
    
    # Core identification and metadata
    goal_id: str  # Unique identifier for this specific objective 
    goal_title: str  # Short title or description of the goal
    
    # Outcome tracking  
    success: bool  # Whether the overall task was successful (True) or failed (False)
    what_failed: List[str]  # Specific error messages that occurred 
    
    # Context and decision information
    risks: List[str]   # Potential future problems identified 
    opportunities: List[str]  # Positive outcomes or improvements found
    
    decisions: List[str]  # Key decisions made during the process  
    duration: float  # Time taken for this iteration (in seconds)
    
    # Additional metadata that can be used to improve learning
    timestamp: str = None  # ISO formatted datetime when entry was created 
    metadata: Dict[str, Any] = None  # Extra information about execution context
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        
        if self.metadata is None:
            self.metadata = {}
            
    
class ReflectionEngine:
    """Enhanced reflection engine for learning from past iterations and improving future performance."""
    
    def __init__(self, *, max_entries: int = 100) -> None:
        """
        Initialize the reflection engine.
        
        Args:
            max_entries (int): Maximum number of entries to keep in memory
        """ 
        self.entries: List[ReflectionEntry] = []
        self.max_entries = max_entries
        
    def record(self, entry: ReflectionEntry) -> None:
        """
        Record a new reflection entry. 
        
        This method adds the provided entry and automatically manages size by removing oldest entries.
        
        Args:
            entry (ReflectionEntry): The entry to be recorded
        """ 
        # Add the new entry  
        self.entries.append(entry)
        
        # Maintain max_entries limit by dropping old ones if needed  
        while len(self.entries) > self.max_entries:  
            self.entries.pop(0)  # Remove oldest
            
    def get_recent_by_goal_id(self, goal_id: str, count: int = 5) -> List[ReflectionEntry]:
        """
        Retrieve recent entries for a specific goal ID.
        
        Args:
            goal_id (str): The unique identifier of the goal
            count (int): Maximum number of recent entries to retrieve
            
        Returns:
            list[ReflectionEntry]: Recent entries matching this goal id, sorted by recency  
        """ 
        # Filter and sort by timestamp in descending order (most recent first)
        filtered = [e for e in self.entries if e.goal_id == goal_id]
        
        return sorted(filtered, key=lambda x: datetime.fromisoformat(x.timestamp), reverse=True)[:count] 
    
    def repeated_errors(self, min_count: int = 2) -> List[str]:
        """
        Find errors that have occurred repeatedly (at least `min_count` times).
        
        Args:
            min_count (int): Minimum number of occurrences to consider an error 'repeated'
            
        Returns:
            list[str]: Error messages that appear more than the minimum count
        """ 
        # Count all unique error messages across entries  
        error_counts = {}
        for entry in self.entries:  
            for err_msg in entry.what_failed:
                if isinstance(err_msg, str):
                    key = err_msg.lower()  # Normalize case to avoid duplicates due to capitalization differences 
                    error_counts[key] = error_counts.get(key, 0) + 1
                    
        # Return only errors that meet the minimum count threshold
        return [err for err, cnt in error_counts.items() if cnt >= min_count]
    
    def get_summary_statistics(self) -> dict[str, Any]:
        """
        Generate summary statistics about all recorded entries.
        
        Returns:
            dict: Summary of success rates, common errors and other metrics  
        """ 
        total = len(self.entries)
        if not self.entries:
            return {"total_entries": 0}
            
        # Calculate overall success rate
        successes = sum(1 for e in self.entries if e.success)  
        failure_rate = (total - successes) / max(total, 1)
        
        # Get most common errors 
        all_errors = []
        for entry in self.entries:
            all_errors.extend(entry.what_failed)
            
        error_counts = {}
        for err in all_errors:   
            key = str(err).lower()
            if isinstance(key, str):
                error_counts[key] = error_counts.get(key, 0) + 1
                
        most_common_error = max(error_counts.items(), key=lambda x: x[1])[0] if error_counts else None
        
        # Calculate average duration
        durations = [e.duration for e in self.entries]
        avg_duration = sum(durations) / len(durations)
        
        return {
            "total_entries": total,
            "success_rate": successes / max(total, 1),
            "failure_rate": failure_rate,
            "most_common_error": most_common_error,
            "average_duration_seconds": avg_duration
        }
    
    def get_entry_by_id(self, entry_id: str) -> Optional[ReflectionEntry]:
        """
        Find a specific entry by its unique ID (if it exists).
        
        Args:
            entry_id (str): The identifier for the desired entry
            
        Returns:
            ReflectionEntry or None if not found
        """ 
        # In practice this would be more efficient with an index, but since we're keeping in memory,
        # just iterate through all entries to find match.
        for e in self.entries:  
            if str(e.goal_id) == entry_id:
                return e
                
        return None
        
    def clear(self) -> None:
        """
        Clear all stored reflection data. 
        """   
        self.entries.clear()
        
    def export_to_json(self, filepath: str = "reflection_data.json") -> None:
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
        Import entries from a JSON file into this engine.
        
        Args:
            filepath (str): Path to the source JSON file
        """  
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Convert back to ReflectionEntry objects 
        self.entries.clear()  # Start fresh
        
        for entry_data in data:   
            try:
                # Create the reflection object from serialized form  
                obj = ReflectionEntry(**entry_data)  
                self.entries.append(obj)
                
            except Exception as e:
                print(f"Warning: Failed to import an entry due to {e}")
                continue
                
    def get_entries_since(self, timestamp: str) -> List[ReflectionEntry]:
        """
        Get all entries that occurred after a specific datetime.
        
        Args:
            timestamp (str): ISO formatted date string 
            
        Returns:
            list[ReflectionEntry]: Entries newer than the specified time
        """  
        try:
            filter_time = datetime.fromisoformat(timestamp)
            
            # Filter by comparing timestamps 
            return [e for e in self.entries if datetime.fromisoformat(e.timestamp) > filter_time]
        
        except Exception as ex:   
            print(f"Warning: Invalid timestamp provided. {ex}")
            return []
    
    def get_successful_entries(self, limit: int = None) -> List[ReflectionEntry]:
        """
        Get all successful entries.
         
        Args:
            limit (int): Maximum number of results to return
            
        Returns:
            list[ReflectionEntry]: Successful entries  
        """ 
        success_entries = [e for e in self.entries if e.success] 
        
        # Sort by recency
        sorted_success = sorted(success_entries, key=lambda x: datetime.fromisoformat(x.timestamp), reverse=True)
        
        if limit is not None:
            return sorted_success[:limit]
            
        return sorted_success
        
    def get_failed_entries(self, limit: int = None) -> List[ReflectionEntry]:
        """
        Get all failed entries.
         
        Args:
            limit (int): Maximum number of results to return
            
        Returns:
            list[ReflectionEntry]: Failed entries  
        """ 
        fail_entries = [e for e in self.entries if not e.success] 
        
        # Sort by recency
        sorted_failures = sorted(fail_entries, key=lambda x: datetime.fromisoformat(x.timestamp), reverse=True)
        
        if limit is not None:
            return sorted_failures[:limit]
            
        return sorted_failures


# Example usage and test functions  
def demo_reflection_engine():
    """Demonstrate how to use the reflection engine."""
    
    # Create a new instance 
    engine = ReflectionEngine(max_entries=10)
    
    print("=== Demo: Reflection Engine ===")
    
    # Test data
    entry1 = ReflectionEntry(
        goal_id="task_001",
        goal_title="Process files",  
        success=True,
        what_failed=[],
        risks=["disk space"],
        opportunities=[], 
        decisions=["use batch processing"], 
        duration=2.5, 
        metadata={"iteration": 3}
    )
    
    entry2 = ReflectionEntry(
        goal_id="task_001",
        goal_title="Process files",  
        success=False,
        what_failed=["timeout after 60 seconds"],
        risks=[], 
        opportunities=[],
        decisions=["retry with timeout increase"], 
        duration=3.7,   
        metadata={"iteration": 4}
    )
    
    entry3 = ReflectionEntry(
        goal_id="task_002",
        goal_title="Data analysis",  
        success=False,
        what_failed=["connection refused"],
        risks=[], 
        opportunities=[],
        decisions=["check network connection"], 
        duration=1.8,   
        metadata={"iteration": 1}
    )
    
    # Record entries
    engine.record(entry1)  
    engine.record(entry2)
    engine.record(entry3)

    print("\n--- Summary Statistics ---")
    stats = engine.get_summary_statistics()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"{key}: {value:.2f}")
        else:
            print(f"{key}: {value}")

    print("\n--- Repeated Errors (min 2 occurrences) ---") 
    repeated = engine.repeated_errors(min_count=2)
    for err in repeated:  
        print(f"Error: '{err}'")

    print("\n--- Recent Entries for task_001 ---")
    recent = engine.get_recent_by_goal_id("task_001", count=5) 
    for entry in recent:
        status_str = "SUCCESS" if entry.success else "FAILURE"
        print(f"[{status_str}] {entry.goal_title} ({entry.timestamp}) - Duration: {entry.duration}s")

if __name__ == "__main__":
    demo_reflection_engine()