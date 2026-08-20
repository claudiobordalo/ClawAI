/**
 * Electron IPC Bridge
 * 
 * Provides a thin abstraction layer between the React frontend
 * and the Electron main process. When running in Electron mode,
 * all backend communication goes through IPC instead of HTTP.
 * When running in browser mode (vite dev), it falls back to HTTP.
 */

import axios from 'axios';

// Dynamic backend URL - set at runtime by Electron
let backendUrl = 'http://127.0.0.1:8000/api';

export function setBackendUrl(url: string): void {
    backendUrl = url;
}

/**
 * Check if we're running inside Electron
 */
function isElectron(): boolean {
    return typeof window !== 'undefined' && window.clawai !== undefined;
}

/**
 * Make an HTTP request to the backend (browser mode).
 * In Electron mode, this is replaced by IPC calls.
 */
async function httpFetch<T>(endpoint: string, options?: {
    method?: string;
    body?: unknown;
}): Promise<T> {
    const response = await axios({
        url: `${backendUrl}${endpoint}`,
        method: options?.method ?? 'GET',
        data: options?.body,
        timeout: 30000,
    });
    return response.data as T;
}

// ==================== Backend Management ====================

export async function backendStart(): Promise<boolean> {
    if (isElectron()) {
        return window.clawai.backend.start();
    }
    // In browser mode, assume backend is already running
    return true;
}

export async function backendStop(): Promise<boolean> {
    if (isElectron()) {
        return window.clawai.backend.stop();
    }
    return true;
}

export async function backendIsRunning(): Promise<boolean> {
    if (isElectron()) {
        return window.clawai.backend.isRunning();
    }
    return true;
}

export async function backendGetPort(): Promise<number> {
    if (isElectron()) {
        return window.clawai.backend.getPort();
    }
    return 8000;
}

// ==================== Dialog ====================

export async function dialogOpenFile(options?: Electron.OpenDialogOptions): Promise<string[]> {
    if (isElectron()) {
        return window.clawai.dialog.openFile(options);
    }
    // Browser fallback: empty array
    return [];
}

export async function dialogSaveFile(options?: Electron.SaveDialogOptions): Promise<string | null> {
    if (isElectron()) {
        return window.clawai.dialog.saveFile(options);
    }
    return null;
}

// ==================== Shell ====================

export async function shellOpenExternal(url: string): Promise<void> {
    if (isElectron()) {
        return window.clawai.shell.openExternal(url);
    }
    window.open(url, '_blank');
}

export async function shellOpenPath(filePath: string): Promise<string> {
    if (isElectron()) {
        return window.clawai.shell.openPath(filePath);
    }
    return filePath;
}

// ==================== App ====================

export async function appGetPath(name: string): Promise<string> {
    if (isElectron()) {
        return window.clawai.app.getPath(name);
    }
    return '';
}

export async function appGetUserDataPath(): Promise<string> {
    if (isElectron()) {
        return window.clawai.app.getUserDataPath();
    }
    return '';
}

// ==================== Window Controls ====================

export async function windowMinimize(): Promise<void> {
    if (isElectron()) {
        return window.clawai.window.minimize();
    }
}

export async function windowMaximize(): Promise<void> {
    if (isElectron()) {
        return window.clawai.window.maximize();
    }
}

export async function windowClose(): Promise<void> {
    if (isElectron()) {
        return window.clawai.window.close();
    }
}

// ==================== WebSocket ====================

let ws: WebSocket | null = null;
let wsUrl = 'ws://127.0.0.1:8000/ws';

export function setWebSocketUrl(url: string): void {
    wsUrl = url;
}

export function getWebSocket(): WebSocket | null {
    return ws;
}

export function connectWebSocket(onMessage: (data: unknown) => void): void {
    if (ws && ws.readyState === WebSocket.OPEN) return;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('[Bridge] WebSocket connected');
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            onMessage(data);
        } catch {
            onMessage(event.data);
        }
    };

    ws.onerror = (err) => {
        console.error('[Bridge] WebSocket error:', err);
    };

    ws.onclose = () => {
        console.log('[Bridge] WebSocket closed');
        ws = null;
    };
}

export function disconnectWebSocket(): void {
    if (ws) {
        ws.close();
        ws = null;
    }
}

export function sendWebSocket(data: unknown): void {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(data));
    }
}
