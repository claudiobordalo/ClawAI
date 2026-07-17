# ClawAI Desktop Build Scripts

## Estrutura de Build

```
ClawAI/
├── python/                    # Python portable embutido (gerado automaticamente)
│   ├── python.exe
│   ├── python312._pth
│   ├── Lib/
│   └── Scripts/
├── clawai/                    # FastAPI backend source
├── frontend/
│   ├── dist/                  # React UI build
│   └── electron/              # Electron main process
├── build_scripts/
│   ├── download_python.bat    # Download Python portable
│   ├── build_complete.bat     # Build completo
│   └── installer.iss          # Inno Setup installer
└── release/                   # Output do build
    ├── ClawAI-Setup.exe       # Instalador final
    └── ClawAI/                # Pasta do app empacotado
```

## Build Completo

```bash
# Executar build completo
build_scripts\build_complete.bat

# Ou manualmente:
1. build_scripts\download_python.bat  # Download Python portable
2. npm install                        # Instalar dependências
3. cd frontend && npm run build       # Build frontend
4. pyinstaller main.py                # Build backend
5. npm run electron:build:win         # Empacotar com electron-builder
```

## Estrutura Final do Instalado

```
C:\Program Files\ClawAI\
├── ClawAI.exe                       # Electron app
├── resources\
│   ├── app\                         # App empacotado
│   │   ├── frontend\
│   │   └── electron\
│   └── python\                      # Python embutido
│       ├── python.exe
│       └── Lib\
│   └── clawai\                      # FastAPI source
├── backend.exe                      # PyInstaller backend (se usado)
└── ...
```

## Instalação

1. Executar `ClawAI-Setup.exe`
2. Seguir wizard do Inno Setup
3. Atalho criado no Desktop e Menu Iniciar
4. Clicar em ClawAI.exe para iniciar

## Componentes

- **Electron**: Frontend desktop (window, tray, IPC)
- **Python Embeddable**: Runtime embutido (sem dependência externa)
- **FastAPI**: Backend server (inicia automaticamente)
- **React + Vite**: UI frontend
- **electron-builder**: Empacotamento
- **Inno Setup**: Instalador Windows
