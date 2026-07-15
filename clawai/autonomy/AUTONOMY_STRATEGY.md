# 🧠 ClawAI: Estratégia de Autonomia Evolutiva

## 🎯 Visão Geral
O objetivo central deste projeto é transitar a ClawAI de uma **Arquitetura Reativa** (onde a IA apenas responde a comandos imediatos) para uma **Arquitetura Proativa** (onde a IA identifica necessidades de evolução, planeja mudanças estruturais e executa melhorias sem intervenção humana constante).

A ClawAI deve se tornar capaz de se "auto-implementar", mantendo-se moderna e eficiente através de ciclos de auto-diagnóstico e manutenção.

---

## 🏗️ Os 4 Pilares da Autonomia

### Pilar 1: Percepção e Diagnóstico (O "Olhar")
A IA precisa monitorar a saúde do projeto proativamente.
- **Análise de Dívida Técnica:** Scanners de Complexidade Ciclomática, Acoplamento e Obsolescência.
- **Monitoramento de Falhas:** Analisar logs do *Reflector* para identificar "Pontos de Dor" recorrentes.
- **Backlog de Evolução:** Um sistema onde a IA popula automaticamente tarefas baseadas em diagnósticos reais.

### Pilar 2: Planejamento Estratégico e Memória (A "Mente")
A IA precisa de contexto de longo prazo para manter a consistência.
- **Memória Evolutiva:** Uso de RAG para armazenar "Decisões de Arquitetura" (porquês das decisões).
- **Roadmapping de Multi-Etapas:** Capacidade de decompor metas complexas em planos sequenciais.
- **Agendamento Proativo:** Ciclos de manutenção em tempos de ociosidade.

### Pilar 3: Execução Segura e Verificação (As "Mãos")
Garantir que a auto-modificação não destrua o sistema.
- **Ciclo de Teste Unitário Automático:** Escrita de teste $\rightarrow$ Execução $\rightarrow$ Refatoração $\rightarrow$ Re-execução.
- **Diff-Aware Coding:** Geração de patches de mudança para verificação de impacto.
- **Verificação de Integridade:** Check de contratos de API e rotas pós-execução.

### Pilar 4: Governança e Meta-Programação (A "Consciência")
A IA melhorando a si mesma.
- **Refatoração de Prompts:** Melhoria dinâmica das instruções de sistema do Planner e Reflector.
- **Auto-Ajuste de Parâmetros:** Ajuste dinâmico de temperatura, tokens e iterações baseadas na complexidade.
- **Hierarquia de Agentes (Swarm):** Criação de sub-agentes especializados temporários para tarefas específicas.

---

## 🗺️ Roadmap de Implementação

| Fase | Nome | Objetivo Principal | Impacto para o Usuário |
| :--- | :--- | :--- | :--- |
| **1** | **Diagnóstico** | `EvolutionAnalyzer` popula `growth_backlog.json` automaticamente. | Visualização de Dívidas Técnicas crescentes. |
| **2** | **Proposta** | IA envia relatórios de evolução e pede permissão para iniciar planos. | Usuário torna-se "Diretor de Engenharia". |
| **3** | **Execução Assistida** | IA executa planos de evolução e pede aprovação em cada "Pull Request". | Usuário revisa o código de melhoria. |
| **4** | **Autonomia Total** | Ciclos de manutenção e modernização em horários ociosos. | ClawAI se mantém moderna sozinha. |

---

## 🛠️ Status Atual do Projeto
- **Fase Atual:** Fase 1 (Diagnóstico)
- **Foco Imediato:** Integração do `growth_backlog.json` consolidado com o motor de planejamento (Fase 2).
- **Backlog Atualizado:** 111+ tarefas → 17 itens consolidados (14 Critical Dependencies + 3 macro-tasks).

### Backlog Consolidado (17 itens)
| ID | Categoria | Prioridade | Descrição |
|----|-----------|------------|-----------|
| EVO-1 a EVO-14 | Architecture | 5 (Crítica) | 14 módulos com alta dependência (6-16 imports) |
| EVO-15 | Modernization | 3 | Tipagem em módulos core (api.py, bootstrap.py, main.py, claw.py) |
| EVO-16 | Modernization | 1 | Tipagem em testes unitários (baixa prioridade) |
| EVO-17 | Refactoring | 4 | Simplificar `_verify_api_in_process` (complexidade 15) |

---

## 📝 Log de Execução e Testes
- [x] **[2026-07-12]** - Definição da Estratégia de Autonomia e criação deste documento.
- [x] **[2026-07-12]** - Higienização inicial do repositório (Remoção de arquivos `.rej` e redundâncias).
- [x] **[DATA]** - **Refatoração do Scanner:** Adição de detecção de código duplicado e análise de acoplamento (Fan-in/Fan-out).
- [ ] **[DATA]** - Integração do `growth_backlog.json` com o motor de planejamento.
- [x] **[DATA]** - **Limpeza do Backlog:** 111+ tarefas → 17 itens consolidados.
