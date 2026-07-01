import { useEffect, useMemo, useRef, useState } from "react";
import type { CSSProperties } from "react";

import { classifyCognition, consultBridge, getBridgeProviders, listCognitionLearning, listCognitionWorkspaces, recommendBridgeTool, superviseCognition, type BridgeProvidersResponse, type CognitionLearningEntry, type CognitionWorkspace } from "./bridge";
import { enqueueAutonomy, getAutonomyState, type AutonomyState } from "./autonomy";
import { getAutoImplementStatus, runVerify, sendChat, startAutoImplement, stopAutoImplement, type AutoImplementReport, type AutoImplementSession, type ChatReply, type VerifyResponse } from "./api";
import { getEvolutionBacklog, getEvolutionHistory, getEvolutionState, rebuildEvolutionBacklog, runEvolutionOnce, startEvolution, stopEvolution, type EvolutionBacklogOverview, type EvolutionCycleRecord, type EvolutionState } from "./evolution";

type SectionKey = "chat" | "workspace" | "evolution" | "memory" | "control" | "integrations";
type Message = { id: number; role: "user" | "assistant"; text: string; reply?: ChatReply };

const SECTIONS: Array<{ key: SectionKey; label: string; hint: string }> = [
    { key: "chat", label: "Chat", hint: "Converse e peça análise" },
    { key: "workspace", label: "Workspace", hint: "Projetos e planos" },
    { key: "evolution", label: "Evolution", hint: "Backlog e ciclos" },
    { key: "memory", label: "Memory", hint: "Aprendizados" },
    { key: "control", label: "Control", hint: "Autonomia e verify" },
    { key: "integrations", label: "Integrations", hint: "Providers e ferramentas" },
];

function fmtMs(value?: number | null): string {
    if (typeof value !== "number" || Number.isNaN(value)) return "-";
    return value < 1000 ? `${Math.round(value)} ms` : `${(value / 1000).toFixed(2)} s`;
}

function fmtDate(value?: string | null): string {
    if (!value) return "-";
    try { return new Date(value).toLocaleString(); } catch { return value; }
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

function apiErrorMessage(error: unknown, fallback: string): string {
    const anyErr = error as { response?: { data?: { detail?: unknown; error?: unknown } }; message?: unknown } | null;
    const detail = anyErr?.response?.data?.detail ?? anyErr?.response?.data?.error;
    if (typeof detail === "string" && detail.trim()) return detail;
    if (typeof anyErr?.message === "string" && anyErr.message.trim()) return anyErr.message;
    return fallback;
}

function styles() {
    return {
        shell: { width: "100%", minWidth: 0, height: "100%", display: "flex", flexDirection: "column", background: "#171717", borderLeft: "1px solid #2d2d2d", color: "#ddd" } as CSSProperties,
        header: { padding: 12, borderBottom: "1px solid #2d2d2d", display: "grid", gap: 10, flex: "0 0 auto" } as CSSProperties,
        titleRow: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 } as CSSProperties,
        title: { fontWeight: 800, fontSize: 16, lineHeight: 1.2 } as CSSProperties,
        subtitle: { marginTop: 2, fontSize: 11, color: "#9ca3af" } as CSSProperties,
        card: { border: "1px solid #2d2d2d", borderRadius: 12, padding: 12, background: "#1f1f1f" } as CSSProperties,
        info: { borderLeft: "3px solid #60a5fa", background: "#162131", padding: 10, borderRadius: 10, fontSize: 11, color: "#dbeafe", lineHeight: 1.45 } as CSSProperties,
        tabs: { display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 } as CSSProperties,
        tabButton: (active: boolean): CSSProperties => ({ height: 34, padding: "0 10px", borderRadius: 10, border: active ? "1px solid #64748b" : "1px solid #2f2f2f", background: active ? "#364152" : "#242424", color: active ? "#fff" : "#ddd", cursor: "pointer", textAlign: "left" }),
        tabLabel: { display: "block", fontWeight: 700, fontSize: 12 } as CSSProperties,
        tabHint: { display: "block", fontSize: 10, marginTop: 1, color: "#9ca3af" } as CSSProperties,
        content: { flex: 1, minHeight: 0, overflow: "hidden", padding: 12, display: "flex", flexDirection: "column", gap: 10 } as CSSProperties,
        pill: { display: "inline-flex", alignItems: "center", padding: "2px 8px", borderRadius: 999, fontSize: 11, fontWeight: 700, background: "#343434", color: "#ddd", whiteSpace: "nowrap" } as CSSProperties,
        button: (active = false, danger = false): CSSProperties => ({ height: 34, padding: "0 12px", borderRadius: 10, border: danger ? "1px solid #7f1d1d" : active ? "1px solid #64748b" : "1px solid #3a3a3a", background: danger ? "#3a1b1b" : active ? "#364152" : "#242424", color: danger ? "#ffb4b4" : active ? "#fff" : "#ddd", cursor: "pointer", whiteSpace: "nowrap" }),
        input: { width: "100%", boxSizing: "border-box", borderRadius: 10, border: "1px solid #3a3a3a", background: "#242424", color: "#ddd", padding: 10, outline: "none" } as CSSProperties,
        textarea: { width: "100%", minHeight: 56, maxHeight: 72, resize: "vertical", boxSizing: "border-box", borderRadius: 10, border: "1px solid #3a3a3a", background: "#242424", color: "#ddd", padding: 10, outline: "none" } as CSSProperties,
        row: { display: "flex", gap: 8, flexWrap: "wrap" } as CSSProperties,
        grid2: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 } as CSSProperties,
        grid3: { display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 } as CSSProperties,
        grid4: { display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 } as CSSProperties,
        small: { fontSize: 11, color: "#9ca3af" } as CSSProperties,
        message: (role: "user" | "assistant"): CSSProperties => ({ border: "1px solid #2d2d2d", borderRadius: 12, padding: 10, background: role === "assistant" ? "#1f1f1f" : "#18232f" }),
        messageRole: (role: "user" | "assistant"): CSSProperties => ({ fontSize: 11, color: role === "assistant" ? "#67e8f9" : "#86efac", marginBottom: 6, fontWeight: 700 }),
        item: (selected = false): CSSProperties => ({ textAlign: "left", border: selected ? "1px solid #60a5fa" : "1px solid #2d2d2d", borderRadius: 10, padding: 10, background: selected ? "#183044" : "#1f1f1f", color: "#ddd", cursor: "pointer" }),
        scrollArea: { minHeight: 0, overflow: "auto" } as CSSProperties,
        chatArea: { flex: 1, minHeight: 0, display: "flex", flexDirection: "column", gap: 10 } as CSSProperties,
    };
}

function Pill({ value }: { value: string }) {
    return <span style={styles().pill}>{value}</span>;
}

function StatusPill({ value }: { value?: string | null }) {
    const status = fmtStatus(value);
    const lower = status.toLowerCase();
    const tone: CSSProperties = lower.includes("running") || lower.includes("active") ? { background: "#1f4d3a", color: "#bff2d0" } : lower.includes("done") || lower.includes("success") || lower.includes("completed") ? { background: "#234b35", color: "#c8f7d1" } : lower.includes("failed") || lower.includes("error") ? { background: "#5b2b2b", color: "#ffb6b6" } : lower.includes("queued") || lower.includes("pending") ? { background: "#5b4636", color: "#ffd59a" } : { background: "#343434", color: "#ddd" };
    return <span style={{ ...styles().pill, ...tone }}>{status}</span>;
}

function Metric({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
    const st = styles();
    return <div style={st.card}><div style={st.small}>{label}</div><div style={{ fontSize: 22, fontWeight: 800, color: "#fff", marginTop: 4 }}>{value}</div>{hint ? <div style={{ ...st.small, marginTop: 4 }}>{hint}</div> : null}</div>;
}

function ProgressBar({ value }: { value: number }) {
    const pct = Math.max(0, Math.min(100, Math.round(value * 100)));
    return <div style={{ width: "100%", height: 8, background: "#2b2b2b", borderRadius: 999, overflow: "hidden" }}><div style={{ width: `${pct}%`, height: "100%", background: "#60a5fa" }} /></div>;
}

function GraphPreview({ nodes, rootId = "root", depth = 0 }: { nodes: any[]; rootId?: string; depth?: number }) {
    const node = nodes.find(item => item.node_id === rootId);
    if (!node) return null;
    const st = styles();
    return <div style={{ marginLeft: depth * 12, paddingLeft: depth ? 10 : 0, borderLeft: depth ? "1px solid #303030" : undefined }}>
        <div style={{ ...st.card, marginBottom: 8 }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}><div style={{ color: "#fff", fontWeight: 700 }}>{node.label}</div><StatusPill value={node.kind} /></div>
            <div style={{ marginTop: 4, ...st.small }}>Score {node.score.toFixed(2)}</div>
            {node.details ? <div style={{ marginTop: 6, fontSize: 11, whiteSpace: "pre-wrap", lineHeight: 1.45 }}>{node.details}</div> : null}
        </div>
        {node.children.map((child: string) => <GraphPreview key={child} nodes={nodes} rootId={child} depth={depth + 1} />)}
    </div>;
}

// function QuickAction({ label, onClick }: { label: string; onClick: () => void }) {
//     return <button type="button" onClick={onClick} style={styles().button()}>{label}</button>;
// }

export default function OperationsHub() {
    const st = styles();
    const [section, setSection] = useState<SectionKey>("chat");
    const [messages, setMessages] = useState<Message[]>([{ id: 1, role: "assistant", text: "ClawAI pronto para operar. Escolha uma tarefa ou faça uma pergunta." }]);
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
    // const [lastClassification, setLastClassification] = useState<any | null>(null);
    // const [lastDecision, setLastDecision] = useState<any | null>(null);
    // const [lastDebate, setLastDebate] = useState<any | null>(null);
    const nextId = useRef(2);
    const pollingLock = useRef(false);
    const chatScrollRef = useRef<HTMLDivElement | null>(null);

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

    useEffect(() => { void refreshAll(); }, []);
    useEffect(() => {
        if (!autoSession?.run_id) return;

        const timer = window.setInterval(() => {
            void refreshAutoSession(autoSession.run_id);
        }, 3000);

        return () => window.clearInterval(timer);
    }, [autoSession?.run_id]);

    useEffect(() => { if (!cognitionWorkspaces.length) return; if (!cognitionWorkspaces.some(ws => ws.workspace_id === selectedWorkspaceId)) setSelectedWorkspaceId(cognitionWorkspaces[0].workspace_id); }, [cognitionWorkspaces, selectedWorkspaceId]);
    useEffect(() => { if (!cognitionLearning.length) return; if (!cognitionLearning.some(item => item.entry_id === selectedLearningId)) setSelectedLearningId(cognitionLearning[0].entry_id); }, [cognitionLearning, selectedLearningId]);
    useEffect(() => { if (section === "chat") chatScrollRef.current?.scrollTo({ top: chatScrollRef.current.scrollHeight }); }, [messages, section]);

    const selectedWorkspace = useMemo(() => cognitionWorkspaces.find(ws => ws.workspace_id === selectedWorkspaceId) ?? cognitionWorkspaces[0] ?? null, [cognitionWorkspaces, selectedWorkspaceId]);
    const selectedLearning = useMemo(() => cognitionLearning.find(item => item.entry_id === selectedLearningId) ?? cognitionLearning[0] ?? null, [cognitionLearning, selectedLearningId]);
    const plans = autonomyState?.plans ?? [];
    const memory = autonomyState?.recent_memory ?? [];
    const latestPlan = plans[0] ?? null;
    const topBacklog = evolutionBacklog?.top_item ?? evolutionBacklog?.items?.[0] ?? null;
    const activeEvolution = evolutionState?.enabled ?? false;
    const graphNodes = selectedWorkspace?.reasoning_graph ?? [];
    const recentHistory = evolutionHistory.slice(0, 5);

    async function sendChatMessage() {
        const text = chatPrompt.trim();
        if (!text || chatSending) return;
        setChatSending(true);
        setChatPrompt("");
        const userId = nextId.current++;
        const assistantId = nextId.current++;
        setMessages(prev => [...prev, { id: userId, role: "user", text }, { id: assistantId, role: "assistant", text: "Pensando..." }]);
        try {
            const reply = await sendChat(text);
            setMessages(prev => prev.map(message => message.id === assistantId ? { ...message, text: reply.answer, reply } : message));
        } catch (error) {
            const message = apiErrorMessage(error, "Não consegui responder agora.");
            setMessages(prev => prev.map(msg => msg.id === assistantId ? { ...msg, text: message } : msg));
        } finally {
            setChatSending(false);
        }
    }

    async function queueObjective() {
        const text = objective.trim(); if (!text) return;
        setTaskBusy(true); setControlError("");
        try { await enqueueAutonomy({ objective: text, test_command: testCommand.trim() || "uv run python -m pytest -q", max_iterations: maxIterations, max_files: maxFiles }); setSection("control"); await refreshAll(); }
        catch (error) { setControlError(apiErrorMessage(error, "Falha ao enfileirar objetivo.")); }
        finally { setTaskBusy(false); }
    }

    async function startAutopilot() {
        const text = objective.trim(); if (!text) return;
        setTaskBusy(true); setControlError("");
        try { const session = await startAutoImplement(text, testCommand.trim() || "uv run python -m pytest -q", maxIterations, maxFiles); setAutoSession(session); setSection("control"); void refreshAutoSession(session.run_id); }
        catch (error) { setControlError(apiErrorMessage(error, "Falha ao iniciar a autonomia direta.")); }
        finally { setTaskBusy(false); }
    }

    async function refreshAutoSession(runId: string) {
        if (pollingLock.current) return;
        pollingLock.current = true;
        try { const latest = await getAutoImplementStatus(runId); setAutoSession(latest); if (["success", "failed", "cancelled", "cancel_requested"].includes(latest.status)) setAutoReport(latest.result ?? null); }
        catch (error) { console.error(error); }
        finally { pollingLock.current = false; }
    }

    async function cancelAutopilot() {
        if (!autoSession) return;
        setTaskBusy(true);
        try { setAutoSession(await stopAutoImplement(autoSession.run_id)); }
        catch (error) { setControlError(apiErrorMessage(error, "Falha ao cancelar a autonomia.")); }
        finally { setTaskBusy(false); }
    }

    async function runVerifyProject() {
        setTaskBusy(true); setControlError("");
        try { const result = await runVerify(); setVerifyResult(result); setSection("control"); }
        catch (error) { setVerifyResult({ success: false, return_code: -1, stdout: "", stderr: apiErrorMessage(error, "Falha ao executar verify.") }); }
        finally { setTaskBusy(false); }
    }

    async function runEvolutionAction(action: "start" | "stop" | "once" | "rebuild") {
        setTaskBusy(true); setControlError("");
        try { if (action === "start") await startEvolution(); else if (action === "stop") await stopEvolution(); else if (action === "once") await runEvolutionOnce(); else await rebuildEvolutionBacklog(); await refreshAll(); setSection("evolution"); }
        catch (error) { setControlError(apiErrorMessage(error, "Falha ao executar o ciclo de evolução.")); }
        finally { setTaskBusy(false); }
    }

    async function runQuickClassify() {
        const text = objective.trim(); if (!text) return;
        setTaskBusy(true);
        try { await classifyCognition(text);
            await refreshAll();
            setSection("workspace"); }
        catch (error) { setControlError(apiErrorMessage(error, "Falha ao classificar o objetivo.")); }
        finally { setTaskBusy(false); }
    }

    async function runQuickDebate() {
        const text = objective.trim(); if (!text) return;
        setTaskBusy(true);
        try { await consultBridge({
                prompt: text,
                system_prompt: text,
            });
            await refreshAll();
            setSection("workspace"); }
        catch (error) { setControlError(apiErrorMessage(error, "Falha ao executar o debate.")); }
        finally { setTaskBusy(false); }
    }

    async function runQuickSupervision() {
        const text = objective.trim(); if (!text) return;
        setTaskBusy(true);
        try {
            const result = await superviseCognition({ prompt: text, objective: text });
            // setLastClassification(result.classification);
            // setLastDecision(result.decision);
            // setLastDebate(result.debate);
            setSelectedWorkspaceId(result.workspace.workspace_id);
            setSelectedLearningId(result.learning_entry.entry_id);
            setSection("workspace");
            await refreshAll();
        } catch (error) { setControlError(apiErrorMessage(error, "Falha ao supervisionar o objetivo.")); }
        finally { setTaskBusy(false); }
    }

    async function runQuickToolChoice() {
        const text = objective.trim(); if (!text) return;
        setTaskBusy(true);
        try { await recommendBridgeTool({
                prompt: text,
                system_prompt: text,
            });
            await refreshAll();
            setSection("integrations");}
        catch (error) { setControlError(apiErrorMessage(error, "Falha ao escolher ferramenta.")); }
        finally { setTaskBusy(false); }
    }

    return (
        <aside style={st.shell}>
            <div style={st.header}>
                <div style={st.titleRow}>
                    <div><div style={st.title}>ClawAI Studio</div><div style={st.subtitle}>Chat, workspace, evolução, memória e integrações em um só lugar</div></div>
                    <StatusPill value={autoSession?.status ?? (autoSession ? "running" : activeEvolution ? "running" : "pending")} />
                </div>

                <div style={st.info}>Workspace ativo e painel lateral redimensionável. Abra outra pasta pelo seletor de projetos sem reiniciar o backend.</div>

                <div style={st.tabs}>{SECTIONS.map(item => <button key={item.key} type="button" onClick={() => setSection(item.key)} style={st.tabButton(section === item.key)}><span style={st.tabLabel}>{item.label}</span><span style={st.tabHint}>{item.hint}</span></button>)}</div>
            </div>

            <div style={st.content}>
                {section === "chat" ? (
                    <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column", gap: 10 }}>
                        <div
                            ref={chatScrollRef}
                            style={{
                                flex: 1,
                                minHeight: 0,
                                overflow: "auto",
                                border: "1px solid #2d2d2d",
                                borderRadius: 14,
                                padding: 12,
                                background: "#181818",
                            }}
                        >
                            <div style={{ display: "grid", gap: 8 }}>
                                {messages.map(message => (
                                    <div key={message.id} style={st.message(message.role)}>
                                        <div style={st.messageRole(message.role)}>
                                            {message.role === "assistant" ? "ClawAI" : "Você"}
                                        </div>
                                        <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.5, color: "#ddd" }}>
                                            {message.text}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div style={{ ...st.card, flex: "0 0 auto", display: "grid", gap: 8 }}>
                            <textarea
                                value={chatPrompt}
                                onChange={e => setChatPrompt(e.target.value)}
                                placeholder="Pergunte ao ClawAI..."
                                style={{
                                    ...st.textarea,
                                    minHeight: 58,
                                    maxHeight: 80,
                                }}
                            />
                            <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 8 }}>
                                <button
                                    type="button"
                                    onClick={() => void sendChatMessage()}
                                    disabled={chatSending || !chatPrompt.trim()}
                                    style={st.button(true)}
                                >
                                    {chatSending ? "Enviando..." : "Enviar"}
                                </button>
                            </div>
                        </div>
                    </div>
                ) : null}

                {section === "workspace" ? (
                    <>
                        <div style={st.card}>
                            <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center" }}><div style={{ fontSize: 13, fontWeight: 800, color: "#fff" }}>Workspace cognitivo</div><Pill value={selectedWorkspace?.classification.category ?? "workspace"} /></div>
                            <div style={{ marginTop: 6, ...st.small }}>Workspace {short(selectedWorkspace?.workspace_id)} · {fmtDate(selectedWorkspace?.updated_at)}</div>
                        </div>
                        <div style={st.grid2}><Metric label="Confiança" value={fmtPct(selectedWorkspace?.classification.confidence ?? 0)} hint={selectedWorkspace?.classification.rationale ?? "Sem classificação"} /><Metric label="Debate" value={selectedWorkspace?.decision.winner_role ?? "-"} hint={selectedWorkspace?.decision.recommended_tool ?? "sem decisão"} /></div>
                        <div style={st.card}><div style={{ fontSize: 12, color: "#9ca3af" }}>Debate final</div><div style={{ marginTop: 6, fontSize: 12, lineHeight: 1.5, whiteSpace: "pre-wrap" }}>{selectedWorkspace?.debate_summary ?? "Sem debate ainda."}</div><div style={{ marginTop: 10 }}><ProgressBar value={selectedWorkspace?.classification.confidence ?? 0} /></div></div>
                        <div style={st.card}><div style={{ fontSize: 13, fontWeight: 800, color: "#fff" }}>Grafo de raciocínio</div><div style={{ marginTop: 10 }}>{graphNodes.length ? <GraphPreview nodes={graphNodes} /> : <div style={st.small}>Sem grafo disponível.</div>}</div></div>
                        {/* <div style={st.card}><div style={{ fontSize: 13, fontWeight: 800, color: "#fff" }}>Última análise</div><div style={{ marginTop: 10, display: "grid", gap: 8 }}><div><span style={st.small}>Classificação:</span><pre style={{ whiteSpace: "pre-wrap", margin: 0 }}>{lastClassification ? JSON.stringify(lastClassification, null, 2) : "—"}</pre></div><div><span style={st.small}>Decisão:</span><pre style={{ whiteSpace: "pre-wrap", margin: 0 }}>{lastDecision ? JSON.stringify(lastDecision, null, 2) : "—"}</pre></div><div><span style={st.small}>Debate:</span><pre style={{ whiteSpace: "pre-wrap", margin: 0 }}>{lastDebate ? JSON.stringify(lastDebate, null, 2) : "—"}</pre></div></div></div> */}
                        <div style={st.card}><div style={{ fontSize: 13, fontWeight: 800, color: "#fff" }}>Plano persistente</div>{latestPlan ? <div style={{ marginTop: 10, display: "grid", gap: 8 }}><div style={{ fontWeight: 800, color: "#fff" }}>{latestPlan.objective}</div><div style={st.small}>Plano {short(latestPlan.plan_id)} · Run {short(latestPlan.last_run_id)}</div><div style={st.small}>Progresso {fmtPct(latestPlan.progress)} · passo {latestPlan.current_index}/{latestPlan.subtasks.length}</div><ProgressBar value={latestPlan.progress} /><div style={{ display: "grid", gap: 6 }}>{latestPlan.subtasks.map((subtask, index) => <div key={`${latestPlan.plan_id}-${index}`} style={st.card}><div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}><div style={{ fontWeight: 700, color: "#fff" }}>{subtask.title}</div><StatusPill value={subtask.status ?? "pending"} /></div><div style={{ marginTop: 4, ...st.small }}>Progresso {fmtPct(subtask.progress ?? 0)}</div>{subtask.note ? <div style={{ marginTop: 4, fontSize: 11, lineHeight: 1.45, whiteSpace: "pre-wrap" }}>{subtask.note}</div> : null}</div>)}</div></div> : <div style={{ marginTop: 8, ...st.small }}>Nenhum plano persistente disponível.</div>}</div>
                    </>
                ) : null}

                {section === "evolution" ? (
                    <>
                        <div style={st.card}><div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center" }}><div style={{ fontSize: 13, fontWeight: 800, color: "#fff" }}>Evolution Engine</div><StatusPill value={evolutionState?.enabled ? "running" : "stopped"} /></div><div style={{ ...st.small, marginTop: 4 }}>Analisa o estado do projeto, gera backlog e aciona o próximo passo.</div></div>
                        <div style={st.grid4}><Metric label="Backlog" value={evolutionState?.backlog_size ?? 0} hint={`${evolutionState?.pending_items ?? 0} pendentes`} /><Metric label="Ciclos" value={evolutionState?.cycles_run ?? 0} hint={evolutionState?.running ? "rodando" : "parado"} /><Metric label="Fila" value={evolutionState?.active_queue_size ?? 0} hint={`${evolutionState?.queued_items ?? 0} enfileirados`} /><Metric label="Prioridade" value={topBacklog ? `${topBacklog.priority}` : "-"} hint={topBacklog ? topBacklog.title : "sem backlog"} /></div>
                        <div style={st.card}><div style={st.row}><button type="button" onClick={() => void runEvolutionAction("start")} disabled={taskBusy || activeEvolution} style={st.button(true)}>Start</button><button type="button" onClick={() => void runEvolutionAction("stop")} disabled={taskBusy || !activeEvolution} style={st.button()}>Stop</button><button type="button" onClick={() => void runEvolutionAction("once")} disabled={taskBusy} style={st.button()}>Run once</button><button type="button" onClick={() => void runEvolutionAction("rebuild")} disabled={taskBusy} style={st.button()}>Rebuild backlog</button></div></div>
                        <div style={st.card}><div style={{ fontSize: 13, fontWeight: 800, color: "#fff" }}>Backlog priorizado</div><div style={{ display: "grid", gap: 8, marginTop: 10 }}>{evolutionBacklog?.items?.length ? evolutionBacklog.items.slice(0, 8).map(item => <div key={item.backlog_id} style={st.card}><div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center" }}><div style={{ fontWeight: 700, color: "#fff" }}>{item.title}</div><Pill value={`${item.priority}`} /></div><div style={{ marginTop: 4, ...st.small }}>{item.category} · {fmtStatus(item.status)}</div><div style={{ marginTop: 6, fontSize: 12, lineHeight: 1.45 }}>{item.description}</div>{item.reasons.length ? <div style={{ marginTop: 6, ...st.small }}>Motivos: {item.reasons.join(" · ")}</div> : null}</div>) : <div style={st.small}>O backlog ainda não foi gerado.</div>}</div></div>
                        <div style={st.card}><div style={{ fontSize: 13, fontWeight: 800, color: "#fff" }}>Ciclos recentes</div><div style={{ display: "grid", gap: 8, marginTop: 10 }}>{recentHistory.length ? recentHistory.map(record => <div key={record.cycle_id} style={st.card}><div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center" }}><div style={{ fontWeight: 700, color: "#fff" }}>Cycle {short(record.cycle_id)}</div><StatusPill value={record.status} /></div><div style={{ marginTop: 4, ...st.small }}>{fmtDate(record.started_at)}</div><div style={{ marginTop: 6, fontSize: 12, lineHeight: 1.45 }}>{record.analysis_summary}</div></div>) : <div style={st.small}>Nenhum ciclo histórico ainda.</div>}</div></div>
                    </>
                ) : null}

                {section === "memory" ? (
                    <>
                        <div style={st.card}><div style={{ fontSize: 13, fontWeight: 800, color: "#fff" }}>Memória e aprendizado</div><div style={{ ...st.small, marginTop: 4 }}>Decisões, padrões reutilizáveis e aprendizados acumulados.</div></div>
                        <div style={st.grid2}><Metric label="Aprendizados" value={cognitionLearning.length} hint="workspaces cognitivos" /><Metric label="Memória" value={memory.length} hint={autonomyState?.recent_memory?.length ? "reutilizável" : "vazia"} /></div>
                        <div style={st.card}><div style={{ fontSize: 13, fontWeight: 800, color: "#fff" }}>Aprendizado selecionado</div>{selectedLearning ? <div style={{ marginTop: 10, display: "grid", gap: 8 }}><div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}><div style={{ fontWeight: 700, color: "#fff" }}>{selectedLearning.objective}</div><Pill value={selectedLearning.category} /></div><div style={st.small}>{fmtDate(selectedLearning.timestamp)}</div><div style={{ fontSize: 12, lineHeight: 1.45, whiteSpace: "pre-wrap" }}>{selectedLearning.summary}</div><div style={st.small}>Ferramenta: {selectedLearning.recommended_tool} · Vencedor: {selectedLearning.winner_role} · Confiança: {fmtPct(selectedLearning.confidence)}</div></div> : <div style={{ marginTop: 8, ...st.small }}>Sem aprendizado selecionado.</div>}</div>
                        <div style={st.card}><div style={{ fontSize: 13, fontWeight: 800, color: "#fff" }}>Memória recente do sistema</div><div style={{ display: "grid", gap: 8, marginTop: 10 }}>{memory.slice(0, 5).map(item => <div key={item.memory_id} style={st.card}><div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}><div style={{ fontWeight: 700, color: "#fff" }}>{item.objective}</div><Pill value={item.outcome} /></div><div style={{ marginTop: 4, ...st.small }}>{fmtDate(item.timestamp)}</div><div style={{ marginTop: 6, fontSize: 12, lineHeight: 1.45 }}>{item.summary}</div></div>)}</div></div>
                    </>
                ) : null}

                {section === "control" ? (
                    <>
                        <div style={st.card}><div style={{ fontSize: 13, fontWeight: 800, color: "#fff" }}>Centro de controle</div><div style={{ ...st.small, marginTop: 4 }}>Crie objetivos, rode o autopilot, valide com verify e continue o ciclo.</div></div>
                        <div style={st.card}><div style={{ display: "grid", gap: 8 }}><textarea value={objective} onChange={e => setObjective(e.target.value)} placeholder="Objetivo principal" style={st.textarea} /><div style={st.grid3}><input value={testCommand} onChange={e => setTestCommand(e.target.value)} placeholder="Comando de teste" style={st.input} /><input type="number" min={1} max={5} value={maxIterations} onChange={e => setMaxIterations(Number(e.target.value) || 1)} style={st.input} /><input type="number" min={1} max={20} value={maxFiles} onChange={e => setMaxFiles(Number(e.target.value) || 1)} style={st.input} /></div><div style={st.grid3}><button type="button" onClick={() => void queueObjective()} disabled={taskBusy || !objective.trim()} style={st.button(true)}>Enfileirar</button><button type="button" onClick={() => void startAutopilot()} disabled={taskBusy || !objective.trim()} style={st.button(true)}>Autopilot</button><button type="button" onClick={() => void runVerifyProject()} disabled={taskBusy} style={st.button()}>Verify</button></div><div style={st.grid2}><button type="button" onClick={() => void runQuickClassify()} disabled={taskBusy || !objective.trim()} style={st.button()}>Classificar</button><button type="button" onClick={() => void runQuickSupervision()} disabled={taskBusy || !objective.trim()} style={st.button()}>Supervisionar</button></div><div style={st.grid2}><button type="button" onClick={() => void runQuickDebate()} disabled={taskBusy || !objective.trim()} style={st.button()}>Debate</button><button type="button" onClick={() => void runQuickToolChoice()} disabled={taskBusy || !objective.trim()} style={st.button()}>Ferramenta</button></div>{controlError ? <div style={{ ...st.info, borderLeftColor: "#f59e0b", background: "#2d2111", color: "#fee2b3" }}>{controlError}</div> : null}</div></div>
                        <div style={st.card}><div style={{ fontSize: 13, fontWeight: 800, color: "#fff" }}>Sessão direta</div>{autoSession ? <div style={{ marginTop: 10, display: "grid", gap: 6 }}><div>Run: {short(autoSession.run_id)} · Iteração {autoSession.current_iteration}/{autoSession.max_iterations}</div><div>Objetivo: {autoSession.objective}</div><div>Tempo: {fmtMs(autoSession.duration_ms)}</div>{autoSession.result ? <div>Resultado: {autoSession.result.success ? "sucesso" : "falhou"}</div> : null}{autoReport ? <div>Commit: {short(autoReport.git_commit)}</div> : null}<div style={st.row}><button type="button" onClick={() => void cancelAutopilot()} disabled={taskBusy} style={st.button(false, true)}>Cancelar</button></div></div> : <div style={{ marginTop: 8, ...st.small }}>Nenhuma sessão direta iniciada.</div>}</div>
                        <div style={st.card}><div style={{ fontSize: 13, fontWeight: 800, color: "#fff" }}>Verificação</div>{verifyResult ? <pre style={{ marginTop: 10, marginBottom: 0, whiteSpace: "pre-wrap", fontSize: 11, lineHeight: 1.5, color: "#ddd" }}>{JSON.stringify(verifyResult, null, 2)}</pre> : <div style={{ marginTop: 8, ...st.small }}>Sem resultados de verify ainda.</div>}</div>
                    </>
                ) : null}

                {section === "integrations" ? (
                    <>
                        <div style={st.card}><div style={{ fontSize: 13, fontWeight: 800, color: "#fff" }}>Integrações e providers</div><div style={{ ...st.small, marginTop: 4 }}>Composio e bridge alimentam a camada de decisão do ClawAI.</div></div>
                        <div style={st.grid2}><Metric label="Providers" value={bridgeProviders?.providers.length ?? 0} hint="modelos disponíveis" /><Metric label="Ferramentas" value={bridgeProviders?.tools.length ?? 0} hint="ações e integrações" /></div>
                        <div style={st.card}><div style={{ fontSize: 13, fontWeight: 800, color: "#fff" }}>Providers</div><div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 10 }}>{bridgeProviders?.providers.length ? bridgeProviders.providers.map(provider => <Pill key={provider} value={provider} />) : <div style={st.small}>Nenhum provider detectado.</div>}</div></div>
                        <div style={st.card}><div style={{ fontSize: 13, fontWeight: 800, color: "#fff" }}>Ferramentas</div><div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 10 }}>{bridgeProviders?.tools.length ? bridgeProviders.tools.map(tool => <Pill key={tool} value={tool} />) : <div style={st.small}>Nenhuma ferramenta detectada.</div>}</div></div>
                    </>
                ) : null}
            </div>
        </aside>
    );
}
