type Tab = {
    path: string;
};

type Props = {
    tabs: Tab[];
    active: string;
    onSelect: (path: string) => void;
    onClose: (path: string) => void;
};

export default function Tabs({
    tabs,
    active,
    onSelect,
    onClose
}: Props) {

    return (

        <div
            style={{
                display: "flex",
                height: 36,
                background: "#252526",
                borderBottom: "1px solid #333",
                overflowX: "auto",
                flexShrink: 0
            }}
        >

            {tabs.map(tab => (

                <div
                    key={tab.path}
                    onClick={() => onSelect(tab.path)}
                    style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 10,
                        padding: "0 14px",
                        cursor: "pointer",
                        borderRight: "1px solid #333",
                        background:
                            active === tab.path
                                ? "#1e1e1e"
                                : "#2d2d30",
                        color: "#ddd",
                        minWidth: 150,
                        userSelect: "none"
                    }}
                >

                    <span
                        style={{
                            flex: 1,
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap"
                        }}
                    >
                        {tab.path.split("/").pop()}
                    </span>

                    <span
                        onClick={(e) => {
                            e.stopPropagation();
                            onClose(tab.path);
                        }}
                        style={{
                            fontWeight: "bold",
                            color: "#999"
                        }}
                    >
                        ×
                    </span>

                </div>

            ))}

        </div>

    );

}
