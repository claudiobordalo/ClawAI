# ClawAI Technical Backlog

Este backlog esta ordenado por dependencia entre componentes. Cada item deve ser implementado em passos pequenos, funcionais e testaveis.

## 1. Nucleo importavel

Garantir que pontos de entrada, imports publicos e inicializacao basica funcionem sem depender de modulos antigos ou inexistentes.

## 2. Model Router

Centralizar selecao de modelos por papel, mantendo compatibilidade com agentes existentes e evitando acoplamento direto ao Ollama.

## 3. Tool Registry unico

Consolidar ferramentas locais, Git, Composio e terminal atras de uma interface unica: `ToolRegistry.execute(...)`.

## 4. Workspace e Context Builder

Ler projetos, indexar arquivos, escolher contexto relevante e evitar carregar arquivos desnecessarios.

## 5. Mission Manager

Representar missoes como ciclo `planejar -> executar -> avaliar -> corrigir -> aprender -> melhorar`.

## 6. Auto Review e Auto Fix

Executar revisao automatica, testes, aplicar correcoes pequenas e repetir ate estabilizar ou encontrar bloqueio real.

## 7. Git Integration

Executar status, diff, commit, push e Pull Request sempre por ferramenta registrada.

## 8. Resource Manager

Medir CPU, RAM, VRAM e processos ativos para ajustar modelos, adiar tarefas pesadas e reduzir consumo quando o computador estiver ocupado.

Primeira entrega: coletar snapshot basico, detectar processos criticos e produzir uma decisao de adaptacao antes de tarefas pesadas.

## 9. Memory e Knowledge Base

Persistir aprendizados, skills e novas ferramentas com origem, utilidade e revisao.

## 10. Metricas e melhoria continua

Registrar tempo de execucao, consumo, falhas, decisoes e melhorias arquiteturais sugeridas.

## Proximo passo

Restaurar a compatibilidade `AIRouter.ask(...)` sobre o `ModelRouter`, pois agentes existentes dependem desse contrato.
