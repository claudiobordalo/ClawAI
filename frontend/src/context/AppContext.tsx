/**
 * AppContext — central state for theme, sidebar visibility and active panel.
 */

import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from "react";

/* ──────────────── Types ──────────────── */

export type PanelId =
    | "chat"
    | "explorer"
    | "editor"
    | "terminal"
    | "git"
    | "planning"
    | "memory"
    | "autonomy"
    | "bridge"
    | "aipanel"
    | "monitor";

export type ThemeMode = "obsidian" | "cyber" | "dark";

interface AppContextValue {
    /* theme */
    theme: ThemeMode;
    toggleTheme: () => void;

    /* sidebar visibility (left panel) */
    sidebarVisible: boolean;
    setSidebarVisible: (visible: boolean) => void;
    toggleSidebar: () => void;

    /* active content panel — the main view in center area */
    activePanel: PanelId | null;
    setActivePanel: (panel: PanelId | null) => void;

    /* docked panels visibility — each right-side pane can be toggled independently */
    visiblePanels: Set<PanelId>;
    togglePanelVisibility: (id: PanelId) => void;

    /* native window state */
    maximized: boolean;
}

const AppContext = createContext<AppContextValue | null>(null);

export function useApp(): AppContextValue {
    const ctx = useContext(AppContext);
    if (!ctx) throw new Error("useApp must be used inside <AppProvider>");
    return ctx;
}

/* ──────────────── Provider ──────────────── */

const DEFAULT_VISIBLE_PANELS: PanelId[] = ["chat", "explorer"]; // defaults shown docked on right

export function AppProvider({ children }: { children: ReactNode }) {
    const [theme, setTheme] = useState<ThemeMode>("obsidian");

    const toggleTheme = useCallback(() => {
        setTheme(prev => (prev === "cyber" ? "dark" : prev === "dark" ? "obsidian" : "cyber"));
    }, []);

    /* Sidebar */
    const [sidebarVisible, setSidebarVisible] = useState(true);
    const toggleSidebar = useCallback(() => setSidebarVisible(p => !p), []);

    /* Active panel (primary content) */
    const [activePanel, setActivePanel] = useState<PanelId | null>(null);

    /* Docked panels visibility — default: chat + explorer shown on right side dock */
    const [visiblePanels, setVisiblePanels] = useState<Set<PanelId>>(() => new Set(DEFAULT_VISIBLE_PANELS));

    const togglePanelVisibility = useCallback((id: PanelId) => {
        setVisiblePanels(prev => {
            const next = new Set(prev);
            if (next.has(id)) next.delete(id); else next.add(id);
            return next;
        });
    }, []);

    /* Window maximized state from native bridge */
    const [maximized, setMaximized] = useState(false);
    useEffect(() => {
        if (typeof window !== "undefined" && (window as any).clawai?.window) {
            try {
                (window as any).clawai.window.isMaximized().then(setMaximized).catch(() => {});
            } catch { /* bridge not available */ }

            const handler = (e: Event) => {
                const state = (e as CustomEvent).detail;
                if (state === "maximized") setMaximized(true);
                else if (state === "unmaximized") setMaximized(false);
            };
            window.addEventListener("window-state", handler);
            return () => window.removeEventListener("window-state", handler);
        }
    }, []);

    const value: AppContextValue = {
        theme, toggleTheme,
        sidebarVisible, setSidebarVisible, toggleSidebar,
        activePanel, setActivePanel,
        visiblePanels, togglePanelVisibility,
        maximized,
    };

    return (
        <AppContext.Provider value={value}>
            {/* Apply data-theme on root element via a wrapper div */}
            <div style={{ display: "flex", flexDirection: "column", height: "100%", width: "100%" }}>
                {children}
            </div>
        </AppContext.Provider>
    );
}
