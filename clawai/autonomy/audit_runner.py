import sys
import os
import json
from pathlib import Path
from typing import List

# Adiciona o diretório raiz ao PYTHONPATH para permitir imports do projeto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from clawai.cognition.evolution_analyzer import EvolutionAnalyzer

def run_audit(target_dir: str):
    project_root = Path(r"D:\ClawAI").resolve()
    target_path = Path(target_dir).resolve()
    
    if not target_path.exists():
        print(f"❌ Erro: O diretório {target_path} não existe.")
        return

    print(f"🚀 Iniciando Auditoria de Dívida Técnica em: {target_path}")
    
    analyzer = EvolutionAnalyzer(str(project_root))
    # A função analyze_project agora salva no growth_backlog.json automaticamente
    new_tasks = analyzer.analyze_project()
    
    print(f"✅ Auditoria concluída para {target_path}. {len(new_tasks)} novas tarefas identificadas.")

if __name__ == "__main__":
    # Se passar um argumento, usa ele como alvo, senão usa o core
    target = sys.argv[1] if len(sys.argv) > 1 else r"D:\ClawAI\clawai\core"
    run_audit(target)
