# Claw AI - Cognitive Modules

This directory contains the core cognitive modules for the Claw AI system, including planning, memory management, and learning capabilities.

## Overview 

The claw ai framework is designed to support autonomous task execution with built-in reasoning, memory retention, and adaptive learning. The following components are included:

- **Planning Engine**: For creating, managing, and refining plans
- **Memory System**: To store contextual information for retrieval during tasks  
- **Learning Engine**: Captures insights from executed actions

## Structure 

```
claw_ai/
├── __init__.py 
│   └─ Initializes the main package.
├── cognition/  
│   ├── __init__.py
│   ├── planning.py      # Planning logic and plan management
│   ├── memory_system.py  # Memory storage for contextual data
│   └── learning_engine.py # Learning from task execution outcomes 
└── README.md            # This file
```

## Usage

These modules can be imported directly:

```python
from claw_ai.cognition import PlanningEngine, MemorySystem, LearningEngine

# Initialize components  
planner = PlanningEngine()
memory = MemorySystem() 
learner = LearningEngine()

# Use them in your workflow...
```