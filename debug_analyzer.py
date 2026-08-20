import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.append(r"D:/ClawAI")

try:
    from clawai.cognition.evolution_analyzer import EvolutionAnalyzer
    analyzer = EvolutionAnalyzer(r"D:/ClawAI")
    print("Métodos da classe EvolutionAnalyzer:")
    for method in dir(analyzer):
        if not method.startswith("__"):
            print(f"- {method}")
except Exception as e:
    print(f"Erro: {e}")
