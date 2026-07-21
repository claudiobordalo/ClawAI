# Claw AI - Cognitive Architecture

This project implements the cognitive architecture for Claw AI, consisting of three core components that work together to manage memory, learning, and planning.

## Components Overview

### 1. Memory System (`memory_system.py`)
- Stores contextual information and states 
- Manages different types of memories (contextual data, processing state)
- Provides search capabilities by tags and content type
- Supports import/export functionality for persistence

### 2. Learning Engine (`learning_engine.py`)  
- Captures insights and patterns learned from AI processing
- Maintains a repository of performance optimizations and best practices
- Enables the system to improve over time through learning

### 3. Planning Engine (`planning.py`)
- Generates execution plans for tasks 
- Manages different stages of plan development (initial, refined)
- Provides search capabilities similar to other components

## Architecture Design

All three components share a common base class `BaseMemorySystem` that provides:
- Unified data structures with consistent interfaces
- Indexing by tags and content types  
- Search functionality across text content
- Export/import capabilities for persistence
- Summary statistics generation

This design ensures consistency while allowing each component to specialize in its specific domain.

## Usage Examples

Each component includes a demo method that shows basic usage:

```python
# Memory System example 
from cognition.memory_system import MemorySystem, MemoryEntry
mem_system = MemorySystem()
entry = MemoryEntry("mem_001", "Staging Environment State", "context", ["environment_context"])
mem_system.add_memory(entry)

# Learning Engine example  
from cognition.learning_engine import LearningEngine, LearningEntry
learner = LearningEngine() 
learn_entry = LearningEntry("learn_001", "Chunked Processing Efficiency", "insight")
learner.add_learning(learn_entry)

# Planning Engine example
from cognition.planning import PlanningEngine, PlanningEntry
planner = PlanningEngine()
plan_entry = PlanningEntry("plan_001", "Batch Processing Strategy", "initial_plan")  
planner.add_plan(plan_entry)
```

## Key Features

- **Unified Interface**: All components follow the same pattern for adding, retrieving, and searching entries
- **Flexible Tagging System**: Entries can be tagged with multiple categories for easy retrieval 
- **Content Type Classification**: Differentiates between various types of information stored
- **Persistent Storage**: Export to/from JSON format for data persistence  
- **Search Capabilities**: Text search across titles and tags

## Directory Structure 

```
cognition/
├── base_memory_system.py     # Common infrastructure shared by all components
├── memory_system.py          # Memory management component 
├── learning_engine.py        # Learning and pattern recognition component
└── planning.py               # Planning and execution strategy component  
```

Each file is designed to be self-contained while leveraging the common functionality from `base_memory_system.py`.