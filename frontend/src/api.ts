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