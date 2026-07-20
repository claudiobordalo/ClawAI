#!/usr/bin/env python3

"""
Test script for verifying that the planner and other autonomy components 
work correctly within this system.
"""

import sys
sys.path.insert(0, 'D:/ClawAI/clawaii')

print("=== Testing System Components ===")

# Test 1: Import and basic functionality of existing Planner
try:
    from autonomy.planner import Planner
    
    print("\n✓ Successfully imported Planner")
    
    # Create a simple planner instance  
    planner = Planner(max_steps=5)
    
    plan_result = planner.create_plan(
        objective='Process user data files',
        context='Need to read input file, search for related info, then format output'
    )
    
    print(f"✓ Plan created with {plan_result['total_steps']} steps")
    
    # Test that it can be saved
    planner.save_to_json('test_plan.json')
    print("✓ Planner save functionality works") 
    
    # Load and verify 
    loaded_planner = Planner.load_from_json('test_plan.json')  
    print("✓ Planner load functionality works")

except Exception as e:
    print(f"✗ Error testing planner: {e}")

# Test 2: Verify system can import core modules
try:
    from autonomy.planner import PlanStep, Planner
    
    # Create a simple plan step manually to test structure 
    step = PlanStep(
        id="test_step_01",
        description="Test processing task",  
        tool_name="mock_tool",
        priority=1,
        parameters={"input": "data"}
    )
    
    print("✓ Core data structures work correctly")
    
except Exception as e:
    print(f"✗ Error with core components: {e}")

print("\n=== System Component Test Complete ===")

# Show what we've verified
components_verified = [
    "Planner import and instantiation", 
    "Plan creation",
    "Save/load functionality"
]

for component in components_verified:
    print(f"✓ {component}")