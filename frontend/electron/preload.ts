import { contextBridge, ipcRenderer } from 'electron';

// ==================== Electron Bridge Interface ====================

interface ElectronBridge {
    // Backend lifecycle
    backend: {
        start: () => Promise<number>;  // Returns port number
        stop: () => Promise<boolean>;
        isRunning: () => Promise<boolean>;
        getPort: () => Promise<number>;
        onStatusChange: (callback: (status: string) => void) => void;
        offStatusChange: (callback: (status: string) => void) => void;
    };

    // File system
    fs: {
        read: (path: string) => Promise<string>;
        write: (path: string, content: string) => Promise<boolean>;
        exists: (path: string) => Promise<boolean>;
        mkdir: (path: string, recursive?: boolean) => Promise<boolean>;
        listDir: (path: string) => Promise<FileInfo[]>;
    };

    // Dialogs
    dialog: {
        openFile: (options?: Record<string, unknown>) => Promise<string[]>;
        openFiles: (options?: Record<string, unknown>) => Promise<string[]>;
        openFolder: (options?: Record<string, unknown>) => Promise<string[]>;
        saveFile: (options?: Record<string, unknown>) => Promise<string | null>;
        showMessageBox: (options: MessageBoxOptions) => Promise<number>;
    };

    // Shell
    shell: {
        openExternal: (url: string) => Promise<void>;
        openPath: (filePath: string) => Promise<string>;
        showItemInFolder: (filePath: string) => Promise<void>;
    };

    // App paths
    app: {
        getPath: (name: 'userData' | 'appData' | 'localData' | 'config' | 'desktop' | 'documents' | 'downloads' | 'music' | 'pictures' | 'videos' | 'recent' | 'logs' | 'crashDumps') => Promise<string>;
        getUserDataPath: () => Promise<string>;
        getVersion: () => Promise<string>;
        getName: () => Promise<string>;
    };

    // Window controls
    window: {
        minimize: () => Promise<void>;
        maximize: () => Promise<void>;
        unmaximize: () => Promise<void>;
        close: () => Promise<void>;
        isMaximized: () => Promise<boolean>;
        setResizable: (resizable: boolean) => Promise<void>;
        setSize: (width: number, height: number) => Promise<void>;
        setTitle: (title: string) => Promise<void>;
    };

    // Settings persistence
    settings: {
        get: (key: string) => Promise<unknown>;
        set: (key: string, value: unknown) => Promise<boolean>;
        getAll: () => Promise<Record<string, unknown>>;
        remove: (key: string) => Promise<boolean>;
    };

    // Clipboard
    clipboard: {
        readText: () => Promise<string>;
        writeText: (text: string) => Promise<void>;
    };

    // Notifications
    notifications: {
        show: (options: NotificationOptions) => Promise<void>;
    };

    // Process info
    process: {
        platform: () => Promise<string>;
        arch: () => Promise<string>;
        memoryUsage: () => Promise<{ rss: number; heapUsed: number; heapTotal: number }>;
    };

    // Dev tools toggle
    devtools: {
        toggle: () => void;
    };
}

// ==================== Types ====================

interface FileInfo {
    name: string;
    path: string;
    type: 'file' | 'directory';
    size: number;
    modified: string;
}

interface MessageBoxOptions {
    title: string;
    message: string;
    type?: 'info' | 'error' | 'warning' | 'question';
    buttons?: string[];
    defaultId?: number;
    cancelId?: number;
}

interface NotificationOptions {
    title: string;
    body: string;
    icon?: string;
}

// ==================== IPC Channel Names ====================

const BACKEND_CHANNELS = {
    STATUS_CHANGE: 'backend:status-change',
    START: 'backend:start',
    STOP: 'backend:stop',
    IS_RUNNING: 'backend:isRunning',
    GET_PORT: 'backend:getPort',
} as const;

const FS_CHANNELS = {
    READ: 'fs:read',
    WRITE: 'fs:write',
    EXISTS: 'fs:exists',
    MKDIR: 'fs:mkdir',
    LIST_DIR: 'fs:listDir',
} as const;

const DIALOG_CHANNELS = {
    OPEN_FILE: 'dialog:openFile',
    OPEN_FILES: 'dialog:openFiles',
    OPEN_FOLDER: 'dialog:openFolder',
    SAVE_FILE: 'dialog:saveFile',
    MESSAGE_BOX: 'dialog:showMessageBox',
} as const;

const SHELL_CHANNELS = {
    OPEN_EXTERNAL: 'shell:openExternal',
    OPEN_PATH: 'shell:openPath',
    SHOW_IN_FOLDER: 'shell:showItemInFolder',
} as const;

const APP_CHANNELS = {
    GET_PATH: 'app:getPath',
    GET_USER_DATA: 'app:getUserData',
    GET_VERSION: 'app:getVersion',
    GET_NAME: 'app:getName',
} as const;

const WINDOW_CHANNELS = {
    MINIMIZE: 'window:minimize',
    MAXIMIZE: 'window:maximize',
    UNMAXIMIZE: 'window:unmaximize',
    CLOSE: 'window:close',
    IS_MAXIMIZED: 'window:isMaximized',
    SET_RESIZABLE: 'window:setResizable',
    SET_SIZE: 'window:setSize',
    SET_TITLE: 'window:setTitle',
} as const;

const SETTINGS_CHANNELS = {
    GET: 'settings:get',
    SET: 'settings:set',
    GET_ALL: 'settings:getAll',
    REMOVE: 'settings:remove',
} as const;

// ==================== Bridge Implementation ====================

const backendBridge = {
    get isRunning(): Promise<boolean> {
        return ipcRenderer.invoke(BACKEND_CHANNELS.IS_RUNNING);
    },
    getPort(): Promise<number> {
        return ipcRenderer.invoke(BACKEND_CHANNELS.GET_PORT);
    },
    start(): Promise<number> {
        return ipcRenderer.invoke(BACKEND_CHANNELS.START);
    },
    stop(): Promise<boolean> {
        return ipcRenderer.invoke(BACKEND_CHANNELS.STOP);
    },
    onStatusChange(callback: (status: string) => void): void {
        const handler = (_event: Electron.IpcRendererEvent, status: string) => callback(status);
        ipcRenderer.on(BACKEND_CHANNELS.STATUS_CHANGE, handler);
        // Return cleanup function
        (backendBridge as any)._removeStatusListener = () => {
            ipcRenderer.removeListener(BACKEND_CHANNELS.STATUS_CHANGE, handler);
        };
    },
    offStatusChange(callback: (status: string) => void): void {
        if ((backendBridge as any)._removeStatusListener) {
            (backendBridge as any)._removeStatusListener();
        }
    },
};

const fsBridge = {
    read(path: string): Promise<string> {
        return ipcRenderer.invoke(FS_CHANNELS.READ, path);
    },
    write(path: string, content: string): Promise<boolean> {
        return ipcRenderer.invoke(FS_CHANNELS.WRITE, path, content);
    },
    exists(path: string): Promise<boolean> {
        return ipcRenderer.invoke(FS_CHANNELS.EXISTS, path);
    },
    mkdir(path: string, recursive = true): Promise<boolean> {
        return ipcRenderer.invoke(FS_CHANNELS.MKDIR, path, recursive);
    },
    listDir(path: string): Promise<FileInfo[]> {
        return ipcRenderer.invoke(FS_CHANNELS.LIST_DIR, path);
    },
};

const dialogBridge = {
    openFile(options?: Record<string, unknown>): Promise<string[]> {
        return ipcRenderer.invoke(DIALOG_CHANNELS.OPEN_FILE, options);
    },
    openFiles(options?: Record<string, unknown>): Promise<string[]> {
        return ipcRenderer.invoke(DIALOG_CHANNELS.OPEN_FILES, options);
    },
    openFolder(options?: Record<string, unknown>): Promise<string[]> {
        return ipcRenderer.invoke(DIALOG_CHANNELS.OPEN_FOLDER, options);
    },
    saveFile(options?: Record<string, unknown>): Promise<string | null> {
        return ipcRenderer.invoke(DIALOG_CHANNELS.SAVE_FILE, options);
    },
    showMessageBox(options: MessageBoxOptions): Promise<number> {
        return ipcRenderer.invoke(DIALOG_CHANNELS.MESSAGE_BOX, options);
    },
};

const shellBridge = {
    openExternal(url: string): Promise<void> {
        return ipcRenderer.invoke(SHELL_CHANNELS.OPEN_EXTERNAL, url);
    },
    openPath(filePath: string): Promise<string> {
        return ipcRenderer.invoke(SHELL_CHANNELS.OPEN_PATH, filePath);
    },
    showItemInFolder(filePath: string): Promise<void> {
        return ipcRenderer.invoke(SHELL_CHANNELS.SHOW_IN_FOLDER, filePath);
    },
};

const appBridge = {
    getPath(name: string): Promise<string> {
        return ipcRenderer.invoke(APP_CHANNELS.GET_PATH, name);
    },
    getUserDataPath(): Promise<string> {
        return ipcRenderer.invoke(APP_CHANNELS.GET_USER_DATA);
    },
    getVersion(): Promise<string> {
        return ipcRenderer.invoke(APP_CHANNELS.GET_VERSION);
    },
    getName(): Promise<string> {
        return ipcRenderer.invoke(APP_CHANNELS.GET_NAME);
    },
};

const windowBridge = {
    minimize(): Promise<void> {
        return ipcRenderer.invoke(WINDOW_CHANNELS.MINIMIZE);
    },
    maximize(): Promise<void> {
        return ipcRenderer.invoke(WINDOW_CHANNELS.MAXIMIZE);
    },
    unmaximize(): Promise<void> {
        return ipcRenderer.invoke(WINDOW_CHANNELS.UNMAXIMIZE);
    },
    close(): Promise<void> {
        return ipcRenderer.invoke(WINDOW_CHANNELS.CLOSE);
    },
    isMaximized(): Promise<boolean> {
        return ipcRenderer.invoke(WINDOW_CHANNELS.IS_MAXIMIZED);
    },
    setResizable(resizable: boolean): Promise<void> {
        return ipcRenderer.invoke(WINDOW_CHANNELS.SET_RESIZABLE, resizable);
    },
    setSize(width: number, height: number): Promise<void> {
        return ipcRenderer.invoke(WINDOW_CHANNELS.SET_SIZE, width, height);
    },
    setTitle(title: string): Promise<void> {
        return ipcRenderer.invoke(WINDOW_CHANNELS.SET_TITLE, title);
    },
};

const settingsBridge = {
    get(key: string): Promise<unknown> {
        return ipcRenderer.invoke(SETTINGS_CHANNELS.GET, key);
    },
    set(key: string, value: unknown): Promise<boolean> {
        return ipcRenderer.invoke(SETTINGS_CHANNELS.SET, key, value);
    },
    getAll(): Promise<Record<string, unknown>> {
        return ipcRenderer.invoke(SETTINGS_CHANNELS.GET_ALL);
    },
    remove(key: string): Promise<boolean> {
        return ipcRenderer.invoke(SETTINGS_CHANNELS.REMOVE, key);
    },
};

const clipboardBridge = {
    readText(): Promise<string> {
        return ipcRenderer.invoke('clipboard:readText');
    },
    writeText(text: string): Promise<void> {
        return ipcRenderer.invoke('clipboard:writeText', text);
    },
};

const notificationsBridge = {
    show(options: NotificationOptions): Promise<void> {
        return ipcRenderer.invoke('notifications:show', options);
    },
};

const processBridge = {
    platform(): Promise<string> {
        return ipcRenderer.invoke('process:platform');
    },
    arch(): Promise<string> {
        return ipcRenderer.invoke('process:arch');
    },
    memoryUsage(): Promise<{ rss: number; heapUsed: number; heapTotal: number }> {
        return ipcRenderer.invoke('process:memoryUsage');
    },
};

const devtoolsBridge = {
    toggle(): void {
        ipcRenderer.send('devtools:toggle');
    },
};

// ==================== Expose Bridge ====================

const bridge: ElectronBridge = {
    backend: backendBridge,
    fs: fsBridge,
    dialog: dialogBridge,
    shell: shellBridge,
    app: appBridge,
    window: windowBridge,
    settings: settingsBridge,
    clipboard: clipboardBridge,
    notifications: notificationsBridge,
    process: processBridge,
    devtools: devtoolsBridge,
};

// Expose to renderer via contextBridge
contextBridge.exposeInMainWorld('clawai', bridge);

// ==================== Type Declarations for Window ====================

declare global {
    interface Window {
        clawai: ElectronBridge;
    }
}
