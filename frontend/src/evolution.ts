import axios from "axios";

const api = axios.create({
    baseURL: "http://127.0.0.1:8000/api"
});

export type EvolutionBacklogItem = {
    backlog_id: string;
    objective_id: string;
    title: string;
    objective: string;
    description: string;
    category: string;
    priority: number;
    status: string;
    reasons: string[];
    tags: string[];
    created_at: string;
    updated_at: string;
    queue_id: string;
    run_id: string;
    attempts: number;
    last_error: string;
    result_summary: string;
    verify_success?: boolean | null;
    auto_enqueued: boolean;
    test_command: string;
    max_iterations: number;
    max_files: number;
};

export type EvolutionState = {
    enabled: boolean;
    running: boolean;
    interval_seconds: number;
    cycles_run: number;
    last_cycle_at: string;
    last_success_at: string;
    last_error: string;
    last_summary: string;
    backlog_size: number;
    pending_items: number;
    queued_items: number;
    running_items: number;
    completed_items: number;
    active_queue_size: number;
    next_cycle_at: string;
    last_queued_title: string;
    last_queued_objective_id: string;
    last_cycle_id: string;
};

export type EvolutionCycleRecord = {
    cycle_id: string;
    started_at: string;
    finished_at: string;
    status: string;
    analysis_summary: string;
    backlog_created: number;
    backlog_queued: number;
    backlog_completed: number;
    queued_title: string;
    queued_objective_id: string;
    queued_queue_id: string;
    queued_run_id: string;
    active_queue_size: number;
    signals: string[];
    errors: string[];
    meta: Record<string, unknown>;
};

export type EvolutionBacklogOverview = {
    counts: { pending: number; queued: number; running: number; completed: number };
    top_item?: EvolutionBacklogItem | null;
    items: EvolutionBacklogItem[];
};

export async function getEvolutionState(): Promise<EvolutionState> {
    const response = await api.get("/evolution/state");
    return response.data as EvolutionState;
}

export async function getEvolutionBacklog(): Promise<EvolutionBacklogOverview> {
    const response = await api.get("/evolution/backlog");
    return response.data as EvolutionBacklogOverview;
}

export async function getEvolutionHistory(limit = 20): Promise<EvolutionCycleRecord[]> {
    const response = await api.get("/evolution/history", {
        params: { limit }
    });
    return response.data as EvolutionCycleRecord[];
}

export async function runEvolutionOnce(): Promise<EvolutionCycleRecord> {
    const response = await api.post("/evolution/run-once");
    return response.data as EvolutionCycleRecord;
}

export async function startEvolution(): Promise<EvolutionState> {
    const response = await api.post("/evolution/start");
    return response.data as EvolutionState;
}

export async function stopEvolution(): Promise<EvolutionState> {
    const response = await api.post("/evolution/stop");
    return response.data as EvolutionState;
}

export async function rebuildEvolutionBacklog(): Promise<EvolutionBacklogOverview> {
    const response = await api.post("/evolution/rebuild");
    return response.data as EvolutionBacklogOverview;
}
