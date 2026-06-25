from __future__ import annotations

from enum import Enum

from clawai.providers.ollama_provider import OllamaProvider


class Model(str, Enum):
    QWEN = "qwen3:8b"
    DEEPSEEK = "deepseek-r1:8b"


class AIRouter:

    def __init__(self) -> None:

        self.provider = OllamaProvider()

    def ask(
        self,
        prompt: str,
        model: Model | None = None,
    ) -> str:

        if model is None:
            model = self.choose_model(prompt)

        return self.provider.chat(
            prompt=prompt,
            model=model.value,
        )

    def choose_model(
        self,
        prompt: str,
    ) -> Model:

        text = prompt.lower()

        reasoning_keywords = (
            "analise",
            "análise",
            "explique",
            "compare",
            "planeje",
            "planejar",
            "arquitetura",
            "estratégia",
            "porque",
            "por que",
            "motivo",
            "debug",
            "erro",
            "investigue",
            "pesquise",
            "research",
        )

        coding_keywords = (
            "python",
            "java",
            "c#",
            "javascript",
            "typescript",
            "sql",
            "html",
            "css",
            "react",
            "fastapi",
            "crie",
            "implemente",
            "refatore",
            "corrija",
            "função",
            "classe",
            "arquivo",
            "código",
            "code",
        )

        if any(word in text for word in reasoning_keywords):
            return Model.DEEPSEEK

        if any(word in text for word in coding_keywords):
            return Model.QWEN

        return Model.QWEN
