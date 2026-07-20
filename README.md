# Claw AI - Cognitive Architecture

This repository contains the cognitive modules for Claw AI, including memory systems, learning engines, and planning capabilities.

## Overview 

The system consists of three main cognitive components:

1. **Memory System**: Stores contextual information and states.
2. **Learning Engine**: Captures insights and patterns from processing experiences.
3. **Planning Engine**: Generates execution plans based on learned knowledge and current context.

Each component provides:
- Storage mechanisms for structured data
- Search capabilities by tags, content types, or text 
- Export/import functionality (JSON format)
- Demo scripts to showcase usage

## Getting Started 

To use these components in your project:

```python
from clawaii.cognition import MemorySystem, LearningEngine, PlanningEngine

# Initialize the systems  
memory_system = MemorySystem()
learning_engine = LearningEngine() 
planning_engine = PlanningEngine()

# Add entries and perform searches as needed...
```

## Directory Structure  

- `clawaii/cognition/` - Core cognitive modules
  - `memory_system.py` - Manages contextual memories
  - `learning_engine.py` - Stores insights and patterns  
  - `planning.py` - Generates execution plans

Each module includes:
- Data structures for representing entries 
- Storage mechanisms with indexing capabilities
- Search functions (by tag, content type, text)
- Export/import methods 

## Usage Examples  

The modules provide demo functionality that can be run directly:

```bash
python clawaii/cognition/memory_system.py  
python clawaii/cognition/learning_engine.py
python clawaii/cognition/planning.py
```

Each will output a summary of its contents and demonstrate search capabilities.