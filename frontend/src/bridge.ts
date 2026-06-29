import axios from "axios";

const api = axios.create({
    baseURL: "http://127.0.0.1:8000/api"
});

export type BridgeParticipantRequest = {
    role: string;
    provider?: string | null;
    model?: string | null;
};

export type BridgeParticipantResult = {
    role: string;
    provider: string;
    model: string;
    content: string;
    elapsed_ms: number;
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
    error?: string;
};

export type BridgeToolDecision = {
    recommended_tool: string;
    reason: string;
    confidence: number;
    winner_role: string;
    source: string;
};

export type BridgeConsultResult = {
    prompt: string;
    system_prompt: string;
    heuristic_tool: string;
    heuristic_reason: string;
    decision: BridgeToolDecision;
    winner_role: string;
    final_answer: string;
    participants: BridgeParticipantResult[];
    elapsed_ms: number;
    parallel_roles: string[];
    judge_model: string;
    judge_provider: string;
    judge_raw: string;
};

export type BridgeProvidersResponse = {
    providers: string[];
    tools: string[];
    default_roles: string[];
};

export type BridgeConsultRequest = {
    prompt: string;
    system_prompt?: string | null;
    participants?: BridgeParticipantRequest[];
    judge_provider?: string | null;
};

export async function getBridgeProviders(): Promise<BridgeProvidersResponse> {
    const response = await api.get("/bridge/providers");
    return response.data as BridgeProvidersResponse;
}

export async function consultBridge(request: BridgeConsultRequest): Promise<BridgeConsultResult> {
    const response = await api.post("/bridge/consult", request);
    return response.data as BridgeConsultResult;
}

export async function recommendBridgeTool(request: BridgeConsultRequest): Promise<BridgeToolDecision> {
    const response = await api.post("/bridge/recommend-tool", request);
    return response.data as BridgeToolDecision;
}
