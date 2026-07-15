# ClawAI - TODO

## 🏆 Marcação de Estágio: Estabilização da Arquitetura (Concluído)

- [x] **701/701 Testes Unitários Passing** (100% de cobertura das camadas core)
- [x] **Cognition Engine** (100% estável)
- [x] **Goal Management** (100% estável)
- [x] **Development Pipeline** (100% estável)
- [x] **Self-Repair** (100% estável)
- [x] **Prompt Engine** (100% estável)
- [x] **Tool System** (100% estável)
- [x] **Workspace** (100% implementado e testado)
- [ ] Corrigir warnings de `datetime.utcnow()` no `trace.py` (Baixa Prioridade)

---

## Sprint Atual: Arquitetura de Workspace (Implementada)

- [x] Implement IgnoreEngine (.gitignore + internal ignore rules + binary detection)
- [x] Implement ProjectTree (lightweight structure only)
- [x] Implement Scanner (discover directories/files, respects IgnoreEngine; does not read file contents)
- [x] Implement FileReader (on-demand read; never cache full file)
- [x] Implement Workspace (open/close/get_tree; wrappers for backward-compatible load_project/build_context)
- [x] Add unit tests for all new components (`tests/unit/test_workspace_components.py`)
- [x] Run pytest and fix any regressions → **701/701 PASSING**

---

## Backlog de Evolução (Selecionados)

### EVO-15: Modernização: Tipagem Completa em Módulos Core
- **Status**: Em Progresso / Parcial
- **Descrição**: Módulos core (`api.py`, `bootstrap.py`, `main.py`, `claw.py`) estão tipados.
- **Pendentes**: Verificar outros módulos críticos não listados acima.

### EVO-17: Refatoração: Simplificar _verify_api_in_process (verify.py)
- **Status**: Pendente
- **Descrição**: Alta complexidade ciclomática detectada. Recomenda-se decomposição em funções menores.

---

## Próximos Passos (Roadmap)

1. [x] **Correção de Qualidade de Código**: Ajustar warnings de `datetime` no `trace.py`.
2. [x] **EVO-17**: Refatorar `verify.py` para reduzir complexidade ciclomática.
3. [ ] **EVO-1 a EVO-14**: Avaliar e priorizar dependências críticas restantes no backlog.
4. [x] **Integração Contínua**: Configurar pipeline de validação automática para os 701 testes.
