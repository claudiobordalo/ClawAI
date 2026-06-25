import axios from "axios";

const api = axios.create({
    baseURL: "http://127.0.0.1:8000/api"
});

export type ChatMessage = {
    role: "system" | "user" | "assistant";
    content: string;
};

export async function sendChat(
    messages: ChatMessage[],
    projectFiles: string[],
    activeFile: string,
    activeContent: string
) {

    const response = await api.post("/chat", {
        messages,
        projectFiles,
        activeFile,
        activeContent
    });

    return response.data;

}

export async function loadTree() {

    const response = await api.get("/tree");

    return response.data;

}

export async function loadFile(path: string) {

    const response = await api.get(
        "/file",
        {
            params: {
                path
            }
        }
    );

    return response.data;

}

export async function saveFile(
    path: string,
    content: string
) {

    await api.post(
        "/file",
        {
            path,
            content
        }
    );

}
