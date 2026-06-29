import axios from "axios";
import type { TreeNode } from "./tree";

const api = axios.create({
    baseURL: "http://127.0.0.1:8000/api"
});

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

export type AutoImplementIteration = {
    iteration: number;
    summary: string;
    changes: AutoImplementChange[];
    test?: AutoImplementTestReport | null;
    verify?: AutoImplementVerifyReport | null;
};

export type AutoImplementVerifyReport = {
    command: string;
    success: boolean;
    return_code: number;
    stdout: string;
    stderr: string;
    duration_ms: number;
    report_json?: Record<string, unknown> | null;
    report_text?: string;
    summary?: string;
    timestamp?: string;
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
    verify_success?: boolean;
    verify_return_code?: number;
    verify_report?: string;
    verify_summary?: string;
    verify_timestamp?: string;
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
};

export async function sendChat(prompt: string): Promise<ChatReply> {
    const response = await api.post("/chat", {
        prompt
    });

    if (typeof response.data === "string") {
        return { answer: response.data };
    }

    return response.data as ChatReply;
}

export async function runAutoImplement(
    objective: string,
    testCommand = "uv run python -m pytest -q",
    maxIterations = 3,
    maxFiles = 15
): Promise<AutoImplementReport> {
    const response = await api.post("/auto/implement", {
        objective,
        test_command: testCommand,
        max_iterations: maxIterations,
        max_files: maxFiles
    });

    return response.data as AutoImplementReport;
}

export async function startAutoImplement(
    objective: string,
    testCommand = "uv run python -m pytest -q",
    maxIterations = 3,
    maxFiles = 15
): Promise<AutoImplementSession> {
    const response = await api.post("/auto/implement/start", {
        objective,
        test_command: testCommand,
        max_iterations: maxIterations,
        max_files: maxFiles
    });

    return response.data as AutoImplementSession;
}

export async function getAutoImplementStatus(
    runId: string
): Promise<AutoImplementSession> {
    const response = await api.get(`/auto/implement/status/${runId}`);
    return response.data as AutoImplementSession;
}

export async function getAutoImplementEvents(
    runId: string,
    after = 0
): Promise<AutoImplementEvent[]> {
    const response = await api.get(`/auto/implement/events/${runId}`, {
        params: { after }
    });
    return response.data as AutoImplementEvent[];
}

export async function stopAutoImplement(
    runId: string
): Promise<AutoImplementSession> {
    const response = await api.post(`/auto/implement/stop/${runId}`);
    return response.data as AutoImplementSession;
}

export type VerifyResponse = {
    success: boolean;
    return_code: number;
    stdout: string;
    stderr: string;
    report_text?: string | null;
    report?: Record<string, unknown> | null;
};

export async function runVerify(): Promise<VerifyResponse> {
    const response = await api.post(`/verify`);
    return response.data as VerifyResponse;
}

export async function loadTree(path = ""): Promise<TreeNode[]> {
    const response = await api.get("/tree", {
        params: path ? { path } : undefined
    });

    return response.data;
}

export async function loadFile(path: string): Promise<string> {
    const response = await api.get(
        "/file",
        {
            params: {
                path
            }
        }
    );

    return response.data;
}

export async function saveFile(
    path: string,
    content: string
): Promise<void> {
    await api.post(
        "/file",
        {
            path,
            content
        }
    );
}
