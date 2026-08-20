import sys
from pathlib import Path
import json

# Adiciona o diretório da cognição ao path para importação direta
sys.path.append(r"D:/ClawAI/clawai/cognition")

try:
    from evolution_analyzer import EvolutionAnalyzer
    
    project_root = r"D:/ClawAI"
    analyzer = EvolutionAnalyzer(project_root)

    print("--- Iniciando Teste de Validação de AST (Modo Direto) ---")
    
    # Executa a análise
    tasks = analyzer.analyze_project()
    print(f"Total de tarefas detectadas: {len(tasks)}")

    # Verificar o resultado no growth_backlog.json
    backlog_path = Path(project_root) / "growth_backlog.json"
    if backlog_path.exists():
        with open(backlog_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Filtrar tarefas relacionadas ao nosso arquivo de teste sintético
        relevant_tasks = [task for task in data if "test_target.py" in str(task.get("file", ""))]
        
        if relevant_tasks:
            print(f"\n✅ Sucesso! Foram encontradas {len(relevant_tasks)} tarefas para 'test_target.py':")
            for task in relevant_tasks:
                print(f"- [Tipo: {task.get('type')}] Descrição: {task.get('description')}")
        else:
            print("\n❌ Falha: Nenhuma tarefa foi gerada para 'test_target.py'.")
    else:
        print(f"\n❌ Erro: O arquivo {backlog_path} não existe.")

except Exception as e:
    import traceback
    traceback.print_exc()
