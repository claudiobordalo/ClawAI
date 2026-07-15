import { useState, useEffect, useRef } from "react";
import {
    FaFolderOpen,
    FaRobot,
    FaPaperPlane,
    FaTimes,
    FaChevronRight,
    FaChevronLeft,
    FaExclamationTriangle,
} from "react-icons/fa";
import { sendChat } from "../api";
import "../App.css";

// --- Types ---
type Message = {
    id: string;
    role: "user" | "assistant";
    content: string;
    loading?: boolean;
};

// --- Components ---

export default function AppShell() {
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [workspacePath, setWorkspacePath] = useState("D:\\ClawAI"); // Default path
    const [messages, setMessages] = useState<Message[]>([
        { id: "welcome", role: "assistant", content: "Olá! Sou a ClawAI. Como posso ajudar no seu projeto hoje?" }
    ]);
    const [input, setInput] = useState("");
    const [isProcessing, setIsProcessing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim() || isProcessing) return;

        const userMsg: Message = { id: Date.now().toString(), role: "user", content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput("");
        setIsProcessing(true);
        setError(null);

        // Add loading placeholder
        const loadingId = (Date.now() + 1).toString();
        setMessages(prev => [...prev, { id: loadingId, role: "assistant", content: "", loading: true }]);

        try {
            const response = await sendChat(userMsg.content);
            
            // Remove loading message
            setMessages(prev => prev.filter(m => m.id !== loadingId));
            
            // Add real response
            const assistantMsg: Message = {
                id: (Date.now() + 2).toString(),
                role: "assistant",
                content: response.answer
            };
            setMessages(prev => [...prev, assistantMsg]);
        } catch (err) {
            // Remove loading message on error
            setMessages(prev => prev.filter(m => m.id !== loadingId));
            
            setError(`Não foi possível conectar ao servidor ClawAI. Verifique se o backend está rodando em localhost:8000.`);
            
            const errorMsgObj: Message = {
                id: (Date.now() + 3).toString(),
                role: "assistant",
                content: "Desculpe, ocorreu um erro ao processar sua solicitação. Verifique a conexão com o backend."
            };
            setMessages(prev => [...prev, errorMsgObj]);
        } finally {
            setIsProcessing(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div style={{ 
            display: "flex", 
            height: "100vh", 
            background: "#0f0f0f", 
            color: "#e4e4e7", 
            fontFamily: "'Inter', 'Segoe UI', sans-serif",
            overflow: "hidden"
        }}>
            {/* Sidebar */}
            <div style={{
                width: sidebarOpen ? 260 : 0,
                background: "#18181b",
                borderRight: sidebarOpen ? "1px solid #27272a" : "none",
                transition: "all 0.3s ease",
                display: "flex",
                flexDirection: "column",
                overflow: "hidden",
                opacity: sidebarOpen ? 1 : 0
            }}>
                <div style={{ padding: 20, borderBottom: "1px solid #27272a" }}>
                    <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600, color: "#ffffff" }}>
                        ClawAI <span style={{ color: "#7c3aed" }}>Desktop</span>
                    </h2>
                </div>

                <div style={{ padding: 16, flex: 1 }}>
                    <div style={{ marginBottom: 16 }}>
                        <label style={{ display: "block", fontSize: 12, color: "#a1a1aa", marginBottom: 6 }}>
                            Workspace Root
                        </label>
                        <div style={{ 
                            display: "flex", 
                            gap: 8,
                            background: "#27272a",
                            borderRadius: 8,
                            padding: 4
                        }}>
                            <input 
                                value={workspacePath}
                                onChange={(e) => setWorkspacePath(e.target.value)}
                                style={{
                                    flex: 1,
                                    background: "transparent",
                                    border: "none",
                                    color: "#ffffff",
                                    padding: "6px 8px",
                                    fontSize: 13,
                                    outline: "none"
                                }}
                            />
                            <button 
                                onClick={() => alert("Funcionalidade de abrir pasta será implementada na próxima versão.")}
                                style={{
                                    background: "#3f3f46",
                                    border: "none",
                                    borderRadius: 6,
                                    color: "#ffffff",
                                    cursor: "pointer",
                                    padding: "0 8px"
                                }}
                            >
                                <FaFolderOpen />
                            </button>
                        </div>
                    </div>

                    <div style={{ fontSize: 12, color: "#71717a", textAlign: "center", marginTop: 20 }}>
                        <FaRobot size={24} style={{ marginBottom: 8, opacity: 0.5 }} />
                        <p>ClawAI Desktop v1.0</p>
                        <p>Arquitetura Proativa</p>
                    </div>
                </div>
            </div>

            {/* Main Chat Area */}
            <div style={{ flex: 1, display: "flex", flexDirection: "column", position: "relative" }}>
                {/* Header */}
                <div style={{
                    height: 56,
                    background: "#18181b",
                    borderBottom: "1px solid #27272a",
                    display: "flex",
                    alignItems: "center",
                    padding: "0 20px",
                    gap: 16
                }}>
                    <button 
                        onClick={() => setSidebarOpen(!sidebarOpen)}
                        style={{
                            background: "transparent",
                            border: "none",
                            color: "#a1a1aa",
                            cursor: "pointer",
                            fontSize: 18
                        }}
                    >
                        {sidebarOpen ? <FaChevronLeft /> : <FaChevronRight />}
                    </button>
                    <span style={{ fontWeight: 500, color: "#ffffff" }}>Nova Conversa</span>
                </div>

                {/* Messages */}
                <div style={{ flex: 1, overflow: "auto", padding: 20 }}>
                    {messages.map((msg) => (
                        <div key={msg.id} style={{
                            marginBottom: 24,
                            display: "flex",
                            gap: 12,
                            maxWidth: "800px",
                            margin: "0 auto"
                        }}>
                            <div style={{
                                width: 32,
                                height: 32,
                                borderRadius: "50%",
                                background: msg.role === "user" ? "#7c3aed" : "#27272a",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                fontSize: 14,
                                flexShrink: 0
                            }}>
                                {msg.role === "user" ? "U" : "AI"}
                            </div>
                            <div style={{ flex: 1 }}>
                                <div style={{ 
                                    background: msg.role === "user" ? "#27272a" : "#1e1e22", 
                                    padding: 16, 
                                    borderRadius: 12,
                                    lineHeight: 1.6,
                                    fontSize: 15
                                }}>
                                    {msg.loading ? (
                                        <div style={{ display: "flex", gap: 4 }}>
                                            <div style={{ width: 8, height: 8, background: "#7c3aed", borderRadius: "50%", animation: "pulse 1s infinite" }} />
                                            <div style={{ width: 8, height: 8, background: "#7c3aed", borderRadius: "50%", animation: "pulse 1s infinite 0.2s" }} />
                                            <div style={{ width: 8, height: 8, background: "#7c3aed", borderRadius: "50%", animation: "pulse 1s infinite 0.4s" }} />
                                        </div>
                                    ) : (
                                        msg.content
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <div style={{
                    padding: 20,
                    background: "#18181b",
                    borderTop: "1px solid #27272a"
                }}>
                    <div style={{
                        maxWidth: "800px",
                        margin: "0 auto",
                        position: "relative"
                    }}>
                        <textarea
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Digite sua mensagem..."
                            rows={1}
                            style={{
                                width: "100%",
                                background: "#27272a",
                                border: "1px solid #3f3f46",
                                borderRadius: 12,
                                padding: "16px 50px 16px 16px",
                                color: "#ffffff",
                                fontSize: 15,
                                resize: "none",
                                outline: "none",
                                fontFamily: "inherit",
                                boxSizing: "border-box"
                            }}
                        />
                        <button
                            onClick={handleSend}
                            disabled={!input.trim() || isProcessing}
                            style={{
                                position: "absolute",
                                right: 12,
                                top: "50%",
                                transform: "translateY(-50%)",
                                background: input.trim() && !isProcessing ? "#7c3aed" : "#3f3f46",
                                border: "none",
                                borderRadius: 8,
                                width: 32,
                                height: 32,
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                cursor: input.trim() && !isProcessing ? "pointer" : "not-allowed",
                                color: "#ffffff"
                            }}
                        >
                            <FaPaperPlane />
                        </button>
                    </div>
                </div>
            </div>

            {/* Error Toast */}
            {error && (
                <div style={{
                    position: "fixed",
                    bottom: 20,
                    right: 20,
                    background: "#27272a",
                    border: "1px solid #ef4444",
                    borderRadius: 12,
                    padding: 16,
                    maxWidth: 400,
                    boxShadow: "0 10px 30px rgba(0,0,0,0.5)"
                }}>
                    <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
                        <FaExclamationTriangle style={{ color: "#ef4444", marginTop: 2 }} />
                        <div style={{ flex: 1 }}>
                            <div style={{ fontWeight: 600, color: "#ef4444", marginBottom: 4 }}>Erro de Conexão</div>
                            <div style={{ fontSize: 13, color: "#a1a1aa" }}>{error}</div>
                        </div>
                        <button 
                            onClick={() => setError(null)}
                            style={{ background: "transparent", border: "none", color: "#a1a1aa", cursor: "pointer" }}
                        >
                            <FaTimes />
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
