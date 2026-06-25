import { useState } from "react";
import axios from "axios";

type Props = {
    project: string;
};

export default function AIPanel({
    project,
}: Props) {

    const [objective, setObjective] = useState("");

    const [planning, setPlanning] = useState("");
    const [research, setResearch] = useState("");
    const [implementation, setImplementation] = useState("");
    const [review, setReview] = useState("");
    const [tests, setTests] = useState("");
    const [preview, setPreview] = useState("");

    const [loading, setLoading] = useState(false);

    async function execute(apply: boolean) {

        if (!objective.trim())
            return;

        setLoading(true);

        try {

            const response = await axios.post(
                "http://127.0.0.1:8000/api/implement",
                {
                    project,
                    objective,
                    apply,
                }
            );

            setPlanning(response.data.planning ?? "");
            setResearch(response.data.research ?? "");
            setImplementation(response.data.implementation ?? "");
            setReview(response.data.review ?? "");
            setTests(response.data.tests ?? "");
            setPreview(response.data.preview ?? "");

        }

        catch (e: any) {

            alert(
                e?.response?.data?.detail ??
                e.message
            );

        }

        finally {

            setLoading(false);

        }

    }

    function Section(
        title: string,
        value: string,
    ) {

        return (
            <>
                <h4
                    style={{
                        margin: "12px 0 4px"
                    }}
                >
                    {title}
                </h4>

                <pre
                    style={{
                        whiteSpace: "pre-wrap",
                        background: "#1e1e1e",
                        border: "1px solid #333",
                        padding: 10,
                        borderRadius: 4
                    }}
                >
                    {value}
                </pre>
            </>
        );

    }

    return (

        <div
            style={{
                display: "flex",
                flexDirection: "column",
                height: "100%",
                overflow: "auto",
                padding: 12,
                background: "#252526",
                color: "#ddd"
            }}
        >

            <h2
                style={{
                    marginTop: 0
                }}
            >
                ClawAI
            </h2>

            <textarea

                value={objective}

                onChange={e =>
                    setObjective(e.target.value)
                }

                placeholder="Descreva a funcionalidade..."

                style={{
                    height: 90,
                    resize: "vertical",
                    marginBottom: 12
                }}

            />

            <div
                style={{
                    display: "flex",
                    gap: 8,
                    marginBottom: 16
                }}
            >

                <button
                    disabled={loading}
                    onClick={() => execute(false)}
                >
                    Planejar
                </button>

                <button
                    disabled={loading}
                    onClick={() => execute(true)}
                >
                    Implementar
                </button>

            </div>

            {Section("🧠 Planejamento", planning)}

            {Section("🔎 Pesquisa", research)}

            {Section("💻 Implementação", implementation)}

            {Section("🧐 Revisão", review)}

            {Section("🧪 Testes", tests)}

            {Section("📄 Preview", preview)}

        </div>

    );

}
