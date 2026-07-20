# ClawAI Desktop Quick Start

## Como abrir o desktop agora

### Opção 1 — Executável já compilado
Se existir `dist\ClawAI.exe`, basta dar duplo clique nele.

### Opção 2 — Rodar a partir do código-fonte
Na raiz do repositório, dê duplo clique em `ClawAI.bat`.

Esse launcher:
- tenta abrir `dist\ClawAI.exe` se ele já existir;
- caso contrário, inicia `python main.py`.

### Opção 3 — Gerar o executável
Se quiser criar o executável do desktop:

```bat
build_desktop.bat
```

Ao final, o executável ficará em:

```text
dist\ClawAI.exe
```

## Estrutura esperada

- `main.py` → entry point do desktop
- `ClawAI.bat` → launcher simples para desenvolvimento e uso local
- `build_desktop.bat` → gera o executável
- `desktop/` → servidor FastAPI + PyWebView
- `frontend/` → React/Vite

## O que não é mais o caminho de uso

O caminho de uso principal não é mais Electron. O desktop deve abrir pelo `main.py`/`desktop_server.py` e ser distribuído como `dist\ClawAI.exe`.

## Observação

Se você só deu `git pull` e não existe `dist\ClawAI.exe`, o desktop ainda não está pronto para ser aberto como executável. Nesse caso, use `ClawAI.bat` ou gere o build primeiro.
