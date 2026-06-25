from __future__ import annotations

from typing import Literal

import requests


class OllamaProvider:

    def __init__(
        self,
        host: str = "http://127.0.0.1:11434"
    ):

        self.host = host.rstrip("/")

    def chat(
        self,
        prompt: str,
        model: Literal[
            "qwen3:8b",
            "deepseek-r1:8b"
        ] = "qwen3:8b",
        temperature: float = 0.2
    ) -> str:

        response = requests.post(
            f"{self.host}/api/chat",
            json={
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False,
                "options": {
                    "temperature": temperature
                }
            },
            timeout=300
        )

        response.raise_for_status()

        data = response.json()

        return data["message"]["content"]
