from __future__ import annotations

import json
import os
import ast
from pathlib import Path
from dataclasses import dataclass, field
from collections import Counter, defaultdict
from typing import List, Dict, Any, Set, Tuple

@dataclass
class EvolutionTask:
    id: str
    title: str
    description: str
    priority: int  # 1 (Low) to 5 (Critical)
    category: str  # e.g., "Refactoring", "Modernization", "Performance", "Security"
    status: str  # "backlog", "planned", "in_progress", "completed"
    impact_score: float
    requirements: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "category": self.category,
            "status": self.status,
            "impact_score": self.impact_score,
            "requirements": self.requirements,
            "metadata": self.metadata
        }

class ComplexityVisitor(ast.NodeVisitor):
    """Calcula a complexidade ciclomática avançada de funções e métodos."""
    def __init__(self):
        self.complexity = 1
        self.max_nesting = 0
        self.current_nesting = 0

    def visit_If(self, node):
        self.complexity += 1
        self.current_nesting += 1
        self.max_nesting = max(self.max_nesting, self.current_nesting)
        self.generic_visit(node)
        self.current_nesting -= 1

    def visit_While(self, node):
        self.complexity += 1
        self.current_nesting += 1
        self.max_nesting = max(self.max_nesting, self.current_nesting)
        self.generic_visit(node)
        self.current_nesting -= 1

    def visit_For(self, node):
        self.complexity += 1
        self.current_nesting += 1
        self.max_nesting = max(self.max_nesting, self.current_nesting)
        self.generic_visit(node)
        self.current_nesting -= 1

    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_ListComp(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_DictComp(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_SetComp(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_GeneratorExp(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_With(self, node):
        self.complexity += 1
        self.current_nesting += 1
        self.max_nesting = max(self.max_nesting, self.current_nesting)
        self.generic_visit(node)
        self.current_nesting -= 1

    def visit_MatchCase(self, node):
        self.complexity += 1
        self.generic_visit(node)

class EvolutionAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.backlog_path = self.project_root / "growth_backlog.json"
        # Cache para evitar re-análise
        self._function_signatures = {}

    def analyze_project(self) -> List[EvolutionTask]:
        """
        Realiza uma análise técnica profunda para identificar oportunidades de evolução.
        Inclui: Complexidade, Acoplamento, Código Duplicado e Tipagem.
        """
        tasks = []
        files_scanned = 0
        import_counts_in = Counter() # Fan-in
        import_counts_out = defaultdict(set) # Fan-out (sets of relative paths)
        
        # 1. Mapear dependências (Fan-in e Fan-out)
        self._map_dependencies(import_counts_in, import_counts_out)

        # 2. Coletar assinaturas para detecção de duplicação
        self._collect_function_signatures()

        # 3. Analisar arquivos
        for path in self.project_root.rglob("*.py"):
            if any(part in path.parts for part in ["__pycache__", ".git", "node_modules", "dist", ".ai_toolbox_backups"]):
                continue
            
            files_scanned += 1
            relative_path = str(path.relative_to(self.project_root))
            
            # A. Análise de Acoplamento (Fan-in/Fan-out)
            fan_in = import_counts_in.get(relative_path, 0)
            fan_out = len(import_counts_out.get(relative_path, set()))
            
            # Prioridade baseada em acoplamento
            coupling_priority = 1
            if fan_in > 10: coupling_priority = 5
            elif fan_in > 5: coupling_priority = 4
            elif fan_in > 3: coupling_priority = 3
            
            # B. Checagem de Tamanho de Arquivo
            size = path.stat().st_size
            if size > 30000:
                tasks.append(EvolutionTask(
                    id=f"EVO-{len(tasks)+1}",
                    title=f"Modularizar {path.name}",
                    description=f"Arquivo excessivamente grande ({size} bytes). Recomenda-se divisão em módulos menores.",
                    priority=3,
                    category="Refactoring",
                    status="backlog",
                    impact_score=0.7,
                    requirements=[relative_path]
                ))

            # C. Análise Estática via AST
            try:
                with open(path, "r", encoding="utf-8") as f:
                    source = f.read()
                    tree = ast.parse(source)
                
                # D. Detecção de Código Duplicado (Local)
                self._check_duplicates_in_file(tree, relative_path, tasks)

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # 1. Verificação de Type Hints Detalhada
                        missing_hints = []
                        has_args_hints = True
                        
                        args_to_check = [a for a in node.args.args if a.arg not in ('self', 'cls')]
                        for arg in args_to_check:
                            if arg.annotation is None:
                                has_args_hints = False
                                missing_hints.append(arg.arg)
                        
                        has_return_hint = node.returns is not None
                        
                        if not has_args_hints or not has_return_hint:
                            # Prioridade aumenta se a função é crítica (alta dependência)
                            task_priority = 2
                            if coupling_priority >= 4: task_priority = 3
                            
                            tasks.append(EvolutionTask(
                                id=f"EVO-{len(tasks)+1}",
                                title=f"Tipagem em {node.name} ({path.name})",
                                description=f"Função '{node.name}' possui anotações de tipo incompletas (Args: {', '.join(missing_hints) if missing_hints else 'OK'}, Return: {'Missing' if not has_return_hint else 'OK'}).",
                                priority=task_priority,
                                category="Modernization",
                                status="backlog",
                                impact_score=0.4,
                                requirements=[relative_path, f"Function: {node.name}"]
                            ))
                        
                        # 2. Complexidade Ciclomática Avançada
                        visitor = ComplexityVisitor()
                        visitor.visit(node)
                        
                        if visitor.complexity > 12:
                            tasks.append(EvolutionTask(
                                id=f"EVO-{len(tasks)+1}",
                                title=f"Simplificar {node.name} ({path.name})",
                                description=f"Alta complexidade ciclomática detectada: {visitor.complexity}. Recomenda-se decomposição.",
                                priority=4,
                                category="Refactoring",
                                status="backlog",
                                impact_score=0.85,
                                requirements=[relative_path, f"Function: {node.name}"]
                            ))
                        elif visitor.max_nesting > 5:
                            # Deep Nesting Check
                            tasks.append(EvolutionTask(
                                id=f"EVO-{len(tasks)+1}",
                                title=f"Reduzir Aninhamento em {node.name} ({path.name})",
                                description=f"Ninhamento excessivo detectado ({visitor.max_nesting} níveis). Recomenda-se extrair funções.",
                                priority=3,
                                category="Refactoring",
                                status="backlog",
                                impact_score=0.6,
                                requirements=[relative_path, f"Function: {node.name}"]
                            ))

                # E. Marcação de Arquivos Críticos (Dependências)
                if fan_in > 3:
                    tasks.append(EvolutionTask(
                        id=f"EVO-{len(tasks)+1}",
                        title=f"Fortalecer {path.name} (Ponto Crítico - Fan-in: {fan_in})",
                        description=f"Arquivo altamente dependente (importado por {fan_in} outros módulos). Requer testes unitários rigorosos e versionamento estável.",
                        priority=coupling_priority,
                        category="Architecture",
                        status="backlog",
                        impact_score=1.0,
                        requirements=[relative_path]
                    ))

            except Exception as e:
                print(f"Erro ao analisar {path}: {e}")

        # F. Tarefas Globais (Código Duplicado entre arquivos)
        duplicate_groups = self._find_global_duplicates()
        for group in duplicate_groups:
            if len(group['locations']) > 1:
                tasks.append(EvolutionTask(
                    id=f"EVO-{len(tasks)+1}",
                    title=f"Eliminar Código Duplicado: {group['locations'][0]['name']}",
                    description=f"Código duplicado encontrado em {len(group['locations'])} locais ({', '.join([d['path'] + ':' + str(d['lineno']) for d in group['locations']])}).",
                    priority=3,
                    category="Refactoring",
                    status="backlog",
                    impact_score=0.6,
                    requirements=[d['path'] for d in group['locations']]
                ))

        # G. Tarefas Globais (Acoplamento Circular)
        dependency_graph = self._map_dependencies(import_counts_in, import_counts_out)
        cycles = self._detect_circular_dependencies(dependency_graph)
        for cycle in cycles:
            cycle_str = " -> ".join(cycle)
            tasks.append(EvolutionTask(
                id=f"EVO-{len(tasks)+1}",
                title=f"Resolver Acoplamento Circular: {cycle[0]}",
                description=f"Dependência circular detectada: {cycle_str}.",
                priority=4,
                category="Architecture",
                status="backlog",
                impact_score=0.9,
                requirements=cycle
            ))

        if not tasks and files_scanned > 0:
            tasks.append(EvolutionTask(
                id="EVO-001",
                title="Análise de Saúde do Projeto",
                description="Nenhuma dívida técnica óbvia detectada nos critérios atuais.",
                priority=1,
                category="Modernization",
                status="backlog",
                impact_score=0.5
            ))

        return tasks

    def _collect_function_signatures(self):
        """Coleta assinaturas e corpo de funções para detecção de duplicação avançada."""
        self._function_signatures = defaultdict(list)
        self._code_blocks = defaultdict(list)  # normalized_code -> [locations]
        
        for path in self.project_root.rglob("*.py"):
            if any(part in path.parts for part in ["__pycache__", ".git", "node_modules", "dist", ".ai_toolbox_backups"]):
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    source = f.read()
                    tree = ast.parse(source)
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Assinatura simples para busca rápida
                        sig = (node.name, len(node.args.args), node.lineno)
                        self._function_signatures[sig].append({
                            "name": node.name,
                            "path": str(path.relative_to(self.project_root)),
                            "lineno": node.lineno
                        })
                        
                        # Extrai o corpo da função para comparação de conteúdo
                        if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                            lines = source.splitlines()
                            body_lines = lines[node.lineno - 1:node.end_lineno]
                            if body_lines:
                                normalized = self._normalize_code(body_lines)
                                if len(normalized) > 20: # Ignora funções muito pequenas
                                    self._code_blocks[normalized].append({
                                        "name": node.name,
                                        "path": str(path.relative_to(self.project_root)),
                                        "lineno": node.lineno,
                                        "length": len(body_lines)
                                    })
            except Exception:
                pass

    def _normalize_code(self, lines: List[str]) -> str:
        """Normaliza o código para comparação (remove whitespace e comentários)."""
        import re
        result = []
        for line in lines:
            # Remove comentários
            line = re.sub(r'#.*$', '', line)
            # Remove whitespace extra
            line = ' '.join(line.split())
            if line:
                result.append(line)
        return '\n'.join(result)

    def _check_duplicates_in_file(self, tree, relative_path, tasks):
        """Detecta duplicação dentro do mesmo arquivo."""
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append({"name": node.name, "lineno": node.lineno, "body_len": len(node.body)})
        
        # Detecção simples de funções com mesmo nome (provavelmente overloading ou duplicação)
        names = Counter(f["name"] for f in functions)
        for name, count in names.items():
            if count > 1:
                tasks.append(EvolutionTask(
                    id=f"EVO-{len(tasks)+1}",
                    title=f"Renomear Funções Duplicadas: {name} ({relative_path})",
                    description=f"Função '{name}' definida {count} vezes no mesmo arquivo.",
                    priority=2,
                    category="Refactoring",
                    status="backlog",
                    impact_score=0.5,
                    requirements=[relative_path, f"Function: {name}"]
                ))

    def _find_global_duplicates(self) -> List[List[Dict]]:
        """Encontra duplicação de código real entre arquivos usando normalização de corpo."""
        duplicate_groups = []
        
        # 1. Detecção por corpo de função (mais precisa)
        for normalized_code, locations in self._code_blocks.items():
            if len(locations) > 1:
                # Verifica se as localizações são distintas
                unique_locs = set((loc['path'], loc['lineno']) for loc in locations)
                if len(unique_locs) > 1:
                    # Verifica se o código é realmente similar (não apenas por coincidência de normalização)
                    # Aqui assumimos que se o código normalizado é igual, é duplicação
                    duplicate_groups.append({
                        "type": "code_block",
                        "locations": locations
                    })
        
        # 2. Complementar com detecção por assinatura (para funções pequenas ou vazias)
        for sig, locations in self._function_signatures.items():
            if len(locations) > 1:
                unique_locs = set((loc['path'], loc['lineno']) for loc in locations)
                if len(unique_locs) > 1:
                    # Verifica se já foi adicionado pelo bloco de código
                    existing = False
                    for group in duplicate_groups:
                        if group['type'] == 'signature':
                            existing_locs = set((loc['path'], loc['lineno']) for loc in group['locations'])
                            if unique_locs == existing_locs:
                                existing = True
                                break
                    if not existing:
                        duplicate_groups.append({
                            "type": "signature",
                            "locations": locations
                        })
                        
        return duplicate_groups

    def _map_dependencies(self, fan_in: Counter, fan_out: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
        """Mapeia imports para calcular Fan-in, Fan-out e retorna o grafo de dependências."""
        dependency_graph = defaultdict(set)
        
        for path in self.project_root.rglob("*.py"):
            if any(part in path.parts for part in ["__pycache__", ".git", "node_modules", "dist", ".ai_toolbox_backups"]):
                continue
            
            try:
                with open(path, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read())
                
                current_rel = str(path.relative_to(self.project_root))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            self._register_import(alias.name, fan_in, fan_out, current_rel, dependency_graph)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            self._register_import(node.module, fan_in, fan_out, current_rel, dependency_graph)
            except Exception:
                pass
                
        return dependency_graph

    def _register_import(self, module_name: str, fan_in: Counter, fan_out: Dict[str, Set[str]], importer: str, dependency_graph: Dict[str, Set[str]]):
        """Registra um import e tenta mapear para arquivos locais."""
        clean_module = module_name.replace("clawai.", "")
        if not clean_module: return

        parts = clean_module.split('.')
        potential_path = Path(*parts)
        
        for root_dir in [self.project_root / "clawai"]:
            target = root_dir / potential_path
            # Verifica se é um arquivo ou diretório com __init__.py
            if target.exists():
                relative = str(target.relative_to(self.project_root))
                fan_in[relative] += 1
                if importer != relative: # Evita auto-import
                    fan_out[importer].add(relative)
                    dependency_graph[importer].add(relative)
                break

    def _detect_circular_dependencies(self, dependency_graph: Dict[str, Set[str]]) -> List[List[str]]:
        """Detecta ciclos de dependência no grafo de módulos."""
        cycles = []
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in dependency_graph.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    # Encontrou um ciclo
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)

            path.pop()
            rec_stack.remove(node)

        for node in dependency_graph:
            if node not in visited:
                dfs(node)

        return cycles

    def save_backlog(self, new_tasks: List[EvolutionTask]):
        """Salva o estado atual do backlog no disco, mesclando com tarefas existentes."""
        existing_tasks = []
        if self.backlog_path.exists():
            try:
                with open(self.backlog_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    existing_tasks = [EvolutionTask(**item) for item in data]
            except Exception:
                pass

        existing_ids = {t.id for t in existing_tasks}
        
        for task in new_tasks:
            if task.id not in existing_ids:
                existing_tasks.append(task)
                existing_ids.add(task.id)

        # Ordenar por prioridade (desc) e depois por ID
        existing_tasks.sort(key=lambda t: (-t.priority, t.id))

        data = [t.to_dict() for t in existing_tasks]
        with open(self.backlog_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Backlog de evolução atualizado com {len(new_tasks)} novas tarefas em: {self.backlog_path}")

    def load_backlog(self) -> List[EvolutionTask]:
        """Carrega o backlog do disco."""
        if not self.backlog_path.exists():
            return []
        with open(self.backlog_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [EvolutionTask(**item) for item in data]
