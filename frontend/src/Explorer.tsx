import { useState } from "react";
import { FaChevronDown, FaChevronRight, FaFileAlt, FaFolder, FaFolderOpen, FaSpinner } from "react-icons/fa";
import type { TreeNode } from "./tree";

type Props = {
    nodes: TreeNode[];
    onOpen: (path: string) => void;
    onLoadChildren: (path: string) => Promise<TreeNode[]>;
};

export default function Explorer({ nodes, onOpen, onLoadChildren }: Props) {
    const [expanded, setExpanded] = useState<Set<string>>(new Set());
    const [loadedChildren, setLoadedChildren] = useState<Record<string, TreeNode[]>>({});
    const [loadingPaths, setLoadingPaths] = useState<Record<string, boolean>>({});

    async function ensureLoaded(path: string) {
        if (Object.prototype.hasOwnProperty.call(loadedChildren, path) || loadingPaths[path]) {
            return;
        }

        setLoadingPaths(prev => ({ ...prev, [path]: true }));

        try {
            const children = await onLoadChildren(path);
            setLoadedChildren(prev => ({ ...prev, [path]: children }));
        } finally {
            setLoadingPaths(prev => ({ ...prev, [path]: false }));
        }
    }

    function toggle(node: TreeNode) {
        if (!node.directory) {
            onOpen(node.path);
            return;
        }

        const willExpand = !expanded.has(node.path);
        const next = new Set(expanded);

        if (willExpand) {
            next.add(node.path);
        } else {
            next.delete(node.path);
        }

        setExpanded(next);

        if (willExpand) {
            void ensureLoaded(node.path);
        }
    }

    function collapseAll() {
        setExpanded(new Set());
    }

    return (
        <div
            style={{
                height: "100%",
                minHeight: 0,
                overflow: "auto",
                background: "#1e1e1e",
                borderRight: "1px solid #333"
            }}
        >
            <div
                style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "10px 12px",
                    position: "sticky",
                    top: 0,
                    zIndex: 2,
                    background: "#1e1e1e",
                    borderBottom: "1px solid #2b2b2b"
                }}
            >
                <strong>Explorer</strong>
                <button onClick={collapseAll} style={{ cursor: "pointer" }}>
                    Collapse All
                </button>
            </div>

            <div style={{ padding: "6px 0 12px" }}>
                {nodes.map(node => (
                    <Node
                        key={node.path}
                        node={node}
                        level={0}
                        expanded={expanded}
                        loadedChildren={loadedChildren}
                        loadingPaths={loadingPaths}
                        toggle={toggle}
                        onOpen={onOpen}
                    />
                ))}
            </div>
        </div>
    );
}

type NodeProps = {
    node: TreeNode;
    level: number;
    expanded: Set<string>;
    loadedChildren: Record<string, TreeNode[]>;
    loadingPaths: Record<string, boolean>;
    toggle: (node: TreeNode) => void;
    onOpen: (path: string) => void;
};

function Node({ node, level, expanded, loadedChildren, loadingPaths, toggle, onOpen }: NodeProps) {
    const open = expanded.has(node.path);
    const children = loadedChildren[node.path] ?? node.children ?? [];

    return (
        <div>
            <div
                style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                    paddingLeft: level * 18 + 8,
                    lineHeight: "28px",
                    cursor: "pointer",
                    userSelect: "none",
                    whiteSpace: "nowrap"
                }}
                onClick={() => toggle(node)}
            >
                {node.directory ? (
                    <>
                        {open ? <FaChevronDown size={10} /> : <FaChevronRight size={10} />}
                        {open ? <FaFolderOpen /> : <FaFolder />}
                    </>
                ) : (
                    <>
                        <span style={{ width: 10 }} />
                        <FaFileAlt />
                    </>
                )}

                {node.name}

                {node.directory && loadingPaths[node.path] ? <FaSpinner className="spin" size={10} style={{ marginLeft: 6 }} /> : null}
            </div>

            {node.directory && open && children.map(child => (
                <Node
                    key={child.path}
                    node={child}
                    level={level + 1}
                    expanded={expanded}
                    loadedChildren={loadedChildren}
                    loadingPaths={loadingPaths}
                    toggle={toggle}
                    onOpen={onOpen}
                />
            ))}
        </div>
    );
}
