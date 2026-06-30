import { useEffect, useMemo, useRef, useState } from "react";
import type { CSSProperties } from "react";

import {
    classifyCognition,
    consultBridge,
    getBridgeProviders,
    listCognitionLearning,
    listCognitionWorkspaces,
    recommendBridgeTool,
    superviseCognition,
    type BridgeConsultResult,
    type BridgeProvidersResponse,
    type BridgeToolDecision,
    type CognitionLearningEntry,
    type CognitionReasoningNode,
    type CognitionTaskClassification,
    type CognitionWorkspace,
} from "./bridge";
import {
    enqueueAutonomy,
    getAutonomyState,
    type AutonomyState,
} from "./autonomy";
import {
    getAutoImplementStatus,
    runAutoImplement,
    runVerify,
    sendChat,
    startAutoImplement,
    stopAutoImplement,
    type AutoImplementReport,
    type AutoImplementSession,
    type ChatReply,
    type VerifyResponse,
} from "./api";
import {
    getEvolutionBacklog,
    getEvolutionHistory,
    getEvolutionState,
    rebuildEvolutionBacklog,
    runEvolutionOnce,
    startEvolution,
    stopEvolution,
    type EvolutionBacklogOverview,
    type EvolutionCycleRecord,
    type EvolutionState,
} from "./evolution";

type SectionKey = "chat" | "workspace" | "evolution" | "memory" | "control" | "integrations";

type Message = {
    id: number;
    role: "user" | "assistant";
    text: string;
    reply?: ChatReply;
};

const SECTIONS: Array<{ key: SectionKey; label: string; hint: string }> = [
    { key: "chat", label: "Chat", hint: "Converse e peça análise" },
    { key: "workspace", label: "Workspace", hint: "Projetos e planos" },
    { key: "evolution", label: "Evolution", hint: "Backlog e ciclos" },
    { key: "memory", label: "Memory", hint: "Aprendizados" },
    { key: "control", label: "Control", hint: "Autonomia e verify" },
    { key: "integrations", label: "Integrations", hint: "Providers e ferramentas" },
];

function fmtMs(value?: number | null): string {
    if (typeof value !== "number" || Number.isNaN(value)) {
        return "-";
    }
    return value < 1000 ? `${Math.round(value)} ms` : `${(value / 1000).toFixed(2)} s`;
}

function fmtDate(value?: string | null): string {
    if (!value) {
        return "-";
    }
    try {
        return new Date(value).toLocaleString();
    } catch {
        return value;
    }
}

function fmtPct(value?: number | null): string {
    return `${Math.round(Math.max(0, Math.min(1, value ?? 0)) * 100)}%`;
}

function fmtStatus(value?: string | null): string {
    return (value ?? "-").replaceAll("_", " ");
}

function short(value?: string | null): string {
    return value ? value.slice(0, 8) : "-";
}

function styles() {
    return {
        shell: {
            width: 440,
            minWidth: 440,
            height: "100%",
            display: "flex",
            flexDirection: "column",
            background: "#171717",
            borderLeft: "1px solid #2d2d2d",
            color: "#ddd",
        } as CSSProperties,
        header: {
            padding: 12,
            borderBottom: "1px solid #2d2d2d",
            display: "grid",
            gap: 10,
        } as CSSProperties,
        titleRow: {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            gap: 8,
        } as CSSProperties,
        title: { fontWeight: 800, fontSize: 16, lineHeight: 1.2 } as CSSProperties,
        subtitle: { marginTop: 2, fontSize: 11, color: "#9ca3af" } as CSSProperties,
        infoCard: {
            border: "1px solid #2c2c2c",
            borderRadius: 12,
            padding: 10,
            background: "#1f1f1f",
        } as CSSProperties,
        pill: {
            display: "inline-flex",
            alignItems: "center",
            padding: "2px 8px",
            borderRadius: 999,
            fontSize: 11,
            fontWeight: 700,
            background: "#343434",
            color: "#ddd",
            whiteSpace: "nowrap",
        } as CSSProperties,
        sectionBar: {
            display: "grid",
            gap: 8,
        } as CSSProperties,
        sectionTabs: {
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: 8,
        } as CSSProperties,
        tabButton: (active: boolean): CSSProperties => ({
            height: 34,
            padding: "0 10px",
            borderRadius: 10,
            border: active ? "1px solid #64748b" : "1px solid #2f2f2f",
            background: active ? "#364152" : "#242424",
            color: active ? "#fff" : "#ddd",
            cursor: "pointer",
            textAlign: "left",
        }),
        tabLabel: { display: "block", fontWeight: 700, fontSize: 12 } as CSSProperties,
        tabHint: { display: "block", fontSize: 10, marginTop: 1, color: "#9ca3af" } as CSSProperties,
        content: {
            flex: 1,
            overflow: "auto",
            padding: 12,
            display: "grid",
            gap: 10,
        } as CSSProperties,
        card: {
            border: "1px solid #2d2d2d",
            borderRadius: 12,
            padding: 12,
            background: "#1f1f1f",
        } as CSSProperties,
        cardTitle: { fontSize: 13, fontWeight: 800, color: "#fff" } as CSSProperties,
        small: { fontSize: 11, color: "#9ca3af" } as CSSProperties,
        input: {
            width: "100%",
            boxSizing: "border-box",
            borderRadius: 10,
            border: "1px solid #3a3a3a",
            background: "#242424",
            color: "#ddd",
            padding: 10,
            outline: "none",
        } as CSSProperties,
        textarea: {
            width: "100%",
            minHeight: 88,
            resize: "vertical",
            boxSizing: "border-box",
            borderRadius: 10,
            border: "1px solid #3a3a3a",
            background: "#242424",
            color: "#ddd",
            padding: 10,
            outline: "none",
        } as CSSProperties,
        button: (active = false, danger = false): CSSProperties => ({
            height: 34,
            padding: "0 12px",
            borderRadius: 10,
            border: danger ? "1px solid #7f1d1d" : active ? "1px solid #64748b" : "1px solid #3a3a3a",
            background: danger ? "#3a1b1b" : active ? "#364152" : "#242424",
            color: danger ? "#ffb4b4" : active ? "#fff" : "#ddd",
            cursor: "pointer",
            whiteSpace: "nowrap",
        }),
        row: { display: "flex", gap: 8, flexWrap: "wrap" } as CSSProperties,
        grid2: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 } as CSSProperties,
        grid3: { display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 } as CSSProperties,
        grid4: { display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 } as CSSProperties,
        mutedNote: {
            borderLeft: "3px solid #60a5fa",
            background: "#162131",
            padding: 10,
            borderRadius: 10,
            fontSize: 11,
            color: "#dbeafe",
            lineHeight: 1.45,
        } as CSSProperties,
        message: (role: "user" | "assistant"): CSSProperties => ({
            border: "1px solid #2d2d2d",
            borderRadius: 12,
            padding: 10,
            background: role === "assistant" ? "#1f1f1f" : "#18232f",
        }),
        messageRole: (role: "user" | "assistant"): CSSProperties => ({
            fontSize: 11,
            color: role === "assistant" ? "#67e8f9" : "#86efac",
            marginBottom: 6,
            fontWeight: 700,
        }),
        listItem: (selected = false): CSSProperties => ({
            textAlign: "left",
            border: selected ? "1px solid #60a5fa" : "1px solid #2d2d2d",
            borderRadius: 10,
            padding: 10,
            background: selected ? "#183044" : "#1f1f1f",
            color: "#ddd",
            cursor: "pointer",
        }),
    };
}

function StatusPill({ value }: { value?: string | null }) {
    const status = fmtStatus(value);
    const lower = status.toLowerCase();
    const tone: CSSProperties = lower.includes("running") || lower.includes("active")
        ? { background: "#1f4d3a", color: "#bff2d0" }
        : lower.includes("done") || lower.includes("success") || lower.includes("completed")
            ? { background: "#234b35", color: "#c8f7d1" }
            : lower.includes("failed") || lower.includes("error")
                ? { background: "#5b2b2b", color: "#ffb6b6" }
                : lower.includes("queued") || lower.includes("pending")
                    ? { background: "#5b4636", color: "#ffd59a" }
                    : { background: "#343434", color: "#ddd" };

    return <span style={{ ...styles().pill, ...tone }}>{status}</span>;
}

function Metric({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
    const s = styles();
    return (
        <div style={s.card}>
            <div style={s.small}>{label}</div>
            <div style={{ fontSize: 22, fontWeight: 800, color: "#fff", marginTop: 4 }}>{value}</div>
            {hint ? <div style={{ ...s.small, marginTop: 4 }}>{hint}</div> : null}
        </div>
    );
}

function ProgressBar({ value }: { value: number }) {
    const pct = Math.max(0, Math.min(100, Math.round(value * 100)));
    return (
        <div style={{ width: "100%", height: 8, background: "#2b2b2b", borderRadius: 999, overflow: "hidden" }}>
            <div style={{ width: `${pct}%`, height: "100%", background: "#60a5fa" }} />
        </div>
    );
}

function GraphPreview({ nodes, rootId = "root", depth = 0 }: { nodes: CognitionReasoningNode[]; rootId?: string; depth?: number }) {
    const node = nodes.find(item => item.node_id === rootId);
    if (!node) {
        return null;
    }

    const s = styles();
    return (
        <div style={{ marginLeft: depth * 12, paddingLeft: depth ? 10 : 0, borderLeft: depth ? "1px solid #303030" : undefined }}>
            <div style={{ ...s.infoCard, marginBottom: 8 }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                    <div style={{ color: "#fff", fontWeight: 700 }}>{node.label}</div>
                    <StatusPill value={node.kind} />
                </div>
                <div style={{ marginTop: 4, ...s.small }}>Score {node.score.toFixed(2)}</div>
                {node.details ? <div style={{ marginTop: 6, fontSize: 11, whiteSpace: "pre-wrap", lineHeight: 1.45 }}>{node.details}</div> : null}
            </div>
            {node.children.map(child => <GraphPreview key={child} nodes={nodes} rootId={child} depth={depth + 1} />)}
        </div>
    );
}

function QuickAction({ label, onClick }: { label: string; onClick: () => void }) {
    const s = styles();
    return <button type="button" onClick={onClick} style={s.button()}>{label}</button>;
}

export default function OperationsHub() {
    const s = styles();
    const [section, setSection] = useState<SectionKey>("chat");

    const [messages, setMessages] = useState<Message[]>([
        { id: 1, role: "assistant", text: "ClawAI pronto para operar. Escolha uma tarefa ou faça uma pergunta." },
    ]);
    const [chatPrompt, setChatPrompt] = useState("");
    const [chatSending, setChatSending] = useState(false);

    const [objective, setObjective] = useState("");
    const [testCommand, setTestCommand] = useState("uv run python -m pytest -q");
    const [maxIterations, setMaxIterations] = useState(3);
    const [maxFiles, setMaxFiles] = useState(15);
    const [taskBusy, setTaskBusy] = useState(false);
    const [controlError, setControlError] = useState("");

    const [autonomyState, setAutonomyState] = useState<AutonomyState | null>(null);
    const [bridgeProviders, setBridgeProviders] = useState<BridgeProvidersResponse | null>(null);
    const [cognitionWorkspaces, setCognitionWorkspaces] = useState<CognitionWorkspace[]>([]);
    const [cognitionLearning, setCognitionLearning] = useState<CognitionLearningEntry[]>([]);
    const [selectedWorkspaceId, setSelectedWorkspaceId] = useState("");
    const [selectedLearningId, setSelectedLearningId] = useState("");

    const [evolutionState, setEvolutionState] = useState<EvolutionState | null>(null);
    const [evolutionBacklog, setEvolutionBacklog] = useState<EvolutionBacklogOverview | null>(null);
    const [evolutionHistory, setEvolutionHistory] = useState<EvolutionCycleRecord[]>([]);

    const [autoSession, setAutoSession] = useState<AutoImplementSession | null>(null);
    const [autoReport, setAutoReport] = useState<AutoImplementReport | null>(null);
    const [verifyResult, setVerifyResult] = useState<VerifyResponse | null>(null);

    const nextId = useRef(2);
    const pollingLock = useRef(false);

    async function refreshAll() {
        try {
            const [autonomy, providers, workspaces, learning, evoState, evoBacklog, evoHistory] = await Promise.all([
                getAutonomyState(),
                getBridgeProviders(),
                listCognitionWorkspaces(),
                listCognitionLearning(40),
                getEvolutionState(),
                getEvolutionBacklog(),
                getEvolutionHistory(12),
            ]);

            setAutonomyState(autonomy);
            setBridgeProviders(providers);
            setCognitionWorkspaces(workspaces);
            setCognitionLearning(learning);
            setEvolutionState(evoState);
            setEvolutionBacklog(evoBacklog);
            setEvolutionHistory(evoHistory);
        } catch (error) {
            console.error("Falha ao atualizar a interface.", error);
        }
    }

    useEffect(() => {
        void refreshAll();
    }, []);

    useEffect(() => {
        const timer = window.setInterval(() => {
            void refreshAll();
            if (autoSession?.run_id) {
                void refreshAutoSession(autoSession.run_id);
            }
        }, 3000);
        return () => window.clearInterval(timer);
    }, [autoSession?.run_id]);

    useEffect(() => {
        if (!cognitionWorkspaces.length) {
            setSelectedWorkspaceId("");
            return;
        }
        if (!cognitionWorkspaces.some(ws => ws.workspace_id === selectedWorkspaceId)) {
            setSelectedWorkspaceId(cognitionWorkspaces[0].workspace_id);
        }
    }, [cognitionWorkspaces, selectedWorkspaceId]);

    useEffect(() => {
        if (!cognitionLearning.length) {
            setSelectedLearningId("");
            return;
        }
        if (!cognitionLearning.some(item => item.entry_id === selectedLearningId)) {
            setSelectedLearningId(cognitionLearning[0].entry_id);
        }
    }, [cognitionLearning, selectedLearningId]);

    const selectedWorkspace = useMemo(
        () => cognitionWorkspaces.find(ws => ws.workspace_id === selectedWorkspaceId) ?? cognitionWorkspaces[0] ?? null,
        [cognitionWorkspaces, selectedWorkspaceId],
    );

    const selectedLearning = useMemo(
        () => cognitionLearning.find(item => item.entry_id === selectedLearningId) ?? cognitionLearning[0] ?? null,
        [cognitionLearning, selectedLearningId],
    );

    const queue = autonomyState?.queue ?? [];
    const plans = autonomyState?.plans ?? [];
    const memory = autonomyState?.recent_memory ?? [];
    const activeQueue = queue.filter(item => item.status === "queued" || item.status === "running");
    const latestPlan = plans[0] ?? null;
    const topBacklog = evolutionBacklog?.top_item ?? evolutionBacklog?.items?.[0] ?? null;
    const activeEvolution = evolutionState?.enabled ?? false;
    const graphNodes = selectedWorkspace?.reasoning_graph ?? [];

    async function sendChatMessage() {
        const text = chatPrompt.trim();
        if (!text || chatSending) {
            return;
        }

        setChatSending(true);
        setChatPrompt("");
        const userId = nextId.current++;
        const assistantId = nextId.current++;
        setMessages(prev => [...prev, { id: userId, role: "user", text }, { id: assistantId, role: "assistant", text: "Pensando..." }]);

        try {
            const reply = await sendChat(text);
            setMessages(prev => prev.map(message => message.id === assistantId ? { ...message, text: reply.answer, reply } : message));
        } catch (error) {
            console.error(error);
            setMessages(prev => prev.map(message => message.id === assistantId ? { ...message, text: "Não consegui responder agora." } : message));
        } finally {
            setChatSending(false);
        }
    }

    async function queueObjective() {
        const text = objective.trim();
        if (!text) {
            return;
        }

        setTaskBusy(true);
        setControlError("");
        try {
            await enqueueAutonomy({
                objective: text,
                test_command: testCommand.trim() || "uv run python -m pytest -q",
                max_iterations: maxIterations,
                max_files: maxFiles,
            });
            setSection("control");
            await refreshAll();
        } catch (error) {
            setControlError(error instanceof Error ? error.message : "Falha ao enfileirar objetivo.");
        } finally {
            setTaskBusy(false);
        }
    }

    async function startAutopilot() {
        const text = objective.trim();
        if (!text) {
            return;
        }

        setTaskBusy(true);
        setControlError("");
        try {
            const session = await startAutoImplement(
                text,
                testCommand.trim() || "uv run python -m pytest -q",
                maxIterations,
                maxFiles,
            );
            setAutoSession(session);
            setSection("control");
            void refreshAutoSession(session.run_id);
        } catch (error) {
            setControlError(error instanceof Error ? error.message : "Falha ao iniciar a autonomia direta.");
        } finally {
            setTaskBusy(false);
        }
    }

    async function refreshAutoSession(runId: string) {
        if (pollingLock.current) {
            return;
        }

        pollingLock.current = true;
        try {
            const latest = await getAutoImplementStatus(runId);
            setAutoSession(latest);
            if (["success", "failed", "cancelled", "cancel_requested"].includes(latest.status)) {
                setAutoReport(latest.result ?? null);
            }
        } catch (error) {
            console.error(error);
        } finally {
            pollingLock.current = false;
        }
    }

    async function cancelAutopilot() {
        if (!autoSession) {
            return;
        }

        setTaskBusy(true);
        try {
            const latest = await stopAutoImplement(autoSession.run_id);
            setAutoSession(latest);
        } catch (error) {
            setControlError(error instanceof Error ? error.message : "Falha ao cancelar a autonomia.");
        } finally {
            setTaskBusy(false);
        }
    }

    async function runVerifyProject() {
        setTaskBusy(true);
        setControlError("");
        try {
            const result = await runVerify();
            setVerifyResult(result);
            setSection("control");
        } catch (error) {
            setVerifyResult({ success: false, return_code: -1, stdout: "", stderr: String(error) });
        } finally {
            setTaskBusy(false);
        }
    }

    async function runEvolutionAction(action: "start" | "stop" | "once" | "rebuild") {
        setTaskBusy(true);
        setControlError("");
        try {
            if (action === "start") {
                await startEvolution();
            } else if (action === "stop") {
                await stopEvolution();
            } else if (action === "once") {
                await runEvolutionOnce();
            } else {
                await rebuildEvolutionBacklog();
            }
            await refreshAll();
            setSection("evolution");
        } catch (error) {
            setControlError(error instanceof Error ? error.message : "Falha ao executar o ciclo de evolução.");
        } finally {
            setTaskBusy(false);
        }
    }

    async function runQuickClassify() {
        const text = objective.trim();
        if (!text) {
            return;
        }
        setTaskBusy(true);
        try {
            await classifyCognition(text);
            setSection("control");
        } catch (error) {
            setControlError(error instanceof Error ? error.message : "Falha ao classificar o objetivo.");
        } finally {
            setTaskBusy(false);
        }
    }

    async function runQuickDebate() {
        const text = objective.trim();
        if (!text) {
            return;
        }
        setTaskBusy(true);
        try {
            await consultBridge({ prompt: text, system_prompt: text });
            setSection("workspace");
        } catch (error) {
            setControlError(error instanceof Error ? error.message : "Falha ao executar o debate.");
        } finally {
            setTaskBusy(false);
        }
    }

    async function runQuickSupervision() {
        const text = objective.trim();
        if (!text) {
            return;
        }
        setTaskBusy(true);
        try {
            const result = await superviseCognition({ prompt: text, objective: text });
            setSelectedWorkspaceId(result.workspace.workspace_id);
            setSelectedLearningId(result.learning_entry.entry_id);
            setSection("workspace");
            await refreshAll();
        } catch (error) {
            setControlError(error instanceof Error ? error.message : "Falha ao supervisionar o objetivo.");
        } finally {
            setTaskBusy(false);
        }
    }

    async function runQuickToolChoice() {
        const text = objective.trim();
        if (!text) {
            return;
        }
        setTaskBusy(true);
        try {
            await recommendBridgeTool({ prompt: text, system_prompt: text });
            setSection("integrations");
        } catch (error) {
            setControlError(error instanceof Error ? error.message : "Falha ao escolher ferramenta.");
        } finally {
            setTaskBusy(false);
        }
    }

    const filteredLearning = cognitionLearning;
    const recentHistory = evolutionHistory.slice(0, 5);
    const recentWorkspaces = cognitionWorkspaces.slice(0, 6);

    return (
        <aside style={s.shell}>
            <div style={s.header}>
                <div style={s.titleRow}>
                    <div>
                        <div style={s.title}>ClawAI Studio</div>
                        <div style={s.subtitle}>Chat, workspace, evolução, memória e integrações em um só lugar</div>
                    </div>
                    <StatusPill value={autoSession?.status ?? (autoSession ? "running" : activeEvolution ? "running" : "pending")} />
                </div>

                <div style={s.infoCard}>
                    <div style={{ fontSize: 11, fontWeight: 800, color: "#fff" }}>Workspace atual</div>
                    <div style={{ marginTop: 4, ...s.small, lineHeight: 1.45 }}>
                        O explorador está conectado ao repositório montado pelo backend. Para trabalhar em outro projeto, o backend precisa ser iniciado nesse diretório ou ganhar suporte explícito a múltiplos workspaces.
                    </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                    <div style={s.infoCard}>
                        <div style={s.small}>Objetivos</div>
                        <div style={{ fontSize: 18, fontWeight: 800, color: "#fff", marginTop: 4 }}>{queue.length}</div>
                        <div style={s.small}>{activeQueue.length} ativos</div>
                    </div>
                    <div style={s.infoCard}>
                        <div style={s.small}>Evolution</div>
                        <div style={{ fontSize: 18, fontWeight: 800, color: "#fff", marginTop: 4 }}>{evolutionState?.backlog_size ?? 0}</div>
                        <div style={s.small}>itens no backlog</div>
                    </div>
                </div>

                <div style={s.sectionTabs}>
                    {SECTIONS.map(item => (
                        <button key={item.key} type="button" onClick={() => setSection(item.key)} style={s.tabButton(section === item.key)}>
                            <span style={s.tabLabel}>{item.label}</span>
                            <span style={s.tabHint}>{item.hint}</span>
                        </button>
                    ))}
                </div>
            </div>

            <div style={s.content}>
                {section === "chat" ? (
                    <>
                        <div style={s.card}>
                            <div style={s.cardTitle}>Chat principal</div>
                            <div style={{ ...s.small, marginTop: 4, lineHeight: 1.45 }}>
                                Aqui o chat fica sempre visível e não depende de atalhos escondidos. Perguntas longas, instruções de implementação e análise de código passam por aqui.
                            </div>
                        </div>

                        <div style={s.card}>
                            <div style={s.row}>
                                <QuickAction label="Analisar projeto" onClick={() => setChatPrompt("Analise o estado atual do projeto e diga qual é o próximo passo mais importante.")} />
                                <QuickAction label="Gerar backlog" onClick={() => setChatPrompt("Gere um backlog técnico priorizado para aumentar a autonomia do ClawAI.")} />
                                <QuickAction label="Corrigir UI" onClick={() => setChatPrompt("Corrija a interface para ficar mais intuitiva e consistente.")} />
                            </div>
                            <div style={{ marginTop: 10 }}>
                                <textarea
                                    value={chatPrompt}
                                    onChange={e => setChatPrompt(e.target.value)}
                                    placeholder="Pergunte ao ClawAI..."
                                    style={s.textarea}
                                />
                            </div>
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginTop: 8 }}>
                                <button type="button" onClick={() => void sendChatMessage()} disabled={chatSending || !chatPrompt.trim()} style={s.button(true)}>
                                    {chatSending ? "Enviando..." : "Enviar"}
                                </button>
                                <button type="button" onClick={() => setSection("control")} style={s.button()}>
                                    Ir para controle
                                </button>
                            </div>
                        </div>

                        <div style={{ display: "grid", gap: 8 }}>
                            {messages.map(message => (
                                <div key={message.id} style={s.message(message.role)}>
                                    <div style={s.messageRole(message.role)}>{message.role === "assistant" ? "ClawAI" : "Você"}</div>
                                    <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.5, color: "#ddd" }}>{message.text}</div>
                                    {message.role === "assistant" && message.reply?.timings ? (
                                        <div style={{ marginTop: 8, ...s.small, lineHeight: 1.5 }}>
                                            <div>Provider: {message.reply.provider ?? "-"} · Modelo: {message.reply.model ?? "-"}</div>
                                            <div>Memória: {String(message.reply.used_memory)} · Web: {String(message.reply.requires_web)}</div>
                                            <div>Total: {fmtMs(message.reply.timings.total_ms)}</div>
                                        </div>
                                    ) : null}
                                </div>
                            ))}
                        </div>
                    </>
                ) : null}

                {section === "workspace" ? (
                    <>
                        <div style={s.card}>
                            <div style={s.cardTitle}>Workspace cognitivo</div>
                            <div style={{ ...s.small, marginTop: 4, lineHeight: 1.45 }}>
                                Esta seção mostra o espaço de raciocínio do ClawAI: workspaces, classificação, decisão e grafo de raciocínio. O sistema de arquivos do projeto continua no explorador à esquerda.
                            </div>
                        </div>

                        <div style={s.card}>
                            <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center" }}>
                                <div style={s.cardTitle}>Workspaces recentes</div>
                                <Pill value={selectedWorkspace?.classification.category ?? "-"} />
                            </div>
                            <div style={{ display: "grid", gap: 8, marginTop: 10 }}>
                                {recentWorkspaces.length ? recentWorkspaces.map(ws => (
                                    <button
                                        key={ws.workspace_id}
                                        type="button"
                                        onClick={() => setSelectedWorkspaceId(ws.workspace_id)}
                                        style={s.listItem(selectedWorkspaceId === ws.workspace_id)}
                                    >
                                        <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                                            <div style={{ fontWeight: 700, color: "#fff" }}>{ws.objective}</div>
                                            <Pill value={ws.classification.category} />
                                        </div>
                                        <div style={{ marginTop: 4, ...s.small }}>Atualizado {fmtDate(ws.updated_at)}</div>
                                    </button>
                                )) : <div style={s.small}>Nenhum workspace encontrado ainda.</div>}
                            </div>
                        </div>

                        {selectedWorkspace ? (
                            <div style={s.card}>
                                <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center" }}>
                                    <div style={s.cardTitle}>{selectedWorkspace.objective}</div>
                                    <Pill value={selectedWorkspace.decision.recommended_tool} />
                                </div>
                                <div style={{ marginTop: 6, ...s.small }}>Workspace {short(selectedWorkspace.workspace_id)} · {fmtDate(selectedWorkspace.updated_at)}</div>
                                <div style={{ marginTop: 10, display: "grid", gap: 8 }}>
                                    <div>
                                        <div style={s.small}>Raciocínio</div>
                                        <div style={{ marginTop: 4, fontSize: 12, lineHeight: 1.5 }}>{selectedWorkspace.classification.rationale}</div>
                                    </div>
                                    <ProgressBar value={selectedWorkspace.classification.confidence} />
                                    <div>
                                        <div style={s.small}>Debate final</div>
                                        <div style={{ marginTop: 4, fontSize: 12, lineHeight: 1.5, whiteSpace: "pre-wrap" }}>{selectedWorkspace.debate_summary}</div>
                                    </div>
                                    <div style={s.grid2}>
                                        <div style={s.infoCard}>
                                            <div style={s.small}>Vencedor</div>
                                            <div style={{ marginTop: 4, fontWeight: 800, color: "#fff" }}>{selectedWorkspace.decision.winner_role}</div>
                                        </div>
                                        <div style={s.infoCard}>
                                            <div style={s.small}>Confiança</div>
                                            <div style={{ marginTop: 4, fontWeight: 800, color: "#fff" }}>{fmtPct(selectedWorkspace.classification.confidence)}</div>
                                        </div>
                                    </div>
                                    <div>
                                        <div style={s.small}>Grafo de raciocínio</div>
                                        <div style={{ marginTop: 6 }}>{graphNodes.length ? <GraphPreview nodes={graphNodes} /> : <div style={s.small}>Sem grafo disponível.</div>}</div>
                                    </div>
                                </div>
                            </div>
                        ) : null}

                        <div style={s.card}>
                            <div style={s.cardTitle}>Plano persistente</div>
                            {latestPlan ? (
                                <div style={{ marginTop: 10, display: "grid", gap: 8 }}>
                                    <div style={{ fontWeight: 800, color: "#fff" }}>{latestPlan.objective}</div>
                                    <div style={s.small}>Plano {short(latestPlan.plan_id)} · Run {short(latestPlan.last_run_id)}</div>
                                    <div style={s.small}>Progresso {fmtPct(latestPlan.progress)} · passo {latestPlan.current_index}/{latestPlan.subtasks.length}</div>
                                    <ProgressBar value={latestPlan.progress} />
                                    <div style={{ display: "grid", gap: 6 }}>
                                        {latestPlan.subtasks.map((subtask, index) => (
                                            <div key={`${latestPlan.plan_id}-${index}`} style={s.infoCard}>
                                                <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                                                    <div style={{ fontWeight: 700 }}>{subtask.title}</div>
                                                    <StatusPill value={subtask.status ?? "pending"} />
                                                </div>
                                                <div style={{ marginTop: 4, ...s.small }}>Progresso {fmtPct(subtask.progress ?? 0)}</div>
                                                {subtask.note ? <div style={{ marginTop: 4, fontSize: 11, lineHeight: 1.45, whiteSpace: "pre-wrap" }}>{subtask.note}</div> : null}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ) : <div style={{ marginTop: 8, ...s.small }}>Nenhum plano persistente disponível.</div>}
                        </div>
                    </>
                ) : null}

                {section === "evolution" ? (
                    <>
                        <div style={s.card}>
                            <div style={s.cardTitle}>Evolution Engine</div>
                            <div style={{ ...s.small, marginTop: 4, lineHeight: 1.45 }}>
                                Analisa o projeto, gera backlog, prioriza melhorias e dispara o próximo passo automaticamente.
                            </div>
                        </div>

                        <div style={s.grid4}>
                            <Metric label="Backlog" value={evolutionState?.backlog_size ?? 0} hint={`${evolutionState?.pending_items ?? 0} pendentes`} />
                            <Metric label="Ciclos" value={evolutionState?.cycles_run ?? 0} hint={evolutionState?.running ? "rodando" : "parado"} />
                            <Metric label="Fila ativa" value={evolutionState?.active_queue_size ?? 0} hint={`${evolutionState?.queued_items ?? 0} enfileirados`} />
                            <Metric label="Saúde" value={topBacklog ? `${topBacklog.priority}` : "-"} hint={topBacklog ? topBacklog.title : "sem prioridade"} />
                        </div>

                        <div style={s.card}>
                            <div style={s.row}>
                                <button type="button" onClick={() => void runEvolutionAction("start")} disabled={taskBusy || activeEvolution} style={s.button(true)}>
                                    Start
                                </button>
                                <button type="button" onClick={() => void runEvolutionAction("stop")} disabled={taskBusy || !activeEvolution} style={s.button()}>
                                    Stop
                                </button>
                                <button type="button" onClick={() => void runEvolutionAction("once")} disabled={taskBusy} style={s.button()}>
                                    Run once
                                </button>
                                <button type="button" onClick={() => void runEvolutionAction("rebuild")} disabled={taskBusy} style={s.button()}>
                                    Rebuild backlog
                                </button>
                            </div>
                        </div>

                        <div style={s.card}>
                            <div style={s.cardTitle}>Melhorias priorizadas</div>
                            <div style={{ display: "grid", gap: 8, marginTop: 10 }}>
                                {evolutionBacklog?.items?.length ? evolutionBacklog.items.slice(0, 8).map(item => (
                                    <div key={item.backlog_id} style={s.infoCard}>
                                        <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center" }}>
                                            <div style={{ fontWeight: 700, color: "#fff" }}>{item.title}</div>
                                            <Pill value={`${item.priority}`} />
                                        </div>
                                        <div style={{ marginTop: 4, ...s.small }}>{item.category} · {fmtStatus(item.status)}</div>
                                        <div style={{ marginTop: 6, fontSize: 12, lineHeight: 1.45 }}>{item.description}</div>
                                        {item.reasons.length ? <div style={{ marginTop: 6, ...s.small }}>Motivos: {item.reasons.join(" · ")}</div> : null}
                                    </div>
                                )) : <div style={s.small}>O backlog ainda não foi gerado.</div>}
                            </div>
                        </div>

                        <div style={s.card}>
                            <div style={s.cardTitle}>Ciclos recentes</div>
                            <div style={{ display: "grid", gap: 8, marginTop: 10 }}>
                                {recentHistory.length ? recentHistory.map(record => (
                                    <div key={record.cycle_id} style={s.infoCard}>
                                        <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center" }}>
                                            <div style={{ fontWeight: 700, color: "#fff" }}>Cycle {short(record.cycle_id)}</div>
                                            <StatusPill value={record.status} />
                                        </div>
                                        <div style={{ marginTop: 4, ...s.small }}>{fmtDate(record.started_at)}</div>
                                        <div style={{ marginTop: 6, fontSize: 12, lineHeight: 1.45 }}>{record.analysis_summary}</div>
                                    </div>
                                )) : <div style={s.small}>Nenhum ciclo histórico ainda.</div>}
                            </div>
                        </div>
                    </>
                ) : null}

                {section === "memory" ? (
                    <>
                        <div style={s.card}>
                            <div style={s.cardTitle}>Memória e aprendizado</div>
                            <div style={{ ...s.small, marginTop: 4, lineHeight: 1.45 }}>
                                Aqui ficam os aprendizados do sistema e o histórico de decisões que podem ser reutilizados nos próximos ciclos.
                            </div>
                        </div>

                        <div style={s.grid2}>
                            <Metric label="Aprendizados" value={cognitionLearning.length} hint="workspaces cognitivos" />
                            <Metric label="Memória de engenharia" value={memory.length} hint={autonomyState?.recent_memory?.length ? "reutilizável" : "vazia"} />
                        </div>

                        <div style={s.card}>
                            <div style={s.cardTitle}>Busca de aprendizado</div>
                            <div style={{ display: "grid", gap: 8, marginTop: 10 }}>
                                {selectedLearning ? (
                                    <div style={s.infoCard}>
                                        <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                                            <div style={{ fontWeight: 700, color: "#fff" }}>{selectedLearning.objective}</div>
                                            <Pill value={selectedLearning.category} />
                                        </div>
                                        <div style={{ marginTop: 4, ...s.small }}>{fmtDate(selectedLearning.timestamp)}</div>
                                        <div style={{ marginTop: 6, fontSize: 12, lineHeight: 1.45, whiteSpace: "pre-wrap" }}>{selectedLearning.summary}</div>
                                        <div style={{ marginTop: 6, ...s.small }}>Ferramenta: {selectedLearning.recommended_tool} · Vencedor: {selectedLearning.winner_role} · Confiança: {fmtPct(selectedLearning.confidence)}</div>
                                    </div>
                                ) : null}
                                <div style={{ display: "grid", gap: 8 }}>
                                    {filteredLearning.slice(0, 8).map(item => (
                                        <button key={item.entry_id} type="button" onClick={() => setSelectedLearningId(item.entry_id)} style={s.listItem(selectedLearningId === item.entry_id)}>
                                            <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                                                <div style={{ fontWeight: 700, color: "#fff" }}>{item.objective}</div>
                                                <Pill value={item.recommended_tool} />
                                            </div>
                                            <div style={{ marginTop: 4, ...s.small }}>{item.summary}</div>
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>

                        <div style={s.card}>
                            <div style={s.cardTitle}>Memória recente do sistema</div>
                            <div style={{ display: "grid", gap: 8, marginTop: 10 }}>
                                {memory.slice(0, 5).map(item => (
                                    <div key={item.memory_id} style={s.infoCard}>
                                        <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                                            <div style={{ fontWeight: 700, color: "#fff" }}>{item.objective}</div>
                                            <Pill value={item.outcome} />
                                        </div>
                                        <div style={{ marginTop: 4, ...s.small }}>{fmtDate(item.timestamp)}</div>
                                        <div style={{ marginTop: 6, fontSize: 12, lineHeight: 1.45 }}>{item.summary}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </>
                ) : null}

                {section === "control" ? (
                    <>
                        <div style={s.card}>
                            <div style={s.cardTitle}>Centro de controle</div>
                            <div style={{ ...s.small, marginTop: 4, lineHeight: 1.45 }}>
                                Crie objetivos, rode o autopilot, valide com verify e deixe o ClawAI continuar o ciclo.
                            </div>
                        </div>

                        <div style={s.card}>
                            <div style={{ display: "grid", gap: 8 }}>
                                <textarea
                                    value={objective}
                                    onChange={e => setObjective(e.target.value)}
                                    placeholder="Objetivo principal"
                                    style={s.textarea}
                                />
                                <div style={s.grid3}>
                                    <input value={testCommand} onChange={e => setTestCommand(e.target.value)} placeholder="Comando de teste" style={s.input} />
                                    <input type="number" min={1} max={5} value={maxIterations} onChange={e => setMaxIterations(Number(e.target.value) || 1)} style={s.input} />
                                    <input type="number" min={1} max={20} value={maxFiles} onChange={e => setMaxFiles(Number(e.target.value) || 1)} style={s.input} />
                                </div>
                                <div style={s.grid3}>
                                    <button type="button" onClick={() => void queueObjective()} disabled={taskBusy || !objective.trim()} style={s.button(true)}>
                                        Enfileirar
                                    </button>
                                    <button type="button" onClick={() => void startAutopilot()} disabled={taskBusy || !objective.trim()} style={s.button(true)}>
                                        Autopilot
                                    </button>
                                    <button type="button" onClick={() => void runVerifyProject()} disabled={taskBusy} style={s.button()}>
                                        Verify
                                    </button>
                                </div>
                                <div style={s.grid2}>
                                    <button type="button" onClick={() => void runQuickClassify()} disabled={taskBusy || !objective.trim()} style={s.button()}>
                                        Classificar
                                    </button>
                                    <button type="button" onClick={() => void runQuickSupervision()} disabled={taskBusy || !objective.trim()} style={s.button()}>
                                        Supervisionar
                                    </button>
                                </div>
                                <details style={s.infoCard}>
                                    <summary style={{ cursor: "pointer", fontWeight: 700, color: "#fff" }}>Ações avançadas</summary>
                                    <div style={{ marginTop: 10, display: "grid", gap: 8 }}>
                                        <div style={s.grid2}>
                                            <button type="button" onClick={() => void runQuickDebate()} disabled={taskBusy || !objective.trim()} style={s.button()}>
                                                Debate
                                            </button>
                                            <button type="button" onClick={() => void runQuickToolChoice()} disabled={taskBusy || !objective.trim()} style={s.button()}>
                                                Ferramenta
                                            </button>
                                        </div>
                                    </div>
                                </details>
                                {controlError ? <div style={{ ...s.mutedNote, borderLeftColor: "#f59e0b", background: "#2d2111", color: "#fee2b3" }}>{controlError}</div> : null}
                            </div>
                        </div>

                        <div style={s.card}>
                            <div style={s.cardTitle}>Sessão direta</div>
                            {autoSession ? (
                                <div style={{ marginTop: 10, display: "grid", gap: 6 }}>
                                    <div>Run: {short(autoSession.run_id)} · Iteração {autoSession.current_iteration}/{autoSession.max_iterations}</div>
                                    <div>Objetivo: {autoSession.objective}</div>
                                    <div>Tempo: {fmtMs(autoSession.duration_ms)}</div>
                                    {autoSession.result ? <div>Resultado: {autoSession.result.success ? "sucesso" : "falhou"}</div> : null}
                                    {autoReport ? <div>Commit: {short(autoReport.git_commit)}</div> : null}
                                    <div style={s.row}>
                                        <button type="button" onClick={() => void cancelAutopilot()} disabled={taskBusy} style={s.button(false, true)}>
                                            Cancelar
                                        </button>
                                    </div>
                                </div>
                            ) : <div style={{ marginTop: 8, ...s.small }}>Nenhuma sessão direta iniciada.</div>}
                        </div>

                        <div style={s.card}>
                            <div style={s.cardTitle}>Verificação</div>
                            {verifyResult ? (
                                <pre style={{ marginTop: 10, marginBottom: 0, whiteSpace: "pre-wrap", fontSize: 11, lineHeight: 1.5, color: "#ddd" }}>
                                    {JSON.stringify(verifyResult, null, 2)}
                                </pre>
                            ) : <div style={{ marginTop: 8, ...s.small }}>Sem resultados de verify ainda.</div>}
                        </div>
                    </>
                ) : null}

                {section === "integrations" ? (
                    <>
                        <div style={s.card}>
                            <div style={s.cardTitle}>Integrações e providers</div>
                            <div style={{ ...s.small, marginTop: 4, lineHeight: 1.45 }}>
                                Composio e o bridge entre modelos alimentam a camada de decisão do ClawAI. Aqui fica visível o que está disponível para o motor cognitivo.
                            </div>
                        </div>

                        <div style={s.grid2}>
                            <Metric label="Providers" value={bridgeProviders?.providers.length ?? 0} hint="modelos disponíveis" />
                            <Metric label="Ferramentas" value={bridgeProviders?.tools.length ?? 0} hint="ações e integrações" />
                        </div>

                        <div style={s.card}>
                            <div style={s.cardTitle}>Providers</div>
                            <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 10 }}>
                                {bridgeProviders?.providers.length ? bridgeProviders.providers.map(provider => <Pill key={provider} value={provider} />) : <div style={s.small}>Nenhum provider detectado.</div>}
                            </div>
                        </div>

                        <div style={s.card}>
                            <div style={s.cardTitle}>Ferramentas</div>
                            <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 10 }}>
                                {bridgeProviders?.tools.length ? bridgeProviders.tools.map(tool => <Pill key={tool} value={tool} />) : <div style={s.small}>Nenhuma ferramenta detectada.</div>}
                            </div>
                        </div>

                        <div style={s.card}>
                            <div style={s.cardTitle}>Workspaces cognitivos</div>
                            <div style={{ display: "grid", gap: 8, marginTop: 10 }}>
                                {recentWorkspaces.length ? recentWorkspaces.map(ws => (
                                    <button key={ws.workspace_id} type="button" onClick={() => setSection("workspace")} style={s.listItem(selectedWorkspaceId === ws.workspace_id)}>
                                        <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                                            <div style={{ fontWeight: 700, color: "#fff" }}>{ws.objective}</div>
                                            <Pill value={ws.classification.category} />
                                        </div>
                                        <div style={{ marginTop: 4, ...s.small }}>Atualizado {fmtDate(ws.updated_at)}</div>
                                    </button>
                                )) : <div style={s.small}>Ainda sem workspaces.</div>}
                            </div>
                        </div>
                    </>
                ) : null}
            </div>
        </aside>
    );
}
