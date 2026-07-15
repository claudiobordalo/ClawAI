import sys
import json
from pathlib import Path

# Garante que o diretório raiz está no path para imports
sys.path.append(r"D:/ClawAI")

try:
    from clawai.cognition.evolution_analyzer import EvolutionAnalyzer
    
    project_root = r"D:/ClawAI"
    analyzer = EvolutionAnalyzer(project_root)

    print("--- Iniciando Teste de Validação de AST ---")
    
    # Executa a análise
    if hasattr(analyzer, 'run_analysis'):
        analyzer.run_analysis()
    elif hasattr(analyzer, 'analyze'):
        analyzer.analyze()
    else:
        print(f"Métodos disponíveis no EvolutionAnalyzer: {dir(analyzer)}")

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
                # Imprime detalhes específicos para validar se a lógica de AST funcionou
                print(f"- [Tipo: {task.get('type')}] Descrição: {task.get('description')}")
        else:
            print("\n❌ Falha: Nenhuma tarefa foi gerada para 'test_target.py'.")
    else:
        print(f"\n❌ Erro: O arquivo {backlog_path} não existe.")

except Exception as e:
    import traceback
    traceback.print_exc()
