import { useState, useEffect, useCallback } from "react";
import {
    FaFolderOpen,
    FaRobot,
    FaPaperPlane,
    FaCode,
    FaTerminal,
    FaCodeBranch,
    FaBrain,
    FaGear,
    FaListCheck,
    FaMicrochip,
    FaDatabase,
    FaSitemap,
    FaChevronRight,
    FaChevronLeft,
    FaWindowMaximize,
    FaWindowMinimize,
    FaXmark,
    FaFolder,
    FaFileCode,
    FaFileLines,
    FaImage,
    FaFile,
    FaMagnifyingGlass,
    FaPlay,
    FaStop,
    FaRotateRight,
    FaFloppyDisk,
    FaChevronDown,
    FaChevronUp,
    FaCogs,
    FaSpinner,
    FaCircleInfo,
} from "react-icons/fa6";
import { sendChat } from "../api";
import { loadTree } from "../api";
import type { TreeNode } from "../tree";
import "../App.css";

// --- Types ---
type Message = {
    id: string;
    role: "user" | "assistant";
    content: string;
    loading?: boolean;
};

type TabId =
    | "chat"
    | "explorer"
    | "editor"
    | "terminal"
    | "git"
    | "planner"
    | "memory"
    | "agents"
    | "tools"
    | "settings"
    | "monitor"
    | "models";

interface Tab {
    id: TabId;
    label: string;
    icon: React.ReactNode;
    disabled?: boolean;
}

// --- Constants ---
const TABS: Tab[] = [
    { id: "chat", label: "Chat", icon: <FaRobot /> },
    { id: "explorer", label: "Workspace", icon: <FaSitemap /> },
    { id: "editor", label: "Editor", icon: <FaCode /> },
    { id: "terminal", label: "Terminal", icon: <FaTerminal /> },
    { id: "git", label: "Git", icon: <FaCodeBranch /> },
    { id: "planner", label: "Planner", icon: <FaListCheck /> },
    { id: "memory", label: "Memory", icon: <FaBrain /> },
    { id: "agents", label: "Agents", icon: <FaGear /> },
    { id: "tools", label: "Tools", icon: <FaGear /> },
    { id: "models", label: "Models", icon: <FaDatabase /> },
    { id: "monitor", label: "Monitor", icon: <FaMicrochip /> },
    { id: "settings", label: "Settings", icon: <FaGear /> },
];

// --- Helper: icon for file type ---
function FileIcon({ name }: { name: string }) {
    const ext = name.split(".").pop()?.toLowerCase();
    if (["ts", "tsx", "js", "jsx", "py", "html", "css", "json", "yaml", "yml", "md", "txt", "sh", "bat"].includes(ext || ""))
        return <FaFileCode size={14} style={{ color: "#7dd3fc" }} />;
    if (["png", "jpg", "jpeg", "gif", "svg", "webp"].includes(ext || ""))
        return <FaImage size={14} style={{ color: "#a78bfa" }} />;
    if (["md", "txt", "pdf"].includes(ext || ""))
        return <FaFileLines size={14} style={{ color: "#fbbf24" }} />;
    return <FaFile size={14} style={{ color: "#71717a" }} />;
}

// --- Main AppShell ---
export default function AppShell() {
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [activeTab, setActiveTab] = useState<TabId>("chat");
    const [messages, setMessages] = useState<Message[]>([
        { id: "welcome", role: "assistant", content: "Olá! Sou a **ClawAI**. Como posso ajudar no seu projeto hoje?" },
    ]);
    const [input, setInput] = useState("");
    const [isProcessing, setIsProcessing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [tree, setTree] = useState<TreeNode[]>([]);
    const [selectedFile, setSelectedFile] = useState<string | null>(null);
    const [fileContent, setFileContent] = useState("");
    const [sidebarWidth, setSidebarWidth] = useState(280);
    const [isDragging, setIsDragging] = useState(false);
    const [workspacePath, setWorkspacePath] = useState("");
    const [health, setHealth] = useState<{ status: string; vision: string; coder: string; reasoning: string } | null>(null);

    // --- Health check ---
    useEffect(() => {
        const checkHealth = async () => {
            try {
                const res = await fetch("http://127.0.0.1:8000/health");
                const data = await res.json();
                setHealth(data);
            } catch {
                setHealth(null);
            }
        };
        checkHealth();
        const interval = setInterval(checkHealth, 10000);
        return () => clearInterval(interval);
    }, []);

    // --- Tree load ---
    useEffect(() => {
        if (activeTab === "explorer" && workspacePath) {
            loadTree("", undefined).then((t) => setTree(t)).catch(() => {});
        }
    }, [activeTab, workspacePath]);

    // --- Send chat ---
    const handleSend = useCallback(async () => {
        if (!input.trim() || isProcessing) return;
        const userMsg: Message = { id: Date.now().toString(), role: "user", content: input };
        setMessages((prev) => [...prev, userMsg]);
        setInput("");
        setIsProcessing(true);
        setError(null);

        const loadingId = (Date.now() + 1).toString();
        setMessages((prev) => [...prev, { id: loadingId, role: "assistant", content: "", loading: true }]);

        try {
            const response = await sendChat(userMsg.content);
            setMessages((prev) => prev.filter((m) => m.id !== loadingId));
            const assistantMsg: Message = {
                id: (Date.now() + 2).toString(),
                role: "assistant",
                content: response.answer,
            };
            setMessages((prev) => [...prev, assistantMsg]);
        } catch (err: any) {
            setMessages((prev) => prev.filter((m) => m.id !== loadingId));
            setError("Não foi possível conectar ao servidor ClawAI.");
            setMessages((prev) => [
                ...prev,
                { id: (Date.now() + 3).toString(), role: "assistant", content: "Erro ao processar a solicitação." },
            ]);
        } finally {
            setIsProcessing(false);
        }
    }, [input, isProcessing]);

    // --- Drag resize ---
    useEffect(() => {
        if (!isDragging) return;
        const onMove = (e: MouseEvent) => {
            setSidebarWidth(Math.max(200, Math.min(500, e.clientX - 60)));
        };
        const onUp = () => setIsDragging(false);
        window.addEventListener("mousemove", onMove);
        window.addEventListener("mouseup", onUp);
        return () => {
            window.removeEventListener("mousemove", onMove);
        };
    }, [isDragging]);

    // --- File open ---
    const handleFileClick = async (node: TreeNode) => {
        if (!node.directory) {
            setSelectedFile(node.name);
            try {
                const content = await fetch(`http://127.0.0.1:8000/api/file?path=${encodeURIComponent(node.path)}`).then((r) => r.text());
                setFileContent(content);
            } catch {
                setFileContent("// Erro ao ler arquivo");
            }
            setActiveTab("editor");
        }
    };

    // --- Render content per tab ---
    const renderContent = () => {
        switch (activeTab) {
            case "chat":
                return <ChatPanel messages={messages} input={input} setInput={setInput} handleSend={handleSend} isProcessing={isProcessing} />;
            case "explorer":
                return <ExplorerPanel tree={tree} onFileClick={handleFileClick} workspacePath={workspacePath} setWorkspacePath={setWorkspacePath} />;
            case "editor":
                return <EditorPanel selectedFile={selectedFile} fileContent={fileContent} setFileContent={setFileContent} />;
            case "terminal":
                return <TerminalPanel />;
            case "git":
                return <GitPanel />;
            case "planner":
                return <PlannerPanel />;
            case "memory":
                return <MemoryPanel />;
            case "agents":
                return <AgentsPanel />;
            case "tools":
                return <ToolsPanel />;
            case "models":
                return <ModelsPanel health={health} />;
            case "monitor":
                return <MonitorPanel />;
            case "settings":
                return <SettingsPanel />;
            default:
                return <ChatPanel messages={messages} input={input} setInput={setInput} handleSend={handleSend} isProcessing={isProcessing} />;
        }
    };

    return (
        <div style={{ display: "flex", height: "100vh", background: "#0a0a0a", color: "#e4e4e7", fontFamily: "'Inter', 'Segoe UI', system-ui, sans-serif", overflow: "hidden" }}>
            {/* Left Sidebar */}
            <div
                style={{
                    width: sidebarOpen ? sidebarWidth : 0,
                    background: "#111113",
                    borderRight: sidebarOpen ? "1px solid #1e1e22" : "none",
                    transition: "width 0.2s ease",
                    display: "flex",
                    flexDirection: "column",
                    overflow: "hidden",
                    flexShrink: 0,
                }}
            >
                {/* Logo */}
                <div
                    style={{
                        padding: "16px 20px",
                        borderBottom: "1px solid #1e1e22",
                        display: "flex",
                        alignItems: "center",
                        gap: 10,
                    }}
                >
                    <div style={{ width: 28, height: 28, borderRadius: 8, background: "linear-gradient(135deg, #7c3aed, #a855f7)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                        <span style={{ color: "#fff", fontSize: 16, fontWeight: 700 }}>C</span>
                    </div>
                    <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 14, fontWeight: 600, color: "#fff" }}>ClawAI</div>
                        <div style={{ fontSize: 10, color: "#71717a" }}>Studio</div>
                    </div>
                    <button
                        onClick={() => setSidebarOpen(false)}
                        style={{ background: "transparent", border: "none", color: "#71717a", cursor: "pointer", padding: 4 }}
                    >
                        <FaChevronLeft size={14} />
                    </button>
                </div>

                {/* Tabs */}
                <div style={{ flex: 1, overflowY: "auto", padding: "8px 0" }}>
                    {TABS.map((tab) => (
                        <div
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            style={{
                                display: "flex",
                                alignItems: "center",
                                gap: 10,
                                padding: "8px 20px",
                                cursor: "pointer",
                                background: activeTab === tab.id ? "#1e1e22" : "transparent",
                                borderLeft: activeTab === tab.id ? "2px solid #7c3aed" : "2px solid transparent",
                                color: activeTab === tab.id ? "#a78bfa" : "#a1a1aa",
                                fontSize: 13,
                                fontWeight: activeTab === tab.id ? 500 : 400,
                                transition: "all 0.15s ease",
                            }}
                            onMouseEnter={(e) => {
                                if (activeTab !== tab.id) e.currentTarget.style.color = "#e4e4e7";
                            }}
                            onMouseLeave={(e) => {
                                if (activeTab !== tab.id) e.currentTarget.style.color = "#a1a1aa";
                            }}
                        >
                            {tab.icon}
                            <span>{tab.label}</span>
                        </div>
                    ))}
                </div>

                {/* Health indicator */}
                <div style={{ padding: "12px 20px", borderTop: "1px solid #1e1e22" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11, color: "#71717a" }}>
                        <div
                            style={{
                                width: 8,
                                height: 8,
                                borderRadius: "50%",
                                background: health ? "#22c55e" : "#ef4444",
                            }}
                        />
                        <span>{health ? "Online" : "Offline"}</span>
                    </div>
                    {health && (
                        <div style={{ fontSize: 10, color: "#52525b", marginTop: 4 }}>
                            Vision: {health.vision}
                        </div>
                    )}
                </div>
            </div>
                    )}
                </div>
            </div>

            {/* Resize handle */}
            {sidebarOpen && (
                <div
                    onMouseDown={() => setIsDragging(true)}
                    style={{
                        width: 4,
                        cursor: "col-resize",
                        background: "transparent",
                        flexShrink: 0,
                    }}
                />
            )}

            {/* Main Content */}
            <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
                {/* Top Bar */}
                <div
                    style={{
                        height: 48,
                        background: "#111113",
                        borderBottom: "1px solid #1e1e22",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        padding: "0 16px",
                        flexShrink: 0,
                    }}
                >
                    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                        {!sidebarOpen && (
                            <button
                                onClick={() => setSidebarOpen(true)}
                                style={{ background: "transparent", border: "none", color: "#a1a1aa", cursor: "pointer", padding: "4px 6px", borderRadius: 4 }}
                            >
                                <FaChevronRight size={14} />
                            </button>
                        )}
                        <span style={{ fontSize: 13, color: "#71717a" }}>
                            {TABS.find((t) => t.id === activeTab)?.label || "ClawAI"}
                        </span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <div style={{ width: 12, height: 12, borderRadius: "50%", background: "#3f3f46", display: "flex", alignItems: "center", justifyContent: "center" }}>
                            <FaWindowMinimize size={8} style={{ color: "#71717a" }} />
                        </div>
                        <div style={{ width: 12, height: 12, borderRadius: "50%", background: "#3f3f46", display: "flex", alignItems: "center", justifyContent: "center" }}>
                            <FaWindowMaximize size={8} style={{ color: "#71717a" }} />
                        </div>
                        <div style={{ width: 12, height: 12, borderRadius: "50%", background: "#ef4444", display: "flex", alignItems: "center", justifyContent: "center" }}>
                            <FaXmark size={7} style={{ color: "#fff" }} />
                        </div>
                    </div>
                </div>

                {/* Tab content */}
                <div style={{ flex: 1, overflow: "hidden" }}>{renderContent()}</div>
            </div>

            {/* Error toast */}
            {error && (
                <div style={{ position: "fixed", bottom: 20, right: 20, background: "#1e1e22", border: "1px solid #ef4444", borderRadius: 12, padding: "12px 16px", maxWidth: 400, boxShadow: "0 10px 30px rgba(0,0,0,0.5)", zIndex: 1000 }}>
                    <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                        <FaCircleInfo style={{ color: "#ef4444", marginTop: 2 }} />
                        <div style={{ flex: 1, fontSize: 13, color: "#a1a1aa" }}>{error}</div>
                        <button onClick={() => setError(null)} style={{ background: "transparent", border: "none", color: "#71717a", cursor: "pointer" }}>
                            <FaXmark size={14} />
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

// --- Chat Panel ---
function ChatPanel({
    messages,
    input,
    setInput,
    handleSend,
    isProcessing,
}: {
    messages: Message[];
    input: string;
    setInput: (v: string) => void;
    handleSend: () => void;
    isProcessing: boolean;
}) {
    return (
        <div style={{ display: "flex", flexDirection: "column", height: "100%", background: "#0a0a0a" }}>
            <div style={{ flex: 1, overflow: "auto", padding: "24px 16px" }}>
                <div style={{ maxWidth: 800, margin: "0 auto" }}>
                    {messages.map((msg) => (
                        <div key={msg.id} style={{ marginBottom: 20, display: "flex", gap: 12 }}>
                            <div
                                style={{
                                    width: 32,
                                    height: 32,
                                    borderRadius: "50%",
                                    background: msg.role === "user" ? "#7c3aed" : "#1e1e22",
                                    display: "flex",
                                    alignItems: "center",
                                    justifyContent: "center",
                                    fontSize: 13,
                                    color: "#fff",
                                    flexShrink: 0,
                                    border: msg.role === "user" ? "none" : "1px solid #27272a",
                                }}
                            >
                                {msg.role === "user" ? "U" : "AI"}
                            </div>
                            <div style={{ flex: 1 }}>
                                <div
                                    style={{
                                        background: msg.role === "user" ? "#1e1e22" : "#0f0f11",
                                        padding: 14,
                                        borderRadius: 12,
                                        lineHeight: 1.6,
                                        fontSize: 14,
                                        border: msg.role === "user" ? "none" : "1px solid #1e1e22",
                                        whiteSpace: "pre-wrap",
                                    }}
                                >
                                    {msg.loading ? (
                                        <div style={{ display: "flex", gap: 4 }}>
                                            {[0, 1, 2].map((i) => (
                                                <div
                                                    key={i}
                                                    style={{
                                                        width: 6,
                                                        height: 6,
                                                        background: "#7c3aed",
                                                        borderRadius: "50%",
                                                        animation: `pulse 1s infinite ${i * 0.2}s`,
                                                    }}
                                                />
                                            ))}
                                        </div>
                                    ) : (
                                        msg.content
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
            <div style={{ padding: "16px", background: "#111113", borderTop: "1px solid #1e1e22" }}>
                <div style={{ maxWidth: 800, margin: "0 auto", position: "relative" }}>
                    <textarea
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === "Enter" && !e.shiftKey) {
                                e.preventDefault();
                                handleSend();
                            }
                        }}
                        placeholder="Digite sua mensagem..."
                        rows={1}
                        style={{
                            width: "100%",
                            background: "#1e1e22",
                            border: "1px solid #27272a",
                            borderRadius: 12,
                            padding: "14px 50px 14px 16px",
                            color: "#fff",
                            fontSize: 14,
                            resize: "none",
                            outline: "none",
                            fontFamily: "inherit",
                            boxSizing: "border-box",
                        }}
                    />
                    <button
                        onClick={handleSend}
                        disabled={!input.trim() || isProcessing}
                        style={{
                            position: "absolute",
                            right: 10,
                            top: "50%",
                            transform: "translateY(-50%)",
                            background: input.trim() && !isProcessing ? "#7c3aed" : "#27272a",
                            border: "none",
                            borderRadius: 8,
                            width: 32,
                            height: 32,
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            cursor: input.trim() && !isProcessing ? "pointer" : "not-allowed",
                            color: "#fff",
                        }}
                    >
                        <FaPaperPlane size={14} />
                    </button>
                </div>
            </div>
        </div>
    );
}

// --- Explorer Panel ---
function ExplorerPanel({
    tree,
    onFileClick,
    workspacePath,
    setWorkspacePath,
}: {
    tree: TreeNode[];
    onFileClick: (node: TreeNode) => void;
    workspacePath: string;
    setWorkspacePath: (v: string) => void;
}) {
    const [expanded, setExpanded] = useState<Set<string>>(new Set());

    const toggle = (path: string) => {
        setExpanded((prev) => {
            const next = new Set(prev);
            if (next.has(path)) next.delete(path);
            else next.add(path);
            return next;
        });
    };

    const renderNode = (node: TreeNode, depth: number) => {
        const isExpanded = expanded.has(node.path);
        const paddingLeft = depth * 16 + 12;

        if (node.type === "directory") {
            return (
                <div key={node.path}>
                    <div
                        onClick={() => toggle(node.path)}
                        style={{
                            display: "flex",
                            alignItems: "center",
                            gap: 8,
                            padding: "4px 8px",
                            cursor: "pointer",
                            fontSize: 13,
                            color: "#a1a1aa",
                            marginLeft: paddingLeft,
                        }}
                        onMouseEnter={(e) => (e.currentTarget.style.background = "#1e1e22")}
                        onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                    >
                        {isExpanded ? <FaChevronDown size={12} /> : <FaChevronRight size={12} />}
                        <FaFolder size={14} style={{ color: "#fbbf24" }} />
                        <span>{node.name}</span>
                    </div>
                    {isExpanded &&
                        (node.children || []).map((child) => renderNode(child, depth + 1))}
                </div>
            );
        }

        return (
            <div
                key={node.path}
                onClick={() => onFileClick(node)}
                style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    padding: "4px 8px",
                    cursor: "pointer",
                    fontSize: 13,
                    color: "#a1a1aa",
                    marginLeft: paddingLeft,
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = "#1e1e22")}
                onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
            >
                <span style={{ width: 12 }} />
                <FileIcon name={node.name} />
                <span>{node.name}</span>
            </div>
        );
    };

    return (
        <div style={{ display: "flex", height: "100%", background: "#0a0a0a" }}>
            {/* File tree */}
            <div style={{ width: 260, borderRight: "1px solid #1e1e22", overflowY: "auto", padding: "8px 0" }}>
                <div style={{ padding: "8px 16px", fontSize: 11, color: "#71717a", textTransform: "uppercase", letterSpacing: 1 }}>
                    Explorer
                </div>
                {workspacePath && (
                    <div style={{ padding: "4px 16px", fontSize: 12, color: "#a78bfa", marginBottom: 8, display: "flex", alignItems: "center", gap: 6 }}>
                        <FaFolderOpen size={12} />
                        {workspacePath}
                    </div>
                )}
                {tree.map((node) => renderNode(node, 0))}
            </div>
            {/* Empty state */}
            <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "#52525b" }}>
                <div style={{ textAlign: "center" }}>
                    <FaSitemap size={48} style={{ marginBottom: 16, opacity: 0.3 }} />
                    <div style={{ fontSize: 14 }}>Selecione um arquivo para visualizar</div>
                </div>
            </div>
        </div>
    );
}

// --- Editor Panel ---
function EditorPanel({
    selectedFile,
    fileContent,
    setFileContent,
}: {
    selectedFile: string | null;
    fileContent: string;
    setFileContent: (v: string) => void;
}) {
    const [lineCount] = useState(1);

    return (
        <div style={{ display: "flex", height: "100%", background: "#0a0a0a" }}>
            {/* Line numbers */}
            <div
                style={{
                    width: 56,
                    background: "#0f0f11",
                    borderRight: "1px solid #1e1e22",
                    padding: "16px 8px",
                    textAlign: "right",
                    fontSize: 13,
                    fontFamily: "'Cascadia Code', 'Fira Code', monospace",
                    color: "#52525b",
                    overflow: "hidden",
                    userSelect: "none",
                }}
            >
                {Array.from({ length: Math.max(1, fileContent.split("\n").length) }, (_, i) => (
                    <div key={i} style={{ lineHeight: "22px" }}>
                        {i + 1}
                    </div>
                ))}
            </div>
            {/* Editor */}
            <textarea
                value={fileContent}
                onChange={(e) => setFileContent(e.target.value)}
                spellCheck={false}
                style={{
                    flex: 1,
                    background: "#0a0a0a",
                    color: "#e4e4e7",
                    border: "none",
                    outline: "none",
                    padding: "16px",
                    fontSize: 14,
                    fontFamily: "'Cascadia Code', 'Fira Code', monospace",
                    lineHeight: "22px",
                    resize: "none",
                    tabSize: 4,
                }}
            />
            {/* Toolbar */}
            <div style={{ width: 60, background: "#111113", borderLeft: "1px solid #1e1e22", display: "flex", flexDirection: "column", alignItems: "center", padding: "8px 0", gap: 4 }}>
                <button title="Salvar" style={{ background: "transparent", border: "none", color: "#71717a", cursor: "pointer", padding: 6, borderRadius: 4 }} onMouseEnter={(e) => (e.currentTarget.style.color = "#fff")} onMouseLeave={(e) => (e.currentTarget.style.color = "#71717a")}>
                    <FaFloppyDisk size={14} />
                </button>
                <button title="Desfazer" style={{ background: "transparent", border: "none", color: "#71717a", cursor: "pointer", padding: 6, borderRadius: 4 }} onMouseEnter={(e) => (e.currentTarget.style.color = "#fff")} onMouseLeave={(e) => (e.currentTarget.style.color = "#71717a")}>
                    <FaRotateRight size={14} />
                </button>
            </div>
        </div>
    );
}

// --- Terminal Panel ---
function TerminalPanel() {
    return (
        <div style={{ height: "100%", background: "#0a0a0a", display: "flex", flexDirection: "column" }}>
            {/* Terminal header */}
            <div style={{ padding: "8px 16px", background: "#111113", borderBottom: "1px solid #1e1e22", display: "flex", alignItems: "center", gap: 8 }}>
                <FaTerminal size={12} style={{ color: "#71717a" }} />
                <span style={{ fontSize: 12, color: "#71717a" }}>Terminal</span>
            </div>
            {/* Terminal body */}
            <div style={{ flex: 1, padding: 16, fontFamily: "'Cascadia Code', 'Fira Code', monospace", fontSize: 13, color: "#a1a1aa", overflowY: "auto" }}>
                <div style={{ color: "#22c55e" }}>ClawAI@studio</div>
                <div style={{ marginBottom: 8 }}>$ <span style={{ color: "#e4e4e7" }}>ps aux | grep clawai</span></div>
                <div style={{ color: "#71717a", marginBottom: 16 }}>uvicorn main:app --host 127.0.0.1 --port 8000</div>
                <div style={{ color: "#22c55e" }}>ClawAI@studio</div>
                <div>$ <span className="typing-cursor" style={{ color: "#e4e4e7" }}>_</span></div>
            </div>
        </div>
    );
}

// --- Git Panel ---
function GitPanel() {
    return (
        <div style={{ height: "100%", background: "#0a0a0a", display: "flex", flexDirection: "column" }}>
            <div style={{ padding: "8px 16px", background: "#111113", borderBottom: "1px solid #1e1e22", display: "flex", alignItems: "center", gap: 8 }}>
                <FaCodeBranch size={12} style={{ color: "#71717a" }} />
                <span style={{ fontSize: 12, color: "#71717a" }}>Git</span>
            </div>
            <div style={{ flex: 1, padding: 24, display: "flex", alignItems: "center", justifyContent: "center", color: "#52525b" }}>
                <div style={{ textAlign: "center" }}>
                    <FaCodeBranch size={48} style={{ marginBottom: 16, opacity: 0.3 }} />
                    <div style={{ fontSize: 14 }}>Integração Git em desenvolvimento</div>
                    <div style={{ fontSize: 12, marginTop: 8, color: "#3f3f46" }}>Branches, commits e diffs serão exibidos aqui</div>
                </div>
            </div>
        </div>
    );
}

// --- Planner Panel ---
function PlannerPanel() {
    return (
        <div style={{ height: "100%", background: "#0a0a0a", display: "flex", flexDirection: "column" }}>
            <div style={{ padding: "8px 16px", background: "#111113", borderBottom: "1px solid #1e1e22", display: "flex", alignItems: "center", gap: 8 }}>
                <FaListCheck size={12} style={{ color: "#71717a" }} />
                <span style={{ fontSize: 12, color: "#71717a" }}>Planner</span>
            </div>
            <div style={{ flex: 1, padding: 24, display: "flex", alignItems: "center", justifyContent: "center", color: "#52525b" }}>
                <div style={{ textAlign: "center" }}>
                    <FaListCheck size={48} style={{ marginBottom: 16, opacity: 0.3 }} />
                    <div style={{ fontSize: 14 }}>Planejador de tarefas</div>
                    <div style={{ fontSize: 12, marginTop: 8, color: "#3f3f46" }}>Criar e gerenciar tarefas do projeto</div>
                </div>
            </div>
        </div>
    );
}

// --- Memory Panel ---
function MemoryPanel() {
    return (
        <div style={{ height: "100%", background: "#0a0a0a", display: "flex", flexDirection: "column" }}>
            <div style={{ padding: "8px 16px", background: "#111113", borderBottom: "1px solid #1e1e22", display: "flex", alignItems: "center", gap: 8 }}>
                <FaBrain size={12} style={{ color: "#71717a" }} />
                <span style={{ fontSize: 12, color: "#71717a" }}>Memory</span>
            </div>
            <div style={{ flex: 1, padding: 24, display: "flex", alignItems: "center", justifyContent: "center", color: "#52525b" }}>
                <div style={{ textAlign: "center" }}>
                    <FaBrain size={48} style={{ marginBottom: 16, opacity: 0.3 }} />
                    <div style={{ fontSize: 14 }}>Memória do sistema</div>
                    <div style={{ fontSize: 12, marginTop: 8, color: "#3f3f46" }}>Conhecimento e contexto carregados</div>
                </div>
            </div>
        </div>
    );
}

// --- Agents Panel ---
function AgentsPanel() {
    return (
        <div style={{ height: "100%", background: "#0a0a0a", display: "flex", flexDirection: "column" }}>
            <div style={{ padding: "8px 16px", background: "#111113", borderBottom: "1px solid #1e1e22", display: "flex", alignItems: "center", gap: 8 }}>
                <FaGear size={12} style={{ color: "#71717a" }} />
                <span style={{ fontSize: 12, color: "#71717a" }}>Agents</span>
            </div>
            <div style={{ flex: 1, padding: 24, display: "flex", alignItems: "center", justifyContent: "center", color: "#52525b" }}>
                <div style={{ textAlign: "center" }}>
                    <FaGear size={48} style={{ marginBottom: 16, opacity: 0.3 }} />
                    <div style={{ fontSize: 14 }}>Gerenciador de Agentes</div>
                    <div style={{ fontSize: 12, marginTop: 8, color: "#3f3f46" }}>Configurar e monitorar agentes autônomos</div>
                </div>
            </div>
        </div>
    );
}

// --- Tools Panel ---
function ToolsPanel() {
    return (
        <div style={{ height: "100%", background: "#0a0a0a", display: "flex", flexDirection: "column" }}>
            <div style={{ padding: "8px 16px", background: "#111113", borderBottom: "1px solid #1e1e22", display: "flex", alignItems: "center", gap: 8 }}>
                <FaCogs size={12} style={{ color: "#71717a" }} />
                <span style={{ fontSize: 12, color: "#71717a" }}>Tools</span>
            </div>
            <div style={{ flex: 1, padding: 24, display: "flex", alignItems: "center", justifyContent: "center", color: "#52525b" }}>
                <div style={{ textAlign: "center" }}>
                    <FaCogs size={48} style={{ marginBottom: 16, opacity: 0.3 }} />
                    <div style={{ fontSize: 14 }}>Ferramentas</div>
                    <div style={{ fontSize: 12, marginTop: 8, color: "#3f3f46" }}>Gerenciar ferramentas e integrações</div>
                </div>
            </div>
        </div>
    );
}

// --- Models Panel ---
function ModelsPanel({ health }: { health: any }) {
    return (
        <div style={{ height: "100%", background: "#0a0a0a", display: "flex", flexDirection: "column" }}>
            <div style={{ padding: "8px 16px", background: "#111113", borderBottom: "1px solid #1e1e22", display: "flex", alignItems: "center", gap: 8 }}>
                <FaDatabase size={12} style={{ color: "#71717a" }} />
                <span style={{ fontSize: 12, color: "#71717a" }}>Models</span>
            </div>
            <div style={{ flex: 1, padding: 24, overflowY: "auto" }}>
                <div style={{ maxWidth: 600, margin: "0 auto" }}>
                    <h3 style={{ fontSize: 16, fontWeight: 600, color: "#fff", marginBottom: 16 }}>Modelos de IA</h3>
                    {health ? (
                        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                            {[
                                { name: "Vision", model: health.vision, status: "online" },
                                { name: "Coder", model: health.coder, status: "online" },
                                { name: "Reasoning", model: health.reasoning, status: "online" },
                            ].map((m) => (
                                <div key={m.name} style={{ background: "#111113", border: "1px solid #1e1e22", borderRadius: 12, padding: 16, display: "flex", alignItems: "center", gap: 16 }}>
                                    <div style={{ width: 40, height: 40, borderRadius: 10, background: "#1e1e22", display: "flex", alignItems: "center", justifyContent: "center" }}>
                                        <FaDatabase size={18} style={{ color: "#7c3aed" }} />
                                    </div>
                                    <div style={{ flex: 1 }}>
                                        <div style={{ fontSize: 14, fontWeight: 500, color: "#fff" }}>{m.name}</div>
                                        <div style={{ fontSize: 12, color: "#71717a" }}>{m.model}</div>
                                    </div>
                                    <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "#22c55e" }}>
                                        <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#22c55e" }} />
                                        Online
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div style={{ textAlign: "center", padding: 40, color: "#52525b" }}>
                            <FaDatabase size={48} style={{ marginBottom: 16, opacity: 0.3 }} />
                            <div>Nenhum modelo detectado</div>
                            <div style={{ fontSize: 12, marginTop: 8, color: "#3f3f46" }}>Verifique se LM Studio ou Ollama está rodando</div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

// --- Monitor Panel ---
function MonitorPanel() {
    return (
        <div style={{ height: "100%", background: "#0a0a0a", display: "flex", flexDirection: "column" }}>
            <div style={{ padding: "8px 16px", background: "#111113", borderBottom: "1px solid #1e1e22", display: "flex", alignItems: "center", gap: 8 }}>
                <FaMicrochip size={12} style={{ color: "#71717a" }} />
                <span style={{ fontSize: 12, color: "#71717a" }}>Monitor</span>
            </div>
            <div style={{ flex: 1, padding: 24, display: "flex", alignItems: "center", justifyContent: "center", color: "#52525b" }}>
                <div style={{ textAlign: "center" }}>
                    <FaMicrochip size={48} style={{ marginBottom: 16, opacity: 0.3 }} />
                    <div style={{ fontSize: 14 }}>Monitor de Recursos</div>
                    <div style={{ fontSize: 12, marginTop: 8, color: "#3f3f46" }}>CPU, RAM, GPU, VRAM em tempo real</div>
                </div>
            </div>
        </div>
    );
}

// --- Settings Panel ---
function SettingsPanel() {
    return (
        <div style={{ height: "100%", background: "#0a0a0a", display: "flex", flexDirection: "column" }}>
            <div style={{ padding: "8px 16px", background: "#111113", borderBottom: "1px solid #1e1e22", display: "flex", alignItems: "center", gap: 8 }}>
                <FaCogs size={12} style={{ color: "#71717a" }} />
                <span style={{ fontSize: 12, color: "#71717a" }}>Settings</span>
            </div>
            <div style={{ flex: 1, padding: 24, overflowY: "auto" }}>
                <div style={{ maxWidth: 600, margin: "0 auto" }}>
                    <h3 style={{ fontSize: 16, fontWeight: 600, color: "#fff", marginBottom: 16 }}>Configurações</h3>
                    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                        <div style={{ background: "#111113", border: "1px solid #1e1e22", borderRadius: 12, padding: 16 }}>
                            <div style={{ fontSize: 14, fontWeight: 500, color: "#fff", marginBottom: 8 }}>API Endpoint</div>
                            <input
                                defaultValue="http://127.0.0.1:8000"
                                style={{ width: "100%", background: "#1e1e22", border: "1px solid #27272a", borderRadius: 8, padding: "10px 12px", color: "#fff", fontSize: 13, outline: "none", boxSizing: "border-box" }}
                            />
                        </div>
                        <div style={{ background: "#111113", border: "1px solid #1e1e22", borderRadius: 12, padding: 16 }}>
                            <div style={{ fontSize: 14, fontWeight: 500, color: "#fff", marginBottom: 8 }}>Workspace Path</div>
                            <input
                                defaultValue="D:\ClawAI"
                                style={{ width: "100%", background: "#1e1e22", border: "1px solid #27272a", borderRadius: 8, padding: "10px 12px", color: "#fff", fontSize: 13, outline: "none", boxSizing: "border-box" }}
                            />
                        </div>
                        <div style={{ background: "#111113", border: "1px solid #1e1e22", borderRadius: 12, padding: 16 }}>
                            <div style={{ fontSize: 14, fontWeight: 500, color: "#fff", marginBottom: 8 }}>Auto-start Backend</div>
                            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                <div style={{ width: 40, height: 22, borderRadius: 11, background: "#7c3aed", position: "relative" }}>
                                    <div style={{ width: 18, height: 18, borderRadius: 9, background: "#fff", position: "absolute", right: 2, top: 2 }} />
                                </div>
                                <span style={{ fontSize: 13, color: "#a1a1aa" }}>Ativado</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
