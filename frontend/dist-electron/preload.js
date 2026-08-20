"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
// ==================== IPC Channel Names ====================
const BACKEND_CHANNELS = {
    STATUS_CHANGE: 'backend:status-change',
    START: 'backend:start',
    STOP: 'backend:stop',
    IS_RUNNING: 'backend:isRunning',
    GET_PORT: 'backend:getPort',
};
const FS_CHANNELS = {
    READ: 'fs:read',
    WRITE: 'fs:write',
    EXISTS: 'fs:exists',
    MKDIR: 'fs:mkdir',
    LIST_DIR: 'fs:listDir',
};
const DIALOG_CHANNELS = {
    OPEN_FILE: 'dialog:openFile',
    OPEN_FILES: 'dialog:openFiles',
    OPEN_FOLDER: 'dialog:openFolder',
    SAVE_FILE: 'dialog:saveFile',
    MESSAGE_BOX: 'dialog:showMessageBox',
};
const SHELL_CHANNELS = {
    OPEN_EXTERNAL: 'shell:openExternal',
    OPEN_PATH: 'shell:openPath',
    SHOW_IN_FOLDER: 'shell:showItemInFolder',
};
const APP_CHANNELS = {
    GET_PATH: 'app:getPath',
    GET_USER_DATA: 'app:getUserData',
    GET_VERSION: 'app:getVersion',
    GET_NAME: 'app:getName',
};
const WINDOW_CHANNELS = {
    MINIMIZE: 'window:minimize',
    MAXIMIZE: 'window:maximize',
    UNMAXIMIZE: 'window:unmaximize',
    CLOSE: 'window:close',
    IS_MAXIMIZED: 'window:isMaximized',
    SET_RESIZABLE: 'window:setResizable',
    SET_SIZE: 'window:setSize',
    SET_TITLE: 'window:setTitle',
};
const SETTINGS_CHANNELS = {
    GET: 'settings:get',
    SET: 'settings:set',
    GET_ALL: 'settings:getAll',
    REMOVE: 'settings:remove',
};
// ==================== Bridge Implementation ====================
const backendBridge = {
    get isRunning() {
        return electron_1.ipcRenderer.invoke(BACKEND_CHANNELS.IS_RUNNING);
    },
    getPort() {
        return electron_1.ipcRenderer.invoke(BACKEND_CHANNELS.GET_PORT);
    },
    start() {
        return electron_1.ipcRenderer.invoke(BACKEND_CHANNELS.START);
    },
    stop() {
        return electron_1.ipcRenderer.invoke(BACKEND_CHANNELS.STOP);
    },
    onStatusChange(callback) {
        const handler = (_event, status) => callback(status);
        electron_1.ipcRenderer.on(BACKEND_CHANNELS.STATUS_CHANGE, handler);
        // Return cleanup function
        backendBridge._removeStatusListener = () => {
            electron_1.ipcRenderer.removeListener(BACKEND_CHANNELS.STATUS_CHANGE, handler);
        };
    },
    offStatusChange(callback) {
        if (backendBridge._removeStatusListener) {
            backendBridge._removeStatusListener();
        }
    },
};
const fsBridge = {
    read(path) {
        return electron_1.ipcRenderer.invoke(FS_CHANNELS.READ, path);
    },
    write(path, content) {
        return electron_1.ipcRenderer.invoke(FS_CHANNELS.WRITE, path, content);
    },
    exists(path) {
        return electron_1.ipcRenderer.invoke(FS_CHANNELS.EXISTS, path);
    },
    mkdir(path, recursive = true) {
        return electron_1.ipcRenderer.invoke(FS_CHANNELS.MKDIR, path, recursive);
    },
    listDir(path) {
        return electron_1.ipcRenderer.invoke(FS_CHANNELS.LIST_DIR, path);
    },
};
const dialogBridge = {
    openFile(options) {
        return electron_1.ipcRenderer.invoke(DIALOG_CHANNELS.OPEN_FILE, options);
    },
    openFiles(options) {
        return electron_1.ipcRenderer.invoke(DIALOG_CHANNELS.OPEN_FILES, options);
    },
    openFolder(options) {
        return electron_1.ipcRenderer.invoke(DIALOG_CHANNELS.OPEN_FOLDER, options);
    },
    saveFile(options) {
        return electron_1.ipcRenderer.invoke(DIALOG_CHANNELS.SAVE_FILE, options);
    },
    showMessageBox(options) {
        return electron_1.ipcRenderer.invoke(DIALOG_CHANNELS.MESSAGE_BOX, options);
    },
};
const shellBridge = {
    openExternal(url) {
        return electron_1.ipcRenderer.invoke(SHELL_CHANNELS.OPEN_EXTERNAL, url);
    },
    openPath(filePath) {
        return electron_1.ipcRenderer.invoke(SHELL_CHANNELS.OPEN_PATH, filePath);
    },
    showItemInFolder(filePath) {
        return electron_1.ipcRenderer.invoke(SHELL_CHANNELS.SHOW_IN_FOLDER, filePath);
    },
};
const appBridge = {
    getPath(name) {
        return electron_1.ipcRenderer.invoke(APP_CHANNELS.GET_PATH, name);
    },
    getUserDataPath() {
        return electron_1.ipcRenderer.invoke(APP_CHANNELS.GET_USER_DATA);
    },
    getVersion() {
        return electron_1.ipcRenderer.invoke(APP_CHANNELS.GET_VERSION);
    },
    getName() {
        return electron_1.ipcRenderer.invoke(APP_CHANNELS.GET_NAME);
    },
};
const windowBridge = {
    minimize() {
        return electron_1.ipcRenderer.invoke(WINDOW_CHANNELS.MINIMIZE);
    },
    maximize() {
        return electron_1.ipcRenderer.invoke(WINDOW_CHANNELS.MAXIMIZE);
    },
    unmaximize() {
        return electron_1.ipcRenderer.invoke(WINDOW_CHANNELS.UNMAXIMIZE);
    },
    close() {
        return electron_1.ipcRenderer.invoke(WINDOW_CHANNELS.CLOSE);
    },
    isMaximized() {
        return electron_1.ipcRenderer.invoke(WINDOW_CHANNELS.IS_MAXIMIZED);
    },
    setResizable(resizable) {
        return electron_1.ipcRenderer.invoke(WINDOW_CHANNELS.SET_RESIZABLE, resizable);
    },
    setSize(width, height) {
        return electron_1.ipcRenderer.invoke(WINDOW_CHANNELS.SET_SIZE, width, height);
    },
    setTitle(title) {
        return electron_1.ipcRenderer.invoke(WINDOW_CHANNELS.SET_TITLE, title);
    },
};
const settingsBridge = {
    get(key) {
        return electron_1.ipcRenderer.invoke(SETTINGS_CHANNELS.GET, key);
    },
    set(key, value) {
        return electron_1.ipcRenderer.invoke(SETTINGS_CHANNELS.SET, key, value);
    },
    getAll() {
        return electron_1.ipcRenderer.invoke(SETTINGS_CHANNELS.GET_ALL);
    },
    remove(key) {
        return electron_1.ipcRenderer.invoke(SETTINGS_CHANNELS.REMOVE, key);
    },
};
const clipboardBridge = {
    readText() {
        return electron_1.ipcRenderer.invoke('clipboard:readText');
    },
    writeText(text) {
        return electron_1.ipcRenderer.invoke('clipboard:writeText', text);
    },
};
const notificationsBridge = {
    show(options) {
        return electron_1.ipcRenderer.invoke('notifications:show', options);
    },
};
const processBridge = {
    platform() {
        return electron_1.ipcRenderer.invoke('process:platform');
    },
    arch() {
        return electron_1.ipcRenderer.invoke('process:arch');
    },
    memoryUsage() {
        return electron_1.ipcRenderer.invoke('process:memoryUsage');
    },
};
const devtoolsBridge = {
    toggle() {
        electron_1.ipcRenderer.send('devtools:toggle');
    },
};
// ==================== Expose Bridge ====================
const bridge = {
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
electron_1.contextBridge.exposeInMainWorld('clawai', bridge);
