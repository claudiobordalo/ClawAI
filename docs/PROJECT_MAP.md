# Mapeamento de Projeto ClawAI

Este documento fornece um mapa arquitetural detalhado do repositório ClawAI, descrevendo a estrutura geral, os componentes principais e o fluxo de execução em tempo de execução. O mapeamento é baseado na análise dos módulos existentes no código-fonte (d:\\ClawAI\\clawai).

## 🧭 Arquitetura Geral
A arquitetura do ClawAI é modular e orientada por serviços, utilizando um sistema central de Orquestração que coordena agentes autônomos e componentes especializados para realizar tarefas complexas. O fluxo principal opera através da interconexão de `Agent`s, gerenciamento de estado (`Memory`), e a orquestração de chamadas externas via `Providers`.

## 📁 Estrutura de Pastas (Folder Tree)
Os módulos principais residem em `clawai/`:
*   **`clawai/core/`**: Contém utilitários e fundações do sistema: gerenciamento de configurações (`config/*`), injeção de dependência (`container/service_container.py`) e utilidades genéricas (`utils/*`).
*   **`clawai/agent/`, `clawai/agents/`**: Responsáveis pela lógica de agentes autônomos (ex: Planner, Executor).
*   **`clawai/orchestrator/`**: O coração do sistema; orquestra a execução e o fluxo geral da tarefa.
*   **`clawai/memory/`**: Gerencia a Memória de Longo Prazo (`MemoryManager`).
*   **`clawai/providers/`**: Módulos que fornecem conexões com LLMs externos (OpenAI, Ollama, Anthropic, Google) e ferramentas.
*   **`clawai/api/`**: Define os endpoints e as interfaces de serviço expostas (`chat_api.py`, `autonomy_api.py`, etc.).

## 🚀 Fluxo Principal de Execução (Main Execution Flow)
1.  O processo é iniciado pelo ponto principal do sistema, tipicamente através dos scripts em `main.py` ou na lógica orquestrada por `clawai/orchestrator/*`.
2.  A Orquestração (`Orchestrator`) recebe uma tarefa de alto nível (Goal).
3.  O fluxo identifica os agentes e as ferramentas necessárias para resolver o Goal, utilizando `clawai/api/*.py` como interface pública.
4.  O **Planejador** (Planner Agent) gera um plano de passos a serem executados (`test_goal_planner.py`).
5.  Cada passo é passado ao **Executor de Ação** (`Action Executor`), que consulta o `MemoryManager` para contexto relevante e chama os *Providers* necessários para executar ações externas (e.g., chamadas LLM).

## 💻 Classes Principais e Módulos Importantes (Main Classes & Modules)
| Componente | Arquivo Principal / Serviço | Função |
| :--- | :--- | :--- |
| **Gerenciador de Memória** | `clawai/memory/memory_manager.py` | Coordena a adição (`add_document`) e busca (`search`) de documentos através da vetorização de *chunks*. |
| **Orquestrador** | `clawai/orchestrator/*` | Coordenadora principal do ciclo de vida do agente, garantindo o fluxo entre agentes e ferramentas. |
| **Service Container** | `clawai/core/container/service_container.py` | Gerencia a injeção de dependência para montar os serviços do sistema (DI). |
| **Configuração** | `configs/config.yaml` | Arquivo central de configurações, definindo hosts de LLMs (`ollama`) e modelos específicos por função (`planner`, `coder`). |
| **API Exposta** | `clawai/api/*` | Interface layer que expõe capacidades específicas como chat, autonomia ou ferramentas. |

## 🛠️ Providers (Fornecedores de Capacidade)
O sistema suporta múltiplos *Providers* implementados em `clawai/providers/implementations/`:
*   `openai_provider.py`: Para integração com OpenAI.
*   `anthropic_provider.py`: Para integração com Anthropic.
*   `google_provider.py`: Para integração com o Google (Vertex AI, etc.).
*   `ollama_provider.py`: Utiliza modelos rodando localmente via Ollama.

A seleção e gerenciamento desses provedores são feitos por `clawai/providers/manager/manager.py`, que recebe as configurações em `configs/config.yaml`.

## 🧠 Sistemas Chave
### Agent System
O sistema de agentes é altamente modularizado, visível na estrutura e nos testes (`test_agent/*`). Agentes como o Planejador (Planner) são responsáveis por decompor tarefas complexas e definir o próximo passo lógico. A lógica de `autonomy` visa permitir que o agente realize ações sem intervenção direta do usuário.

### Memory System
Gerenciado por `MemoryManager` em `clawai/memory/`. Utiliza:
*   **Chunker (`clawai/memory/chunker.py`)**: Quebra documentos grandes em pedaços gerenciáveis (chunks).
*   **Embedding Service (`clawai/memory/embeddings/embedding_service.py`)**: Converte texto para vetores numéricos (embeddings) usando modelos definidos, como `nomic-embed-text`.
*   **Vector Store (`clawai/memory/stores/vector_store.py`)**: Armazena os chunks e seus embeddings em um banco de dados vetorial (sugerido pelo artefato `database/world.db`).

### Database System
Não há um módulo dedicado de código na estrutura do pacote `clawai/database` vazio. No entanto, a persistência é sugerida por:
1.  O arquivo local `database/world.db`.
2.  As referências em `configs/config.yaml` aos caminhos `data/memory` e `data/projects`, indicando o armazenamento de estado estruturado.
3.  A manipulação de vetores (embeddings) dentro do Memory Manager, que deve persistir dados vetoriais.

## ⚙️ Backend e APIs
O back-end é exposto por uma série de serviços em `clawai/api/*`. Cada API lida com um domínio funcional específico:
*   `chat_api.py`: Serviço de conversação de chat.
*   `autonomy_api.py`: Funções relacionadas à autonomia do agente e execução de tarefas complexas.
*   `workspaces_api.py`: Gerenciamento e contexto da sessão de trabalho (Workspaces).
*   `tools_api.py`: Exposição programática das ferramentas disponíveis para os agentes.

## 🎨 Frontend
A estrutura física em `clawai/frontend` está vazia, sugerindo que a interface gráfica pode ser construída separadamente ou utilizar um *framework* de frontend não modularizado no diretório. As interações são controladas pelo back-end através das APIs mencionadas acima.

## ✅ Testes (Tests)
A cobertura de testes é extensa e detalhada (`tests/*`). Os módulos testam quase todos os aspectos do sistema: desde `test_agent/*` (Ciclo de vida dos agentes), até funções específicas como `test_patch_planner.py` e lógica crítica de `Memory` (`test_memory_query.py`), confirmando a profundidade de testes em todas as áreas críticas da arquitetura.

## 💡 Pontos Técnicos, Dívida Técnica e Oportunidades
**Dívida/Oportunidades:**
1.  **Gerenciamento de Estado/Sessão**: A necessidade de persistência é central (uso do `database/world.db` e caminhos `data/memory`), mas a abstração da camada de acesso aos dados persiste como um foco de melhoria arquitetural.
2.  **Fluxo Contínuo**: O sistema possui fortes mecanismos de auto-reparo (`clawai/selfrepair/*`) e análise de ciclo de vida, indicando uma capacidade avançada de manutenção que pode ser exposta mais diretamente ao usuário final.