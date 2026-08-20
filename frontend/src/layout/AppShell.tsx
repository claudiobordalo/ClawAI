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
    { id: "tools", label: "Tools", icon: <FaCogs /> },
    { id: "models", label: "Models", icon: <FaDatabase /> },
    { id: "monitor", label: "Monitor", icon: <FaMicrochip /> },
    { id: "settings", label: "Settings", icon: <FaCogs /> },
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
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [treeData, setTreeData] = useState<TreeNode | null>(null);
    const [health, setHealth] = useState<any>(null);

    // --- Chat Panel ---
    function ChatPanel() {
        return (
            <div style={{ height: "100%", background: "#0a0a0a", display: "flex", flexDirection: "column" }}>
                <div style={{ padding: "8px 16px", background: "#111113", borderBottom: "1px solid #1e1e22", display: "flex", alignItems: "center", gap: 8 }}>
                    <FaRobot size={12} style={{ color: "#71717a" }} />
                    <span style={{ fontSize: 12, color: "#71717a" }}>Chat</span>
                </div>
                <div style={{ flex: 1, padding: 24 }}>
                    {messages.map((msg) => (
                        <div key={msg.id} style={{ marginBottom: 16 }}>
                            <div style={{ fontSize: 13, fontWeight: 500, color: msg.role === "user" ? "#7dd3fc" : "#a78bfa", marginBottom: 4 }}>{msg.role}</div>
                            <div>{msg.content}</div>
                        </div>
                    ))}
                </div>
                <div style={{ padding: 16, background: "#111113", borderTop: "1px solid #1e1e22" }}>
                    <div style={{ display: "flex", gap: 8 }}>
                        <input
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            placeholder="Digite uma mensagem..."
                            onKeyDown={(e) => {
                                if (e.key === "Enter") {
                                    e.preventDefault();
                                    // Handle sending message here
                                }
                            }}
                            style={{ flex: 1, background: "#1e1e22", border: "1px solid #27272a", borderRadius: 8, padding: "10px 12px", color: "#fff", fontSize: 13, outline: "none" }}
                        />
                        <button
                            onClick={() => {
                                // Handle sending message here
                            }}
                            style={{ background: "#7c3aed", border: "none", borderRadius: 8, padding: "0 16px", color: "#fff", fontSize: 13, cursor: "pointer" }}
                        >
                            <FaPaperPlane size={14} />
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    // --- Explorer Panel ---
    function ExplorerPanel() {
        return (
            <div style={{ height: "100%", background: "#0a0a0a", display: "flex", flexDirection: "column" }}>
                <div style={{ padding: "8px 16px", background: "#111113", borderBottom: "1px solid #1e1e22", display: "flex", alignItems: "center", gap: 8 }}>
                    <FaSitemap size={12} style={{ color: "#71717a" }} />
                    <span style={{ fontSize: 12, color: "#71717a" }}>Explorer</span>
                </div>
                <div style={{ flex: 1, padding: 24, display: "flex", alignItems: "center", justifyContent: "center", color: "#52525b" }}>
                    <div style={{ textAlign: "center" }}>
                        <FaFolderOpen size={48} style={{ marginBottom: 16, opacity: 0.3 }} />
                        <div style={{ fontSize: 14 }}>Explorador de Arquivos</div>
                        <div style={{ fontSize: 12, marginTop: 8, color: "#3f3f46" }}>Navegue pelo seu workspace aqui</div>
                    </div>
                </div>
            </div>
        );
    }

    // --- Editor Panel ---
    function EditorPanel() {
        return (
            <div style={{ height: "100%", background: "#0a0a0a", display: "flex", flexDirection: "column" }}>
                <div style={{ padding: "8px 16px", background: "#111113", borderBottom: "1px solid #1e1e22", display: "flex", alignItems: "center", gap: 8 }}>
                    <FaCode size={12} style={{ color: "#71717a" }} />
                    <span style={{ fontSize: 12, color: "#71717a" }}>Editor</span>
                </div>
                <div style={{ flex: 1, padding: 24, display: "flex", alignItems: "center", justifyContent: "center", color: "#52525b" }}>
                    <div style={{ textAlign: "center" }}>
                        <FaCode size={48} style={{ marginBottom: 16, opacity: 0.3 }} />
                        <div style={{ fontSize: 14 }}>Editor de Código</div>
                        <div style={{ fontSize: 12, marginTop: 8, color: "#3f3f46" }}>Edite arquivos diretamente no editor</div>
                    </div>
                </div>
            </div>
        );
    }

    // --- Terminal Panel ---
    function TerminalPanel() {
        return (
            <div style={{ height: "100%", background: "#0a0a0a", display: "flex", flexDirection: "column" }}>
                <div style={{ padding: "8px 16px", background: "#111113", borderBottom: "1px solid #1e1e22", display: "flex", alignItems: "center", gap: 8 }}>
                    <FaTerminal size={12} style={{ color: "#71717a" }} />
                    <span style={{ fontSize: 12, color: "#71717a" }}>Terminal</span>
                </div>
                <div style={{ flex: 1, padding: 24, display: "flex", alignItems: "center", justifyContent: "center", color: "#52525b" }}>
                    <div style={{ textAlign: "center" }}>
                        <FaTerminal size={48} style={{ marginBottom: 16, opacity: 0.3 }} />
                        <div style={{ fontSize: 14 }}>Terminal</div>
                        <div style={{ fontSize: 12, marginTop: 8, color: "#3f3f46" }}>Execute comandos do sistema aqui</div>
                    </div>
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
                                {[{ name: "Vision", model: health.vision, status: "online" },
                                  { name: "Coder", model: health.coder, status: "online" },
                                  { name: "Reasoning", model: health.reasoning, status: "online" }].map((m) => (
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
                                    defaultValue="D:\\ClawAI"
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

    // --- Main render logic ---
    const getActivePanel = () => {
        switch (activeTab) {
            case "chat": return <ChatPanel />;
            case "explorer": return <ExplorerPanel />;
            case "editor": return <EditorPanel />;
            case "terminal": return <TerminalPanel />;
            case "git": return <GitPanel />;
            case "planner": return <PlannerPanel />;
            case "memory": return <MemoryPanel />;
            case "agents": return <AgentsPanel />;
            case "tools": return <ToolsPanel />;
            case "models": return <ModelsPanel health={health} />;
            case "monitor": return <MonitorPanel />;
            case "settings": return <SettingsPanel />;
        }
    };

    // --- Initial load ---
    useEffect(() => {
        const fetchHealth = async () => {
            try {
                // Simulate fetching health data
                setHealth({
                    vision: "gpt-4-vision-preview",
                    coder: "gpt-4-coder",
                    reasoning: "claude-3-opus"
                });
            } catch (error) {
                console.error("Failed to fetch health:", error);
            }
        };

        fetchHealth();
    }, []);

    return (
        <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
            {/* Top Bar */}
            <div style={{ padding: 8, background: "#111113", borderBottom: "1px solid #1e1e22", display: "flex", alignItems: "center", gap: 4 }}>
                {TABS.map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        style={{
                            padding: "6px 8px",
                            background: activeTab === tab.id ? "#1e1e22" : "transparent",
                            border: "none",
                            borderRadius: 4,
                            color: activeTab === tab.id ? "#fff" : "#71717a",
                            fontSize: 12,
                            cursor: "pointer",
                        }}
                    >
                        {tab.icon}
                        <span style={{ marginLeft: 6 }}>{tab.label}</span>
                    </button>
                ))}
            </div>

            {/* Main Content */}
            <div style={{ flex: 1, display: "flex", flexDirection: sidebarOpen ? "row" : "column" }}>
                <div
                    style={{
                        width: sidebarOpen ? 250 : 48,
                        background: "#111113",
                        borderRight: "1px solid #1e1e22",
                        display: "flex",
                        flexDirection: "column"
                    }}
                >
                    <div
                        onClick={() => setSidebarOpen(!sidebarOpen)}
                        style={{
                            padding: 8,
                            cursor: "pointer",
                            color: "#71717a",
                            textAlign: sidebarOpen ? "right" : "center",
                            borderBottom: "1px solid #1e1e22"
                        }}
                    >
                        {sidebarOpen ? <FaChevronLeft size={14} /> : <FaChevronRight size={14} />}
                    </div>
                    
                    {/* Sidebar Content */}
                    <div style={{ flex: 1, padding: "8px 0" }}>
                        {TABS.map((tab) => (
                            tab.id !== "chat" && 
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                disabled={tab.disabled}
                                style={{
                                    width: "100%",
                                    padding: "8px 12px",
                                    background: activeTab === tab.id ? "#1e1e22" : "transparent",
                                    border: "none",
                                    display: "flex",
                                    alignItems: "center",
                                    gap: 8,
                                    color: activeTab === tab.id ? "#fff" : "#71717a",
                                    fontSize: 13,
                                    cursor: "pointer"
                                }}
                            >
                                {tab.icon}
                                <span>{sidebarOpen && tab.label}</span>
                            </button>
                        ))}
                    </div>

                    {/* Settings Button */}
                    <div style={{ padding: 8, borderTop: "1px solid #1e1e22" }}>
                        <button
                            onClick={() => setActiveTab("settings")}
                            style={{
                                width: "100%",
                                padding: "8px 12px",
                                background: activeTab === "settings" ? "#1e1e22" : "transparent",
                                border: "none",
                                display: "flex",
                                alignItems: "center",
                                gap: 8,
                                color: activeTab === "settings" ? "#fff" : "#71717a",
                                fontSize: 13,
                                cursor: "pointer"
                            }}
                        >
                            <FaCogs size={14} />
                            {sidebarOpen && <span>Settings</span>}
                        </button>
                    </div>
                </div>

                {/* Active Panel */}
                <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
                    {getActivePanel()}
                </div>
            </div>
        </div>
    );
}