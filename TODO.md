# TODO – ClawAI Studio Roadmap & Progress Tracker

## 📋 Pendências Gerais (Pré-migração)
- [x] Investigar e corrigir erro provável no `clawai/agent/agent_loop.py` relacionado a `max_iterations` inexistente em `AgentConfiguration`.
- [ ] Verificar se o bug foi resolvido corretamente.
- [x] Rodar testes unitários relevantes (`tests/unit/test_agent.py`).
- [x] Rodar suíte completa (`pytest -q`) — 701 tests passaram, mas houve `PermissionError` no teardown do pytest (Windows) em `pytest-current`.

---

## 🏗️ Migração para ClawAI.exe standalone (PyWebView + FastAPI)

### Fase 1: Base ✅ Concluída
- [x] **Tarefa 1.1** — Criar `main.py` entry point principal que inicializa backend + PyWebView window
- [x] **Tarefa 1.2** — Adaptar BackendManager para iniciar FastAPI como subprocesso embutido (via threading)
- [x] **Tarefa 1.3** — Configurar Vite/React frontend (já existente, serve estáticos via FastAPI)
- [x] **Tarefa 1.4** — Bridge HTTP/WebSocket entre PyWebView e backend API REST

### Fase 2: Build & Distribuição ✅ Concluída
- [x] **Tarefa 2.1** — Atualizar `build_exe.py` para usar `.spec`, remove duplicação de --add-data/hidden-imports
- [x] **Tarefa 2.2** — Configurar PyInstaller spec (`ClawAI.spec`) centralizada com datas, hidden imports, excludes
- [ ] **Tarefa 2.3** — Testar build completo e verificar tamanho do executável final

### Fase 3: Funcionalidades Desktop ✅ Concluída (implementação) / ⏳ Em verificação
- [x] **Tarefa 3.1** — Title bar customizada via frontend CSS + `webview.create_window()` com título nativo no taskbar
- [ ] **Tarefa 3.2** — Tray icon funcional com menu de contexto (Show/Hide/Quit) via `pystray`
- [x] **Tarefa 3.3** — Settings persistence migrada para arquivo JSON local (`clawai/settings.json`) sem Electron IPC
- [x] **Tarefa 3.4** — Drag-to-move na title bar implementado no frontend (CSS/JS)

### Fase 4: Otimização & Polimento ⏳ Pendente
- [ ] **Tarefa 4.1** — Adicionar auto-update via GitHub Releases ou servidor de updates
- [x] **Tarefa 4.2** — Configurar startup automático no Windows (via registry key em `main.py`)
- [ ] **Tarefa 4.3** — Monitor de recursos integrado ao frontend (`/api/desktop/metrics` já implementado)
- [ ] **Tarefa 4.4** — Testes end-to-end do executável final

### Fase 5: Model Management ✅ Concluída (implementação) / ⏳ Em verificação
- [x] **Tarefa 5.1** — Detectar automaticamente modelos de LM Studio (`/v1/models`)
- [x] **Tarefa 5.2** — Detectar automaticamente modelos de Ollama (`/api/tags`)
- [ ] **Tarefa 5.3** — Detectar automaticamente configurações OpenAI (API key + list_models)
- [x] **Tarefa 5.4** — Endpoint `/api/desktop/models` para troca dinâmica de modelo sem reiniciar
- [x] **Tarefa 5.5** — Detectar contexto máximo, multimodalidade, function calling via API metadata

### Fase 6: Gerenciador de Modelos ✅ Concluída (implementação) / ⏳ Em verificação
- [ ] **Tarefa 6.x** — Interface frontend para gerenciar modelos carregados
- [x] **Tarefa 6.1** — Endpoint `/api/desktop/metrics` com CPU, RAM, GPU (pynvml), disco

### Fase 7: Testes & Deploy ⏳ Pendente
- [ ] **Tarefa 7.x** — Executar `python build_exe.py --test-build` e verificar resultado
- [ ] **Tarefa 7.y** — Validar que o exe funciona sem navegador externo aberto
- [ ] **Tarefa 7.z** — Criar installer (NSIS/Inno Setup opcional)

---

## 📊 Status por Módulo

| Módulo | Status | Observações |
|--------|--------|-------------|
| `main.py` | ✅ Atualizado | Desktop mode default, CLI via env var |
| `desktop_server.py` | ✅ Reescrito | FastAPI + PyWebView integrado com auto-detect models |
| `ClawAI.spec` | ✅ Criado | Centraliza todas as opções do PyInstaller |
| `build_exe.py` | ✅ Atualizado | Usa `.spec`, remove duplicação |
| `desktop_tray.py` | ✅ Novo | Tray icon opcional com pystray (lazy-loaded) |
| Frontend (`frontend/`) | ⏳ Existente, não modificado nesta etapa | React/Vite já configurado; serve via FastAPI estáticos |

## 📐 Decisões Arquiteturais Recentes

### 2026-07-18: PyWebView vs Electron
**Decisão:** Usar **PyWebView** como engine desktop principal.
**Motivo:** Zero dependência de Node.js/Electron; menor footprint (~30 MB vs ~150+ MB); integração nativa com WebView do Windows (Edge/Chromium).

### 2026-07-18: Backend embutido via threading
**Decisão:** FastAPI roda no **mesmo processo Python**, em thread separada.
**Motivo:** Evita dependência de `clawai.bat` ou scripts auxiliares; simplifica PyInstaller (um único exe).

### 2026-07-18: Single-file vs multi-folder distribuído
**Decisão:** **Single-folder** (`dist/ClawAI.exe`, `frontend/dist/*`) para desenvolvimento inicial.
Motivo: Mais fácil de debugar; PyInstaller singlefile (`--onefile`) tem problemas com sub-processos e arquivos extra em MEIPASS.

### 2026-07-18: Model auto-detection strategy
**Decisão:** Detectar LM Studio (port 1234) + Ollama (port 11434) via HTTP no startup; OpenAI por API key env var.
Motivo: Sem necessidade de configuração manual para usuários locais — o app descobre automaticamente os backends disponíveis.
