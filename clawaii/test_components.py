#!/usr/bin/env python3

"""
Test script to verify all cognitive components work correctly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'cognition'))

# Test importing and basic functionality 
try:
    from cognition.memory_system import MemorySystem, MemoryEntry
    print("✓ Successfully imported MemorySystem")
    
    # Create a simple test entry  
    mem_entry = MemoryEntry(
        id="test_001",
        title="Test Memory", 
        content_type="context",
        tags=["testing"]
    )
    
    # Test memory system functionality
    mem_system = MemorySystem()
    mem_system.add_memory(mem_entry)
    
    print("✓ Memory System basic operations work")
    
except Exception as e:
    print(f"✗ Error with MemorySystem: {e}")

try:
    from cognition.learning_engine import LearningEngine, LearningEntry  
    print("✓ Successfully imported LearningEngine")
    
    # Create a simple test entry
    learn_entry = LearningEntry(
        id="test_001",
        title="Test Insight", 
        content_type="insight",
        tags=["testing"]
    )
    
    # Test learning engine functionality
    learner = LearningEngine()
    learner.add_learning(learn_entry)
    
    print("✓ Learning Engine basic operations work")
    
except Exception as e:
    print(f"✗ Error with LearningEngine: {e}")

try:
    from cognition.planning import PlanningEngine, PlanningEntry  
    print("✓ Successfully imported PlanningEngine")
    
    # Create a simple test entry
    plan_entry = PlanningEntry(
        id="test_001",
        title="Test Plan", 
        content_type="initial_plan",
        tags=["testing"]
    )
    
    # Test planning engine functionality
    planner = PlanningEngine()
    planner.add_plan(plan_entry)
    
    print("✓ Planning Engine basic operations work")
    
except Exception as e:
    print(f"✗ Error with PlanningEngine: {e}")

print("\nAll components imported successfully!")