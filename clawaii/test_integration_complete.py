"""
Complete integration test for all Claw AI cognitive components.
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

def test_complete_integration():
    """Test the complete integration of all cognitive components."""
    
    print("=== Complete Claw AI Integration Test ===\n")
    
    # Initialize all systems 
    memory_system = MemorySystem()
    learning_engine = LearningEngine()  
    planning_engine = PlanningEngine()
    reflection_engine = ReflectionEngine()
    failure_analyzer = FailureAnalysisEngine()

    print("--- 1. Initial Setup ---") 
    
    # Add context to the memory system
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
    
    # Show current state
    mem_summary = memory_system.get_summary()
    print(f"  Current memories: {mem_summary['total_entries']}")
    
    print("\n--- 2. Planning with Context ---") 
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
        
    # Show current plans
    plan_summary = planning_engine.get_summary()
    print(f"  Current plans: {plan_summary['total_entries']}")
    
    print("\n--- 3. Execution and Reflection ---") 
    
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
    
    # Show reflections
    reflect_summary = reflection_engine.get_summary()
    print(f"  Total executions recorded: {reflect_summary['total_entries']}")
    
    print("\n--- 4. Analyzing Failures ---") 
    
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

    print("\n--- 5. Learning from Executions ---") 
    
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
    
    # Show current learnings
    learn_summary = learning_engine.get_summary()
    print(f"  Total learned patterns: {learn_summary['total_entries']}")
        
    print("\n--- 6. Next Planning with Learning ---") 
    
    try:
        # Get recent learnings to influence next planning  
        recent_learnings = learning_engine.get_recent_learnings() 
        
        if len(recent_learnings) > 0:
            plan_entry_2 = PlanningEntry(
                id="plan_improved_processing",
                title="Improved Processing Strategy", 
                content_type="refined_plan",
                tags=["planning", "improvement"]
            )
            
            planning_engine.add_plan(plan_entry_2)
            print("✓ Generated improved processing strategy incorporating learning")
        else:
            # Fallback plan if no learnings
            plan_entry_3 = PlanningEntry(
                id="plan_fallback",
                title="Fallback Processing Plan", 
                content_type="fallback_plan",
                tags=["planning"]
            )
            
            planning_engine.add_plan(plan_entry_3)
            print("✓ Generated fallback processing strategy")
        
        # Show final plans
        plan_summary_final = planning_engine.get_summary()
        print(f"  Total plans: {plan_summary_final['total_entries']}")
    
    except Exception as e:
        print(f"Error during next planning phase: {e}")

    print("\n--- Final System Status ---") 
    
    try:
        mem_summary = memory_system.get_summary()
        learn_summary = learning_engine.get_summary()  
        plan_summary = planning_engine.get_summary()
        
        print("Memory System:")
        for key, value in mem_summary.items():
            if isinstance(value, dict):
                print(f"  {key}: {value}")
            else:
                print(f"  {key}: {value}")

        print("\nLearning Engine:")  
        for key, value in learn_summary.items():
            if isinstance(value, dict):
                print(f"  {key}: {value}") 
            else:
                print(f"  {key}: {value}")
                
        print("\nPlanning System:")
        for key, value in plan_summary.items(): 
            if isinstance(value, dict):
                print(f"  {key}: {value}")
            else:
                print(f"  {key}: {value}")

    except Exception as e:  
        print(f"Error during summary generation: {e}")

    # Final demonstration
    print("\n--- Integration Complete ---")
    
if __name__ == "__main__":
    test_complete_integration()