import { useEffect, useMemo, useState } from "react";
import MonacoEditor from "@monaco-editor/react";

import Explorer from "./Explorer";
import ChatPanel from "./ChatPanel";
import { loadFile, loadTree, saveFile } from "./api";
import type { TreeNode } from "./tree";
import "./App.css";

type Tab = {
    path: string;
    content: string;
    original: string;
    modified: boolean;
};

export default function App() {
    const [tree, setTree] = useState<TreeNode[]>([]);
    const [tabs, setTabs] = useState<Tab[]>([]);
    const [active, setActive] = useState("");

    useEffect(() => {
        void loadRootTree();
    }, []);

    useEffect(() => {
        function onKeyDown(e: KeyboardEvent) {
            const key = e.key.toLowerCase();

            if ((e.ctrlKey || e.metaKey) && key === "s") {
                e.preventDefault();
                void saveCurrent();
            }

            if ((e.ctrlKey || e.metaKey) && key === "w") {
                e.preventDefault();
                if (active) {
                    closeTab(active);
                }
            }
        }

        window.addEventListener("keydown", onKeyDown);

        return () => window.removeEventListener("keydown", onKeyDown);
    }, [tabs, active]);

    async function loadRootTree() {
        try {
            setTree(await loadTree());
        } catch (error) {
            console.error("Falha ao carregar a árvore do projeto.", error);
            setTree([]);
        }
    }

    async function loadChildren(path: string) {
        try {
            return await loadTree(path);
        } catch (error) {
            console.error(`Falha ao carregar children de ${path}`, error);
            return [];
        }
    }

    async function openFile(path: string) {
        const existing = tabs.find(t => t.path === path);

        if (existing) {
            setActive(path);
            return;
        }

        const text = await loadFile(path);

        setTabs(prev => [
            ...prev,
            {
                path,
                content: text,
                original: text,
                modified: false
            }
        ]);

        setActive(path);
    }

    async function saveCurrent() {
        const current = tabs.find(t => t.path === active);

        if (!current || !current.modified) {
            return;
        }

        await saveFile(current.path, current.content);

        setTabs(prev =>
            prev.map(tab =>
                tab.path === current.path
                    ? {
                        ...tab,
                        original: tab.content,
                        modified: false
                    }
                    : tab
            )
        );
    }

    function closeTab(path: string) {
        const tab = tabs.find(t => t.path === path);

        if (!tab) {
            return;
        }

        if (tab.modified && !confirm("Descartar alterações deste arquivo?")) {
            return;
        }

        const next = tabs.filter(t => t.path !== path);

        setTabs(next);

        if (active === path) {
            const index = tabs.findIndex(t => t.path === path);

            if (next.length === 0) {
                setActive("");
            } else if (index > 0) {
                setActive(next[index - 1].path);
            } else {
                setActive(next[0].path);
            }
        }
    }

    const current = useMemo(
        () => tabs.find(t => t.path === active),
        [tabs, active]
    );

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

    return (
        <div
            style={{
                display: "grid",
                gridTemplateColumns: "340px 1fr 380px",
                height: "100vh",
                background: "#1e1e1e",
                overflow: "hidden"
            }}
        >
            <Explorer
                nodes={tree}
                onOpen={openFile}
                onLoadChildren={loadChildren}
            />

            <div
                style={{
                    display: "flex",
                    flexDirection: "column",
                    overflow: "hidden"
                }}
            >
                <div
                    style={{
                        display: "flex",
                        height: 36,
                        background: "#252526",
                        borderBottom: "1px solid #333",
                        overflowX: "auto"
                    }}
                >
                    {tabs.map(tab => (
                        <div
                            key={tab.path}
                            onClick={() => setActive(tab.path)}
                            style={{
                                display: "flex",
                                alignItems: "center",
                                gap: 8,
                                padding: "0 12px",
                                cursor: "pointer",
                                background: active === tab.path ? "#1e1e1e" : "#2d2d30",
                                borderRight: "1px solid #333",
                                color: "#ddd",
                                userSelect: "none"
                            }}
                        >
                            <span>
                                {tab.modified ? "● " : ""}
                                {tab.path.split("/").pop()}
                            </span>

                            <span
                                onClick={(e) => {
                                    e.stopPropagation();
                                    closeTab(tab.path);
                                }}
                                style={{ color: "#999" }}
                            >
                                ×
                            </span>
                        </div>
                    ))}
                </div>

                <MonacoEditor
                    height="100%"
                    theme="vs-dark"
                    language={language(current?.path ?? "")}
                    value={current?.content ?? ""}
                    options={{
                        automaticLayout: true,
                        minimap: { enabled: true },
                        fontSize: 14,
                        scrollBeyondLastLine: false
                    }}
                    onChange={(value) => {
                        if (!current) {
                            return;
                        }

                        const text = value ?? "";

                        setTabs(prev =>
                            prev.map(tab =>
                                tab.path === current.path
                                    ? {
                                        ...tab,
                                        content: text,
                                        modified: text !== tab.original
                                    }
                                    : tab
                            )
                        );
                    }}
                />
            </div>

            <ChatPanel />
        </div>
    );
}