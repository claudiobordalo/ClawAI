"""
Main integration demo showing how all cognitive components work together.
"""

import sys
import os

# Add the cognition directory to Python path  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'cognition'))

from cognition.memory_system import MemorySystem, MemoryEntry 
from cognition.learning_engine import LearningEngine, LearningEntry
from cognition.planning import PlanningEngine, PlanningEntry
from cognition.reflection_engine import ReflectionEngine, ReflectionEntry
from cognition.failure_analysis import FailureAnalysisEngine

def demo_integration():
    """Demonstrate the full integration of all cognitive components."""
    
    print("=== Claw AI Cognitive Architecture Integration Demo ===\n")
    
    # 1. Initialize all systems 
    memory_system = MemorySystem()
    learning_engine = LearningEngine()  
    planning_engine = PlanningEngine()
    reflection_engine = ReflectionEngine()
    failure_analyzer = FailureAnalysisEngine()

    print("--- Step 1: Initial Setup ---") 
    
    # Add some initial context to the memory system
    mem_entry_1 = MemoryEntry(
        id="mem_env_staging",
        title="Staging Environment State", 
        content_type="context",
        tags=["environment_context", "staging"]
    )
    
    mem_entry_2 = MemoryEntry(  
        id="mem_process_state",
        title="Processing Pipeline Status",
        content_type="state",
        tags=["processing_state"]  
    )

    memory_system.add_memory(mem_entry_1)
    memory_system.add_memory(mem_entry_2)   

    print("✓ Added initial context to Memory System")
    
    # 2. Planning Engine consults Memory System before generating plans
    print("\n--- Step 2: Planning with Context ---") 
    print("Planning engine consulting memory system for current state...")
    
    # Get relevant memories that might influence planning  
    env_context = memory_system.search_by_tag("environment_context")
    processing_state = memory_system.search_by_text("processing")

    plan_entry_1 = PlanningEntry(
        id="plan_batch_processing",
        title="Batch Processing Strategy", 
        content_type="initial_plan",
        tags=["planning", "batch_processing"]
    )
    
    planning_engine.add_plan(plan_entry_1)
    print("✓ Generated initial batch processing strategy")
        
    # 3. Simulate task execution with reflection
    print("\n--- Step 3: Execution and Reflection ---") 
    
    # Add a successful execution to the system 
    success_result = {
        "processed_records": 1500,
        "duration_seconds": 42,  
        "memory_used_mb": 89.5
    }
    
    reflection_engine.add_execution_result("ProcessBatchData", success_result, True)
    print("✓ Recorded successful execution: ProcessBatchData")
    
    # Add a failed execution to the system 
    failure_result = {
        "error": "Connection timeout",
        "attempted_retries": 3,
        "final_status": "failed"
    }
    
    reflection_engine.add_execution_result("ProcessNetworkRequest", failure_result, False)  
    print("✓ Recorded failed execution: ProcessNetworkRequest")
    
    # 4. Failure Analysis Engine processes failures
    print("\n--- Step 4: Analyzing Failures ---") 
    
    try:
        # Get the latest failed reflection 
        all_reflections = list(reflection_engine._entries.values())
        failure_refs = [r for r in all_reflections if isinstance(r, ReflectionEntry) and not r.success]
        
        if failure_refs:
            print("Analyzing failures...")
            
            # Analyze each failure
            for fail_ref in failure_refs: 
                analysis_result = failure_analyzer.analyze_failure(fail_ref)
                print(f"✓ Analysis completed for {fail_ref.task_id}")
                
    except Exception as e:
        print(f"Error during failure analysis: {e}")

    # 5. Learning Engine receives results from executions
    print("\n--- Step 5: Learning from Executions ---") 
    
    try:
        # Get all successful and failed reflections 
        success_reflections = reflection_engine.get_successful_executions()
        fail_reflections = reflection_engine.get_failed_executions() 
        
        for ref in success_reflections + fail_reflections:
            learning_entry_title = f"Insight: {ref.task_id} - {'Success' if ref.success else 'Failure'}"
            
            # Create a simple learning entry based on execution outcome
            learn_entry = LearningEntry(
                id=f"learn_{len(learning_engine._entries) + 1:03d}",
                title=learning_entry_title,
                content_type="execution_insight",
                tags=["learning", "performance"]
            )
            
            # Add to learning engine 
            if ref.success:
                learn_entry.tags.append("successful_execution")
            else:
                learn_entry.tags.append("failed_execution")  
                
            learning_engine.add_learning(learn_entry)
        
        print(f"✓ Added {len(success_reflections) + len(fail_reflections)} execution insights to Learning Engine")
            
    except Exception as e: 
        print(f"Error during learning process: {e}")
    
    # 6. Show system summaries
    print("\n--- Step 6: System Status ---") 
    
    try:
        mem_summary = memory_system.get_summary()
        learn_summary = learning_engine.get_summary()  
        plan_summary = planning_engine.get_summary()
        
        print("Memory System Summary:")
        for key, value in mem_summary.items():
            if isinstance(value, dict):
                print(f"  {key}: {value}")
            else:
                print(f"  {key}: {value}")

        print("\nLearning Engine Summary:")  
        for key, value in learn_summary.items():
            if isinstance(value, dict):
                print(f"  {key}: {value}") 
            else:
                print(f"  {key}: {value}")
                
        print("\nPlanning System Summary:")
        for key, value in plan_summary.items(): 
            if isinstance(value, dict):
                print(f"  {key}: {value}")
            else:
                print(f"  {key}: {value}")

    except Exception as e:  
        print(f"Error during summary generation: {e}")

    # Show final integration demo
    print("\n--- Integration Demo Complete ---")
    
if __name__ == "__main__":
    demo_integration()