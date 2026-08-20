import json
import os
from typing import Dict, List, Any

def parse_growth_backlog(backlog_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Parses the growth_backlog.json and buckets functions into priority levels.
    This feeds the multi-step planner with actionable targets.
    
    Args:
        backlog_path (str): Path to the growth_backlog.json file.
        
    Returns:
        Dict[str, List]: A dictionary containing 'high_impact', 'medium', and 'routine' buckets.
    """
    if not os.path.exists(backlog_path):
        return {"error": f"Backlog file not found at {backlog_path}"}

    with open(backlog_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    buckets = {
        "high_impact": [],
        "medium": [],
        "routine": []
    }

    for item in data:
        # Logic for High Impact: Critical files or high cyclomatic complexity (> 10)
        is_critical = item.get('is_critical', False)
        complexity = item.get('complexity', 0)
        
        if is_critical or complexity > 10:
            buckets["high_impact"].append(item)
        elif complexity > 5:
            buckets["medium"].append(item)
        else:
            buckets["routine"].append(item)

    return buckets

if __name__ == "__main__":
    # Example usage for testing (assuming the file exists in the root or relative path)
    backlog_file = "growth_backlog.json"
    if os.path.exists(backlog_file):
        parsed_data = parse_growth_backlog(backlog_file)
        print(json.dumps(parsed_data, indent=2))
    else:
        print(f"Please ensure {backlog_file} exists to test the parser.")
