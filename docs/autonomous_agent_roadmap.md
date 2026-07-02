# Roadmap do ClawAI para agente autônomo

## Visão
O ClawAI deve evoluir de um assistente orientado a chat para um agente autônomo de engenharia de software capaz de trabalhar sobre qualquer workspace, decidir ferramentas, editar código, executar testes, corrigir erros e replanejar.

## Princípios
- O Python mantém o runtime, execução, permissões, estado e observabilidade.
- O LLM decide o plano, as ações e a estratégia.
- A evolução deve ser incremental e compatível.
- O sistema deve ser modular, extensível e orientado a contratos.

## Fases de evolução
1. Runtime e estado estruturado
2. ToolContext e providers
3. Contratos tipados para ações e reflexão
4. ActionExecutor com validação e execução
5. Providers locais, MCP e Composio
6. Memória, observabilidade e proteções
7. Workspace discovery, search, editor, git, terminal e test runner

## Contratos centrais
- Action
- ActionResult
- ExecutionPlan
- ExecutionState
- PlannerResult
- ReflectionResult
- ToolContext
- ToolMetadata
- Permission
- ProviderResult

## Próximos blocos recomendados
- ActionExecutor
- PermissionManager
- MemoryManager
- StateStore
- WorkspaceManager
- SearchTool
- EditorTool
- GitTool
- TerminalTool
- TestRunnerTool
- DiagnosticsTool
