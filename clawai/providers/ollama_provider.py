from __future__ import annotations

from typing import Any

import requests


class OllamaProvider:

    def __init__(
        self,
        host: str = "http://127.0.0.1:11434",
    ):

        self.host = host.rstrip("/")

    def chat(

        self,

        messages: list[dict[str, str]],

        model: str = "qwen3:8b",

        temperature: float = 0.2,

        stream: bool = False,

        options: dict[str, Any] | None = None,

    ) -> dict:

        payload = {

            "model": model,

            "messages": messages,

            "stream": stream,

            "options": {

                "temperature": temperature,

                **(options or {}),

            },

        }

        response = requests.post(

            f"{self.host}/api/chat",

            json=payload,

            timeout=600,

        )

        response.raise_for_status()

        return response.json()

    def prompt(

        self,

        prompt: str,

        model: str = "qwen3:8b",

        temperature: float = 0.2,

    ) -> str:

        response = self.chat(

            model=model,

            temperature=temperature,

            messages=[

                {

                    "role": "user",

                    "content": prompt,

                }

            ],

        )

        return response["message"]["content"]


ollama = OllamaProvider()
