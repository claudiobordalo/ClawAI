from __future__ import annotations

import json 
import time  
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, asdict  
from datetime import datetime


@dataclass
class PlanningEntry:
    """Data class to represent a single planning entry in the engine."""
    
    # Core identification and metadata
    id: str  # Unique identifier for this specific plan iteration 
    goal_id: str  # Reference to associated task or objective
    
    # Execution tracking  
    success: bool  # Whether the overall task was successful (True) or failed (False)
    what_failed: List[str]  # Specific error messages that occurred 
    
    # Context and decision information
    context_info: Dict[str, Any]   # Information about execution environment 
    plan_summary: str  # Summary of actions planned for this iteration
    
    duration: float  # Time taken for this iteration (in seconds)
    
    timestamp: str = None  # ISO formatted datetime when entry was created 
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class PlanningEngine:
    """Enhanced planning engine that tracks iterations and provides feedback loops."""
    
    def __init__(self, *, max_entries: int = 100) -> None:
        """
        Initialize the planning engine.
        
        Args:
            max_entries (int): Maximum number of entries to keep in memory
        """ 
        self.entries: List[PlanningEntry] = []
        self.max_entries = max_entries
        
    def record(self, entry: PlanningEntry) -> None:
        """
        Record a new planning entry. 
        
        This method adds the provided entry and automatically manages size by removing oldest entries.
        
        Args:
            entry (PlanningEntry): The entry to be recorded
        """ 
        # Add the new entry  
        self.entries.append(entry)
        
        # Maintain max_entries limit by dropping old ones if needed  
        while len(self.entries) > self.max_entries:  
            self.entries.pop(0)  # Remove oldest
            
    def get_recent_by_goal_id(self, goal_id: str, count: int = 5) -> List[PlanningEntry]:
        """
        Retrieve recent entries for a specific goal ID.
        
        Args:
            goal_id (str): The unique identifier of the goal
            count (int): Maximum number of recent entries to retrieve
            
        Returns:
            list[PlanningEntry]: Recent entries matching this goal id, sorted by recency  
        """ 
        # Filter and sort by timestamp in descending order (most recent first)
        filtered = [e for e in self.entries if e.goal_id == goal_id]
        
        return sorted(filtered, key=lambda x: datetime.fromisoformat(x.timestamp), reverse=True)[:count] 
    
    def get_insights_by_context(self, context_key: str, 
                                context_value: Union[str, int]) -> List[PlanningEntry]:
        """
        Find all planning entries where a specific piece of contextual information matches.
        
        Args:
            context_key (str): The key in the `context_info` dict to filter on
            context_value (str | int): Value that should match
            
        Returns: 
            list[PlanningEntry]: Entries with matching context values  
        """ 
        # Filter entries by specified contextual value 
        return [e for e in self.entries if str(e.context_info.get(context_key, "")) == str(context_value)]
        
    def get_insights_by_failure(self, error_pattern: str) -> List[PlanningEntry]:
        """
        Find all planning entries where the failure message contains a pattern.
        
        Args:
            error_pattern (str): Pattern to search for in what_failed
            
        Returns:
            list[PlanningEntry]: Entries with matching failures  
        """ 
        # Filter by checking if any of the failed messages contain the pattern
        return [e for e in self.entries if any(error_pattern.lower() in err.lower() for err in e.what_failed)]
    
    def get_insights_summary(self) -> dict[str, Any]:
        """
        Generate a summary of all planning insights.
        
        Returns:
            dict: Summary including success rate and key learnings  
        """ 
        total = len(self.entries)
        if not self.entries:
            return {"total_entries": 0}
            
        # Calculate overall success rate
        successes = sum(1 for e in self.entries if e.success)  
        failure_rate = (total - successes) / max(total, 1)
        
        # Get most common failures 
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
    
    def get_entry_by_id(self, entry_id: str) -> Optional[PlanningEntry]:
        """
        Find a specific planning entry by its unique ID (if it exists).
        
        Args:
            entry_id (str): The identifier for the desired entry
            
        Returns:
            PlanningEntry or None if not found
        """ 
        # In practice this would be more efficient with an index, but since we're keeping in memory,
        # just iterate through all entries to find match.
        for e in self.entries:  
            if str(e.id) == entry_id:
                return e
                
        return None
        
    def clear(self) -> None:
        """
        Clear all stored planning data. 
        """   
        self.entries.clear()
        
    def export_to_json(self, filepath: str = "planning_data.json") -> None:
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
            
        # Convert back to PlanningEntry objects 
        self.entries.clear()  # Start fresh
        
        for entry_data in data:   
            try:
                # Create the planning object from serialized form  
                obj = PlanningEntry(**entry_data)  
                self.entries.append(obj)
                
            except Exception as e:
                print(f"Warning: Failed to import an entry due to {e}")
                continue
                
    def get_entries_since(self, timestamp: str) -> List[PlanningEntry]:
        """
        Get all entries that occurred after a specific datetime.
        
        Args:
            timestamp (str): ISO formatted date string 
            
        Returns:
            list[PlanningEntry]: Entries newer than the specified time
        """  
        try:
            filter_time = datetime.fromisoformat(timestamp)
            
            # Filter by comparing timestamps 
            return [e for e in self.entries if datetime.fromisoformat(e.timestamp) > filter_time]
        
        except Exception as ex:   
            print(f"Warning: Invalid timestamp provided. {ex}")
            return []
    
    def get_successful_entries(self, limit: int = None) -> List[PlanningEntry]:
        """
        Get all successful entries.
         
        Args:
            limit (int): Maximum number of results to return
            
        Returns:
            list[PlanningEntry]: Successful entries  
        """ 
        success_entries = [e for e in self.entries if e.success] 
        
        # Sort by recency
        sorted_success = sorted(success_entries, key=lambda x: datetime.fromisoformat(x.timestamp), reverse=True)
        
        if limit is not None:
            return sorted_success[:limit]
            
        return sorted_success
        
    def get_failed_entries(self, limit: int = None) -> List[PlanningEntry]:
        """
        Get all failed entries.
         
        Args:
            limit (int): Maximum number of results to return
            
        Returns:
            list[PlanningEntry]: Failed entries  
        """ 
        fail_entries = [e for e in self.entries if not e.success] 
        
        # Sort by recency
        sorted_failures = sorted(fail_entries, key=lambda x: datetime.fromisoformat(x.timestamp), reverse=True)
        
        if limit is not None:
            return sorted_failures[:limit]
            
        return sorted_failures


# Example usage and test functions  
def demo_planning_engine():
    """Demonstrate how to use the planning engine."""
    
    # Create a new instance 
    engine = PlanningEngine(max_entries=10)
    
    print("=== Demo: Planning Engine ===")
    
    # Test data
    entry1 = PlanningEntry(
        id="plan_001",
        goal_id="task_001",  
        success=True,
        what_failed=[],
        context_info={"environment": "production"},
        plan_summary="Batch process large files in chunks with retry logic.",
        duration=2.5
    )
    
    entry2 = PlanningEntry(
        id="plan_002",
        goal_id="task_001",  
        success=False,
        what_failed=["timeout after 60 seconds"],
        context_info={"environment": "staging"},
        plan_summary="Process large files in chunks with retry logic.",
        duration=3.7
    )
    
    entry3 = PlanningEntry(
        id="plan_003",
        goal_id="task_002",  
        success=False,
        what_failed=["connection refused"],
        context_info={"environment": "development"},
        plan_summary="Establish secure network connection to remote server.",
        duration=1.8
    )
    
    # Record entries
    engine.record(entry1)  
    engine.record(entry2)
    engine.record(entry3)

    print("\n--- Insights Summary ---")
    summary = engine.get_insights_summary()
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"{key}: {value:.2f}")
        else:
            print(f"{key}: {value}")

    print("\n--- Planning Entries from Staging Environment ---") 
    staging_entries = engine.get_insights_by_context("environment", "staging")
    for entry in staging_entries:  
        print(f"ID: {entry.id} | Plan Summary: '{entry.plan_summary}'")

    print("\n--- Planning Entries with Timeout Failures ---")
    timeout_entries = engine.get_insights_by_failure("timeout") 
    for entry in timeout_entries:
        print(f"ID: {entry.id} | Failure: {', '.join(entry.what_failed)}")


if __name__ == "__main__":
    demo_planning_engine()