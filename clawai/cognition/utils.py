from __future__ import annotations

import json
import re

from clawai.ai.router import ModelRole


def limit_text(text: str, limit: int = 6000) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[:limit] + "\n..."


def clamp_float(value: object, minimum: float, maximum: float) -> float:
    try:
        number = float(value)
    except Exception:
        return minimum
    return max(minimum, min(maximum, number))


def extract_json(text: str) -> dict[str, object] | None:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE)
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    candidate = match.group(0) if match else cleaned
    try:
        data = json.loads(candidate)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def first_line(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def bullets(text: str) -> list[str]:
    items: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if re.match(r"^(\d+[\.)]|[-*•])\s+", line):
            items.append(re.sub(r"^(\d+[\.)]|[-*•])\s+", "", line).strip())
    first = first_line(text)
    return items or ([first] if first else [])


def role_from_name(value: str) -> ModelRole:
    return {
        "planner": ModelRole.PLANNER,
        "coder": ModelRole.CODER,
        "reviewer": ModelRole.REVIEWER,
        "vision": ModelRole.VISION,
        "embedding": ModelRole.EMBEDDING,
    }.get(value.strip().lower(), ModelRole.DEFAULT)