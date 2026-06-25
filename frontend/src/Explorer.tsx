import { useState } from "react";
import {
    FaFolder,
    FaFolderOpen,
    FaFileAlt,
    FaChevronRight,
    FaChevronDown
} from "react-icons/fa";
import type { TreeNode } from "./tree";

type Props = {
    nodes: TreeNode[];
    onOpen: (path: string) => void;
};

export default function Explorer({ nodes, onOpen }: Props) {

    const [expanded, setExpanded] = useState<Set<string>>(new Set());

    function toggle(path: string) {

        const next = new Set(expanded);

        if (next.has(path))
            next.delete(path);
        else
            next.add(path);

        setExpanded(next);
    }

    function collapseAll() {
        setExpanded(new Set());
    }

    return (
        <div
            style={{
                height: "100vh",
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
                    padding: "10px"
                }}
            >
                <strong>Explorer</strong>

                <button
                    onClick={collapseAll}
                    style={{
                        cursor: "pointer"
                    }}
                >
                    Collapse All
                </button>
            </div>

            {nodes.map(node => (
                <Node
                    key={node.path}
                    node={node}
                    level={0}
                    expanded={expanded}
                    toggle={toggle}
                    onOpen={onOpen}
                />
            ))}

        </div>
    );
}

function Node({
    node,
    level,
    expanded,
    toggle,
    onOpen
}: any) {

    const open = expanded.has(node.path);

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
                onClick={() => {

                    if (node.directory)
                        toggle(node.path);
                    else
                        onOpen(node.path);

                }}
            >

                {node.directory ? (
                    <>
                        {open ? <FaChevronDown size={10}/> : <FaChevronRight size={10}/>}
                        {open ? <FaFolderOpen/> : <FaFolder/>}
                    </>
                ) : (
                    <>
                        <span style={{ width: 10 }} />
                        <FaFileAlt/>
                    </>
                )}

                {node.name}

            </div>

            {node.directory && open &&

                node.children.map((child: TreeNode) => (

                    <Node
                        key={child.path}
                        node={child}
                        level={level + 1}
                        expanded={expanded}
                        toggle={toggle}
                        onOpen={onOpen}
                    />

                ))

            }

        </div>
    );
}
