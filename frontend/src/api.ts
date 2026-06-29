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


export async function runVerify(): Promise<VerifyResponse> {
    const response = await api.post("/verify");
    return response.data as VerifyResponse;
}
