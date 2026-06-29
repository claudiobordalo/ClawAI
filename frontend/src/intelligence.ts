import axios from "axios";

const api = axios.create({
    baseURL: "http://127.0.0.1:8000/api"
});

export type IntelligenceAnalysis = {
    prompt: string;
    objective: string;
    classification: Record<string, unknown>;
    decision: Record<string, unknown>;
    memory_hits: Record<string, unknown>[];
    discovered_tools: Record<string, unknown>[];
    parallel_agents: string[];
    reasoning: string;
    model_strategy: Record<string, unknown>;
};

export type IntelligenceState = {
    tools: Record<string, unknown>[];
    memory: Record<string, unknown>;
    providers: string[];
    bridge_tools: string[];
};

export type ComposioStatus = {
    configured: boolean;
    tools: number;
    connections: number;
    providers: string[];
    sample_tools: string[];
};

export async function getIntelligenceState(): Promise<IntelligenceState> {
    const response = await api.get("/intelligence/state");
    return response.data as IntelligenceState;
}

export async function analyzeIntelligence(prompt: string, objective?: string): Promise<IntelligenceAnalysis> {
    const response = await api.post("/intelligence/analyze", {
        prompt,
        objective: objective ?? null,
    });
    return response.data as IntelligenceAnalysis;
}

export async function searchIntelligenceMemory(query: string, limit = 10): Promise<Record<string, unknown>[]> {
    const response = await api.get("/intelligence/memory/search", {
        params: { query, limit },
    });
    return response.data as Record<string, unknown>[];
}

export async function getComposioStatus(): Promise<ComposioStatus> {
    const response = await api.get("/integrations/composio/status");
    return response.data as ComposioStatus;
}

export async function getComposioTools(forceRefresh = false): Promise<Record<string, unknown>[]> {
    const response = await api.get("/integrations/composio/tools", {
        params: { force_refresh: forceRefresh },
    });
    return response.data as Record<string, unknown>[];
}
