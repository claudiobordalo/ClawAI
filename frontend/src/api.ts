import axios from "axios";

// ==================== Environment Detection ====================

const isElectron = typeof window !== 'undefined' && window.clawai !== undefined;

// Backend URL - will be updated by Electron main process
let backendBaseUrl = isElectron
    ? "http://127.0.0.1:8000/api"  // Placeholder, updated by updateBackendUrl()
    : "http://127.0.0.1:8000/api";

// Initialize backend URL asynchronously
if (isElectron) {
    updateBackendUrl();
}

// ==================== Axios Instance ====================

const api = axios.create({
    baseURL: backendBaseUrl,
    timeout: 30000,
    headers: {
        "Content-Type": "application/json",
    },
});

// ==================== Electron Bridge ====================

interface ElectronBridge {
    backend: {
        start: () => Promise<boolean>;
        stop: () => Promise<boolean>;
        isRunning: () => Promise<boolean>;
        getPort: () => Promise<number>;
    };
    dialog: {
        openFile: (options?: Electron.OpenDialogOptions) => Promise<string[]>;
        saveFile: (options?: Electron.SaveDialogOptions) => Promise<string | null>;
    };
    shell: {
        openExternal: (url: string) => Promise<void>;
        openPath: (filePath: string) => Promise<string>;
    };
    app: {
        getPath: (name: string) => Promise<string>;
        getUserDataPath: () => Promise<string>;
    };
    window: {
        minimize: () => Promise<void>;
        maximize: () => Promise<void>;
        close: () => Promise<void>;
    };
}

declare global {
    interface Window {
        clawai?: ElectronBridge;
    }
}

/**
 * Get the current backend port, checking Electron bridge if available
 */
async function getBackendPort(): Promise<number> {
    if (isElectron && window.clawai?.backend) {
        try {
            return await window.clawai.backend.getPort();
        } catch {
            return 8000;
        }
    }
    return 8000;
}

/**
 * Update the backend URL with the current port
 */
export async function updateBackendUrl(): Promise<void> {
    const port = await getBackendPort();
    backendBaseUrl = `http://127.0.0.1:${port}/api`;
    api.defaults.baseURL = backendBaseUrl;
}

/**
 * Initialize backend via Electron bridge
 */
export async function initBackend(): Promise<boolean> {
    if (!isElectron || !window.clawai?.backend) {
        return false;
    }
    return await window.clawai.backend.start();
}

/**
 * Stop backend via Electron bridge
 */
export async function shutdownBackend(): Promise<void> {
    if (!isElectron || !window.clawai?.backend) {
        return;
    }
    await window.clawai.backend.stop();
}

// ==================== Types ====================

export type SearchTimings = {
    memory_ms?: number;
    knowledge_ms?: number;
    prompt_ms?: number;
    total_ms?: number;
};

export type ChatTimings = {
    search?: SearchTimings;
    model_ms?: number;
    postprocess_ms?: number;
    total_ms?: number;
};

export type ChatReply = {
    answer: string;
    used_memory?: boolean;
    used_knowledge?: boolean;
    requires_web?: boolean;
    provider?: string;
    model?: string;
    memory_saved?: boolean;
    timings?: ChatTimings;
};

export type VerifyStep = {
    name: string;
    command: string;
    success: boolean;
    return_code: number;
    duration_ms: number;
    stdout?: string;
    stderr?: string;
    skipped?: boolean;
    note?: string | null;
};

export type VerifyReport = {
    status?: string;
    started_at?: string;
    finished_at?: string;
    duration_ms?: number;
    steps?: VerifyStep[];
    tests_total?: number | null;
    tests_passed?: number | null;
    tests_failed?: number | null;
    tests_skipped?: number | null;
    tests_errors?: number | null;
    warnings?: number | null;
    api_health_ok?: boolean | null;
    api_chat_ok?: boolean | null;
    api_tree_ok?: boolean | null;
    api_file_ok?: boolean | null;
    api_answer_preview?: string | null;
};

export type VerifyResponse = {
    success: boolean;
    return_code: number;
    stdout: string;
    stderr: string;
    report?: VerifyReport | string | null;
    report_text?: string | null;
    report_data?: VerifyReport | null;
};

export type AutoImplementChange = {
    path: string;
    status: string;
    bytes_written: number;
    backup_path?: string | null;
};

export type AutoImplementTestReport = {
    command: string;
    success: boolean;
    return_code: number;
    stdout: string;
    stderr: string;
    duration_ms: number;
};

export type AutoImplementVerifyReport = {
    command: string;
    success: boolean;
    return_code: number;
    stdout: string;
    stderr: string;
    report_text: string;
    report_data: VerifyReport | Record<string, unknown>;
    summary: string;
    timestamp: string;
    duration_ms: number;
};

export type AutoImplementIteration = {
    iteration: number;
    summary: string;
    changes: AutoImplementChange[];
    test?: AutoImplementTestReport | null;
    verify?: AutoImplementVerifyReport | null;
};

export type AutoImplementReport = {
    objective: string;
    summary: string;
    provider: string;
    model: string;
    candidate_files: string[];
    iterations: AutoImplementIteration[];
    success: boolean;
    test_command: string;
    duration_ms: number;
    verify_success?: boolean | null;
    verify_return_code?: number | null;
    verify_summary?: string | null;
    verify_timestamp?: string | null;
    verify_report?: string | null;
    verify_report_data?: VerifyReport | Record<string, unknown> | null;
    git_enabled?: boolean | null;
    git_base_branch?: string | null;
    git_branch?: string | null;
    git_snapshot_commit?: string | null;
    git_commit?: string | null;
    git_commit_success?: boolean | null;
    git_commit_message?: string | null;
    git_rollback_performed?: boolean | null;
    git_rollback_reason?: string | null;
    git_dirty_snapshot?: boolean | null;
};

export type AutoImplementEvent = {
    index: number;
    step: string;
    status: string;
    message: string;
    iteration?: number | null;
    elapsed_ms?: number | null;
    files: string[];
    summary?: string | null;
    test?: AutoImplementTestReport | null;
    error?: string | null;
};

export type AutoImplementSession = {
    run_id: string;
    objective: string;
    test_command: string;
    max_iterations: number;
    max_files: number;
    status: string;
    current_iteration: number;
    started_at?: string | null;
    finished_at?: string | null;
    duration_ms: number;
    cancel_requested: boolean;
    error?: string | null;
    summary: string;
    events: AutoImplementEvent[];
    result?: AutoImplementReport | null;
    verify_success?: boolean | null;
    verify_return_code?: number | null;
    verify_summary?: string | null;
    verify_timestamp?: string | null;
    verify_report?: string | null;
    verify_report_data?: VerifyReport | Record<string, unknown> | null;
    git_enabled?: boolean | null;
    git_base_branch?: string | null;
    git_branch?: string | null;
    git_snapshot_commit?: string | null;
    git_commit?: string | null;
    git_commit_success?: boolean | null;
    git_commit_message?: string | null;
    git_rollback_performed?: boolean | null;
    git_rollback_reason?: string | null;
    git_dirty_snapshot?: boolean | null;
};

export type WorkspaceInfo = {
    workspace_id: string;
    name: string;
    root: string;
    active: boolean;
};

export type WorkspaceSummary = {
    current: WorkspaceInfo;
    workspaces: WorkspaceInfo[];
};

export type ResourceMonitor = {
    cpu_percent: number;
    memory: {
        total: number;
        used: number;
        percent: number;
    };
    gpu?: {
        used_memory_mb: number;
        total_memory_mb: number;
        percent: number;
        temperature?: number;
        power_watts?: number;
    }[];
    disk: {
        total: number;
        used: number;
        percent: number;
    };
};

export type HealthStatus = {
    status: string;
    uptime_seconds: number;
    memory_usage_mb: number;
    threads: number;
    active_agents: number;
    total_messages: number;
};

// ==================== API Functions ====================

export async function sendChat(prompt: string): Promise<ChatReply> {
    const response = await api.post("/chat", { prompt });
    if (typeof response.data === "string") {
        return { answer: response.data };
    }
    return response.data as ChatReply;
}

export async function runAutoImplement(objective: string, testCommand = "uv run python -m pytest -q", maxIterations = 3, maxFiles = 15): Promise<AutoImplementReport> {
    const response = await api.post("/auto/implement", {
        objective,
        test_command: testCommand,
        max_iterations: maxIterations,
        max_files: maxFiles
    });
    return response.data as AutoImplementReport;
}

export async function startAutoImplement(objective: string, testCommand = "uv run python -m pytest -q", maxIterations = 3, maxFiles = 15): Promise<AutoImplementSession> {
    const response = await api.post("/auto/implement/start", {
        objective,
        test_command: testCommand,
        max_iterations: maxIterations,
        max_files: maxFiles
    });
    return response.data as AutoImplementSession;
}

export async function getAutoImplementStatus(runId: string): Promise<AutoImplementSession> {
    const response = await api.get(`/auto/implement/status/${runId}`);
    return response.data as AutoImplementSession;
}

export async function getAutoImplementEvents(runId: string, after = 0): Promise<AutoImplementEvent[]> {
    const response = await api.get(`/auto/implement/events/${runId}`, { params: { after } });
    return response.data as AutoImplementEvent[];
}

export async function stopAutoImplement(runId: string): Promise<AutoImplementSession> {
    const response = await api.post(`/auto/implement/stop/${runId}`);
    return response.data as AutoImplementSession;
}

export async function runVerify(): Promise<VerifyResponse> {
    const response = await api.post("/verify");
    return response.data as VerifyResponse;
}

export async function listWorkspaces(): Promise<WorkspaceSummary> {
    const response = await api.get("/workspaces");
    return response.data as WorkspaceSummary;
}

export async function getCurrentWorkspace(): Promise<WorkspaceInfo> {
    const response = await api.get("/workspaces/current");
    return response.data as WorkspaceInfo;
}

export async function openWorkspace(path: string, name?: string): Promise<{ workspace: WorkspaceInfo; summary: WorkspaceSummary }> {
    const response = await api.post("/workspaces/open", { path, name: name ?? null });
    return response.data as { workspace: WorkspaceInfo; summary: WorkspaceSummary };
}

export async function selectWorkspace(workspaceId: string): Promise<{ workspace: WorkspaceInfo; summary: WorkspaceSummary }> {
    const response = await api.post("/workspaces/select", { workspace_id: workspaceId });
    return response.data as { workspace: WorkspaceInfo; summary: WorkspaceSummary };
}

export async function closeWorkspace(workspaceId: string): Promise<{ workspaces: WorkspaceInfo[]; summary: WorkspaceSummary }> {
    const response = await api.post(`/workspaces/close/${workspaceId}`);
    return response.data as { workspaces: WorkspaceInfo[]; summary: WorkspaceSummary };
}

export async function loadTree(path = "", workspaceId?: string): Promise<TreeNode[]> {
    const response = await api.get("/tree", { params: { ...(path ? { path } : {}), ...(workspaceId ? { workspace_id: workspaceId } : {}) } });
    return response.data as TreeNode[];
}

export async function loadFile(path: string, workspaceId?: string): Promise<string> {
    const response = await api.get("/file", { params: { path, ...(workspaceId ? { workspace_id: workspaceId } : {}) } });
    return response.data as string;
}

export async function saveFile(path: string, content: string, workspaceId?: string): Promise<void> {
    await api.post("/file", { path, content, ...(workspaceId ? { workspace_id: workspaceId } : {}) });
}

export async function getResourceMonitor(): Promise<ResourceMonitor> {
    const response = await api.get("/monitor/resources");
    return response.data as ResourceMonitor;
}

export async function getHealthStatus(): Promise<HealthStatus> {
    const response = await api.get("/monitor/health");
    return response.data as HealthStatus;
}

// ==================== Dialog Helpers ====================

export async function openFileDialog(): Promise<string | null> {
    if (isElectron && window.clawai?.dialog) {
        const files = await window.clawai.dialog.openFile({
            properties: ['openFile'],
        });
        return files[0] ?? null;
    }
    return null;
}

export async function saveFileDialog(defaultName?: string): Promise<string | null> {
    if (isElectron && window.clawai?.dialog) {
        return await window.clawai.dialog.saveFile({
            defaultFileName: defaultName,
        });
    }
    return null;
}

// ==================== Model Info ====================

export type ModelInfo = {
    id: string;
    name: string;
    provider: string;
    loaded: boolean;
    context_length: number;
    multimodal: boolean;
    function_calling: boolean;
    embeddings: boolean;
    gpu: boolean;
    vram_mb?: number;
    total_vram_mb?: number;
    tokens_per_second?: number;
    status?: string;
};

export type ModelProvider = {
    name: string;
    type: string;
    url?: string;
    models: ModelInfo[];
    status: string;
    config?: Record<string, unknown>;
};

export async function listModels(): Promise<ModelProvider[]> {
    const response = await api.get("/models");
    return response.data as ModelProvider[];
}

export async function getModelInfo(modelId: string): Promise<ModelInfo> {
    const response = await api.get(`/models/${modelId}`);
    return response.data as ModelInfo;
}

export async function switchModel(modelId: string): Promise<{ success: boolean; message: string }> {
    const response = await api.post(`/models/switch`, { model_id: modelId });
    return response.data as { success: boolean; message: string };
}

export async function getModelProviders(): Promise<{ ollama: ModelProvider; lmstudio: ModelProvider; openai: ModelProvider }> {
    const response = await api.get("/models/providers");
    return response.data;
}
