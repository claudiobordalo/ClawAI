import sys
sys.path.insert(0, 'D:/ClawAI/clawaii')

# Test the existing planner functionality directly 
from autonomy.planner import Planner

print("=== Testing Current Planner Implementation ===")

planner = Planner(max_steps=10)
objective = "Process user data files"
context = "Need to read input file, search for related info, then format output"

plan = planner.create_plan(objective, context) 

print(f"Created Plan: {plan['objective']}")
print(f"Steps: {plan['total_steps']}")

if plan["steps"]:
    print("\nPlan Steps:")
    for i, step in enumerate(plan["steps"]):  
        tool_info = f" using {step.get('tool_name', 'N/A')}" if step.get("tool_name") else ""
        depends_str = " (depends on: {})".format(", ".join(step.get("depends_on", []))) \
                     if step.get("depends_on") and len(step["depends_on"]) > 0 else ""  
        
        print(f"   {i+1}. {step['description']}{tool_info} - Priority:{step['priority']} {depends_str}")

# Test execution functionality
executed = []
while True:
    next_step = planner.get_next_step(executed) 
    if not next_step:  
        break
        
    print(f"\nExecuting step '{next_step.description}'")
    
    # Mark as done for simulation purposes
    executed.append(next_step.id)

summary = planner.get_plan_summary(executed)
print("\nPlan Summary:")
for key, value in summary.items():
    if isinstance(value, float):
        print(f"  {key}: {value:.1f}%")
    else:
        print(f"  {key}: {value}")

# Test saving/loading
try:
    planner.save_to_json('test_plan.json')
    loaded_planner = Planner.load_from_json('test_plan.json') 
    print("\n✓ Save/Load functionality works correctly")
except Exception as e:
    print(f"\n✗ Error with save/load: {e}")