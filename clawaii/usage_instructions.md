# Como utilizar o Claw AI

## Estrutura do Projeto

O Claw AI é composto por três componentes principais localizados na pasta `cognition`:

1. **Memory System** (`memory_system.py`) - Gerencia informações contextuais e estados
2. **Learning Engine** (`learning_engine.py`) - Captura insights e padrões aprendidos 
3. **Planning Engine** (`planning.py`) - Gera planos de execução para tarefas

## Como usar cada componente individualmente

### Memory System (Sistema de Memória)
```python
from cognition.memory_system import MemorySystem, MemoryEntry

# Criar sistema de memória
mem_system = MemorySystem()

# Adicionar uma entrada de memória
entry = MemoryEntry("mem_001", "Estado do Ambiente de Staging", "context", ["environment_context"])
mem_system.add_memory(entry)

# Buscar por tags
results = mem_system.search_by_tag("environment_context")

# Exportar para JSON (persistência)
mem_system.export_to_json("memory_export.json")
```

### Learning Engine (Motor de Aprendizado)
```python
from cognition.learning_engine import LearningEngine, LearningEntry

# Criar motor de aprendizado  
learner = LearningEngine()

# Adicionar um insight de aprendizagem
learn_entry = LearningEntry(
    id="learn_001", 
    title="Eficiência do Processamento em Blocos",
    content_type="insight"
)
learner.add_learning(learn_entry)

# Obter insights mais recentes  
recent_learnings = learner.get_recent_learnings()

# Exportar para JSON
learner.export_to_json("learning_export.json")
```

### Planning Engine (Motor de Planejamento) 
```python
from cognition.planning import PlanningEngine, PlanningEntry

# Criar motor de planejamento
planner = PlanningEngine()

# Adicionar um plano  
plan_entry = PlanningEntry(
    id="plan_001", 
    title="Estratégia de Processamento em Bloco",
    content_type="initial_plan"
)
planner.add_plan(plan_entry)

# Buscar planos por tipo
plans = planner.search_by_content_type("initial_plan")

# Exportar para JSON  
planner.export_to_json("plan_export.json")
```

## Exemplo completo de integração

```python
from cognition.memory_system import MemorySystem, MemoryEntry
from cognition.learning_engine import LearningEngine, LearningEntry 
from cognition.planning import PlanningEngine, PlanningEntry

# Inicializar todos os componentes
memory = MemorySystem()
learning = LearningEngine()  
planner = PlanningEngine()

# Adicionar contexto inicial ao sistema de memória
context_entry = MemoryEntry("ctx_001", "Ambiente de Staging Ativo", "context", ["environment_context"])
memory.add_memory(context_entry)

# Gerar plano baseado no contexto existente 
plan_entry = PlanningEntry("plan_001", "Estratégia Inicial de Processamento", "initial_plan")
planner.add_plan(plan_entry)

print("Sistema Claw AI configurado e pronto para uso!")
```

## Executando testes

Para verificar se tudo está funcionando corretamente:

```bash
cd D:/ClawAI/clawaii
python test_integration_complete.py
```