import { useState } from "react";

type Message = {
    role: "user" | "assistant";
    text: string;
};

type Props = {
    onSend: (prompt: string) => void;
};

export default function ChatPanel({ onSend }: Props) {

    const [messages, setMessages] = useState<Message[]>([
        {
            role: "assistant",
            text: "Olá! Sou o ClawAI. Como posso ajudar?"
        }
    ]);

    const [prompt, setPrompt] = useState("");

    function send() {

        const text = prompt.trim();

        if (!text)
            return;

        setMessages(prev => [
            ...prev,
            {
                role: "user",
                text
            }
        ]);

        onSend(text);

        setPrompt("");

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

                {messages.map((m, i) => (

                    <div
                        key={i}
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
                            {m.role === "assistant"
                                ? "ClawAI"
                                : "Você"}
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
                            send();

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
                    onClick={send}
                    style={{
                        width: "100%",
                        marginTop: 10,
                        height: 36,
                        cursor: "pointer"
                    }}
                >
                    Enviar
                </button>

            </div>

        </div>

    );

}
