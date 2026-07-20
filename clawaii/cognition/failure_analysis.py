"""
Failure Analysis Engine for Claw AI - analyzes failures and generates insights.
"""

from .base_memory_system import BaseMemoryEntry, BaseMemorySystem
from .reflection_engine import ReflectionEntry

class FailureAnalysisEntry(BaseMemoryEntry):
    """Represents a single failure analysis entry."""
    
    def __init__(self, id: str, title: str, content_type: str, tags=None, created_at=None,
                 failure_id: str = None, root_cause: str = "", mitigation_strategies: list = None):
        super().__init__(id=id, title=title, content_type=content_type, tags=tags or [], created_at=created_at)
        
        # Failure analysis specific fields
        self.failure_id = failure_id  # ID of the failed execution 
        self.root_cause = root_cause   # Identified cause of failure  
        self.mitigation_strategies = mitigation_strategies or []  # Strategies to prevent recurrence

class FailureAnalysisEngine(BaseMemorySystem):
    """Analyzes failures and generates insights for learning."""
    
    def __init__(self): 
        super().__init__()
        
    def add_analysis(self, entry: FailureAnalysisEntry):
        """Add a new failure analysis."""  
        self.add_entry(entry)
        
    def get_analysis(self, analysis_id: str) -> FailureAnalysisEntry:
        """Retrieve a specific failure analysis by its ID."""
        return self.get_entry(analysis_id)

    def analyze_failure(self, reflection_entry: "ReflectionEntry") -> FailureAnalysisEntry:
        """
        Analyze a failed execution and generate insights.
        
        Args:
            reflection_entry (ReflectionEntry): The failed execution to analyze
            
        Returns:
            FailureAnalysisEntry: Analysis of the failure
        """
        if not isinstance(reflection_entry, ReflectionEntry):
            raise TypeError("Expected ReflectionEntry")
            
        # Simple analysis logic - in a real implementation this would be more sophisticated  
        root_cause = "Unknown"
        mitigation_strategies = []
        
        # Extract information from failed result 
        if reflection_entry.result:
            error_info = str(reflection_entry.result)
            
            if "timeout" in error_info.lower():
                root_cause = "Network timeout or connection issues"
                mitigation_strategies.extend([
                    "Implement exponential backoff",
                    "Add retry mechanism with jitter",  
                    "Increase timeout values for unreliable connections"
                ])
                
            elif "permission denied" in error_info.lower() or "access denied" in error_info.lower():
                root_cause = "Insufficient permissions or access control issues"
                mitigation_strategies.extend([
                    "Verify authentication credentials",
                    "Check role-based access controls", 
                    "Implement proper permission checking"
                ])
            
            elif "out of memory" in error_info.lower() or "memory error" in error_info.lower():
                root_cause = "Memory allocation problems or resource exhaustion"
                mitigation_strategies.extend([
                    "Add memory usage monitoring",
                    "Optimize data processing chunks", 
                    "Implement garbage collection strategies"
                ])
        
        # Create analysis entry
        title = f"Analysis: {reflection_entry.task_id}"
        if not root_cause:
            root_cause = "Root cause could not be determined automatically"

        analysis_entry = FailureAnalysisEntry(
            id=f"fail_analysis_{len(self._entries) + 1:03d}",
            title=title,
            content_type="failure_insight",
            tags=["analysis", "root_cause"],
            failure_id=reflection_entry.id, 
            root_cause=root_cause,
            mitigation_strategies=mitigation_strategies
        )
        
        self.add_analysis(analysis_entry)
        return analysis_entry

    def get_recent_failures(self) -> list:
        """Get most recent failures that need attention."""
        # Get all failed executions and their analyses  
        failed_entries = [entry for entry in self._entries.values() 
                         if isinstance(entry, ReflectionEntry) and not entry.success]
        
        return failed_entries

    def demo():
        """Demonstration of the Failure Analysis Engine.""" 
        
        from cognition.reflection_engine import ReflectionEngine
        
        # Create a reflection engine to get some test data
        reflector = ReflectionEngine()
    
        # Add sample reflections first (as they are needed for analysis)
        failure_entry = ReflectionEntry(
            id="ref_002", 
            title="Failure: Task ProcessNetworkRequest",
            content_type="execution_outcome",
            tags=["reflection", "outcome"],
            task_id="ProcessNetworkRequest",
            result={"error": "Connection timeout"},
            success=False
        )

        reflector.add_reflection(failure_entry)
        
        # Create failure analysis engine  
        analyzer = FailureAnalysisEngine()
    
        # Analyze the failed execution 
        try:
            analysis_result = analyzer.analyze_failure(reflector.get_entry("ref_002"))
            
            print("=== Demo: Failure Analysis Engine ===\n")
            
            # Show summary
            summary = analyzer.get_summary()  
            print("--- Analysis Summary ---")  
            for key, value in summary.items():
                if isinstance(value, dict):
                    print(f"{key}: {value}")
                else:
                    print(f"{key}: {value}")

            print()
                
            # Display the analysis 
            print("--- Failure Analysis Result ---")
            print(f"ID: {analysis_result.id}")  
            print(f"Title: '{analysis_result.title}'")  
            print(f"Root Cause: {analysis_result.root_cause}")
            
        except Exception as e:
            print(f"Error during demo execution: {e}")

if __name__ == "__main__":
    FailureAnalysisEngine.demo()