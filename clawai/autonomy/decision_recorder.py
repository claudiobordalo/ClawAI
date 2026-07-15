import json
import os
from datetime import datetime
from typing import Dict, Any

def record_decision(category: str, rationale: str, impact: str, decision_id: str) -> str:
    """
    Records an architectural or refactoring decision as a structured JSON file.
    This allows for clean RAG indexing of the ClawAI's evolution history.
    
    Args:
        category (str): Type of decision (e.g., 'architecture', 'refactor', 'infrastructure')
        rationale (str): The reasoning behind the decision.
        impact (str): The expected impact on the system.
        decision_id (str): A unique identifier for the decision (e.g., 'DEC-001').
        
    Returns:
        str: The path to the saved JSON file.
    """
    # Ensure the recorder directory exists
    base_dir = os.path.dirname(os.path.abspath(__file__))
    recorder_dir = os.path.join(base_dir, "recorder_")
    if not os.path.exists(recorder_dir):
        os.makedirs(recorder_dir)

    # Generate filename based on timestamp and ID
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{decision_id}.json"
    file_path = os.path.join(recorder_dir, filename)

    decision_data = {
        "decision_id": decision_id,
        "timestamp": datetime.now().isoformat(),
        "category": category,
        "rationale": rationale,
        "impact": impact,
        "metadata": {
            "source": "autonomy_module",
            "version": "1.0.0"
        }
    }

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(decision_data, f, indent=4, ensure_ascii=False)

    return file_path

if __name__ == "__main__":
    # Example usage for testing
    record_decision(
        category="architecture",
        rationale="Switching to AST-based analysis in evolution_analyzer.py to improve accuracy of complexity metrics.",
        impact="High - Enables more precise identification of technical debt and critical code paths.",
        decision_id="DEC-001"
    )
