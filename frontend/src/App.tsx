import { useEffect, useMemo, useRef, useState } from "react";
import MonacoEditor from "@monaco-editor/react";
import { FaBolt, FaChevronDown, FaCode, FaFolderOpen, FaLayerGroup, FaMemory, FaProjectDiagram, FaRobot, FaSearch, FaStream, FaTasks, FaTimes, FaTrashAlt } from "react-icons/fa";

import Explorer from "./Explorer";
import OperationsHub from "./OperationsHub";
import {
    getCurrentWorkspace,
    listWorkspaces,
    loadFile,
    loadTree,
    openWorkspace,
    saveFile,
    selectWorkspace,
    type WorkspaceInfo,
    type WorkspaceSummary,
} from "./api";
import type { TreeNode } from "./tree";
import "./App.css";

type Tab = {
    path: string;
    content: string;
    original: string;
    modified: boolean;
};

type WorkspaceTabsState = Record<string, { tabs: Tab[]; active: string }>;

type DockSection = "explorer" | "projects";

type Command = {
    id: string;
    label: string;
    hint: string;
    action: () => void | Promise<void>;
};

const INITIAL_LEFT_WIDTH = 320;
const INITIAL_RIGHT_WIDTH = 560;
const MIN_LEFT_WIDTH = 260;
const MIN_RIGHT_WIDTH = 360;
const MIN_EDITOR_WIDTH = 420;

function clamp(value: number, min: number, max: number) {
    return Math.max(min, Math.min(max, value));
}

export default function App() {
    const [tree, setTree] = useState<TreeNode[]>([]);
    const [workspaceSummary, setWorkspaceSummary] = useState<WorkspaceSummary | null>(null);
    const [workspaceError, setWorkspaceError] = useState("");
    const [activeWorkspaceId, setActiveWorkspaceId] = useState("");
    const [workspaceTabs, setWorkspaceTabs] = useState<WorkspaceTabsState>({});
    const [leftSection, setLeftSection] = useState<DockSection>("explorer");
    const [leftWidth, setLeftWidth] = useState(INITIAL_LEFT_WIDTH);
    const [rightWidth, setRightWidth] = useState(INITIAL_RIGHT_WIDTH);
    const [rightVisible, setRightVisible] = useState(true);
    const [paletteOpen, setPaletteOpen] = useState(false);
    const [paletteQuery, setPaletteQuery] = useState("");
    const [openFolderValue, setOpenFolderValue] = useState("");
    const [busy, setBusy] = useState(false);
    const [lastRefresh, setLastRefresh] = useState(0);
    const dragState = useRef<"left" | "right" | null>(null);

    useEffect(() => {
        void bootstrap();
    }, []);

    useEffect(() => {
        function onKeyDown(e: KeyboardEvent) {
            const key = e.key.toLowerCase();

            if ((e.ctrlKey || e.metaKey) && key === "s") {
                e.preventDefault();
                void saveCurrent();
                return;
            }

            if ((e.ctrlKey || e.metaKey) && key === "k") {
                e.preventDefault();
                setPaletteOpen(prev => !prev);
                setPaletteQuery("");
                return;
            }

            if ((e.ctrlKey || e.metaKey) && key === "o") {
                e.preventDefault();
                void promptOpenWorkspace();
                return;
            }

            if ((e.ctrlKey || e.metaKey) && key === "b") {
                e.preventDefault();
                setLeftSection(prev => prev === "explorer" ? "projects" : "explorer");
                return;
            }

            if ((e.ctrlKey || e.metaKey) && key === "w") {
                e.preventDefault();
                const current = currentTab;
                if (current) {
                    void closeTab(current.path);
                }
            }
        }

        window.addEventListener("keydown", onKeyDown);
        return () => window.removeEventListener("keydown", onKeyDown);
    }, [currentTab]);

    useEffect(() => {
        const onMouseMove = (event: MouseEvent) => {
            if (!dragState.current) {
                return;
            }

            if (dragState.current === "left") {
                const next = clamp(event.clientX - 52, MIN_LEFT_WIDTH, window.innerWidth * 0.42);
                setLeftWidth(next);
            }

            if (dragState.current === "right" && rightVisible) {
                const next = clamp(window.innerWidth - event.clientX, MIN_RIGHT_WIDTH, window.innerWidth * 0.5);
                setRightWidth(next);
            }
        };

        const onMouseUp = () => {
            dragState.current = null;
            document.body.style.cursor = "default";
            document.body.style.userSelect = "auto";
        };

        window.addEventListener("mousemove", onMouseMove);
        window.addEventListener("mouseup", onMouseUp);
        return () => {
            window.removeEventListener("mousemove", onMouseMove);
            window.removeEventListener("mouseup", onMouseUp);
        };
    }, [rightVisible]);

    const workspaces = workspaceSummary?.workspaces ?? [];
    const activeWorkspace = useMemo(
        () => workspaces.find(item => item.workspace_id === activeWorkspaceId) ?? workspaceSummary?.current ?? null,
        [activeWorkspaceId, workspaces, workspaceSummary],
    );

    const activeWorkspaceEntry = activeWorkspaceId ? workspaceTabs[activeWorkspaceId] : undefined;
    const activeTabs = activeWorkspaceEntry?.tabs ?? [];
    const activePath = activeWorkspaceEntry?.active ?? "";
    const currentTab = activeTabs.find(tab => tab.path === activePath) ?? activeTabs[0] ?? null;

    const commands = useMemo<Command[]>(() => [
        { id: "open-workspace", label: "Open Folder", hint: "Escolher outro projeto", action: promptOpenWorkspace },
        { id: "switch-explorer", label: "Explorer", hint: "Painel de arquivos", action: () => setLeftSection("explorer") },
        { id: "switch-projects", label: "Projects", hint: "Gerenciar workspaces", action: () => setLeftSection("projects") },
        { id: "toggle-right", label: rightVisible ? "Hide Right Panel" : "Show Right Panel", hint: "Chat / Evolution / Memory", action: () => setRightVisible(prev => !prev) },
        { id: "refresh", label: "Refresh Workspace", hint: "Recarregar árvore e projetos", action: refreshAll },
        { id: "save", label: "Save File", hint: "Salvar arquivo ativo", action: saveCurrent },
    ], [rightVisible, currentTab, activeWorkspaceId, tree, workspaceSummary]);

    const filteredCommands = commands.filter(command => {
        const q = paletteQuery.trim().toLowerCase();
        if (!q) {
            return true;
        }
        return `${command.label} ${command.hint}`.toLowerCase().includes(q);
    });

    async function bootstrap() {
        setBusy(true);
        try {
            const summary = await listWorkspaces();
            setWorkspaceSummary(summary);
            const current = summary.current ?? (await getCurrentWorkspace());
            setActiveWorkspaceId(current.workspace_id);
            await loadWorkspace(current.workspace_id, summary);
        } catch (error) {
            console.error("Falha ao iniciar o workspace.", error);
            setWorkspaceError(error instanceof Error ? error.message : "Falha ao iniciar o workspace.");
        } finally {
            setBusy(false);
        }
    }

    async function refreshAll() {
        setBusy(true);
        try {
            const summary = await listWorkspaces();
            setWorkspaceSummary(summary);
            const nextWorkspaceId = activeWorkspaceId || summary.current.workspace_id;
            if (nextWorkspaceId) {
                await loadWorkspace(nextWorkspaceId, summary);
            }
            setLastRefresh(Date.now());
        } catch (error) {
            console.error("Falha ao atualizar a interface.", error);
            setWorkspaceError(error instanceof Error ? error.message : "Falha ao atualizar a interface.");
        } finally {
            setBusy(false);
        }
    }

    async function loadWorkspace(workspaceId: string, summary?: WorkspaceSummary) {
        try {
            const nextTree = await loadTree("", workspaceId);
            setTree(nextTree);
            setWorkspaceError("");
            const activeSummary = summary ?? workspaceSummary;
            if (activeSummary) {
                setWorkspaceSummary(activeSummary);
            }
            if (workspaceId && !workspaceTabs[workspaceId]) {
                setWorkspaceTabs(prev => ({ ...prev, [workspaceId]: { tabs: [], active: "" } }));
            }
        } catch (error) {
            console.error("Falha ao carregar a árvore do projeto.", error);
            setTree([]);
            setWorkspaceError(error instanceof Error ? error.message : "Falha ao carregar a árvore do projeto.");
        }
    }

    async function promptOpenWorkspace() {
        const path = window.prompt("Caminho completo da pasta do projeto:", openFolderValue || activeWorkspace?.root || "");
        if (!path) {
            return;
        }

        setOpenFolderValue(path);
        const name = window.prompt("Nome do workspace (opcional):", activeWorkspace?.name ?? "") ?? undefined;
        await openWorkspaceFromPath(path, name?.trim() ? name.trim() : undefined);
    }

    async function openWorkspaceFromPath(path: string, name?: string) {
        setBusy(true);
        try {
            const response = await openWorkspace(path, name);
            setWorkspaceSummary(response.summary);
            setActiveWorkspaceId(response.workspace.workspace_id);
            await loadWorkspace(response.workspace.workspace_id, response.summary);
            setLeftSection("explorer");
        } catch (error) {
            setWorkspaceError(error instanceof Error ? error.message : "Falha ao abrir o workspace.");
        } finally {
            setBusy(false);
        }
    }

    async function changeWorkspace(workspaceId: string) {
        if (!workspaceId || workspaceId === activeWorkspaceId) {
            return;
        }

        setBusy(true);
        try {
            const response = await selectWorkspace(workspaceId);
            setWorkspaceSummary(response.summary);
            setActiveWorkspaceId(workspaceId);
            await loadWorkspace(workspaceId, response.summary);
        } catch (error) {
            setWorkspaceError(error instanceof Error ? error.message : "Falha ao trocar de workspace.");
        } finally {
            setBusy(false);
        }
    }

    async function loadChildren(path: string) {
        try {
            return await loadTree(path, activeWorkspaceId);
        } catch (error) {
            console.error(`Falha ao carregar children de ${path}`, error);
            return [];
        }
    }

    async function openFile(path: string) {
        if (!activeWorkspaceId) {
            return;
        }

        const existing = activeTabs.find(tab => tab.path === path);
        if (existing) {
            setWorkspaceTabs(prev => ({
                ...prev,
                [activeWorkspaceId]: {
                    tabs: prev[activeWorkspaceId]?.tabs ?? [],
                    active: path,
                }
            }));
            return;
        }

        const text = await loadFile(path, activeWorkspaceId);
        setWorkspaceTabs(prev => ({
            ...prev,
            [activeWorkspaceId]: {
                tabs: [...(prev[activeWorkspaceId]?.tabs ?? []), { path, content: text, original: text, modified: false }],
                active: path,
            }
        }));
    }

    async function saveCurrent() {
        if (!currentTab || !currentTab.modified || !activeWorkspaceId) {
            return;
        }

        await saveFile(currentTab.path, currentTab.content, activeWorkspaceId);
        setWorkspaceTabs(prev => ({
            ...prev,
            [activeWorkspaceId]: {
                tabs: (prev[activeWorkspaceId]?.tabs ?? []).map(tab => tab.path === currentTab.path ? { ...tab, original: tab.content, modified: false } : tab),
                active: currentTab.path,
            }
        }));
    }

    async function closeTab(path: string) {
        if (!activeWorkspaceId) {
            return;
        }

        const tab = activeTabs.find(t => t.path === path);
        if (!tab) {
            return;
        }

        if (tab.modified && !window.confirm("Descartar alterações deste arquivo?")) {
            return;
        }

        setWorkspaceTabs(prev => {
            const existing = prev[activeWorkspaceId]?.tabs ?? [];
            const nextTabs = existing.filter(t => t.path !== path);
            const nextActive = prev[activeWorkspaceId]?.active === path ? (nextTabs[0]?.path ?? "") : prev[activeWorkspaceId]?.active ?? "";
            return {
                ...prev,
                [activeWorkspaceId]: { tabs: nextTabs, active: nextActive },
            };
        });
    }

    function updateCurrentTab(content: string) {
        if (!currentTab || !activeWorkspaceId) {
            return;
        }

        setWorkspaceTabs(prev => ({
            ...prev,
            [activeWorkspaceId]: {
                tabs: (prev[activeWorkspaceId]?.tabs ?? []).map(tab => tab.path === currentTab.path ? { ...tab, content, modified: content !== tab.original } : tab),
                active: currentTab.path,
            }
        }));
    }

    function language(path: string) {
        switch (path.split(".").pop()?.toLowerCase()) {
            case "py": return "python";
            case "ts":
            case "tsx": return "typescript";
            case "js":
            case "jsx": return "javascript";
            case "json": return "json";
            case "sql": return "sql";
            case "md": return "markdown";
            case "yaml":
            case "yml": return "yaml";
            case "css": return "css";
            case "html": return "html";
            default: return "plaintext";
        }
    }

    async function runCommand(command: Command) {
        setPaletteOpen(false);
        setPaletteQuery("");
        await Promise.resolve(command.action());
    }

    const mainWidth = `calc(100vw - ${rightVisible ? leftWidth + rightWidth + 60 : leftWidth + 54}px)`;

    return (
        <div style={{ height: "100vh", background: "#1e1e1e", color: "#ddd", overflow: "hidden" }}>
            <div
                style={{
                    height: 48,
                    borderBottom: "1px solid #333",
                    background: "#252526",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "0 12px",
                    gap: 12,
                }}
            >
                <div style={{ display: "flex", alignItems: "center", gap: 10, minWidth: 0 }}>
                    <strong style={{ whiteSpace: "nowrap" }}>ClawAI Studio</strong>
                    <span style={{ color: "#8b949e", fontSize: 12, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", maxWidth: 420 }}>
                        {activeWorkspace ? `${activeWorkspace.name} · ${activeWorkspace.root}` : "Nenhum workspace ativo"}
                    </span>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <select
                        value={activeWorkspaceId}
                        onChange={e => void changeWorkspace(e.target.value)}
                        style={{ background: "#1e1e1e", color: "#ddd", border: "1px solid #444", borderRadius: 8, height: 32, padding: "0 8px", minWidth: 220 }}
                    >
                        {workspaces.map(ws => (
                            <option key={ws.workspace_id} value={ws.workspace_id}>
                                {ws.active ? `● ${ws.name}` : ws.name}
                            </option>
                        ))}
                    </select>

                    <button type="button" onClick={() => void promptOpenWorkspace()} style={{ height: 32, padding: "0 12px", borderRadius: 8, border: "1px solid #444", background: "#2d2d30", color: "#ddd", cursor: "pointer" }}>
                        Open Folder
                    </button>

                    <button type="button" onClick={() => setPaletteOpen(true)} style={{ height: 32, padding: "0 12px", borderRadius: 8, border: "1px solid #444", background: "#2d2d30", color: "#ddd", cursor: "pointer", display: "flex", alignItems: "center", gap: 8 }}>
                        <FaSearch /> Command Palette
                    </button>

                    <button type="button" onClick={() => void saveCurrent()} style={{ height: 32, padding: "0 12px", borderRadius: 8, border: "1px solid #444", background: "#2d2d30", color: "#ddd", cursor: "pointer", display: "flex", alignItems: "center", gap: 8 }}>
                        <FaCode /> Save
                    </button>
                </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: `52px ${leftWidth}px 6px minmax(0, 1fr) ${rightVisible ? `6px ${rightWidth}px` : "0px"}`, height: "calc(100vh - 48px)", minHeight: 0, overflow: "hidden" }}>
                <div
                    style={{
                        background: "#1b1b1b",
                        borderRight: "1px solid #333",
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        gap: 10,
                        paddingTop: 10,
                    }}
                >
                    <DockButton active={leftSection === "explorer"} icon={<FaFolderOpen />} label="Explorer" onClick={() => setLeftSection("explorer")} />
                    <DockButton active={leftSection === "projects"} icon={<FaProjectDiagram />} label="Projects" onClick={() => setLeftSection("projects")} />
                    <DockButton active={false} icon={<FaMemory />} label="Memory" onClick={() => setPaletteOpen(true)} />
                    <DockButton active={false} icon={<FaTasks />} label="Commands" onClick={() => setPaletteOpen(true)} />
                    <DockButton active={false} icon={<FaBolt />} label="Refresh" onClick={() => void refreshAll()} />
                    <div style={{ marginTop: "auto", marginBottom: 12, display: "flex", flexDirection: "column", gap: 8 }}>
                        <DockButton active={false} icon={<FaStream />} label="Toggle panel" onClick={() => setRightVisible(prev => !prev)} />
                    </div>
                </div>

                <div style={{ minWidth: 0, display: "flex", flexDirection: "column", overflow: "hidden", background: "#1e1e1e" }}>
                    <div style={{ height: 36, borderBottom: "1px solid #333", background: "#252526", display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 10px", gap: 10 }}>
                        <div style={{ fontSize: 12, color: "#8b949e" }}>
                            {leftSection === "explorer" ? "Explorer" : "Projects"}
                        </div>
                        <div style={{ fontSize: 12, color: "#8b949e" }}>
                            {busy ? "Updating…" : `Updated ${lastRefresh ? new Date(lastRefresh).toLocaleTimeString() : "just now"}`}
                        </div>
                    </div>

                    <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column", overflow: "hidden" }}>
                        {leftSection === "explorer" ? (
                            <Explorer nodes={tree} onOpen={openFile} onLoadChildren={loadChildren} />
                        ) : (
                            <ProjectPanel
                                summary={workspaceSummary}
                                currentId={activeWorkspaceId}
                                onSelect={id => void changeWorkspace(id)}
                                onOpenFolder={() => void promptOpenWorkspace()}
                                onClose={id => workspaceSummary ? void closeWorkspace(id) : undefined}
                            />
                        )}
                    </div>
                </div>

                <ResizeHandle
                    onMouseDown={() => {
                        dragState.current = "left";
                        document.body.style.cursor = "col-resize";
                        document.body.style.userSelect = "none";
                    }}
                />

                <div style={{ minWidth: 0, display: "flex", flexDirection: "column", overflow: "hidden", background: "#1e1e1e" }}>
                    <div style={{ height: 36, borderBottom: "1px solid #333", background: "#252526", display: "flex", alignItems: "center", overflowX: "auto", overflowY: "hidden" }}>
                        {activeTabs.length ? activeTabs.map(tab => (
                            <div
                                key={tab.path}
                                onClick={() => setWorkspaceTabs(prev => ({ ...prev, [activeWorkspaceId]: { tabs: prev[activeWorkspaceId]?.tabs ?? [], active: tab.path } }))}
                                style={{
                                    display: "flex",
                                    alignItems: "center",
                                    gap: 8,
                                    padding: "0 12px",
                                    height: 36,
                                    cursor: "pointer",
                                    background: activePath === tab.path ? "#1e1e1e" : "#2d2d30",
                                    borderRight: "1px solid #333",
                                    color: "#ddd",
                                    userSelect: "none",
                                    whiteSpace: "nowrap"
                                }}
                            >
                                <span>{tab.modified ? "● " : ""}{tab.path.split("/").pop()}</span>
                                <span
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        void closeTab(tab.path);
                                    }}
                                    style={{ color: "#999", paddingLeft: 2 }}
                                >
                                    ×
                                </span>
                            </div>
                        )) : (
                            <div style={{ color: "#8b949e", padding: "0 12px", fontSize: 12 }}>Open a file from the explorer</div>
                        )}
                    </div>

                    <div style={{ flex: 1, minHeight: 0 }}>
                        <MonacoEditor
                            height="100%"
                            theme="vs-dark"
                            language={language(currentTab?.path ?? "")}
                            value={currentTab?.content ?? ""}
                            options={{ automaticLayout: true, minimap: { enabled: true }, fontSize: 14, scrollBeyondLastLine: false, wordWrap: "on" }}
                            onChange={(value) => updateCurrentTab(value ?? "")}
                        />
                    </div>
                </div>

                {rightVisible ? (
                    <>
                        <ResizeHandle
                            onMouseDown={() => {
                                dragState.current = "right";
                                document.body.style.cursor = "col-resize";
                                document.body.style.userSelect = "none";
                            }}
                        />

                        <div style={{ minWidth: 0, overflow: "hidden", background: "#1e1e1e" }}>
                            <OperationsHub />
                        </div>
                    </>
                ) : null}
            </div>

            {paletteOpen ? (
                <div
                    onMouseDown={() => setPaletteOpen(false)}
                    style={{
                        position: "fixed",
                        inset: 0,
                        background: "rgba(0,0,0,0.45)",
                        zIndex: 100,
                        display: "flex",
                        alignItems: "flex-start",
                        justifyContent: "center",
                        paddingTop: 84,
                    }}
                >
                    <div
                        onMouseDown={e => e.stopPropagation()}
                        style={{
                            width: "min(760px, calc(100vw - 32px))",
                            background: "#1f1f1f",
                            border: "1px solid #3a3a3a",
                            borderRadius: 16,
                            boxShadow: "0 18px 40px rgba(0,0,0,.45)",
                            overflow: "hidden"
                        }}
                    >
                        <div style={{ padding: 14, borderBottom: "1px solid #333", display: "flex", gap: 10, alignItems: "center" }}>
                            <FaSearch />
                            <input autoFocus value={paletteQuery} onChange={e => setPaletteQuery(e.target.value)} placeholder="Command Palette — type to search..." style={{ flex: 1, background: "transparent", border: "none", outline: "none", color: "#fff", fontSize: 14 }} />
                            <button type="button" onClick={() => setPaletteOpen(false)} style={{ background: "transparent", border: "none", color: "#999", cursor: "pointer" }}><FaTimes /></button>
                        </div>
                        <div style={{ maxHeight: 360, overflow: "auto" }}>
                            {filteredCommands.length ? filteredCommands.map(command => (
                                <button key={command.id} type="button" onClick={() => void runCommand(command)} style={{ width: "100%", textAlign: "left", padding: "12px 14px", background: "transparent", border: "none", borderBottom: "1px solid #2c2c2c", color: "#ddd", cursor: "pointer", display: "flex", justifyContent: "space-between", gap: 12 }}>
                                    <span>{command.label}</span>
                                    <span style={{ color: "#8b949e", fontSize: 12 }}>{command.hint}</span>
                                </button>
                            )) : <div style={{ padding: 14, color: "#8b949e" }}>No commands found.</div>}
                        </div>
                    </div>
                </div>
            ) : null}

            {workspaceError ? (
                <div style={{ position: "fixed", left: 16, bottom: 16, zIndex: 110, background: "#3a1b1b", color: "#ffb4b4", border: "1px solid #7f1d1d", borderRadius: 10, padding: "10px 12px", maxWidth: 520 }}>
                    {workspaceError}
                </div>
            ) : null}
        </div>
    );
}

function DockButton({ active, icon, label, onClick }: { active: boolean; icon: React.ReactNode; label: string; onClick: () => void }) {
    return (
        <button
            type="button"
            onClick={onClick}
            title={label}
            style={{
                width: 38,
                height: 38,
                borderRadius: 10,
                border: active ? "1px solid #6f84a3" : "1px solid transparent",
                background: active ? "#343c4f" : "#2a2a2a",
                color: "#ddd",
                cursor: "pointer",
                display: "grid",
                placeItems: "center",
            }}
        >
            {icon}
        </button>
    );
}

function ResizeHandle({ onMouseDown }: { onMouseDown: () => void }) {
    return <div onMouseDown={onMouseDown} style={{ width: 6, cursor: "col-resize", background: "linear-gradient(90deg, transparent, rgba(255,255,255,.05), transparent)" }} />;
}

function ProjectPanel({ summary, currentId, onSelect, onOpenFolder, onClose }: { summary: WorkspaceSummary | null; currentId: string; onSelect: (id: string) => void; onOpenFolder: () => void; onClose: (id: string) => void; }) {
    const workspaces = summary?.workspaces ?? [];
    return (
        <div style={{ display: "flex", flexDirection: "column", minHeight: 0, overflow: "hidden" }}>
            <div style={{ padding: 12, borderBottom: "1px solid #333", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10 }}>
                <strong>Projects</strong>
                <button onClick={onOpenFolder} style={{ cursor: "pointer" }}>Open Folder</button>
            </div>
            <div style={{ padding: 12, display: "grid", gap: 10, overflow: "auto" }}>
                {summary ? (
                    <div style={{ background: "#232323", border: "1px solid #333", borderRadius: 12, padding: 12 }}>
                        <div style={{ color: "#8b949e", fontSize: 12 }}>Current</div>
                        <div style={{ marginTop: 4, fontWeight: 700 }}>{summary.current.name}</div>
                        <div style={{ marginTop: 4, color: "#8b949e", fontSize: 12, wordBreak: "break-all" }}>{summary.current.root}</div>
                    </div>
                ) : null}

                <div style={{ display: "grid", gap: 8 }}>
                    {workspaces.map(ws => (
                        <button
                            key={ws.workspace_id}
                            onClick={() => onSelect(ws.workspace_id)}
                            style={{
                                textAlign: "left",
                                background: ws.workspace_id === currentId ? "#2f3a4f" : "#232323",
                                border: ws.workspace_id === currentId ? "1px solid #6f84a3" : "1px solid #333",
                                color: "#ddd",
                                borderRadius: 12,
                                padding: 12,
                                cursor: "pointer",
                            }}
                        >
                            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
                                <strong>{ws.active ? `● ${ws.name}` : ws.name}</strong>
                                <button
                                    type="button"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        onClose(ws.workspace_id);
                                    }}
                                    style={{ background: "transparent", border: "none", color: "#999", cursor: "pointer" }}
                                >
                                    <FaTrashAlt />
                                </button>
                            </div>
                            <div style={{ marginTop: 6, color: "#8b949e", fontSize: 12, wordBreak: "break-all" }}>{ws.root}</div>
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}
