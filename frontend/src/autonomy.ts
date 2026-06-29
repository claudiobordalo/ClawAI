import axios from "axios";

const api = axios.create({
    baseURL: "http://127.0.0.1:8000/api"
});

export type PlanningSubtask = {
    title: string;
    status?: string;
    progress?: number;
    note?: string;
};

export type PlanningState = {
    objective_id: string;
    objective: string;
    plan_id: string;
    created_at: string;
    updated_at: string;
    status: string;
    subtasks: PlanningSubtask[];
    current_index: number;
    progress: number;
    last_run_id?: string;
    last_summary?: string;
};

export type EngineeringMemoryEntry = {
    memory_id: string;
    objective_id: string;
    objective: string;
    timestamp: string;
    outcome: string;
    summary: string;
    decisions: string[];
    errors: string[];
    solutions: string[];
    files: string[];
    git_commit?: string;
    verify_success?: boolean | null;
    notes?: string;
};

export type AutonomyQueueItem = {
    queue_id: string;
    objective_id: string;
    objective: string;
    test_command: string;
    max_iterations: number;
    max_files: number;
    enqueued_at: string;
    status: string;
    run_id?: string;
    order: number;
    summary?: string;
    error?: string;
    result_success?: boolean | null;
    git_merge_success?: boolean | null;
    git_merge_reason?: string;
};

export type AutonomyState = {
    plans: PlanningState[];
    queue: AutonomyQueueItem[];
    recent_memory: EngineeringMemoryEntry[];
};

export type AutonomyObjectiveRequest = {
    objective: string;
    test_command?: string;
    max_iterations?: number;
    max_files?: number;
};

export async function enqueueAutonomy(request: AutonomyObjectiveRequest): Promise<AutonomyQueueItem> {
    const response = await api.post("/autonomy/queue", request);
    return response.data as AutonomyQueueItem;
}

export async function getAutonomyQueue(): Promise<AutonomyQueueItem[]> {
    const response = await api.get("/autonomy/queue");
    return response.data as AutonomyQueueItem[];
}

export async function getAutonomyPlans(): Promise<PlanningState[]> {
    const response = await api.get("/autonomy/plans");
    return response.data as PlanningState[];
}

export async function getAutonomyPlan(objectiveId: string): Promise<PlanningState> {
    const response = await api.get(`/autonomy/plans/${objectiveId}`);
    return response.data as PlanningState;
}

export async function getAutonomyMemory(objective = "", limit = 20): Promise<EngineeringMemoryEntry[]> {
    const response = await api.get("/autonomy/memory", {
        params: { objective, limit }
    });
    return response.data as EngineeringMemoryEntry[];
}

export async function getAutonomyState(): Promise<AutonomyState> {
    const response = await api.get("/autonomy/state");
    return response.data as AutonomyState;
}
