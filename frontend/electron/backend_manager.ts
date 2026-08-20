import { spawn, ChildProcess } from 'child_process';
import { app } from 'electron';
import * as path from 'path';
import * as fs from 'fs';
import * as net from 'net';

/**
 * BackendManager handles the lifecycle of the ClawAI FastAPI server.
 *
 * In development mode:
 * - Uses system Python
 * - Reads clawai/ from source directory
 * - Reads api.py from root
 *
 * In packaged mode:
 * - Uses embedded Python from resourcesPath/python/
 * - Reads clawai/ from resourcesPath/python/clawai/
 * - Reads api.py from resourcesPath/python/
 * - Copies python/clawi to userData for user-specific files
 */
export class BackendManager {
    private process: ChildProcess | null = null;
    private port: number = 8000;
    private isRunning: boolean = false;
    private retryCount: number = 0;
    private readonly maxRetries: number = 3;
    private readonly retryDelay: number = 2000;

    constructor() {
        // Port will be set in start() after async port detection
        this.port = 8000;
    }

    /**
     * Start the backend server
     */
    async start(): Promise<void> {
        if (this.isRunning) {
            return;
        }

        // Find available port (async)
        this.port = await this.findAvailablePort();
        console.log(`[BackendManager] Selected port: ${this.port}`);

        console.log('[BackendManager] Starting backend...');

        const pythonPath = this.findPython();
        if (!pythonPath) {
            throw new Error('Python interpreter not found. Please ensure Python 3.10+ is installed.');
        }

        // Determine working directory and server script based on mode
        const { serverScript, workDir } = this.findServerAndDir();
        if (!serverScript) {
            throw new Error('Server script (api.py) not found.');
        }

        // In packaged mode, copy python/clawi to userData for user-specific files
        const userDataPath = app.getPath('userData');
        const userDataClawi = path.join(userDataPath, 'clawai');
        if (app.isPackaged) {
            await this.ensureClawiDir(userDataClawi);
        }

        // Build command arguments
        const args = [
            serverScript,
            '--host', '127.0.0.1',
            '--port', String(this.port),
            '--reload', 'false',
        ];

        // Environment variables
        const env = {
            ...process.env,
            CLAWAI_USER_DATA: userDataPath,
            CLAWAI_BACKEND_PORT: String(this.port),
            CLAWAI_PACKAGED: String(app.isPackaged),
            PYTHONIOENCODING: 'utf-8',
        };

        try {
            this.process = spawn(pythonPath, args, {
                cwd: workDir,
                env,
                stdio: ['pipe', 'pipe', 'pipe'],
                detached: false,
            });

            // Handle stdout
            this.process.stdout?.on('data', (data) => {
                const text = data.toString();
                console.log(`[BackendManager] ${text.trim()}`);

                // Check if server is ready
                if (text.includes('Uvicorn running') || text.includes('Application startup complete')) {
                    this.isRunning = true;
                    this.retryCount = 0;
                    console.log(`[BackendManager] Backend ready on port ${this.port}`);
                }
            });

            // Handle stderr
            this.process.stderr?.on('data', (data) => {
                const text = data.toString();
                console.error(`[BackendManager] ${text.trim()}`);
            });

            // Handle process exit
            this.process.on('exit', (code, signal) => {
                console.log(`[BackendManager] Process exited with code ${code}, signal ${signal}`);
                this.isRunning = false;
                this.process = null;
            });

            this.process.on('error', (err) => {
                console.error('[BackendManager] Process error:', err);
                this.isRunning = false;
                this.process = null;

                // Retry if we haven't exceeded max retries
                if (this.retryCount < this.maxRetries) {
                    this.retryCount++;
                    console.log(`[BackendManager] Retrying in ${this.retryDelay}ms (attempt ${this.retryCount}/${this.maxRetries})`);
                    setTimeout(() => this.start(), this.retryDelay);
                }
            });

            // Wait for server to be ready
            await this.waitForServer();

        } catch (err) {
            console.error('[BackendManager] Failed to start backend:', err);
            throw err;
        }
    }

    /**
     * Stop the backend server
     */
    async stop(): Promise<void> {
        if (!this.isRunning || !this.process) {
            return;
        }

        console.log('[BackendManager] Stopping backend...');

        if (process.platform === 'win32') {
            // On Windows, we need to kill the process tree
            try {
                await import('child_process').then(cp => {
                    cp.exec(`taskkill //PID ${this.process!.pid} //F //T`);
                });
            } catch {
                this.process.kill('SIGTERM');
            }
        } else {
            this.process.kill('SIGTERM');
        }

        // Wait for process to exit
        const timeout = new Promise<void>((resolve) => {
            setTimeout(resolve, 5000);
        });

        const exit = new Promise<void>((resolve) => {
            if (!this.process) {
                resolve();
                return;
            }
            this.process.on('exit', () => resolve());
        });

        await Promise.race([exit, timeout]);
        this.isRunning = false;
        this.process = null;
        console.log('[BackendManager] Backend stopped');
    }

    /**
     * Check if backend is running
     */
    isRunningCheck(): boolean {
        return this.isRunning;
    }

    /**
     * Get the backend port
     */
    get portNumber(): number {
        return this.port;
    }

    // ==================== Private Helpers ====================

    /**
     * Find an available port starting from 8000.
     * Returns 8000 if free, otherwise scans for the next available port.
     */
    private async findAvailablePort(): Promise<number> {
        // First try the default port
        if (await this.isPortFree(8000)) {
            return 8000;
        }
        // Scan for next available port
        for (let port = 8001; port < 9000; port++) {
            if (await this.isPortFree(port)) {
                return port;
            }
        }
        throw new Error('No available ports found (8000-8999)');
    }

    /**
     * Check if a port is free using a try-connect approach.
     */
    private isPortFree(port: number): Promise<boolean> {
        return new Promise((resolve) => {
            const server = net.createServer();
            server.once('error', () => {
                resolve(false);
                server.close();
            });
            server.once('listening', () => {
                server.close();
                resolve(true);
            });
            server.listen(port, '127.0.0.1');
        });
    }

    /**
     * Find the server script path and working directory.
     * Returns different paths based on dev vs packaged mode.
     */
    private findServerAndDir(): { serverScript: string | null; workDir: string } {
        if (!app.isPackaged) {
            // Development mode: use source directory
            const sourceDir = path.resolve(__dirname, '..', '..');
            const serverScript = path.join(sourceDir, 'api.py');

            if (fs.existsSync(serverScript)) {
                return { serverScript, workDir: sourceDir };
            }
        } else {
            // Packaged mode: use resourcesPath/python/
            const resourcesPath = process.resourcesPath;
            if (resourcesPath) {
                // electron-builder puts extraResources at resourcesPath/<to>/
                const serverScript = path.join(resourcesPath, 'python', 'api.py');
                const workDir = path.join(resourcesPath, 'python');

                if (fs.existsSync(serverScript)) {
                    return { serverScript, workDir };
                }

                // Fallback: check if electron-builder flattened the structure
                const flatScript = path.join(resourcesPath, 'api.py');
                if (fs.existsSync(flatScript)) {
                    return { serverScript: flatScript, workDir: resourcesPath };
                }
            }
        }

        return { serverScript: null, workDir: '' };
    }

    private findPython(): string | null {
        // Priority 1: Embedded Python (packaged mode)
        if (app.isPackaged) {
            const embeddedPython = this.findEmbeddedPython();
            if (embeddedPython) {
                console.log('[BackendManager] Using embedded Python at:', embeddedPython);
                return embeddedPython;
            }
        }

        // Priority 2: System Python (dev mode or fallback)
        return this.findSystemPython();
    }

    private findEmbeddedPython(): string | null {
        if (!app.isPackaged || !process.resourcesPath) {
            return null;
        }

        const candidates = [
            path.join(process.resourcesPath, 'python', 'python.exe'),
            path.join(process.resourcesPath, 'python311', 'python.exe'),
            path.join(process.resourcesPath, 'python312', 'python.exe'),
        ];

        for (const candidate of candidates) {
            if (this.isPythonAvailable(candidate)) {
                return candidate;
            }
        }

        return null;
    }

    private findSystemPython(): string | null {
        const candidates = [
            'python',
            'python3',
            'py',
            'C:\\Python311\\python.exe',
            'C:\\Python312\\python.exe',
            'C:\\Python313\\python.exe',
            'C:\\Program Files\\Python311\\python.exe',
            'C:\\Program Files\\Python312\\python.exe',
            'C:\\Program Files\\Python313\\python.exe',
            'C:\\Users\\' + (process.env.USERNAME || '') + '\\AppData\\Local\\Programs\\Python\\Python311\\python.exe',
            'C:\\Users\\' + (process.env.USERNAME || '') + '\\AppData\\Local\\Programs\\Python\\Python312\\python.exe',
            'C:\\Users\\' + (process.env.USERNAME || '') + '\\AppData\\Local\\Programs\\Python\\Python313\\python.exe',
        ];

        for (const candidate of candidates) {
            if (this.isPythonAvailable(candidate)) {
                console.log(`[BackendManager] Found Python at: ${candidate}`);
                return candidate;
            }
        }

        // Try to find via where command
        try {
            const { execSync } = require('child_process');
            const output = execSync('where python', { timeout: 3000, encoding: 'utf-8' });
            const lines = output.trim().split('\n').filter(l => l.trim());
            if (lines.length > 0) {
                console.log(`[BackendManager] Found Python via 'where': ${lines[0]}`);
                return lines[0];
            }
        } catch {
            // Ignore
        }

        return null;
    }

    private isPythonAvailable(pythonPath: string): boolean {
        try {
            const { execSync } = require('child_process');
            execSync(`"${pythonPath}" --version`, { timeout: 3000 });
            return true;
        } catch {
            return false;
        }
    }

    private async ensureClawiDir(dest: string): Promise<void> {
        if (fs.existsSync(dest)) {
            return;
        }

        console.log('[BackendManager] Copying clawi directory to userData...');

        // Source directory - use resourcesPath/python/clawai for packaged mode
        let src: string;
        if (!app.isPackaged) {
            src = path.join(__dirname, '..', '..', 'clawai');
        } else {
            // In packaged mode, use resourcesPath/python/clawai
            src = path.join(process.resourcesPath, 'python', 'clawai');
        }

        if (fs.existsSync(src)) {
            await fs.promises.mkdir(dest, { recursive: true });
            await this.copyDir(src, dest);
            console.log('[BackendManager] clawi directory copied to userData');
        } else {
            console.warn('[BackendManager] clawi source directory not found at:', src);
        }
    }

    private async copyDir(src: string, dest: string): Promise<void> {
        const entries = await fs.promises.readdir(src, { withFileTypes: true });

        for (const entry of entries) {
            const srcPath = path.join(src, entry.name);
            const destPath = path.join(dest, entry.name);

            if (entry.isDirectory()) {
                // Skip node_modules, .git, and __pycache__
                if (entry.name === 'node_modules' || entry.name === '.git' || entry.name === '__pycache__') {
                    continue;
                }
                await fs.promises.mkdir(destPath, { recursive: true });
                await this.copyDir(srcPath, destPath);
            } else {
                await fs.promises.copyFile(srcPath, destPath);
            }
        }
    }

    private async waitForServer(): Promise<void> {
        const timeout = 30000; // 30 seconds
        const start = Date.now();

        while (Date.now() - start < timeout) {
            // Try to connect to the port
            const connected = await this.tryConnect(this.port);
            if (connected) {
                this.isRunning = true;
                return;
            }

            await new Promise(resolve => setTimeout(resolve, 500));
        }

        throw new Error('Backend server did not start within timeout');
    }

    private async tryConnect(port: number, timeout = 3000): Promise<boolean> {
        return new Promise((resolve) => {
            const socket = new net.Socket();
            const timer = setTimeout(() => {
                socket.destroy();
                resolve(false);
            }, timeout);

            socket.once('connect', () => {
                clearTimeout(timer);
                socket.destroy();
                resolve(true);
            });

            socket.once('error', () => {
                clearTimeout(timer);
                resolve(false);
            });

            socket.connect(port, '127.0.0.1');
        });
    }
}
