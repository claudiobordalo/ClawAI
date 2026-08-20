import sys
from pathlib import Path

# Ensure the project root is in the path
sys.path.append(r"D:/ClawAI")

try:
    from clawai.cognition.evolution_analyzer import EvolutionAnalyzer
    
    project_root = Path(r"D:/ClawAI")
    core_dir = project_root / "clawai"
    
    # Define exclusions to avoid noise and large libraries
    exclude_dirs = {'.git', '__pycache__', 'venv', '.venv', 'node_modules', '.idea', '.vscode'}
    
    print(f"--- Iniciando Análise de Evolução (Foco: {core_dir}) ---")
    # We pass the core directory to limit scope
    analyzer = EvolutionAnalyzer(str(core_dir))
    
    tasks = analyzer.analyze_project()
    
    # Salva o backlog
    analyzer.save_backlog(tasks)
    
    print(f"Sucesso! Total de tarefas identificadas: {len(tasks)}")
    
    categories = {}
    for t in tasks:
        categories[t.category] = categories.get(t.category, 0) + 1
        
    print("\nResumo por Categoria:")
    for cat, count in categories.items():
        print(f"- {cat}: {count}")
        
    high_priority = sorted([t for t in tasks if t.priority >= 4], key=lambda x: x.impact_score, reverse=True)[:10]
    if high_priority:
        print("\nTop Prioridades Críticas:")
        for i, task in enumerate(high_priority, 1):
            print(f"{i}. [{task.id}] {task.title} (Impacto: {task.impact_score}) - {task.description}")
    else:
        print("\nNenhuma tarefa de alta prioridade detectada.")

except Exception as e:
    import traceback
    traceback.print_exc()
