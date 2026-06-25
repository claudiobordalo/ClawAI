import { useMemo } from "react";

type Tab = {
    path: string;
    modified: boolean;
};

type Props = {
    tabs: Tab[];
    active: string;
};

export default function StatusBar({
    tabs,
    active
}: Props) {

    const current = useMemo(
        () => tabs.find(t => t.path === active),
        [tabs, active]
    );

    return (

        <div
            style={{
                height: 24,
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "0 10px",
                background: "#007acc",
                color: "white",
                fontSize: 12,
                userSelect: "none"
            }}
        >

            <div>
                {current
                    ? current.path
                    : "Nenhum arquivo aberto"}
            </div>

            <div
                style={{
                    display: "flex",
                    gap: 20
                }}
            >

                <span>
                    Abas: {tabs.length}
                </span>

                <span>
                    {current
                        ? (current.modified
                            ? "Não salvo"
                            : "Salvo")
                        : ""}
                </span>

            </div>

        </div>

    );

}
