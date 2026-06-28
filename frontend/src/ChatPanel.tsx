import { useEffect, useRef, useState } from "react";
import { streamChat, type ChatReply } from "./api";

type Message = {
    id: number;
    role: "user" | "assistant";
    text: string;
    reply?: ChatReply;
};

function formatTime(ms: number): string {
    if (ms < 1000) {
        return `${Math.round(ms)} ms`;
    }

    return `${(ms / 1000).toFixed(2)} s`;
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

    const timerRef = useRef<number | null>(null);
    const startedAtRef = useRef(0);
    const nextIdRef = useRef(2);

    useEffect(() => {
        return () => {
            if (timerRef.current !== null) {
                window.clearInterval(timerRef.current);
            }
        };
    }, []);

    function stopTimer() {
        if (timerRef.current !== null) {
            window.clearInterval(timerRef.current);
            timerRef.current = null;
        }
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

        let streamedAnswer = "";
        let streamStarted = false;

        try {
            const reply = await streamChat(
                text,
                (chunk) => {
                    if (!streamStarted) {
                        streamStarted = true;
                        stopTimer();
                    }

                    streamedAnswer += chunk;

                    setMessages(prev =>
                        prev.map(message =>
                            message.id === assistantId
                                ? {
                                    ...message,
                                    text: streamedAnswer
                                }
                                : message
                        )
                    );
                }
            );

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

                        {m.role === "assistant" && m.reply ? (
                            <div
                                style={{
                                    marginTop: 6,
                                    fontSize: 11,
                                    color: "#9aa0a6",
                                    lineHeight: 1.45
                                }}
                            >
                                <div>
                                    Provider: {m.reply.provider} · Modelo: {m.reply.model}
                                </div>
                                <div>
                                    Memória: {m.reply.used_memory ? "sim" : "não"} · Conhecimento: {m.reply.used_knowledge ? "sim" : "não"} · Web: {m.reply.requires_web ? "sim" : "não"}
                                </div>
                                <div>
                                    Memória salva: {m.reply.memory_saved ? "sim" : "não"}
                                </div>
                                <div>
                                    Busca memória: {formatTime(m.reply.timings.search.memory_ms)}
                                </div>
                                <div>
                                    Busca conhecimento: {formatTime(m.reply.timings.search.knowledge_ms)}
                                </div>
                                <div>
                                    Construção do prompt: {formatTime(m.reply.timings.search.prompt_ms)}
                                </div>
                                <div>
                                    Busca total: {formatTime(m.reply.timings.search.total_ms)}
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