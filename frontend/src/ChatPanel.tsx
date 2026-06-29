import { useEffect, useRef, useState } from "react";
import {
    getAutoImplementStatus,
    sendChat,
    startAutoImplement,
    stopAutoImplement,
    runVerify,
    type AutoImplementReport,
    type AutoImplementSession,
    type ChatReply
} from "./api";

type Message = {
    id: number;
    role: "user" | "assistant";
    text: string;
    reply?: ChatReply;
};

function formatTime(ms?: number): string {
    if (typeof ms !== "number" || Number.isNaN(ms)) {
        return "--";
    }

    if (ms < 1000) {
        return `${Math.round(ms)} ms`;
    }

    return `${(ms / 1000).toFixed(2)} s`;
}

function yesNo(value?: boolean): string {
    if (typeof value !== "boolean") {
        return "-";
    }

    return value ? "sim" : "não";
}

export default function ChatPanel() {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: 1,
            role: "assistant",
            text: "Olá! Sou o ClawAI. Como posso ajudar?"
        }
    ]);

    const [prompt, setPrompt] = useState("");
    const [sending, setSending] = useState(false);

    const [autoObjective, setAutoObjective] = useState("");
    const [autoTestCommand, setAutoTestCommand] = useState("uv run python -m pytest -q");
    const [autoIterations, setAutoIterations] = useState(3);
    const [autoRunning, setAutoRunning] = useState(false);
    const [autoReport, setAutoReport] = useState<AutoImplementReport | null>(null);
    const [autoSession, setAutoSession] = useState<AutoImplementSession | null>(null);
    const [autoError, setAutoError] = useState("");

    const timerRef = useRef<number | null>(null);
    const pollRef = useRef<number | null>(null);
    const pollingRef = useRef(false);
    const startedAtRef = useRef(0);
    const nextIdRef = useRef(2);

    useEffect(() => {
        return () => {
            if (timerRef.current !== null) {
                window.clearInterval(timerRef.current);
            }
            if (pollRef.current !== null) {
                window.clearInterval(pollRef.current);
            }
        };
    }, []);

    function stopTimer() {
        if (timerRef.current !== null) {
            window.clearInterval(timerRef.current);
            timerRef.current = null;
        }
    }

    function stopPolling() {
        if (pollRef.current !== null) {
            window.clearInterval(pollRef.current);
            pollRef.current = null;
        }
        pollingRef.current = false;
    }

    function isTerminalStatus(status?: string) {
        return status === "success" || status === "failed" || status === "cancelled" || status === "cancel_requested";
    }

    async function send() {
        const text = prompt.trim();

        if (!text || sending) {
            return;
        }

        setPrompt("");

        const userId = nextIdRef.current++;
        const assistantId = nextIdRef.current++;

        setMessages(prev => [
            ...prev,
            {
                id: userId,
                role: "user",
                text
            },
            {
                id: assistantId,
                role: "assistant",
                text: "Pensando... 0 ms"
            }
        ]);

        setSending(true);
        startedAtRef.current = performance.now();

        stopTimer();

        timerRef.current = window.setInterval(() => {
            const elapsed = performance.now() - startedAtRef.current;

            setMessages(prev =>
                prev.map(message =>
                    message.id === assistantId
                        ? {
                            ...message,
                            text: `Pensando... ${formatTime(elapsed)}`
                        }
                        : message
                )
            );
        }, 100);

        try {
            const reply = await sendChat(text);
            const elapsed = performance.now() - startedAtRef.current;

            stopTimer();

            setMessages(prev =>
                prev.map(message =>
                    message.id === assistantId
                        ? {
                            ...message,
                            text: reply.answer,
                            reply
                        }
                        : message
                )
            );

            void elapsed;
        } catch (error) {
            console.error("Falha ao obter resposta do ClawAI.", error);

            stopTimer();

            setMessages(prev =>
                prev.map(message =>
                    message.id === assistantId
                        ? {
                            ...message,
                            text: "Não consegui obter uma resposta agora."
                        }
                        : message
                )
            );
        } finally {
            setSending(false);
        }
    }

    async function refreshAutoSession(runId: string) {
        if (pollingRef.current) {
            return;
        }

        pollingRef.current = true;

        try {
            const latest = await getAutoImplementStatus(runId);
            setAutoSession(latest);

            if (isTerminalStatus(latest.status)) {
                stopPolling();
                setAutoRunning(false);
                setAutoReport(latest.result ?? null);
            }
        } catch (error) {
            console.error("Falha ao atualizar a sessão automática.", error);
        } finally {
            pollingRef.current = false;
        }
    }


    async function runAuto() {
        const objective = autoObjective.trim();

        if (!objective || autoRunning) {
            return;
        }

        setAutoError("");
        setAutoReport(null);
        setAutoSession(null);
        setAutoRunning(true);

        try {
            const session = await startAutoImplement(
                objective,
                autoTestCommand.trim() || "uv run python -m pytest -q",
                autoIterations,
                15
            );

            setAutoSession(session);

            stopPolling();
            pollRef.current = window.setInterval(() => {
                void refreshAutoSession(session.run_id);
            }, 1000);

            void refreshAutoSession(session.run_id);
        } catch (error) {
            const message =
                error instanceof Error
                    ? error.message
                    : "Falha ao executar a auto-implementação.";

            console.error(message, error);
            setAutoError(message);
            setAutoRunning(false);
        }
    }

    async function cancelAuto() {
        if (!autoSession || isTerminalStatus(autoSession.status)) {
            return;
        }

        try {
            const session = await stopAutoImplement(autoSession.run_id);
            setAutoSession(session);
            setAutoRunning(false);
            stopPolling();
        } catch (error) {
            console.error("Falha ao cancelar a auto-implementação.", error);
        }
    }

    async function verifyProject() {

        try {

            const result = await runVerify();

            console.log(result);

            alert(
                result.success
                    ? "Projeto verificado com sucesso."
                    : "Falha na verificação."
            );

        }
        catch (error) {

            console.error(error);

            alert("Não foi possível executar o verify.");

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
                    fontWeight: "bold"
                }}
            >
                ClawAI Chat
            </div>

            <div
                style={{
                    flex: 1,
                    overflow: "auto",
                    padding: 12
                }}
            >
                {messages.map((m) => (
                    <div
                        key={m.id}
                        style={{
                            marginBottom: 14
                        }}
                    >
                        <div
                            style={{
                                fontSize: 12,
                                color:
                                    m.role === "assistant"
                                        ? "#4FC3F7"
                                        : "#81C784",
                                marginBottom: 4
                            }}
                        >
                            {m.role === "assistant" ? "ClawAI" : "Você"}
                        </div>

                        <div
                            style={{
                                background: "#252526",
                                color: "#ddd",
                                padding: 10,
                                borderRadius: 6,
                                whiteSpace: "pre-wrap"
                            }}
                        >
                            {m.text}
                        </div>

                        {m.role === "assistant" && m.reply?.timings ? (
                            <div
                                style={{
                                    marginTop: 6,
                                    fontSize: 11,
                                    color: "#9aa0a6",
                                    lineHeight: 1.45
                                }}
                            >
                                <div>
                                    Provider: {m.reply.provider ?? "-"} · Modelo: {m.reply.model ?? "-"}
                                </div>
                                <div>
                                    Memória: {yesNo(m.reply.used_memory)} · Conhecimento: {yesNo(m.reply.used_knowledge)} · Web: {yesNo(m.reply.requires_web)}
                                </div>
                                <div>
                                    Memória salva: {yesNo(m.reply.memory_saved)}
                                </div>
                                <div>
                                    Busca memória: {formatTime(m.reply.timings.search?.memory_ms)}
                                </div>
                                <div>
                                    Busca conhecimento: {formatTime(m.reply.timings.search?.knowledge_ms)}
                                </div>
                                <div>
                                    Construção do prompt: {formatTime(m.reply.timings.search?.prompt_ms)}
                                </div>
                                <div>
                                    Busca total: {formatTime(m.reply.timings.search?.total_ms)}
                                </div>
                                <div>
                                    Modelo: {formatTime(m.reply.timings.model_ms)}
                                </div>
                                <div>
                                    Pós-processamento: {formatTime(m.reply.timings.postprocess_ms)}
                                </div>
                                <div>
                                    Total: {formatTime(m.reply.timings.total_ms)}
                                </div>
                            </div>
                        ) : null}
                    </div>
                ))}
            </div>

            <details
                open
                style={{
                    padding: 12,
                    borderTop: "1px solid #333",
                    color: "#ddd"
                }}
            >
                <summary
                    style={{
                        cursor: "pointer",
                        fontWeight: "bold",
                        marginBottom: 10
                    }}
                >
                    Auto implementação
                </summary>

                <div
                    style={{
                        display: "grid",
                        gap: 10
                    }}
                >
                    <textarea
                        rows={3}
                        value={autoObjective}
                        placeholder="Descreva o que o ClawAI deve implementar..."
                        onChange={e => setAutoObjective(e.target.value)}
                        style={{
                            width: "100%",
                            resize: "none",
                            background: "#252526",
                            color: "#ddd",
                            border: "1px solid #444",
                            borderRadius: 6,
                            padding: 10,
                            boxSizing: "border-box"
                        }}
                    />

                    <div
                        style={{
                            display: "grid",
                            gridTemplateColumns: "1fr 110px",
                            gap: 8
                        }}
                    >
                        <input
                            value={autoTestCommand}
                            onChange={e => setAutoTestCommand(e.target.value)}
                            placeholder="uv run python -m pytest -q"
                            style={{
                                width: "100%",
                                background: "#252526",
                                color: "#ddd",
                                border: "1px solid #444",
                                borderRadius: 6,
                                padding: 10,
                                boxSizing: "border-box"
                            }}
                        />

                        <input
                            type="number"
                            min={1}
                            max={5}
                            value={autoIterations}
                            onChange={e => setAutoIterations(Number(e.target.value) || 1)}
                            title="Iterações"
                            style={{
                                width: "100%",
                                background: "#252526",
                                color: "#ddd",
                                border: "1px solid #444",
                                borderRadius: 6,
                                padding: 10,
                                boxSizing: "border-box"
                            }}
                        />
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
                        <button
                            onClick={() => void runAuto()}
                            disabled={autoRunning || !autoObjective.trim()}
                            style={{
                                width: "100%",
                                height: 36,
                                cursor: autoRunning ? "wait" : "pointer",
                                opacity: autoRunning || !autoObjective.trim() ? 0.7 : 1
                            }}
                        >
                            {autoRunning ? "Executando..." : "Auto implementar"}
                        </button>

                        <button
                            onClick={() => void cancelAuto()}
                            disabled={!autoSession || !autoRunning}
                            style={{
                                width: "100%",
                                height: 36,
                                cursor: !autoSession || !autoRunning ? "not-allowed" : "pointer",
                                opacity: !autoSession || !autoRunning ? 0.7 : 1
                            }}
                        >
                            Cancelar
                        </button>

                        <button
                            onClick={() => void verifyProject()}
                            disabled={autoRunning}
                            style={{
                                width: "100%",
                                height: 36,
                                cursor: autoRunning ? "wait" : "pointer",
                                opacity: autoRunning ? 0.7 : 1
                            }}
                        >
                            Verify
                        </button>
                    </div>

                    {autoError ? (
                        <div
                            style={{
                                fontSize: 12,
                                color: "#ff8a80",
                                whiteSpace: "pre-wrap"
                            }}
                        >
                            {autoError}
                        </div>
                    ) : null}

                    {autoSession ? (
                        <div
                            style={{
                                fontSize: 11,
                                color: "#9aa0a6",
                                lineHeight: 1.45,
                                maxHeight: 260,
                                overflow: "auto",
                                border: "1px solid #333",
                                borderRadius: 6,
                                padding: 10,
                                background: "#1f1f1f"
                            }}
                        >
                            <div>
                                Sessão: {autoSession.run_id.slice(0, 8)} · Status: {autoSession.status} · Iteração: {autoSession.current_iteration}/{autoSession.max_iterations}
                            </div>
                            <div>
                                Objetivo: {autoSession.objective}
                            </div>
                            <div>
                                Teste: {autoSession.test_command}
                            </div>
                            <div>
                                Tempo: {formatTime(autoSession.duration_ms)}
                            </div>
                            {autoSession.error ? (
                                <div style={{ color: "#ff8a80", marginTop: 4 }}>
                                    Erro: {autoSession.error}
                                </div>
                            ) : null}
                            {autoSession.summary ? (
                                <div style={{ marginTop: 4 }}>
                                    Resumo: {autoSession.summary}
                                </div>
                            ) : null}

                            <div style={{ marginTop: 8 }}>
                                <strong>Eventos</strong>
                            </div>

                            {autoSession.events.length ? (
                                autoSession.events.map(event => (
                                    <details
                                        key={event.index}
                                        style={{
                                            marginTop: 8,
                                            border: "1px solid #333",
                                            borderRadius: 6,
                                            padding: 8,
                                            background: "#242424"
                                        }}
                                    >
                                        <summary style={{ cursor: "pointer" }}>
                                            #{event.index} · {event.step} · {event.status}
                                        </summary>
                                        <div style={{ marginTop: 8 }}>
                                            <div>{event.message}</div>
                                            <div>Iteração: {event.iteration ?? "-"}</div>
                                            <div>Tempo: {formatTime(event.elapsed_ms ?? undefined)}</div>
                                            {event.files.length ? (
                                                <div style={{ marginTop: 6, whiteSpace: "pre-wrap" }}>
                                                    Arquivos: {event.files.join(", ")}
                                                </div>
                                            ) : null}
                                            {event.summary ? (
                                                <div style={{ marginTop: 6, whiteSpace: "pre-wrap" }}>
                                                    Resumo: {event.summary}
                                                </div>
                                            ) : null}
                                            {event.test ? (
                                                <div style={{ marginTop: 6 }}>
                                                    Teste: {event.test.success ? "ok" : "falhou"} · {formatTime(event.test.duration_ms)}
                                                </div>
                                            ) : null}
                                            {event.error ? (
                                                <div style={{ marginTop: 6, color: "#ff8a80", whiteSpace: "pre-wrap" }}>
                                                    {event.error}
                                                </div>
                                            ) : null}
                                        </div>
                                    </details>
                                ))
                            ) : (
                                <div style={{ marginTop: 6 }}>Aguardando progresso...</div>
                            )}
                        </div>
                    ) : null}


                    {autoReport ? (
                        <div
                            style={{
                                fontSize: 11,
                                color: "#9aa0a6",
                                lineHeight: 1.45,
                                maxHeight: 260,
                                overflow: "auto",
                                border: "1px solid #333",
                                borderRadius: 6,
                                padding: 10,
                                background: "#1f1f1f"
                            }}
                        >
                            <div>
                                Resultado: {autoReport.success ? "sucesso" : "parcial"} · Tempo: {formatTime(autoReport.duration_ms)}
                            </div>
                            <div>
                                Provider: {autoReport.provider} · Modelo: {autoReport.model}
                            </div>
                            <div>
                                Teste: {autoReport.test_command}
                            </div>
                            <div>
                                Resumo: {autoReport.summary}
                            </div>
                            <div>
                                Arquivos candidatos: {autoReport.candidate_files.length}
                            </div>

                            {autoReport.candidate_files.length ? (
                                <div style={{ marginTop: 6 }}>
                                    <strong>Candidatos</strong>
                                    <div style={{ whiteSpace: "pre-wrap" }}>
                                        {autoReport.candidate_files.slice(0, 12).join(", ")}
                                        {autoReport.candidate_files.length > 12 ? " ..." : ""}
                                    </div>
                                </div>
                            ) : null}

                            <div style={{ marginTop: 8 }}>
                                <strong>Iterações</strong>
                            </div>

                            {autoReport.iterations.map(iteration => (
                                <details
                                    key={iteration.iteration}
                                    style={{
                                        marginTop: 8,
                                        border: "1px solid #333",
                                        borderRadius: 6,
                                        padding: 8,
                                        background: "#242424"
                                    }}
                                >
                                    <summary style={{ cursor: "pointer" }}>
                                        Iteração {iteration.iteration} · {" "}
                                        {iteration.test?.success ? "teste ok" : "teste falhou"}
                                    </summary>

                                    <div style={{ marginTop: 8 }}>
                                        <div>
                                            Resumo: {iteration.summary}
                                        </div>

                                        <div style={{ marginTop: 6 }}>
                                            Alterações: {iteration.changes.length}
                                        </div>

                                        {iteration.changes.length ? (
                                            <ul style={{ margin: "6px 0 0 16px", padding: 0 }}>
                                                {iteration.changes.map(change => (
                                                    <li key={`${iteration.iteration}-${change.path}`}>
                                                        {change.path} · {change.status} · {change.bytes_written} bytes
                                                        {change.backup_path ? ` · backup: ${change.backup_path}` : ""}
                                                    </li>
                                                ))}
                                            </ul>
                                        ) : null}

                                        {iteration.test ? (
                                            <details style={{ marginTop: 8 }}>
                                                <summary style={{ cursor: "pointer" }}>
                                                    Teste {iteration.test.success ? "ok" : "falhou"} · {formatTime(iteration.test.duration_ms)}
                                                </summary>

                                                <div
                                                    style={{
                                                        marginTop: 8,
                                                        whiteSpace: "pre-wrap",
                                                        maxHeight: 180,
                                                        overflow: "auto"
                                                    }}
                                                >
                                                    <div>Return code: {iteration.test.return_code}</div>
                                                    <div style={{ marginTop: 6 }}>
                                                        STDOUT:
                                                    </div>
                                                    <pre style={{ whiteSpace: "pre-wrap", margin: 0 }}>
                                                        {iteration.test.stdout || "(vazio)"}
                                                    </pre>
                                                    <div style={{ marginTop: 6 }}>
                                                        STDERR:
                                                    </div>
                                                    <pre style={{ whiteSpace: "pre-wrap", margin: 0 }}>
                                                        {iteration.test.stderr || "(vazio)"}
                                                    </pre>
                                                </div>
                                            </details>
                                        ) : null}
                                    </div>
                                </details>
                            ))}
                        </div>
                    ) : null}
                </div>
            </details>

            <div
                style={{
                    padding: 12,
                    borderTop: "1px solid #333"
                }}
            >
                <textarea
                    rows={4}
                    value={prompt}
                    placeholder="Pergunte ao ClawAI..."
                    onChange={e => setPrompt(e.target.value)}
                    onKeyDown={e => {
                        if (e.key === "Enter" && !e.shiftKey) {
                            e.preventDefault();
                            void send();
                        }
                    }}
                    style={{
                        width: "100%",
                        resize: "none",
                        background: "#252526",
                        color: "#ddd",
                        border: "1px solid #444",
                        borderRadius: 6,
                        padding: 10,
                        boxSizing: "border-box"
                    }}
                />

                <button
                    onClick={() => void send()}
                    disabled={sending}
                    style={{
                        width: "100%",
                        marginTop: 10,
                        height: 36,
                        cursor: sending ? "wait" : "pointer",
                        opacity: sending ? 0.7 : 1
                    }}
                >
                    {sending ? "Enviando..." : "Enviar"}
                </button>
            </div>
        </div>
    );
}