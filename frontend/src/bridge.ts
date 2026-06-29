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

export type CognitionTaskClassification = {
    category: string;
    recommended_tool: string;
    confidence: number;
    rationale: string;
    tags: string[];
    parallel_roles: string[];
};

export type CognitionReasoningNode = {
    node_id: string;
    label: string;
    kind: string;
    score: number;
    details: string;
    children: string[];
};

export type CognitionWorkspace = {
    workspace_id: string;
    objective_id: string;
    objective: string;
    prompt: string;
    created_at: string;
    updated_at: string;
    classification: CognitionTaskClassification;
    decision: BridgeToolDecision;
    debate_summary: string;
    reasoning_graph: CognitionReasoningNode[];
};

export type CognitionLearningEntry = {
    entry_id: string;
    objective_id: string;
    objective: string;
    prompt: string;
    timestamp: string;
    category: string;
    recommended_tool: string;
    winner_role: string;
    confidence: number;
    summary: string;
    notes?: string;
    provider?: string;
    judge_provider?: string;
};

export type CognitionSupervisionResult = {
    objective: string;
    prompt: string;
    objective_id: string;
    workspace_id: string;
    classification: CognitionTaskClassification;
    decision: BridgeToolDecision;
    debate: BridgeConsultResult;
    reasoning_graph: CognitionReasoningNode[];
    learning_entry: CognitionLearningEntry;
    workspace: CognitionWorkspace;
};

export type CognitionSuperviseRequest = {
    prompt: string;
    objective?: string | null;
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

export async function classifyCognition(prompt: string): Promise<CognitionTaskClassification> {
    const response = await api.post("/cognition/classify", { prompt });
    return response.data as CognitionTaskClassification;
}

export async function superviseCognition(request: CognitionSuperviseRequest): Promise<CognitionSupervisionResult> {
    const response = await api.post("/cognition/supervise", request);
    return response.data as CognitionSupervisionResult;
}

export async function listCognitionWorkspaces(): Promise<CognitionWorkspace[]> {
    const response = await api.get("/cognition/workspaces");
    return response.data as CognitionWorkspace[];
}

export async function getCognitionWorkspace(workspaceId: string): Promise<CognitionWorkspace> {
    const response = await api.get(`/cognition/workspaces/${workspaceId}`);
    return response.data as CognitionWorkspace;
}

export async function listCognitionLearning(limit = 20): Promise<CognitionLearningEntry[]> {
    const response = await api.get("/cognition/learning", {
        params: { limit }
    });
    return response.data as CognitionLearningEntry[];
}
