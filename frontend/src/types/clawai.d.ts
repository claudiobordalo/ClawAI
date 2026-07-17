// Type declarations for the clawai API exposed via Electron preload
interface BackendAPI {
    start(): Promise<boolean>;
    stop(): Promise<boolean>;
    isRunning(): Promise<boolean>;
    getPort(): Promise<number>;
}

interface DialogAPI {
    openFile(options?: Electron.OpenDialogOptions): Promise<string[]>;
    saveFile(options?: Electron.SaveDialogOptions): Promise<string | null>;
}

interface ShellAPI {
    openExternal(url: string): Promise<void>;
    openPath(filePath: string): Promise<string>;
}

interface AppAPI {
    getPath(name: string): Promise<string>;
    getUserDataPath(): Promise<string>;
}

interface WindowAPI {
    minimize(): Promise<void>;
    maximize(): Promise<void>;
    close(): Promise<void>;
}

interface ClawAI {
    backend: BackendAPI;
    dialog: DialogAPI;
    shell: ShellAPI;
    app: AppAPI;
    window: WindowAPI;
}

declare global {
    interface Window {
        clawai: ClawAI;
    }
}

export {};
