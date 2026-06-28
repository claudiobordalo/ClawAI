import axios from "axios";
import type { TreeNode } from "./tree";

const API_BASE_URL = "http://127.0.0.1:8000/api";

const api = axios.create({
    baseURL: API_BASE_URL
});

export type SearchTimings = {
    memory_ms: number;
    knowledge_ms: number;
    prompt_ms: number;
    total_ms: number;
};

export type ChatTimings = {
    search: SearchTimings;
    model_ms: number;
    postprocess_ms: number;
    total_ms: number;
};

export type ChatReply = {
    answer: string;
    used_memory: boolean;
    used_knowledge: boolean;
    requires_web: boolean;
    provider: string;
    model: string;
    memory_saved: boolean;
    timings: ChatTimings;
};

type SseFrame = {
    event: string;
    data: any;
};

function parseSseFrame(frame: string): SseFrame {
    let event = "message";
    const dataLines: string[] = [];

    for (const rawLine of frame.split(/\r?\n/)) {
        const line = rawLine.trimEnd();

        if (line.startsWith("event:")) {
            event = line.slice(6).trim();
            continue;
        }

        if (line.startsWith("data:")) {
            dataLines.push(line.slice(5).trimStart());
        }
    }

    const dataText = dataLines.join("\n");

    if (!dataText) {
        return { event, data: {} };
    }

    try {
        return {
            event,
            data: JSON.parse(dataText)
        };
    } catch {
        return {
            event,
            data: { text: dataText }
        };
    }
}

export async function sendChat(prompt: string): Promise<ChatReply> {
    const response = await api.post("/chat", {
        prompt
    });

    return response.data as ChatReply;
}

export async function streamChat(
    prompt: string,
    onDelta: (chunk: string) => void,
): Promise<ChatReply> {
    const response = await fetch(
        `${API_BASE_URL}/chat/stream`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            },
            body: JSON.stringify({
                prompt
            })
        }
    );

    if (!response.ok) {
        const body = await response.text().catch(() => "");
        throw new Error(body || `HTTP ${response.status}`);
    }

    if (!response.body) {
        throw new Error("Streaming não disponível no navegador.");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");

    let buffer = "";
    let reply: ChatReply | null = null;

    while (true) {
        const { value, done } = await reader.read();

        if (done) {
            break;
        }

        buffer += decoder.decode(value, { stream: true });

        while (true) {
            const separator = buffer.indexOf("\n\n");

            if (separator === -1) {
                break;
            }

            const frame = buffer.slice(0, separator);
            buffer = buffer.slice(separator + 2);

            if (!frame.trim()) {
                continue;
            }

            const parsed = parseSseFrame(frame);

            if (parsed.event === "delta") {
                const chunk = String(parsed.data?.text ?? "");

                if (chunk) {
                    onDelta(chunk);
                }
                continue;
            }

            if (parsed.event === "final") {
                reply = parsed.data.reply as ChatReply;
                continue;
            }

            if (parsed.event === "error") {
                const message = String(
                    parsed.data?.message ?? "Erro no streaming."
                );

                throw new Error(message);
            }
        }
    }

    if (!reply) {
        throw new Error("A resposta terminou sem evento final.");
    }

    return reply;
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