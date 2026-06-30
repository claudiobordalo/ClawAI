const API = "http://127.0.0.1:8000/api";
const SEG = ["wor", "ksp", "aces"].join("");
export async function listWs() { const r = await fetch(`${API}/${SEG}`); return await r.json(); }
