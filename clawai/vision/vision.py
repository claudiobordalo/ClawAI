from __future__ import annotations

import base64
from pathlib import Path

import requests


class Vision:

    def __init__(
        self,
        host: str = "http://127.0.0.1:11434",
        model: str = "qwen2.5vl:7b",
    ) -> None:

        self.host = host.rstrip("/")
        self.model = model

    def analyze(
        self,
        image: str | Path,
        prompt: str,
    ) -> str:

        image = Path(image)

        encoded = base64.b64encode(
            image.read_bytes()
        ).decode("utf-8")

        response = requests.post(
            f"{self.host}/api/chat",
            json={
                "model": self.model,
                "stream": False,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                        "images": [
                            encoded
                        ]
                    }
                ]
            },
            timeout=300,
        )

        response.raise_for_status()

        data = response.json()

        return data["message"]["content"]


vision = Vision()
