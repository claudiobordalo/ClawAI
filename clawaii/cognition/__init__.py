"""
Cognitive modules for Claw AI.
"""

# This file makes the cognition directory a Python package

__version__ = "0.1.0"
__author__ = "Claw AI Team"

from .memory_system import MemorySystem, MemoryEntry 
from .learning_engine import LearningEngine, LearningEntry
from .planning import PlanningEngine, PlanningEntry 

# Export main classes for easy importing  
__all__ = [
    'MemorySystem', 
    'MemoryEntry',
    'LearningEngine',
    'LearningEntry',
    'PlanningEngine',
    'PlanningEntry'
]