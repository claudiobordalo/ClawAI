import { useEffect, useMemo, useState } from "react";
import {
    consultBridge,
    getBridgeProviders,
    recommendBridgeTool,
    type BridgeConsultResult,
    type BridgeParticipantRequest,
    type BridgeProvidersResponse,
    type BridgeToolDecision,
} from "./bridge";

type Props = {
    onBack?: () => void;
};

type RoleConfig = {
    role: string;
    provider: string;
    model: string;
};

function inputStyle() {
    return {
        width: "100%",
        background: "#252526",
        color: "#ddd",
        border: "1px solid #444",
        borderRadius: 6,
        padding: 10,
        boxSizing: "border-box" as const,
    };
}

function smallButtonStyle(active = false) {
    return {
        height: 30,
        padding: "0 10px",
        cursor: "pointer",
        border: "1px solid #444",
        borderRadius: 6,
        background: active ? "#3a3f4b" : "#262626",
        color: "#ddd",
    } as const;
}

function sectionStyle() {
    return {
        border: "1px solid #333",
        borderRadius: 8,
        padding: 10,
        background: "#1f1f1f",
    } as const;
}

function badgeStyle() {
    return {
        display: "inline-flex",
        alignItems: "center",
        padding: "2px 8px",
        borderRadius: 999,
        fontSize: 11,
        fontWeight: 600,
        background: "#2d3e5f",
        color: "#c6d9ff",
    } as const;
}

function shortTime(ms?: number) {
    if (typeof ms !== "number" || Number.isNaN(ms)) {
        return "--";
    }
    return ms < 1000 ? `${Math.round(ms)} ms` : `${(ms / 1000).toFixed(2)} s`;
}

function providerListLabel(providers: string[]) {
    return providers.length ? providers.join(", ") : "nenhum provider disponível";
}

const DEFAULT_ROLES: RoleConfig[] = [
    { role: "planner", provider: "", model: "" },
    { role: "coder", provider: "", model: "" },
    { role: "reviewer", provider: "", model: "" },
];

export default function BridgePanel({ onBack }: Props) {
    const [providers, setProviders] = useState<BridgeProvidersResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [prompt, setPrompt] = useState("");
    const [systemPrompt, setSystemPrompt] = useState("");
    const [judgeProvider, setJudgeProvider] = useState("");
    const [roles, setRoles] = useState<RoleConfig[]>(DEFAULT_ROLES);
    const [result, setResult] = useState<BridgeConsultResult | null>(null);
    const [decision, setDecision] = useState<BridgeToolDecision | null>(null);
    const [busy, setBusy] = useState(false);

    useEffect(() => {
        let mounted = true;
        setLoading(true);
        void getBridgeProviders()
            .then(data => {
                if (!mounted) {
                    return;
                }
                setProviders(data);
                setJudgeProvider(data.providers[0] ?? "");
                setError("");
            })
            .catch(err => {
                console.error("Falha ao carregar providers da ponte.", err);
                if (mounted) {
                    setError("Não foi possível carregar os providers da ponte.");
                }
            })
            .finally(() => {
                if (mounted) {
                    setLoading(false);
                }
            });

        return () => {
            mounted = false;
        };
    }, []);

    const availableProviders = providers?.providers ?? [];
    const availableTools = providers?.tools ?? [];

    const participantRequests = useMemo<BridgeParticipantRequest[]>(() => {
        return roles.map(role => ({
            role: role.role,
            provider: role.provider.trim() || null,
            model: role.model.trim() || null,
        }));
    }, [roles]);

    function updateRole(index: number, patch: Partial<RoleConfig>) {
        setRoles(prev => prev.map((role, i) => (i === index ? { ...role, ...patch } : role)));
    }

    async function runConsult() {
        const normalizedPrompt = prompt.trim();
        if (!normalizedPrompt || busy) {
            return;
        }

        setBusy(true);
        setError("");
        setResult(null);
        setDecision(null);

        try {
            const response = await consultBridge({
                prompt: normalizedPrompt,
                system_prompt: systemPrompt.trim() || null,
                participants: participantRequests,
                judge_provider: judgeProvider.trim() || null,
            });
            setResult(response);
            setDecision(response.decision);
        } catch (err) {
            console.error("Falha ao consultar a ponte de modelos.", err);
            setError("Não foi possível consultar a ponte de modelos.");
        } finally {
            setBusy(false);
        }
    }

    async function runRecommend() {
        const normalizedPrompt = prompt.trim();
        if (!normalizedPrompt || busy) {
            return;
        }

        setBusy(true);
        setError("");
        setDecision(null);

        try {
            const response = await recommendBridgeTool({
                prompt: normalizedPrompt,
                system_prompt: systemPrompt.trim() || null,
                participants: participantRequests,
                judge_provider: judgeProvider.trim() || null,
            });
            setDecision(response);
        } catch (err) {
            console.error("Falha ao recomendar ferramenta.", err);
            setError("Não foi possível recomendar uma ferramenta.");
        } finally {
            setBusy(false);
        }
    }

    return (
        <div
            style={{
                width: 380,
                display: "flex",
                flexDirection: "column",
                background: "#181818",
                borderLeft: "1px solid #333",
            }}
        >
            <div
                style={{
                    padding: "12px",
                    borderBottom: "1px solid #333",
                    color: "#ddd",
                    fontWeight: "bold",
                    display: "flex",
                    justifyContent: "space-between",
                    gap: 8,
                }}
            >
                <span>Ponte de Modelos</span>
                <button type="button" onClick={onBack} style={smallButtonStyle()}>
                    Voltar
                </button>
            </div>

            <div style={{ flex: 1, overflow: "auto", padding: 12, display: "grid", gap: 10 }}>
                {error ? (
                    <div
                        style={{
                            fontSize: 12,
                            color: "#ff8a80",
                            whiteSpace: "pre-wrap",
                            border: "1px solid #5b2b2b",
                            borderRadius: 8,
                            padding: 10,
                            background: "#2a1c1c",
                        }}
                    >
                        {error}
                    </div>
                ) : null}

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                    <div style={sectionStyle()}>
                        <div style={{ fontSize: 11, color: "#9aa0a6" }}>Providers</div>
                        <div style={{ fontSize: 13, color: "#fff", marginTop: 4 }}>
                            {loading ? "Carregando..." : providerListLabel(availableProviders)}
                        </div>
                    </div>
                    <div style={sectionStyle()}>
                        <div style={{ fontSize: 11, color: "#9aa0a6" }}>Ferramentas</div>
                        <div style={{ fontSize: 13, color: "#fff", marginTop: 4 }}>
                            {availableTools.length ? availableTools.join(", ") : "chat"}
                        </div>
                    </div>
                </div>

                <section style={sectionStyle()}>
                    <div style={{ fontWeight: 700, fontSize: 12, marginBottom: 8, color: "#ddd" }}>Consulta</div>
                    <div style={{ display: "grid", gap: 8 }}>
                        <textarea
                            rows={3}
                            value={prompt}
                            placeholder="Escreva a pergunta/objetivo para o debate entre modelos..."
                            onChange={e => setPrompt(e.target.value)}
                            style={{ ...inputStyle(), resize: "none" }}
                        />
                        <textarea
                            rows={2}
                            value={systemPrompt}
                            placeholder="Contexto adicional opcional"
                            onChange={e => setSystemPrompt(e.target.value)}
                            style={{ ...inputStyle(), resize: "none" }}
                        />
                        <input
                            value={judgeProvider}
                            onChange={e => setJudgeProvider(e.target.value)}
                            placeholder="Provider do juiz (ex.: ollama, openai)"
                            style={inputStyle()}
                        />
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                            <button
                                type="button"
                                onClick={() => void runConsult()}
                                disabled={busy || !prompt.trim()}
                                style={{
                                    height: 36,
                                    borderRadius: 6,
                                    border: "1px solid #444",
                                    background: busy ? "#3a3a3a" : "#2d6cdf",
                                    color: "#fff",
                                    cursor: busy || !prompt.trim() ? "not-allowed" : "pointer",
                                }}
                            >
                                {busy ? "Consultando..." : "Consultar"}
                            </button>
                            <button
                                type="button"
                                onClick={() => void runRecommend()}
                                disabled={busy || !prompt.trim()}
                                style={{
                                    height: 36,
                                    borderRadius: 6,
                                    border: "1px solid #444",
                                    background: busy ? "#3a3a3a" : "#262626",
                                    color: "#fff",
                                    cursor: busy || !prompt.trim() ? "not-allowed" : "pointer",
                                }}
                            >
                                Escolher ferramenta
                            </button>
                        </div>
                    </div>
                </section>

                <section style={sectionStyle()}>
                    <div style={{ fontWeight: 700, fontSize: 12, marginBottom: 8, color: "#ddd" }}>Participantes</div>
                    <div style={{ display: "grid", gap: 8 }}>
                        {roles.map((role, index) => (
                            <div
                                key={role.role}
                                style={{
                                    border: "1px solid #333",
                                    borderRadius: 8,
                                    padding: 8,
                                    background: "#242424",
                                    display: "grid",
                                    gap: 6,
                                }}
                            >
                                <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                                    <div style={{ fontSize: 12, color: "#fff", fontWeight: 700 }}>{role.role}</div>
                                    <span style={badgeStyle()}>{role.role}</span>
                                </div>
                                <input
                                    value={role.provider}
                                    onChange={e => updateRole(index, { provider: e.target.value })}
                                    placeholder="provider (vazio = automático)"
                                    style={inputStyle()}
                                />
                                <input
                                    value={role.model}
                                    onChange={e => updateRole(index, { model: e.target.value })}
                                    placeholder="model (vazio = padrão do role)"
                                    style={inputStyle()}
                                />
                            </div>
                        ))}
                    </div>
                </section>

                {decision ? (
                    <section style={sectionStyle()}>
                        <div style={{ fontWeight: 700, fontSize: 12, marginBottom: 8, color: "#ddd" }}>Decisão</div>
                        <div style={{ display: "grid", gap: 6, fontSize: 12, color: "#ddd" }}>
                            <div>
                                Ferramenta: <strong>{decision.recommended_tool}</strong>
                            </div>
                            <div>
                                Motivo: {decision.reason}
                            </div>
                            <div>
                                Confiança: {Math.round((decision.confidence ?? 0) * 100)}%
                            </div>
                            <div>
                                Vencedor: {decision.winner_role}
                            </div>
                            <div>
                                Fonte: {decision.source}
                            </div>
                        </div>
                    </section>
                ) : null}

                {result ? (
                    <section style={sectionStyle()}>
                        <div style={{ fontWeight: 700, fontSize: 12, marginBottom: 8, color: "#ddd" }}>Resultado final</div>
                        <div style={{ display: "grid", gap: 6, fontSize: 12, color: "#ddd" }}>
                            <div>Tempo total: {shortTime(result.elapsed_ms)}</div>
                            <div>Modelo juiz: {result.judge_provider}/{result.judge_model}</div>
                            <div>Ferramenta heurística: {result.heuristic_tool}</div>
                            <div>Motivo heurístico: {result.heuristic_reason}</div>
                            <div>Resposta final:</div>
                            <pre style={{ whiteSpace: "pre-wrap", margin: 0, color: "#fff" }}>
                                {result.final_answer}
                            </pre>
                        </div>
                    </section>
                ) : null}

                {result ? (
                    <section style={sectionStyle()}>
                        <div style={{ fontWeight: 700, fontSize: 12, marginBottom: 8, color: "#ddd" }}>Saídas dos modelos</div>
                        <div style={{ display: "grid", gap: 8 }}>
                            {result.participants.map(participant => (
                                <details
                                    key={`${participant.role}-${participant.provider}-${participant.model}`}
                                    style={{
                                        border: "1px solid #333",
                                        borderRadius: 8,
                                        padding: 8,
                                        background: "#242424",
                                    }}
                                >
                                    <summary style={{ cursor: "pointer" }}>
                                        {participant.role} · {participant.provider}/{participant.model}
                                    </summary>
                                    <div style={{ marginTop: 8, fontSize: 11, color: "#ddd", display: "grid", gap: 6 }}>
                                        <div>Tempo: {shortTime(participant.elapsed_ms)}</div>
                                        <div>Tokens: {participant.total_tokens || participant.prompt_tokens || participant.completion_tokens ? `${participant.total_tokens} total` : "-"}</div>
                                        {participant.error ? <div style={{ color: "#ff8a80" }}>Erro: {participant.error}</div> : null}
                                        <pre style={{ whiteSpace: "pre-wrap", margin: 0 }}>
                                            {participant.content || "(sem conteúdo)"}
                                        </pre>
                                    </div>
                                </details>
                            ))}
                        </div>
                    </section>
                ) : null}

                {decision && !result ? (
                    <section style={sectionStyle()}>
                        <div style={{ fontWeight: 700, fontSize: 12, marginBottom: 8, color: "#ddd" }}>Resumo rápido</div>
                        <div style={{ whiteSpace: "pre-wrap", fontSize: 12, color: "#ddd" }}>
                            {decision.recommended_tool}: {decision.reason}
                        </div>
                    </section>
                ) : null}
            </div>
        </div>
    );
}
