import { app, BrowserWindow, ipcMain, dialog, shell, Tray, Menu, nativeTheme, screen, clipboard } from 'electron';
import * as path from 'path';
import * as fs from 'fs';
import { BackendManager } from './backend_manager';

// ==================== Globals ====================

let mainWindow: BrowserWindow | null = null;
let tray: Tray | null = null;
let backendManager: BackendManager | null = null;
let isAppQuitting = false;
let backendPort: number = 8000;
let backendInitialized = false;

// ==================== App State ====================

interface AppState {
    lastWorkspace: string | null;
    windowBounds: Electron.Rectangle | null;
    theme: 'dark' | 'light' | 'system';
    fontSize: number;
    autoStart: boolean;
    autoUpdate: boolean;
    sidebarWidth: number;
    terminalFontSize: number;
    modelProvider: string;
    modelProviderUrl: string;
    lastActivePanel: string;
}

const defaultState: AppState = {
    lastWorkspace: null,
    windowBounds: null,
    theme: 'dark',
    fontSize: 14,
    autoStart: false,
    autoUpdate: true,
    sidebarWidth: 250,
    terminalFontSize: 13,
    modelProvider: 'ollama',
    modelProviderUrl: 'http://localhost:11434',
    lastActivePanel: 'chat',
};

// ==================== Settings Management ====================

function getSettingsPath(): string {
    return path.join(app.getPath('userData'), 'settings.json');
}

function loadSettings(): AppState {
    try {
        const settingsPath = getSettingsPath();
        if (fs.existsSync(settingsPath)) {
            const data = JSON.parse(fs.readFileSync(settingsPath, 'utf-8'));
            return { ...defaultState, ...data };
        }
    } catch (err) {
        console.error('[Main] Failed to load settings:', err);
    }
    return { ...defaultState };
}

function saveSettings(settings: AppState): void {
    try {
        const settingsPath = getSettingsPath();
        const dir = path.dirname(settingsPath);
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
        fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2));
    } catch (err) {
        console.error('[Main] Failed to save settings:', err);
    }
}

// ==================== Tray Management ====================

function createTray(): void {
    const iconPath = path.join(__dirname, '..', 'public', 'icon.png');
    const fallbackIcon = path.join(__dirname, '..', 'public', 'icon.ico');

    // Use .ico for Windows tray
    const trayIcon = app.isPackaged
        ? path.join(process.resourcesPath, 'public', 'icon.ico')
        : fallbackIcon;

    tray = new Tray(trayIcon);
    tray.setToolTip('ClawAI');

    const contextMenu = Menu.buildFromTemplate([
        {
            label: 'Abrir ClawAI',
            click: () => {
                if (mainWindow) {
                    if (mainWindow.isMinimized()) mainWindow.restore();
                    mainWindow.focus();
                }
            },
        },
        { type: 'separator' },
        {
            label: 'Chat',
            click: () => mainWindow?.webContents.send('tray-action', 'chat'),
        },
        {
            label: 'Explorador',
            click: () => mainWindow?.webContents.send('tray-action', 'explorer'),
        },
        {
            label: 'Configurações',
            click: () => mainWindow?.webContents.send('tray-action', 'settings'),
        },
        { type: 'separator' },
        {
            label: 'Reiniciar Backend',
            click: async () => {
                await restartBackend();
            },
        },
        { type: 'separator' },
        {
            label: 'Sair',
            click: () => app.quit(),
        },
    ]);

    tray.setContextMenu(contextMenu);

    tray.on('click', () => {
        if (mainWindow) {
            if (mainWindow.isVisible()) {
                mainWindow.minimize();
            } else {
                if (mainWindow.isMinimized()) mainWindow.restore();
                mainWindow.focus();
            }
        }
    });
}

// ==================== Window Management ====================

function createWindow(): void {
    const settings = loadSettings();

    // Restore window bounds or use defaults
    let bounds: Electron.Rectangle;
    if (settings.windowBounds) {
        const primaryDisplay = screen.getPrimaryDisplay();
        const workArea = primaryDisplay.workAreaSize;

        // Validate bounds are within work area
        const isValid =
            settings.windowBounds.width <= workArea.width &&
            settings.windowBounds.height <= workArea.height &&
            settings.windowBounds.width >= 900 &&
            settings.windowBounds.height >= 600;

        if (isValid) {
            bounds = settings.windowBounds;
        } else {
            bounds = getDefaultBounds();
        }
    } else {
        bounds = getDefaultBounds();
    }

    mainWindow = new BrowserWindow({
        x: bounds.x,
        y: bounds.y,
        width: bounds.width,
        height: bounds.height,
        minWidth: 900,
        minHeight: 600,
        title: 'ClawAI',
        show: false,
        frame: false,
        transparent: false,
        backgroundColor: '#1a1b26',
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js'),
            devTools: {
                enabled: process.env.NODE_ENV === 'development',
            },
        },
        icon: path.join(__dirname, '..', 'public', 'icon.png'),
    });

    // Apply theme
    applyTheme(settings.theme);

    // Load content
    if (process.env.NODE_ENV === 'development') {
        mainWindow.loadURL('http://127.0.0.1:5173');
    } else {
        mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'));
    }

    // Show window when ready
    mainWindow.once('ready-to-show', () => {
        mainWindow?.show();
    });

    // Handle window events
    mainWindow.on('close', (event) => {
        if (!isAppQuitting) {
            event.preventDefault();
            mainWindow?.minimize();
        }
    });

    mainWindow.on('closed', () => {
        // Save window bounds before closing
        if (mainWindow) {
            const settings = loadSettings();
            settings.windowBounds = mainWindow.getBounds();
            saveSettings(settings);
        }
        mainWindow = null;
    });

    // Handle maximize/restore
    mainWindow.on('maximize', () => {
        mainWindow?.webContents.send('window-state', 'maximized');
    });

    mainWindow.on('unmaximize', () => {
        mainWindow?.webContents.send('window-state', 'normal');
    });

    // Handle resize - save bounds
    mainWindow.on('resize', () => {
        if (mainWindow) {
            const settings = loadSettings();
            settings.windowBounds = mainWindow.getBounds();
            saveSettings(settings);
        }
    });
}

function getDefaultBounds(): Electron.Rectangle {
    const primaryDisplay = screen.getPrimaryDisplay();
    const { width: screenWidth, height: screenHeight } = primaryDisplay.workAreaSize;

    const windowWidth = Math.min(1400, screenWidth * 0.85);
    const windowHeight = Math.min(900, screenHeight * 0.85);

    return {
        x: Math.floor((screenWidth - windowWidth) / 2),
        y: Math.floor((screenHeight - windowHeight) / 2),
        width: windowWidth,
        height: windowHeight,
    };
}

function applyTheme(theme: 'dark' | 'light' | 'system'): void {
    if (theme === 'system') {
        nativeTheme.themeSource = 'default';
    } else {
        nativeTheme.themeSource = theme;
    }
}

// ==================== Backend Lifecycle ====================

async function startBackend(): Promise<number> {
    try {
        if (backendManager) {
            const isRunning = await backendManager.isRunningCheck();
            if (isRunning) {
                backendPort = backendManager.portNumber;
                return backendManager.portNumber;
            }
        }

        backendManager = new BackendManager();
        const port = await backendManager.start();
        backendPort = port;
        backendInitialized = true;
        console.log(`[Main] Backend started on port ${port}`);

        // Notify renderer with port info
        mainWindow?.webContents.send('backend:status-change', 'running');
        mainWindow?.webContents.send('backend:port', port);

        return port;
    } catch (err) {
        console.error('[Main] Failed to start backend:', err);
        backendInitialized = false;
        mainWindow?.webContents.send('backend:status-change', 'error');
        throw err;
    }
}

async function stopBackend(): Promise<boolean> {
    if (backendManager) {
        try {
            await backendManager.stop();
            console.log('[Main] Backend stopped');
            backendInitialized = false;
            mainWindow?.webContents.send('backend:status-change', 'stopped');
            return true;
        } catch (err) {
            console.error('[Main] Error stopping backend:', err);
            backendInitialized = false;
            return false;
        } finally {
            backendManager = null;
        }
    }
    return false;
}

async function restartBackend(): Promise<boolean> {
    await stopBackend();
    return await startBackend();
}

// ==================== IPC Handlers ====================

function registerIpcHandlers(): void {
    // ==================== Backend ====================
    ipcMain.handle('backend:start', async () => {
        const port = await startBackend();
        return port;
    });

    ipcMain.handle('backend:stop', async () => {
        await stopBackend();
        return true;
    });

    ipcMain.handle('backend:isRunning', async () => {
        if (!backendManager) return false;
        return backendManager.isRunningCheck();
    });

    ipcMain.handle('backend:getPort', async () => {
        return backendPort || 8000;
    });

    ipcMain.handle('backend:getInitialized', async () => {
        return backendInitialized;
    });

    // ==================== File System ====================
    ipcMain.handle('fs:read', async (_event, filePath: string) => {
        try {
            return fs.readFileSync(filePath, 'utf-8');
        } catch (err: unknown) {
            const error = err as Error;
            throw new Error(`Failed to read file: ${error.message}`);
        }
    });

    ipcMain.handle('fs:write', async (_event, filePath: string, content: string) => {
        try {
            const dir = path.dirname(filePath);
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
            fs.writeFileSync(filePath, content, 'utf-8');
            return true;
        } catch (err: unknown) {
            const error = err as Error;
            throw new Error(`Failed to write file: ${error.message}`);
        }
    });

    ipcMain.handle('fs:exists', async (_event, filePath: string) => {
        return fs.existsSync(filePath);
    });

    ipcMain.handle('fs:mkdir', async (_event, dirPath: string, recursive = true) => {
        try {
            fs.mkdirSync(dirPath, { recursive });
            return true;
        } catch {
            return false;
        }
    });

    ipcMain.handle('fs:listDir', async (_event, dirPath: string) => {
        try {
            const entries = fs.readdirSync(dirPath, { withFileTypes: true });
            return entries.map((entry) => ({
                name: entry.name,
                path: path.join(dirPath, entry.name),
                type: entry.isDirectory() ? 'directory' : 'file',
                size: entry.isDirectory() ? 0 : entry.size || 0,
                modified: entry.isDirectory()
                    ? ''
                    : new Date().toISOString(),
            }));
        } catch (err: unknown) {
            const error = err as Error;
            throw new Error(`Failed to list directory: ${error.message}`);
        }
    });

    // ==================== Dialogs ====================
    ipcMain.handle('dialog:openFile', async (_event, options) => {
        const result = await dialog.showOpenDialog(mainWindow!, {
            properties: ['openFile'],
            ...(options || {}),
        });
        return result.canceled ? [] : result.filePaths;
    });

    ipcMain.handle('dialog:openFiles', async (_event, options) => {
        const result = await dialog.showOpenDialog(mainWindow!, {
            properties: ['openFile', 'multiSelections'],
            ...(options || {}),
        });
        return result.canceled ? [] : result.filePaths;
    });

    ipcMain.handle('dialog:openFolder', async (_event, options) => {
        const result = await dialog.showOpenDialog(mainWindow!, {
            properties: ['openDirectory'],
            ...(options || {}),
        });
        return result.canceled ? [] : result.filePaths;
    });

    ipcMain.handle('dialog:saveFile', async (_event, options) => {
        const result = await dialog.showSaveDialog(mainWindow!, options || {});
        return result.canceled ? null : result.filePath ?? null;
    });

    ipcMain.handle('dialog:showMessageBox', async (_event, options) => {
        const result = await dialog.showMessageBox(mainWindow!, options || {});
        return result.response;
    });

    // ==================== Shell ====================
    ipcMain.handle('shell:openExternal', async (_event, url: string) => {
        await shell.openExternal(url);
    });

    ipcMain.handle('shell:openPath', async (_event, filePath: string) => {
        return shell.openPath(filePath);
    });

    ipcMain.handle('shell:showItemInFolder', async (_event, filePath: string) => {
        shell.showItemInFolder(filePath);
    });

    // ==================== App ====================
    ipcMain.handle('app:getPath', async (_event, name: string) => {
        return app.getPath(name as Parameters<typeof app.getPath>[0]);
    });

    ipcMain.handle('app:getUserData', async () => {
        return app.getPath('userData');
    });

    ipcMain.handle('app:getVersion', async () => {
        return app.getVersion();
    });

    ipcMain.handle('app:getName', async () => {
        return app.getName();
    });

    // ==================== Window ====================
    ipcMain.handle('window:minimize', () => {
        mainWindow?.minimize();
    });

    ipcMain.handle('window:maximize', () => {
        if (mainWindow?.isMaximized()) {
            mainWindow.unmaximize();
        } else {
            mainWindow?.maximize();
        }
    });

    ipcMain.handle('window:unmaximize', () => {
        mainWindow?.unmaximize();
    });

    ipcMain.handle('window:close', () => {
        mainWindow?.close();
    });

    ipcMain.handle('window:isMaximized', () => {
        return mainWindow?.isMaximized() ?? false;
    });

    ipcMain.handle('window:setResizable', (_event, resizable: boolean) => {
        mainWindow?.setResizable(resizable);
    });

    ipcMain.handle('window:setSize', (_event, width: number, height: number) => {
        mainWindow?.setSize(width, height);
    });

    ipcMain.handle('window:setTitle', (_event, title: string) => {
        mainWindow?.setTitle(title);
    });

    // ==================== Settings ====================
    ipcMain.handle('settings:get', async (_event, key: string) => {
        const settings = loadSettings();
        return (settings as Record<string, unknown>)[key];
    });

    ipcMain.handle('settings:set', async (_event, key: string, value: unknown) => {
        const settings = loadSettings();
        (settings as Record<string, unknown>)[key] = value;
        saveSettings(settings);
        return true;
    });

    ipcMain.handle('settings:getAll', async () => {
        return loadSettings();
    });

    ipcMain.handle('settings:remove', async (_event, key: string) => {
        const settings = loadSettings();
        delete (settings as Record<string, unknown>)[key];
        saveSettings(settings);
        return true;
    });

    // ==================== Clipboard ====================
    ipcMain.handle('clipboard:readText', () => {
        return clipboard.readText();
    });

    ipcMain.handle('clipboard:writeText', (_event, text: string) => {
        clipboard.writeText(text);
    });

    // ==================== Notifications ====================
    ipcMain.handle('notifications:show', async (_event, options) => {
        if (mainWindow) {
            mainWindow.webContents.send('notification', options);
        }
    });

    // ==================== Process Info ====================
    ipcMain.handle('process:platform', () => {
        return process.platform;
    });

    ipcMain.handle('process:arch', () => {
        return process.arch;
    });

    ipcMain.handle('process:memoryUsage', () => {
        const mem = process.memoryUsage();
        return {
            rss: mem.rss,
            heapUsed: mem.heapUsed,
            heapTotal: mem.heapTotal,
        };
    });

    // ==================== DevTools ====================
    ipcMain.on('devtools:toggle', () => {
        if (mainWindow?.webContents) {
            if (mainWindow.webContents.isDevToolsOpened()) {
                mainWindow.webContents.closeDevTools();
            } else {
                mainWindow.webContents.openDevTools();
            }
        }
    });
}

// ==================== App Lifecycle ====================

app.whenReady().then(async () => {
    console.log('[Main] App ready, initializing...');

    // Initialize backend
    try {
        await startBackend();
    } catch (err) {
        console.error('[Main] Backend init failed, will retry on demand:', err);
    }

    // Register IPC handlers
    registerIpcHandlers();

    // Create system tray
    createTray();

    // Create main window
    createWindow();

    console.log('[Main] ClawAI Desktop initialized');
});

app.on('window-all-closed', () => {
    // On Windows, don't quit automatically - minimize to tray
    if (process.platform !== 'darwin') {
        // Let the 'close' handler handle minimizing
    }
});

app.on('will-quit', async () => {
    isAppQuitting = true;
    await stopBackend();
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

// Prevent multiple instances
const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
    app.quit();
} else {
    app.on('second-instance', (_event, commandLine) => {
        if (mainWindow) {
            if (mainWindow.isMinimized()) mainWindow.restore();
            mainWindow.focus();
        }
        // Handle URL protocol if needed
        const url = commandLine[commandLine.length - 1];
        if (url?.startsWith('clawai://')) {
            mainWindow?.webContents.send('url-opened', url);
        }
    });
}

// Graceful shutdown
process.on('SIGINT', async () => {
    isAppQuitting = true;
    await stopBackend();
    app.quit();
});

process.on('SIGTERM', async () => {
    isAppQuitting = true;
    await stopBackend();
    app.quit();
});
