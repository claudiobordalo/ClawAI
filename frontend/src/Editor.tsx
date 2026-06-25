import MonacoEditor from "@monaco-editor/react";

type Props = {
    path: string;
    content: string;
};

export default function Editor({ path, content }: Props) {

    function language(file: string) {

        const ext = file.split(".").pop()?.toLowerCase();

        switch (ext) {

            case "py":
                return "python";

            case "ts":
            case "tsx":
                return "typescript";

            case "js":
            case "jsx":
                return "javascript";

            case "json":
                return "json";

            case "sql":
                return "sql";

            case "md":
                return "markdown";

            case "yaml":
            case "yml":
                return "yaml";

            default:
                return "plaintext";
        }
    }

    return (

        <MonacoEditor
            height="100%"
            theme="vs-dark"
            language={language(path)}
            value={content}
            options={{
                automaticLayout: true,
                minimap: {
                    enabled: true
                },
                fontSize: 14,
                wordWrap: "off",
                scrollBeyondLastLine: false
            }}
        />

    );

}
