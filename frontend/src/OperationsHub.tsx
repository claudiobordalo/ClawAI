import { useEffect, useMemo, useRef, useState } from "react";

import AutonomyPanel from "./AutonomyPanel";
import BridgePanel from "./BridgePanel";
import {
    classifyCognition,
    getBridgeProviders,
    listCognitionLearning,
    listCognitionWorkspaces,
    recommendBridgeTool,
    superviseCognition,
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
    runVerify,
    sendChat,
    startAutoImplement,
    stopAutoImplement,
    type AutoImplementReport,
    type AutoImplementSession,
    type ChatReply,
} from "./api";

type TabKey = "dashboard" | "workspace" | "graph" | "agents" | "memory" | "tools" | "control" | "chat";

type Message = { id: number; role: "user" | "assistant"; text: string; reply?: ChatReply };

const TABS: TabKey[] = ["dashboard", "workspace", "graph", "agents", "memory", "tools", "control", "chat"];

function fmtMs(n?: number | null) { return typeof n === "number" && !Number.isNaN(n) ? (n < 1000 ? `${Math.round(n)} ms` : `${(n / 1000).toFixed(2)} s`) : "-"; }
function fmtDate(v?: string | null) { return v ? new Date(v).toLocaleString() : "-"; }
function fmtPct(v?: number | null) { return `${Math.round(Math.max(0, Math.min(1, v ?? 0)) * 100)}%`; }
function short(v?: string | null) { return v ? v.slice(0, 8) : "-"; }
function pillTone(v?: string | null): React.CSSProperties {
    const s = (v ?? "").toLowerCase();
    const map: Record<string, React.CSSProperties> = {
        queued: { background: "#5b4636", color: "#ffd59a" }, running: { background: "#1f4d3a", color: "#bff2d0" },
        done: { background: "#234b35", color: "#c8f7d1" }, failed: { background: "#5b2b2b", color: "#ffb6b6" },
        active: { background: "#2d3e5f", color: "#c6d9ff" }, pending: { background: "#444", color: "#eee" },
        completed: { background: "#234b35", color: "#c8f7d1" }, success: { background: "#234b35", color: "#c8f7d1" },
    };
    return map[s] ?? { background: "#363636", color: "#ddd" };
}
function Pill({ value }: { value?: string | null }) { return <span style={{ display: "inline-flex", padding: "2px 8px", borderRadius: 999, fontSize: 11, fontWeight: 600, ...pillTone(value) }}>{value ? value.replaceAll("_", " ") : "-"}</span>; }
function card(): React.CSSProperties { return { border: "1px solid #333", borderRadius: 10, padding: 10, background: "#1f1f1f" }; }
function input(): React.CSSProperties { return { width: "100%", background: "#252526", color: "#ddd", border: "1px solid #444", borderRadius: 8, padding: 10, boxSizing: "border-box" }; }
function btn(active = false): React.CSSProperties { return { height: 32, padding: "0 10px", border: "1px solid #444", borderRadius: 8, background: active ? "#364151" : "#262626", color: "#ddd", cursor: "pointer" }; }
function metric(label: string, value: string | number, hint?: string) {
    return <div style={{ ...card(), display: "grid", gap: 4 }}><div style={{ fontSize: 11, color: "#9aa0a6" }}>{label}</div><div style={{ fontSize: 20, color: "#fff", fontWeight: 800 }}>{value}</div><div style={{ fontSize: 11, color: "#9aa0a6" }}>{hint ?? ""}</div></div>;
}
function nodeView(nodes: CognitionReasoningNode[], id = "root", depth = 0): React.ReactNode {
    const node = nodes.find(n => n.node_id === id); if (!node) return null;
    return <div style={{ marginLeft: depth * 10, paddingLeft: depth ? 10 : 0, borderLeft: depth ? "1px solid #333" : undefined }}>
        <div style={{ ...card(), marginBottom: 8 }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}><div style={{ color: "#fff", fontWeight: 700 }}>{node.label}</div><Pill value={node.kind} /></div>
            <div style={{ marginTop: 4, fontSize: 11, color: "#9aa0a6" }}>Score {node.score.toFixed(2)}</div>
            {node.details ? <div style={{ marginTop: 6, fontSize: 11, whiteSpace: "pre-wrap" }}>{node.details}</div> : null}
        </div>
        {node.children.map(child => <div key={child}>{nodeView(nodes, child, depth + 1)}</div>)}
    </div>;
}

export default function OperationsHub() {
    const [tab, setTab] = useState<TabKey>("dashboard");
    const [autonomy, setAutonomy] = useState<AutonomyState | null>(null);
    const [providers, setProviders] = useState<{ providers: string[]; tools: string[]; default_roles: string[] } | null>(null);
    const [workspaces, setWorkspaces] = useState<CognitionWorkspace[]>([]);
    const [learning, setLearning] = useState<CognitionLearningEntry[]>([]);
    const [selectedWorkspaceId, setSelectedWorkspaceId] = useState("");
    const [selectedLearningId, setSelectedLearningId] = useState("");
    const [objective, setObjective] = useState("");
    const [prompt, setPrompt] = useState("");
    const [testCommand, setTestCommand] = useState("uv run python -m pytest -q");
    const [maxIterations, setMaxIterations] = useState(3);
    const [maxFiles, setMaxFiles] = useState(15);
    const [messages, setMessages] = useState<Message[]>([{ id: 1, role: "assistant", text: "ClawAI pronto para operar." }]);
    const [chatPrompt, setChatPrompt] = useState("");
    const [busy, setBusy] = useState(false);
    const [verifyRunning, setVerifyRunning] = useState(false);
    const [verifyResult, setVerifyResult] = useState<unknown>(null);
    const [autoSession, setAutoSession] = useState<AutoImplementSession | null>(null);
    const [autoReport, setAutoReport] = useState<AutoImplementReport | null>(null);
    const [autoRunning, setAutoRunning] = useState(false);
    const [classification, setClassification] = useState<CognitionTaskClassification | null>(null);
    const [decision, setDecision] = useState<{ recommended_tool: string; reason: string; confidence: number; winner_role: string; source: string } | null>(null);
    const [debate, setDebate] = useState<{ final_answer: string; participants: { role: string; provider: string; model: string; content: string; elapsed_ms: number; error?: string }[]; decision: { recommended_tool: string; reason: string; confidence: number; winner_role: string; source: string }; heuristic_tool: string; heuristic_reason: string } | null>(null);
    const pollLock = useRef(false);
    const nextId = useRef(2);

    async function refresh() {
        try {
            const [a, p, w, l] = await Promise.all([getAutonomyState(), getBridgeProviders(), listCognitionWorkspaces(), listCognitionLearning(40)]);
            setAutonomy(a); setProviders(p); setWorkspaces(w); setLearning(l);
        } catch (e) { console.error(e); }
    }

    useEffect(() => { void refresh(); }, []);
    useEffect(() => {
        const t = window.setInterval(() => { void refresh(); if (autoSession?.run_id && autoRunning) void refreshAuto(autoSession.run_id); }, 2500);
        return () => window.clearInterval(t);
    }, [autoSession?.run_id, autoRunning]);

    useEffect(() => { if (workspaces.length && !workspaces.some(w => w.workspace_id === selectedWorkspaceId)) setSelectedWorkspaceId(workspaces[0].workspace_id); }, [workspaces, selectedWorkspaceId]);
    useEffect(() => { if (learning.length && !learning.some(l => l.entry_id === selectedLearningId)) setSelectedLearningId(learning[0].entry_id); }, [learning, selectedLearningId]);

    const selectedWorkspace = useMemo(() => workspaces.find(w => w.workspace_id === selectedWorkspaceId) ?? workspaces[0] ?? null, [workspaces, selectedWorkspaceId]);
    const selectedLearning = useMemo(() => learning.find(l => l.entry_id === selectedLearningId) ?? learning[0] ?? null, [learning, selectedLearningId]);
    const queue = autonomy?.queue ?? []; const plans = autonomy?.plans ?? []; const memory = autonomy?.recent_memory ?? [];
    const latestWorkspace = workspaces[0] ?? null; const latestLearning = learning[0] ?? null; const latestPlan = plans[0] ?? null; const activeQueue = queue.filter(q => q.status === "queued" || q.status === "running");
    const currentNodes = selectedWorkspace?.reasoning_graph ?? [];

    async function sendChatMessage() {
        const text = chatPrompt.trim(); if (!text || busy) return; setBusy(true); setChatPrompt("");
        const userId = nextId.current++; const assistantId = nextId.current++;
        setMessages(prev => [...prev, { id: userId, role: "user", text }, { id: assistantId, role: "assistant", text: "Pensando..." }]);
        try { const reply = await sendChat(text); setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, text: reply.answer, reply } : m)); }
        catch (e) { console.error(e); setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, text: "Não consegui responder agora." } : m)); }
        finally { setBusy(false); }
    }

    async function runSupervision() {
        const text = prompt.trim() || objective.trim(); if (!text || busy) return; setBusy(true);
        try {
            const result = await superviseCognition({ prompt: text, objective: objective.trim() || text });
            setClassification(result.classification); setDecision(result.decision); setDebate({
                final_answer: result.debate.final_answer,
                participants: result.debate.participants,
                decision: result.debate.decision,
                heuristic_tool: result.debate.heuristic_tool,
                heuristic_reason: result.debate.heuristic_reason,
            });
            setSelectedWorkspaceId(result.workspace.workspace_id); setSelectedLearningId(result.learning_entry.entry_id); setTab("workspace"); void refresh();
        } catch (e) { console.error(e); }
        finally { setBusy(false); }
    }

    async function runClassify() { const text = prompt.trim() || objective.trim(); if (!text || busy) return; setBusy(true); try { setClassification(await classifyCognition(text)); setTab("agents"); } catch (e) { console.error(e); } finally { setBusy(false); } }
    async function runToolChoice() { const text = prompt.trim() || objective.trim(); if (!text || busy) return; setBusy(true); try { setDecision(await recommendBridgeTool({ prompt: text, system_prompt: objective.trim() || null })); setTab("tools"); } catch (e) { console.error(e); } finally { setBusy(false); } }
    async function runDebate() { const text = prompt.trim() || objective.trim(); if (!text || busy) return; setBusy(true); try { const r = await consultBridge({ prompt: text, system_prompt: objective.trim() || null }); setDecision(r.decision); setDebate({ final_answer: r.final_answer, participants: r.participants, decision: r.decision, heuristic_tool: r.heuristic_tool, heuristic_reason: r.heuristic_reason }); setTab("graph"); } catch (e) { console.error(e); } finally { setBusy(false); } }
    async function enqueueObjective() { const text = objective.trim(); if (!text || busy) return; setBusy(true); try { await enqueueAutonomy({ objective: text, test_command: testCommand.trim() || "uv run python -m pytest -q", max_iterations: maxIterations, max_files: maxFiles }); void refresh(); setTab("control"); } catch (e) { console.error(e); } finally { setBusy(false); } }
    async function runVerifyProject() { setVerifyRunning(true); try { setVerifyResult(await runVerify()); setTab("control"); } catch (e) { console.error(e); setVerifyResult({ error: String(e) }); } finally { setVerifyRunning(false); } }
    async function startAutopilot() { const text = objective.trim(); if (!text || autoRunning) return; setAutoRunning(true); try { const session = await startAutoImplement(text, testCommand.trim() || "uv run python -m pytest -q", maxIterations, maxFiles); setAutoSession(session); void refreshAuto(session.run_id); } catch (e) { setAutoRunning(false); console.error(e); } }
    async function refreshAuto(runId: string) { if (pollLock.current) return; pollLock.current = true; try { const latest = await getAutoImplementStatus(runId); setAutoSession(latest); if (["success", "failed", "cancelled", "cancel_requested"].includes(latest.status)) { setAutoRunning(false); setAutoReport(latest.result ?? null); } } catch (e) { console.error(e); } finally { pollLock.current = false; } }
    async function cancelAutopilot() { if (!autoSession) return; try { const latest = await stopAutoImplement(autoSession.run_id); setAutoSession(latest); setAutoRunning(false); } catch (e) { console.error(e); } }

    const graphNodes = currentNodes.length ? currentNodes : debate ? [
        { node_id: "root", label: debate.decision.recommended_tool, kind: "decision", score: debate.decision.confidence, details: debate.decision.reason, children: [] },
    ] as CognitionReasoningNode[] : [];

    return (
        <div style={{ width: 440, minWidth: 440, height: "100%", display: "flex", flexDirection: "column", background: "#181818", borderLeft: "1px solid #333" }}>
            <div style={{ padding: 12, borderBottom: "1px solid #333", display: "flex", justifyContent: "space-between", gap: 8 }}>
                <div style={{ display: "grid" }}>
                    <span style={{ color: "#ddd", fontWeight: 800 }}>ClawAI Operations Center</span>
                    <span style={{ fontSize: 11, color: "#9aa0a6" }}>Dashboard cognitivo, workspaces, agentes, memória e controle</span>
                </div>
                <Pill value={autoSession?.status ?? (autoRunning ? "running" : "pending")} />
            </div>

            <div style={{ padding: 10, borderBottom: "1px solid #2b2b2b", background: "#1b1b1b", display: "grid", gap: 8 }}>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 }}>
                    {TABS.map(t => <button key={t} type="button" onClick={() => setTab(t)} style={btn(tab === t)}>{t}</button>)}
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                    <input value={objective} onChange={e => setObjective(e.target.value)} placeholder="Objetivo principal" style={input()} />
                    <input value={prompt} onChange={e => setPrompt(e.target.value)} placeholder="Prompt de supervisão / debate" style={input()} />
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 110px 110px", gap: 8 }}>
                    <input value={testCommand} onChange={e => setTestCommand(e.target.value)} placeholder="Comando de teste" style={input()} />
                    <input type="number" min={1} max={5} value={maxIterations} onChange={e => setMaxIterations(Number(e.target.value) || 1)} style={input()} />
                    <input type="number" min={1} max={20} value={maxFiles} onChange={e => setMaxFiles(Number(e.target.value) || 1)} style={input()} />
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 }}>
                    <button type="button" onClick={() => void enqueueObjective()} disabled={busy || !objective.trim()} style={btn()}>Enfileirar</button>
                    <button type="button" onClick={() => void startAutopilot()} disabled={autoRunning || !objective.trim()} style={btn()}>Autopilot</button>
                    <button type="button" onClick={() => void runVerifyProject()} disabled={verifyRunning} style={btn()}>{verifyRunning ? "Verificando..." : "Verify"}</button>
                    <button type="button" onClick={() => void runClassify()} disabled={busy || !(prompt.trim() || objective.trim())} style={btn()}>Classificar</button>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
                    <button type="button" onClick={() => void runDebate()} disabled={busy || !(prompt.trim() || objective.trim())} style={btn()}>Debate</button>
                    <button type="button" onClick={() => void runSupervision()} disabled={busy || !(prompt.trim() || objective.trim())} style={btn()}>Supervisionar</button>
                    <button type="button" onClick={() => void runToolChoice()} disabled={busy || !(prompt.trim() || objective.trim())} style={btn()}>Ferramenta</button>
                </div>
            </div>

            <div style={{ flex: 1, overflow: "auto", padding: 12, display: "grid", gap: 10 }}>
                {tab === "dashboard" ? <>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 8 }}>
                        {metric("Objetivos na fila", queue.length, `${activeQueue.length} ativos`)}
                        {metric("Workspaces", workspaces.length, `${learning.length} entradas de aprendizado`)}
                        {metric("Planos", plans.length, `${memory.length} memórias`)}
                        {metric("Providers", providers?.providers.length ?? 0, `${providers?.tools.length ?? 0} ferramentas`)}
                    </div>
                    <div style={card()}>
                        <div style={{ color: "#ddd", fontWeight: 700, marginBottom: 8 }}>Fila</div>
                        <div style={{ display: "grid", gap: 8 }}>
                            {queue.slice(0, 4).map(item => <div key={item.queue_id} style={card()}><div style={{ display: "flex", justifyContent: "space-between" }}><div style={{ color: "#fff", fontWeight: 700, fontSize: 12 }}>{item.objective}</div><Pill value={item.status} /></div><div style={{ marginTop: 4, fontSize: 11, color: "#9aa0a6" }}>Ordem {item.order} · {fmtDate(item.enqueued_at)}</div></div>)}
                        </div>
                    </div>
                    <div style={card()}>
                        <div style={{ color: "#ddd", fontWeight: 700, marginBottom: 8 }}>Workspaces recentes</div>
                        <div style={{ display: "grid", gap: 8 }}>
                            {workspaces.slice(0, 4).map(ws => <button key={ws.workspace_id} type="button" onClick={() => { setSelectedWorkspaceId(ws.workspace_id); setTab("workspace"); }} style={{ textAlign: "left", border: selectedWorkspaceId === ws.workspace_id ? "1px solid #4FC3F7" : "1px solid #333", borderRadius: 8, padding: 8, background: selectedWorkspaceId === ws.workspace_id ? "#233240" : "#242424", color: "#ddd" }}><div style={{ display: "flex", justifyContent: "space-between" }}><div style={{ color: "#fff", fontWeight: 700, fontSize: 12 }}>{ws.objective}</div><Pill value={ws.classification.category} /></div><div style={{ marginTop: 4, fontSize: 11, color: "#9aa0a6" }}>Atualizado {fmtDate(ws.updated_at)}</div></button>)}
                        </div>
                    </div>
                </> : null}

                {tab === "workspace" ? <>
                    <AutonomyPanel onBack={() => setTab("dashboard")} />
                    <div style={card()}>
                        <div style={{ color: "#ddd", fontWeight: 700, marginBottom: 8 }}>Workspace inteligente</div>
                        {selectedWorkspace ? <>
                            <div style={{ display: "flex", justifyContent: "space-between" }}><div style={{ color: "#fff", fontWeight: 700 }}>{selectedWorkspace.objective}</div><Pill value={selectedWorkspace.classification.category} /></div>
                            <div style={{ marginTop: 6, fontSize: 11, color: "#9aa0a6" }}>Workspace {short(selectedWorkspace.workspace_id)} · {fmtDate(selectedWorkspace.updated_at)}</div>
                            <div style={{ marginTop: 8, fontSize: 12, color: "#ddd" }}>{selectedWorkspace.classification.rationale}</div>
                            <div style={{ marginTop: 8, border: "1px solid #333", borderRadius: 8, padding: 8, background: "#242424" }}><div style={{ fontSize: 11, color: "#9aa0a6" }}>Debate final</div><div style={{ marginTop: 4, whiteSpace: "pre-wrap", color: "#ddd", fontSize: 12 }}>{selectedWorkspace.debate_summary}</div></div>
                        </> : <div style={{ color: "#9aa0a6", fontSize: 12 }}>Nenhum workspace selecionado.</div>}
                    </div>
                </> : null}

                {tab === "graph" ? <div style={card()}>{graphNodes.length ? nodeView(graphNodes) : <div style={{ color: "#9aa0a6", fontSize: 12 }}>Nenhum grafo disponível.</div>}</div> : null}

                {tab === "agents" ? <div style={{ display: "grid", gap: 8 }}>
                    <AgentCard title="Supervisor" status={classification ? "completed" : "pending"} detail={classification ? `${classification.category} → ${classification.recommended_tool}\n${classification.rationale}` : "Aguardando classificação."} />
                    <AgentCard title="Planner" status={selectedWorkspace?.classification.parallel_roles.includes("planner") ? "running" : "pending"} detail={currentNodes.find(node => node.kind === "participant" && node.label.startsWith("planner"))?.details ?? "Sem saída do planner."} />
                    <AgentCard title="Coder" status={selectedWorkspace?.classification.parallel_roles.includes("coder") ? "running" : "pending"} detail={currentNodes.find(node => node.kind === "participant" && node.label.startsWith("coder"))?.details ?? "Sem saída do coder."} />
                    <AgentCard title="Reviewer" status={selectedWorkspace?.classification.parallel_roles.includes("reviewer") ? "running" : "pending"} detail={currentNodes.find(node => node.kind === "participant" && node.label.startsWith("reviewer"))?.details ?? "Sem saída do reviewer."} />
                    <AgentCard title="Juiz" status={decision ? "completed" : "pending"} detail={decision ? `${decision.recommended_tool}\n${decision.reason}` : "Aguardando decisão final."} />
                </div> : null}

                {tab === "memory" ? <div style={{ display: "grid", gap: 8 }}>
                    <input value={query} onChange={e => setQuery(e.target.value)} placeholder="Buscar na memória" style={input()} />
                    {selectedLearning ? <div style={card()}><div style={{ display: "flex", justifyContent: "space-between" }}><div style={{ color: "#fff", fontWeight: 700 }}>{selectedLearning.objective}</div><Pill value={selectedLearning.category} /></div><div style={{ marginTop: 6, fontSize: 11, color: "#9aa0a6" }}>{fmtDate(selectedLearning.timestamp)}</div><div style={{ marginTop: 6, fontSize: 12, color: "#ddd", whiteSpace: "pre-wrap" }}>{selectedLearning.summary}</div></div> : null}
                    {learning.filter(item => !query.trim() || item.objective.toLowerCase().includes(query.toLowerCase()) || item.summary.toLowerCase().includes(query.toLowerCase())).slice(0, 8).map(item => <button key={item.entry_id} type="button" onClick={() => setSelectedLearningId(item.entry_id)} style={{ textAlign: "left", border: selectedLearningId === item.entry_id ? "1px solid #4FC3F7" : "1px solid #333", borderRadius: 8, padding: 8, background: selectedLearningId === item.entry_id ? "#233240" : "#242424", color: "#ddd" }}><div style={{ display: "flex", justifyContent: "space-between" }}><div style={{ color: "#fff", fontWeight: 700, fontSize: 12 }}>{item.objective}</div><Pill value={item.recommended_tool} /></div><div style={{ marginTop: 4, fontSize: 11, color: "#9aa0a6" }}>{item.summary}</div></button>)}
                </div> : null}

                {tab === "tools" ? <>
                    <BridgePanel onBack={() => setTab("dashboard")} />
                    <div style={card()}>
                        <div style={{ color: "#ddd", fontWeight: 700, marginBottom: 8 }}>Monitor de providers</div>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>{providers?.providers.length ? providers.providers.map(p => <Pill key={p} value={p} />) : <span style={{ color: "#9aa0a6" }}>Nenhum provider detectado</span>}</div>
                        <div style={{ marginTop: 10, display: "flex", flexWrap: "wrap", gap: 6 }}>{providers?.tools.length ? providers.tools.map(t => <Pill key={t} value={t} />) : null}</div>
                    </div>
                </> : null}

                {tab === "control" ? <div style={{ display: "grid", gap: 8 }}>
                    <div style={card()}><div style={{ color: "#ddd", fontWeight: 700, marginBottom: 8 }}>Centro de controle</div><div style={{ display: "grid", gap: 8 }}><div style={{ display: "grid", gridTemplateColumns: "1fr 110px 110px", gap: 8 }}><input value={objective} onChange={e => setObjective(e.target.value)} placeholder="Objetivo" style={input()} /><input type="number" min={1} max={5} value={maxIterations} onChange={e => setMaxIterations(Number(e.target.value) || 1)} style={input()} /><input type="number" min={1} max={20} value={maxFiles} onChange={e => setMaxFiles(Number(e.target.value) || 1)} style={input()} /></div><input value={testCommand} onChange={e => setTestCommand(e.target.value)} placeholder="Comando de teste" style={input()} /><div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}><button type="button" onClick={() => void enqueueObjective()} disabled={busy || !objective.trim()} style={btn()}>Enfileirar</button><button type="button" onClick={() => void startAutopilot()} disabled={autoRunning || !objective.trim()} style={btn()}>Autopilot</button><button type="button" onClick={() => void runVerifyProject()} disabled={verifyRunning} style={btn()}>{verifyRunning ? "Verificando..." : "Verify"}</button></div><div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}><button type="button" onClick={() => void runClassify()} disabled={busy || !(prompt.trim() || objective.trim())} style={btn()}>Classificar</button><button type="button" onClick={() => void runDebate()} disabled={busy || !(prompt.trim() || objective.trim())} style={btn()}>Debate</button><button type="button" onClick={() => void runSupervision()} disabled={busy || !(prompt.trim() || objective.trim())} style={btn()}>Supervisionar</button></div><div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}><button type="button" onClick={() => void runToolChoice()} disabled={busy || !(prompt.trim() || objective.trim())} style={btn()}>Ferramenta</button><button type="button" onClick={() => void cancelAutopilot()} disabled={!autoSession || !autoRunning} style={btn()}>Cancelar autopilot</button></div></div></div>
                    <div style={card()}><div style={{ color: "#ddd", fontWeight: 700, marginBottom: 8 }}>Sessão direta</div>{autoError ? <div style={{ color: "#ff8a80", fontSize: 12, marginBottom: 8, whiteSpace: "pre-wrap" }}>{autoError}</div> : null}{autoSession ? <div style={{ display: "grid", gap: 6, fontSize: 12, color: "#ddd" }}><div>Run: {short(autoSession.run_id)} · Iteração {autoSession.current_iteration}/{autoSession.max_iterations}</div><div>Objetivo: {autoSession.objective}</div><div>Tempo: {fmtMs(autoSession.duration_ms)}</div>{autoSession.result ? <div>Resultado: {autoSession.result.success ? "sucesso" : "falhou"}</div> : null}{autoReport ? <div>Commit: {short(autoReport.git_commit)}</div> : null}</div> : <div style={{ color: "#9aa0a6", fontSize: 12 }}>Nenhuma sessão direta iniciada.</div>}</div>
                    <div style={card()}><div style={{ color: "#ddd", fontWeight: 700, marginBottom: 8 }}>Verificação</div>{verifyResult ? <pre style={{ margin: 0, whiteSpace: "pre-wrap", fontSize: 11, color: "#ddd" }}>{JSON.stringify(verifyResult, null, 2)}</pre> : <div style={{ color: "#9aa0a6", fontSize: 12 }}>Sem resultados de verify ainda.</div>}</div>
                    <div style={card()}><div style={{ color: "#ddd", fontWeight: 700, marginBottom: 8 }}>Fila e memória</div><div style={{ display: "grid", gap: 8 }}>{queue.slice(0, 4).map(item => <div key={item.queue_id} style={card()}><div style={{ display: "flex", justifyContent: "space-between" }}><div style={{ color: "#fff", fontWeight: 700, fontSize: 12 }}>{item.objective}</div><Pill value={item.status} /></div><div style={{ marginTop: 4, fontSize: 11, color: "#9aa0a6" }}>{item.test_command}</div></div>)}{memory.slice(0, 3).map(item => <div key={item.memory_id} style={card()}><div style={{ display: "flex", justifyContent: "space-between" }}><div style={{ color: "#fff", fontWeight: 700, fontSize: 12 }}>{item.objective}</div><Pill value={item.outcome} /></div><div style={{ marginTop: 4, fontSize: 11, color: "#9aa0a6" }}>{item.summary}</div></div>)}</div></div>
                </div> : null}

                {tab === "chat" ? <div style={{ display: "grid", gap: 8 }}>
                    {messages.map(message => <div key={message.id} style={card()}><div style={{ fontSize: 11, color: message.role === "assistant" ? "#4FC3F7" : "#81C784", marginBottom: 4 }}>{message.role === "assistant" ? "ClawAI" : "Você"}</div><div style={{ color: "#ddd", whiteSpace: "pre-wrap", fontSize: 12 }}>{message.text}</div>{message.role === "assistant" && message.reply?.timings ? <div style={{ marginTop: 6, fontSize: 11, color: "#9aa0a6" }}>Provider: {message.reply.provider ?? "-"} · Modelo: {message.reply.model ?? "-"} · Total: {fmtMs(message.reply.timings.total_ms)}</div> : null}</div>)}
                    <textarea rows={3} value={chatPrompt} onChange={e => setChatPrompt(e.target.value)} placeholder="Pergunte ao ClawAI" style={{ ...input(), resize: "none" }} />
                    <button type="button" onClick={() => void sendChatMessage()} disabled={chatSending || !chatPrompt.trim()} style={btn()}>{chatSending ? "Enviando..." : "Enviar"}</button>
                </div> : null}
            </div>
        </div>
    );
}
