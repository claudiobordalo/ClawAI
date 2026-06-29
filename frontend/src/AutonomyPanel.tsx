import { useEffect, useState, type CSSProperties } from "react";
import {
    enqueueAutonomy,
    getAutonomyState,
    type AutonomyState,
    type EngineeringMemoryEntry,
    type PlanningState,
    type AutonomyQueueItem
} from "./autonomy";

type Props = {
    onBack?: () => void;
};

function formatTime(value?: string): string {
    if (!value) {
        return "-";
    }

    try {
        return new Date(value).toLocaleString();
    } catch {
        return value;
    }
}

function formatPercent(value?: number): string {
    if (typeof value !== "number" || Number.isNaN(value)) {
        return "0%";
    }

    const bounded = Math.max(0, Math.min(1, value));
    return `${Math.round(bounded * 100)}%`;
}

function shortId(value?: string): string {
    if (!value) {
        return "-";
    }

    return value.slice(0, 8);
}

function statusLabel(value?: string): string {
    if (!value) {
        return "-";
    }

    return value
        .replaceAll("_", " ")
        .split(" ")
        .filter(Boolean)
        .map(part => part.charAt(0).toUpperCase() + part.slice(1))
        .join(" ");
}

function badgeStyle(status?: string): CSSProperties {
    const normalized = (status ?? "").toLowerCase();
    const palette: Record<string, CSSProperties> = {
        queued: { background: "#5b4636", color: "#ffd59a" },
        running: { background: "#1f4d3a", color: "#bff2d0" },
        done: { background: "#234b35", color: "#c8f7d1" },
        failed: { background: "#5b2b2b", color: "#ffb6b6" },
        active: { background: "#2d3e5f", color: "#c6d9ff" },
        completed: { background: "#234b35", color: "#c8f7d1" }
    };

    return {
        display: "inline-flex",
        alignItems: "center",
        padding: "2px 8px",
        borderRadius: 999,
        fontSize: 11,
        fontWeight: 600,
        ...(palette[normalized] ?? { background: "#363636", color: "#ddd" })
    };
}

function sectionStyle(): CSSProperties {
    return {
        border: "1px solid #333",
        borderRadius: 8,
        padding: 10,
        background: "#1f1f1f"
    };
}

function sectionTitleStyle(): CSSProperties {
    return {
        fontWeight: 700,
        fontSize: 12,
        marginBottom: 8,
        color: "#ddd"
    };
}

function inputStyle(): CSSProperties {
    return {
        width: "100%",
        background: "#252526",
        color: "#ddd",
        border: "1px solid #444",
        borderRadius: 6,
        padding: 10,
        boxSizing: "border-box"
    };
}

function smallButtonStyle(active = false): CSSProperties {
    return {
        height: 30,
        padding: "0 10px",
        cursor: "pointer",
        border: "1px solid #444",
        borderRadius: 6,
        background: active ? "#3a3f4b" : "#262626",
        color: "#ddd"
    };
}

function StatCard({ label, value }: { label: string; value: string | number; }) {
    return (
        <div
            style={{
                ...sectionStyle(),
                display: "flex",
                flexDirection: "column",
                gap: 4
            }}
        >
            <div style={{ fontSize: 11, color: "#9aa0a6" }}>{label}</div>
            <div style={{ fontSize: 18, fontWeight: 700, color: "#fff" }}>{value}</div>
        </div>
    );
}

function ProgressBar({ value }: { value: number }) {
    const pct = Math.max(0, Math.min(100, Math.round(value * 100)));
    return (
        <div
            style={{
                width: "100%",
                height: 8,
                background: "#2c2c2c",
                borderRadius: 999,
                overflow: "hidden",
                marginTop: 6
            }}
        >
            <div
                style={{
                    width: `${pct}%`,
                    height: "100%",
                    background: "#4FC3F7"
                }}
            />
        </div>
    );
}

function QueueCard({ item }: { item: AutonomyQueueItem }) {
    return (
        <div
            style={{
                border: "1px solid #333",
                borderRadius: 8,
                padding: 10,
                background: "#242424"
            }}
        >
            <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                <div style={{ fontWeight: 700, color: "#fff" }}>{item.objective}</div>
                <span style={badgeStyle(item.status)}>{statusLabel(item.status)}</span>
            </div>
            <div style={{ marginTop: 6, fontSize: 11, color: "#9aa0a6" }}>
                Ordem {item.order} · {shortId(item.run_id)} · {formatTime(item.enqueued_at)}
            </div>
            <div style={{ marginTop: 6, fontSize: 11, color: "#ddd", whiteSpace: "pre-wrap" }}>
                Teste: {item.test_command}
            </div>
            {item.summary ? (
                <div style={{ marginTop: 6, fontSize: 11, whiteSpace: "pre-wrap" }}>
                    Resumo: {item.summary}
                </div>
            ) : null}
            {item.error ? (
                <div style={{ marginTop: 6, fontSize: 11, color: "#ff8a80", whiteSpace: "pre-wrap" }}>
                    Erro: {item.error}
                </div>
            ) : null}
        </div>
    );
}

function PlanCard({ plan, selected, onSelect }: { plan: PlanningState; selected: boolean; onSelect: () => void; }) {
    return (
        <button
            type="button"
            onClick={onSelect}
            style={{
                width: "100%",
                textAlign: "left",
                border: selected ? "1px solid #4FC3F7" : "1px solid #333",
                borderRadius: 8,
                padding: 10,
                background: selected ? "#233240" : "#242424",
                color: "#ddd",
                cursor: "pointer"
            }}
        >
            <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                <div style={{ fontWeight: 700, color: "#fff" }}>{plan.objective}</div>
                <span style={badgeStyle(plan.status)}>{statusLabel(plan.status)}</span>
            </div>
            <div style={{ marginTop: 6, fontSize: 11, color: "#9aa0a6" }}>
                {shortId(plan.plan_id)} · Atualizado {formatTime(plan.updated_at)}
            </div>
            <div style={{ marginTop: 6, fontSize: 11, color: "#ddd" }}>
                Progresso {formatPercent(plan.progress)}
            </div>
            <ProgressBar value={plan.progress} />
        </button>
    );
}

export default function AutonomyPanel({ onBack }: Props) {
    const [state, setState] = useState<AutonomyState | null>(null);
    const [loading, setLoading] = useState(false);
    const [refreshing, setRefreshing] = useState(false);
    const [error, setError] = useState("");

    const [selectedPlanId, setSelectedPlanId] = useState("");
    const [objective, setObjective] = useState("");
    const [testCommand, setTestCommand] = useState("uv run python -m pytest -q");
    const [maxIterations, setMaxIterations] = useState(3);
    const [maxFiles, setMaxFiles] = useState(15);
    const [submitting, setSubmitting] = useState(false);

    async function refreshState() {
        setRefreshing(true);
        try {
            const next = await getAutonomyState();
            setState(next);
            setError("");
        } catch (err) {
            console.error("Falha ao carregar o estado de autonomia.", err);
            setError("Não foi possível carregar o estado de autonomia.");
        } finally {
            setRefreshing(false);
            setLoading(false);
        }
    }

    useEffect(() => {
        let mounted = true;

        async function bootstrap() {
            setLoading(true);
            try {
                const next = await getAutonomyState();
                if (!mounted) {
                    return;
                }
                setState(next);
                setError("");
            } catch (err) {
                console.error("Falha ao carregar o estado de autonomia.", err);
                if (mounted) {
                    setError("Não foi possível carregar o estado de autonomia.");
                }
            } finally {
                if (mounted) {
                    setLoading(false);
                }
            }
        }

        void bootstrap();

        const timer = window.setInterval(() => {
            void refreshState();
        }, 2500);

        return () => {
            mounted = false;
            window.clearInterval(timer);
        };
    }, []);

    useEffect(() => {
        if (!state?.plans.length) {
            setSelectedPlanId("");
            return;
        }

        const stillExists = state.plans.some(plan => plan.objective_id === selectedPlanId);
        if (!stillExists) {
            setSelectedPlanId(state.plans[0].objective_id);
        }
    }, [state, selectedPlanId]);

    const selectedPlan = state?.plans.find(plan => plan.objective_id === selectedPlanId) ?? state?.plans[0] ?? null;
    const queue = state?.queue ?? [];
    const plans = state?.plans ?? [];
    const memory = state?.recent_memory ?? [];

    const activeQueue = queue.filter(item => item.status === "queued" || item.status === "running");
    const completedQueue = queue.filter(item => item.status === "done" || item.status === "failed");
    const successMemory = memory.filter(entry => entry.outcome === "success").length;
    const failedMemory = memory.filter(entry => entry.outcome === "failed").length;

    async function submitObjective() {
        const normalizedObjective = objective.trim();
        if (!normalizedObjective || submitting) {
            return;
        }

        setSubmitting(true);
        try {
            await enqueueAutonomy({
                objective: normalizedObjective,
                test_command: testCommand.trim() || "uv run python -m pytest -q",
                max_iterations: maxIterations,
                max_files: maxFiles
            });
            setObjective("");
            await refreshState();
        } catch (err) {
            console.error("Falha ao enfileirar objetivo.", err);
            setError("Não foi possível enfileirar o objetivo.");
        } finally {
            setSubmitting(false);
        }
    }

    return (
        <div
            style={{
                width: 380,
                display: "flex",
                flexDirection: "column",
                background: "#181818",
                borderLeft: "1px solid #333"
            }}
        >
            <div
                style={{
                    padding: "12px",
                    borderBottom: "1px solid #333",
                    color: "#ddd",
                    fontWeight: "bold",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: 8
                }}
            >
                <span>Autonomia</span>
                <div style={{ display: "flex", gap: 8 }}>
                    <button type="button" onClick={onBack} style={smallButtonStyle()}>
                        Voltar
                    </button>
                    <button
                        type="button"
                        onClick={() => void refreshState()}
                        disabled={loading || refreshing}
                        style={smallButtonStyle()}
                    >
                        {refreshing ? "Atualizando..." : "Atualizar"}
                    </button>
                </div>
            </div>

            <div
                style={{
                    flex: 1,
                    overflow: "auto",
                    padding: 12,
                    display: "grid",
                    gap: 10
                }}
            >
                {error ? (
                    <div
                        style={{
                            fontSize: 12,
                            color: "#ff8a80",
                            whiteSpace: "pre-wrap",
                            border: "1px solid #5b2b2b",
                            borderRadius: 8,
                            padding: 10,
                            background: "#2a1c1c"
                        }}
                    >
                        {error}
                    </div>
                ) : null}

                <div
                    style={{
                        display: "grid",
                        gridTemplateColumns: "1fr 1fr",
                        gap: 8
                    }}
                >
                    <StatCard label="Planos" value={plans.length} />
                    <StatCard label="Fila ativa" value={activeQueue.length} />
                    <StatCard label="Memórias" value={memory.length} />
                    <StatCard label="Sucesso / Falha" value={`${successMemory}/${failedMemory}`} />
                </div>

                <section style={sectionStyle()}>
                    <div style={sectionTitleStyle()}>Novo objetivo</div>
                    <div style={{ display: "grid", gap: 8 }}>
                        <textarea
                            rows={3}
                            value={objective}
                            placeholder="Descreva o próximo objetivo da fila..."
                            onChange={e => setObjective(e.target.value)}
                            style={{
                                ...inputStyle(),
                                resize: "none"
                            }}
                        />
                        <input
                            value={testCommand}
                            onChange={e => setTestCommand(e.target.value)}
                            placeholder="uv run python -m pytest -q"
                            style={inputStyle()}
                        />
                        <div
                            style={{
                                display: "grid",
                                gridTemplateColumns: "1fr 1fr",
                                gap: 8
                            }}
                        >
                            <input
                                type="number"
                                min={1}
                                max={5}
                                value={maxIterations}
                                onChange={e => setMaxIterations(Number(e.target.value) || 1)}
                                style={inputStyle()}
                                title="Máximo de iterações"
                            />
                            <input
                                type="number"
                                min={1}
                                max={20}
                                value={maxFiles}
                                onChange={e => setMaxFiles(Number(e.target.value) || 1)}
                                style={inputStyle()}
                                title="Máximo de arquivos"
                            />
                        </div>
                        <button
                            type="button"
                            onClick={() => void submitObjective()}
                            disabled={submitting || !objective.trim()}
                            style={{
                                height: 36,
                                borderRadius: 6,
                                border: "1px solid #444",
                                background: submitting ? "#3a3a3a" : "#2d6cdf",
                                color: "#fff",
                                cursor: submitting || !objective.trim() ? "not-allowed" : "pointer"
                            }}
                        >
                            {submitting ? "Enfileirando..." : "Adicionar à fila"}
                        </button>
                    </div>
                </section>

                <section style={sectionStyle()}>
                    <div style={sectionTitleStyle()}>Plano atual</div>
                    {selectedPlan ? (
                        <div style={{ display: "grid", gap: 8 }}>
                            <div style={{ fontSize: 12, color: "#ddd" }}>
                                {selectedPlan.objective}
                            </div>
                            <div style={{ fontSize: 11, color: "#9aa0a6" }}>
                                Atualizado {formatTime(selectedPlan.updated_at)} · ID {shortId(selectedPlan.plan_id)} · Run {shortId(selectedPlan.last_run_id)}
                            </div>
                            <div style={{ fontSize: 11, color: "#ddd" }}>
                                Progresso {formatPercent(selectedPlan.progress)} · índice {selectedPlan.current_index}/{selectedPlan.subtasks.length}
                            </div>
                            <ProgressBar value={selectedPlan.progress} />
                            <div style={{ display: "grid", gap: 6, marginTop: 4 }}>
                                {selectedPlan.subtasks.map((subtask, index) => (
                                    <div
                                        key={`${selectedPlan.objective_id}-${index}`}
                                        style={{
                                            border: "1px solid #333",
                                            borderRadius: 6,
                                            padding: 8,
                                            background: "#242424"
                                        }}
                                    >
                                        <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                                            <div style={{ fontSize: 12, color: "#fff" }}>{subtask.title}</div>
                                            <span style={badgeStyle(subtask.status)}>{statusLabel(subtask.status)}</span>
                                        </div>
                                        <div style={{ marginTop: 4, fontSize: 11, color: "#9aa0a6" }}>
                                            Progresso {formatPercent(subtask.progress ?? 0)}
                                        </div>
                                        {subtask.note ? (
                                            <div style={{ marginTop: 4, fontSize: 11, whiteSpace: "pre-wrap" }}>
                                                {subtask.note}
                                            </div>
                                        ) : null}
                                    </div>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div style={{ fontSize: 12, color: "#9aa0a6" }}>
                            Nenhum plano disponível.
                        </div>
                    )}
                </section>

                <section style={sectionStyle()}>
                    <div style={sectionTitleStyle()}>Planos</div>
                    {plans.length ? (
                        <div style={{ display: "grid", gap: 8 }}>
                            {plans.map(plan => (
                                <PlanCard
                                    key={plan.objective_id}
                                    plan={plan}
                                    selected={plan.objective_id === selectedPlanId}
                                    onSelect={() => setSelectedPlanId(plan.objective_id)}
                                />
                            ))}
                        </div>
                    ) : (
                        <div style={{ fontSize: 12, color: "#9aa0a6" }}>
                            Ainda não há planos persistidos.
                        </div>
                    )}
                </section>

                <section style={sectionStyle()}>
                    <div style={sectionTitleStyle()}>Fila</div>
                    {queue.length ? (
                        <div style={{ display: "grid", gap: 8 }}>
                            {queue.map(item => (
                                <QueueCard key={item.queue_id} item={item} />
                            ))}
                        </div>
                    ) : (
                        <div style={{ fontSize: 12, color: "#9aa0a6" }}>
                            A fila está vazia.
                        </div>
                    )}
                </section>

                <section style={sectionStyle()}>
                    <div style={sectionTitleStyle()}>Memória de engenharia</div>
                    {memory.length ? (
                        <div style={{ display: "grid", gap: 8 }}>
                            {memory.map((entry: EngineeringMemoryEntry) => (
                                <details
                                    key={entry.memory_id}
                                    style={{
                                        border: "1px solid #333",
                                        borderRadius: 8,
                                        padding: 8,
                                        background: "#242424"
                                    }}
                                >
                                    <summary style={{ cursor: "pointer" }}>
                                        {statusLabel(entry.outcome)} · {entry.objective}
                                    </summary>
                                    <div style={{ marginTop: 8, fontSize: 11, color: "#ddd", display: "grid", gap: 6 }}>
                                        <div>Quando: {formatTime(entry.timestamp)}</div>
                                        <div>Resumo: {entry.summary}</div>
                                        {entry.git_commit ? (
                                            <div>Commit: {shortId(entry.git_commit)}</div>
                                        ) : null}
                                        {entry.verify_success !== undefined && entry.verify_success !== null ? (
                                            <div>Verify: {entry.verify_success ? "PASS" : "FAIL"}</div>
                                        ) : null}
                                        {entry.decisions.length ? (
                                            <div style={{ whiteSpace: "pre-wrap" }}>
                                                Decisões: {entry.decisions.join(" · ")}
                                            </div>
                                        ) : null}
                                        {entry.solutions.length ? (
                                            <div style={{ whiteSpace: "pre-wrap" }}>
                                                Soluções: {entry.solutions.join(" · ")}
                                            </div>
                                        ) : null}
                                        {entry.errors.length ? (
                                            <div style={{ whiteSpace: "pre-wrap", color: "#ff8a80" }}>
                                                Erros: {entry.errors.join(" · ")}
                                            </div>
                                        ) : null}
                                        {entry.files.length ? (
                                            <div style={{ whiteSpace: "pre-wrap" }}>
                                                Arquivos: {entry.files.join(", ")}
                                            </div>
                                        ) : null}
                                        {entry.notes ? (
                                            <div style={{ whiteSpace: "pre-wrap" }}>
                                                Notas: {entry.notes}
                                            </div>
                                        ) : null}
                                    </div>
                                </details>
                            ))}
                        </div>
                    ) : (
                        <div style={{ fontSize: 12, color: "#9aa0a6" }}>
                            Nenhuma memória registrada ainda.
                        </div>
                    )}
                </section>

                <section style={sectionStyle()}>
                    <div style={sectionTitleStyle()}>Histórico</div>
                    <div style={{ fontSize: 12, color: "#9aa0a6" }}>
                        Planos concluídos: {completedQueue.length}
                    </div>
                    <div style={{ marginTop: 8, display: "grid", gap: 6 }}>
                        {queue
                            .filter(item => item.status === "done" || item.status === "failed")
                            .slice(0, 8)
                            .map(item => (
                                <div
                                    key={`history-${item.queue_id}`}
                                    style={{
                                        border: "1px solid #333",
                                        borderRadius: 6,
                                        padding: 8,
                                        background: "#242424"
                                    }}
                                >
                                    <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                                        <div style={{ fontSize: 12, color: "#fff" }}>{item.objective}</div>
                                        <span style={badgeStyle(item.status)}>{statusLabel(item.status)}</span>
                                    </div>
                                    <div style={{ marginTop: 4, fontSize: 11, color: "#9aa0a6" }}>
                                        {formatTime(item.enqueued_at)} · {item.summary || item.error || "Sem resumo"}
                                    </div>
                                </div>
                            ))}
                    </div>
                </section>
            </div>
        </div>
    );
}
