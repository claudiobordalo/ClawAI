"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
const path = __importStar(require("path"));
const fs = __importStar(require("fs"));
const backend_manager_1 = require("./backend_manager");
// ==================== Globals ====================
let mainWindow = null;
let tray = null;
let backendManager = null;
let isAppQuitting = false;
let backendPort = 8000;
let backendInitialized = false;
const defaultState = {
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
function getSettingsPath() {
    return path.join(electron_1.app.getPath('userData'), 'settings.json');
}
function loadSettings() {
    try {
        const settingsPath = getSettingsPath();
        if (fs.existsSync(settingsPath)) {
            const data = JSON.parse(fs.readFileSync(settingsPath, 'utf-8'));
            return { ...defaultState, ...data };
        }
    }
    catch (err) {
        console.error('[Main] Failed to load settings:', err);
    }
    return { ...defaultState };
}
function saveSettings(settings) {
    try {
        const settingsPath = getSettingsPath();
        const dir = path.dirname(settingsPath);
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
        fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2));
    }
    catch (err) {
        console.error('[Main] Failed to save settings:', err);
    }
}
// ==================== Tray Management ====================
function createTray() {
    const iconPath = path.join(__dirname, '..', 'public', 'icon.png');
    const fallbackIcon = path.join(__dirname, '..', 'public', 'icon.ico');
    // Use .ico for Windows tray
    const trayIcon = electron_1.app.isPackaged
        ? path.join(process.resourcesPath, 'public', 'icon.ico')
        : fallbackIcon;
    tray = new electron_1.Tray(trayIcon);
    tray.setToolTip('ClawAI');
    const contextMenu = electron_1.Menu.buildFromTemplate([
        {
            label: 'Abrir ClawAI',
            click: () => {
                if (mainWindow) {
                    if (mainWindow.isMinimized())
                        mainWindow.restore();
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
            click: () => electron_1.app.quit(),
        },
    ]);
    tray.setContextMenu(contextMenu);
    tray.on('click', () => {
        if (mainWindow) {
            if (mainWindow.isVisible()) {
                mainWindow.minimize();
            }
            else {
                if (mainWindow.isMinimized())
                    mainWindow.restore();
                mainWindow.focus();
            }
        }
    });
}
// ==================== Window Management ====================
function createWindow() {
    const settings = loadSettings();
    // Restore window bounds or use defaults
    let bounds;
    if (settings.windowBounds) {
        const primaryDisplay = electron_1.screen.getPrimaryDisplay();
        const workArea = primaryDisplay.workAreaSize;
        // Validate bounds are within work area
        const isValid = settings.windowBounds.width <= workArea.width &&
            settings.windowBounds.height <= workArea.height &&
            settings.windowBounds.width >= 900 &&
            settings.windowBounds.height >= 600;
        if (isValid) {
            bounds = settings.windowBounds;
        }
        else {
            bounds = getDefaultBounds();
        }
    }
    else {
        bounds = getDefaultBounds();
    }
    mainWindow = new electron_1.BrowserWindow({
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
    }
    else {
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
function getDefaultBounds() {
    const primaryDisplay = electron_1.screen.getPrimaryDisplay();
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
function applyTheme(theme) {
    if (theme === 'system') {
        electron_1.nativeTheme.themeSource = 'default';
    }
    else {
        electron_1.nativeTheme.themeSource = theme;
    }
}
// ==================== Backend Lifecycle ====================
async function startBackend() {
    try {
        if (backendManager) {
            const isRunning = await backendManager.isRunningCheck();
            if (isRunning) {
                backendPort = backendManager.portNumber;
                return backendManager.portNumber;
            }
        }
        backendManager = new backend_manager_1.BackendManager();
        const port = await backendManager.start();
        backendPort = port;
        backendInitialized = true;
        console.log(`[Main] Backend started on port ${port}`);
        // Notify renderer with port info
        mainWindow?.webContents.send('backend:status-change', 'running');
        mainWindow?.webContents.send('backend:port', port);
        return port;
    }
    catch (err) {
        console.error('[Main] Failed to start backend:', err);
        backendInitialized = false;
        mainWindow?.webContents.send('backend:status-change', 'error');
        throw err;
    }
}
async function stopBackend() {
    if (backendManager) {
        try {
            await backendManager.stop();
            console.log('[Main] Backend stopped');
            backendInitialized = false;
            mainWindow?.webContents.send('backend:status-change', 'stopped');
            return true;
        }
        catch (err) {
            console.error('[Main] Error stopping backend:', err);
            backendInitialized = false;
            return false;
        }
        finally {
            backendManager = null;
        }
    }
    return false;
}
async function restartBackend() {
    await stopBackend();
    return await startBackend();
}
// ==================== IPC Handlers ====================
function registerIpcHandlers() {
    // ==================== Backend ====================
    electron_1.ipcMain.handle('backend:start', async () => {
        const port = await startBackend();
        return port;
    });
    electron_1.ipcMain.handle('backend:stop', async () => {
        await stopBackend();
        return true;
    });
    electron_1.ipcMain.handle('backend:isRunning', async () => {
        if (!backendManager)
            return false;
        return backendManager.isRunningCheck();
    });
    electron_1.ipcMain.handle('backend:getPort', async () => {
        return backendPort || 8000;
    });
    electron_1.ipcMain.handle('backend:getInitialized', async () => {
        return backendInitialized;
    });
    // ==================== File System ====================
    electron_1.ipcMain.handle('fs:read', async (_event, filePath) => {
        try {
            return fs.readFileSync(filePath, 'utf-8');
        }
        catch (err) {
            const error = err;
            throw new Error(`Failed to read file: ${error.message}`);
        }
    });
    electron_1.ipcMain.handle('fs:write', async (_event, filePath, content) => {
        try {
            const dir = path.dirname(filePath);
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
            fs.writeFileSync(filePath, content, 'utf-8');
            return true;
        }
        catch (err) {
            const error = err;
            throw new Error(`Failed to write file: ${error.message}`);
        }
    });
    electron_1.ipcMain.handle('fs:exists', async (_event, filePath) => {
        return fs.existsSync(filePath);
    });
    electron_1.ipcMain.handle('fs:mkdir', async (_event, dirPath, recursive = true) => {
        try {
            fs.mkdirSync(dirPath, { recursive });
            return true;
        }
        catch {
            return false;
        }
    });
    electron_1.ipcMain.handle('fs:listDir', async (_event, dirPath) => {
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
        }
        catch (err) {
            const error = err;
            throw new Error(`Failed to list directory: ${error.message}`);
        }
    });
    // ==================== Dialogs ====================
    electron_1.ipcMain.handle('dialog:openFile', async (_event, options) => {
        const result = await electron_1.dialog.showOpenDialog(mainWindow, {
            properties: ['openFile'],
            ...(options || {}),
        });
        return result.canceled ? [] : result.filePaths;
    });
    electron_1.ipcMain.handle('dialog:openFiles', async (_event, options) => {
        const result = await electron_1.dialog.showOpenDialog(mainWindow, {
            properties: ['openFile', 'multiSelections'],
            ...(options || {}),
        });
        return result.canceled ? [] : result.filePaths;
    });
    electron_1.ipcMain.handle('dialog:openFolder', async (_event, options) => {
        const result = await electron_1.dialog.showOpenDialog(mainWindow, {
            properties: ['openDirectory'],
            ...(options || {}),
        });
        return result.canceled ? [] : result.filePaths;
    });
    electron_1.ipcMain.handle('dialog:saveFile', async (_event, options) => {
        const result = await electron_1.dialog.showSaveDialog(mainWindow, options || {});
        return result.canceled ? null : result.filePath ?? null;
    });
    electron_1.ipcMain.handle('dialog:showMessageBox', async (_event, options) => {
        const result = await electron_1.dialog.showMessageBox(mainWindow, options || {});
        return result.response;
    });
    // ==================== Shell ====================
    electron_1.ipcMain.handle('shell:openExternal', async (_event, url) => {
        await electron_1.shell.openExternal(url);
    });
    electron_1.ipcMain.handle('shell:openPath', async (_event, filePath) => {
        return electron_1.shell.openPath(filePath);
    });
    electron_1.ipcMain.handle('shell:showItemInFolder', async (_event, filePath) => {
        electron_1.shell.showItemInFolder(filePath);
    });
    // ==================== App ====================
    electron_1.ipcMain.handle('app:getPath', async (_event, name) => {
        return electron_1.app.getPath(name);
    });
    electron_1.ipcMain.handle('app:getUserData', async () => {
        return electron_1.app.getPath('userData');
    });
    electron_1.ipcMain.handle('app:getVersion', async () => {
        return electron_1.app.getVersion();
    });
    electron_1.ipcMain.handle('app:getName', async () => {
        return electron_1.app.getName();
    });
    // ==================== Window ====================
    electron_1.ipcMain.handle('window:minimize', () => {
        mainWindow?.minimize();
    });
    electron_1.ipcMain.handle('window:maximize', () => {
        if (mainWindow?.isMaximized()) {
            mainWindow.unmaximize();
        }
        else {
            mainWindow?.maximize();
        }
    });
    electron_1.ipcMain.handle('window:unmaximize', () => {
        mainWindow?.unmaximize();
    });
    electron_1.ipcMain.handle('window:close', () => {
        mainWindow?.close();
    });
    electron_1.ipcMain.handle('window:isMaximized', () => {
        return mainWindow?.isMaximized() ?? false;
    });
    electron_1.ipcMain.handle('window:setResizable', (_event, resizable) => {
        mainWindow?.setResizable(resizable);
    });
    electron_1.ipcMain.handle('window:setSize', (_event, width, height) => {
        mainWindow?.setSize(width, height);
    });
    electron_1.ipcMain.handle('window:setTitle', (_event, title) => {
        mainWindow?.setTitle(title);
    });
    // ==================== Settings ====================
    electron_1.ipcMain.handle('settings:get', async (_event, key) => {
        const settings = loadSettings();
        return settings[key];
    });
    electron_1.ipcMain.handle('settings:set', async (_event, key, value) => {
        const settings = loadSettings();
        settings[key] = value;
        saveSettings(settings);
        return true;
    });
    electron_1.ipcMain.handle('settings:getAll', async () => {
        return loadSettings();
    });
    electron_1.ipcMain.handle('settings:remove', async (_event, key) => {
        const settings = loadSettings();
        delete settings[key];
        saveSettings(settings);
        return true;
    });
    // ==================== Clipboard ====================
    electron_1.ipcMain.handle('clipboard:readText', () => {
        return electron_1.clipboard.readText();
    });
    electron_1.ipcMain.handle('clipboard:writeText', (_event, text) => {
        electron_1.clipboard.writeText(text);
    });
    // ==================== Notifications ====================
    electron_1.ipcMain.handle('notifications:show', async (_event, options) => {
        if (mainWindow) {
            mainWindow.webContents.send('notification', options);
        }
    });
    // ==================== Process Info ====================
    electron_1.ipcMain.handle('process:platform', () => {
        return process.platform;
    });
    electron_1.ipcMain.handle('process:arch', () => {
        return process.arch;
    });
    electron_1.ipcMain.handle('process:memoryUsage', () => {
        const mem = process.memoryUsage();
        return {
            rss: mem.rss,
            heapUsed: mem.heapUsed,
            heapTotal: mem.heapTotal,
        };
    });
    // ==================== DevTools ====================
    electron_1.ipcMain.on('devtools:toggle', () => {
        if (mainWindow?.webContents) {
            if (mainWindow.webContents.isDevToolsOpened()) {
                mainWindow.webContents.closeDevTools();
            }
            else {
                mainWindow.webContents.openDevTools();
            }
        }
    });
}
// ==================== App Lifecycle ====================
electron_1.app.whenReady().then(async () => {
    console.log('[Main] App ready, initializing...');
    // Initialize backend
    try {
        await startBackend();
    }
    catch (err) {
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
electron_1.app.on('window-all-closed', () => {
    // On Windows, don't quit automatically - minimize to tray
    if (process.platform !== 'darwin') {
        // Let the 'close' handler handle minimizing
    }
});
electron_1.app.on('will-quit', async () => {
    isAppQuitting = true;
    await stopBackend();
});
electron_1.app.on('activate', () => {
    if (electron_1.BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});
// Prevent multiple instances
const gotLock = electron_1.app.requestSingleInstanceLock();
if (!gotLock) {
    electron_1.app.quit();
}
else {
    electron_1.app.on('second-instance', (_event, commandLine) => {
        if (mainWindow) {
            if (mainWindow.isMinimized())
                mainWindow.restore();
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
    electron_1.app.quit();
});
process.on('SIGTERM', async () => {
    isAppQuitting = true;
    await stopBackend();
    electron_1.app.quit();
});
