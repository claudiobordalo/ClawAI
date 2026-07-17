"""
Detector e gerenciador de modelos de IA.

Detecta automaticamente modelos disponíveis em:
- LM Studio (localhost:1234)
- Ollama (localhost:11434)
- OpenAI (via API key)

Exibe informações detalhadas:
- Nome do modelo
- Contexto máximo
- Multimodalidade
- Function calling
- Embeddings
- Uso de GPU / VRAM
- Tokens por segundo
"""

import asyncio
import json
import os
import platform
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Optional


class ModelProvider(str, Enum):
    LM_STUDIO = "lm_studio"
    OLLAMA = "ollama"
    OPENAI = "openai"
    LOCAL = "local"


class ModelCapability(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    FUNCTION_CALLING = "function_calling"
    EMBEDDINGS = "embeddings"
    TOOL_USE = "tool_use"


@dataclass
class ModelInfo:
    """Informações detalhadas sobre um modelo."""
    id: str
    name: str
    provider: ModelProvider
    context_length: int = 0
    capabilities: list[str] = field(default_factory=list)
    is_multimodal: bool = False
    supports_function_calling: bool = False
    supports_embeddings: bool = False
    gpu_layers: int = 0
    total_layers: int = 0
    vram_usage_mb: float = 0.0
    vram_total_mb: float = 0.0
    tokens_per_second: float = 0.0
    is_loaded: bool = False
    is_default: bool = False
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ModelStats:
    """Estatísticas globais dos modelos."""
    total_models: int = 0
    loaded_models: int = 0
    available_providers: list[str] = field(default_factory=list)
    total_vram_mb: float = 0.0
    used_vram_mb: float = 0.0
    active_provider: ModelProvider | None = None


class ModelDetector:
    """Detecta e gerencia modelos de IA disponíveis."""

    def __init__(self):
        self._models: list[ModelInfo] = []
        self._api_url: str = "http://localhost:8000"
        self._detected: bool = False

    def set_api_url(self, url: str):
        self._api_url = url

    async def detect_all(self) -> list[ModelInfo]:
        """Executa a detecção completa de todos os provedores."""
        self._models = []

        # Detecta do backend (fonte principal de verdade)
        backend_models = await self._detect_from_backend()
        self._models.extend(backend_models)

        # Detecta do LM Studio
        lm_models = await self._detect_lm_studio()
        self._models.extend(lm_models)

        # Detecta do Ollama
        ollama_models = await self._detect_ollama()
        self._models.extend(ollama_models)

        # Detecta do OpenAI
        openai_models = await self._detect_openai()
        self._models.extend(openai_models)

        self._detected = True
        return self._models

    async def get_loaded_models(self) -> list[ModelInfo]:
        """Retorna apenas modelos carregados/ativos."""
        if not self._detected:
            await self.detect_all()
        return [m for m in self._models if m.is_loaded or m.is_default]

    async def get_all_models(self) -> list[ModelInfo]:
        """Retorna todos os modelos detectados."""
        if not self._detected:
            await self.detect_all()
        return self._models

    async def get_stats(self) -> ModelStats:
        """Retorna estatísticas globais."""
        if not self._detected:
            await self.detect_all()

        loaded = [m for m in self._models if m.is_loaded or m.is_default]
        providers = set(m.provider.value for m in self._models)
        vram_total = max((m.vram_total_mb for m in self._models), default=0)
        vram_used = sum(m.vram_usage_mb for m in self._models)

        return ModelStats(
            total_models=len(self._models),
            loaded_models=len(loaded),
            available_provider=list(providers),
            total_vram_mb=vram_total,
            used_vram_mb=vram_used,
            active_provider=(
                loaded[0].provider if loaded else None
            ),
        )

    async def _detect_from_backend(self) -> list[ModelInfo]:
        """Detecta modelos via API do backend ClawAI."""
        models = []
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Endpoint de modelos do backend
                resp = await client.get(f"{self._api_url}/models")
                if resp.status_code == 200:
                    data = resp.json()
                    for m in data:
                        models.append(self._parse_backend_model(m))
                else:
                    # Tenta endpoint alternativo
                    resp = await client.get(f"{self._api_url}/v1/models")
                    if resp.status_code == 200:
                        data = resp.json()
                        items = data.get("data", data) if isinstance(data, dict) else data
                        for m in items:
                            models.append(self._parse_v1_model(m))
        except Exception:
            pass
        return models

    async def _detect_lm_studio(self) -> list[ModelInfo]:
        """Detecta modelos do LM Studio."""
        models = []
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Verifica se LM Studio está rodando
                resp = await client.get("http://localhost:1234/v1/models", timeout=3.0)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("data", [])
                    for item in items:
                        model_id = item.get("id", "unknown")
                        name = item.get("id", model_id).split("/")[-1]
                        models.append(ModelInfo(
                            id=model_id,
                            name=name,
                            provider=ModelProvider.LM_STUDIO,
                            is_loaded=True,
                            context_length=item.get("context_length", 0),
                            capabilities=[
                                ModelCapability.TEXT,
                                ModelCapability.FUNCTION_CALLING,
                            ],
                            supports_function_calling=True,
                            metadata={
                                "original_data": item,
                            },
                        ))
        except Exception:
            pass
        return models

    async def _detect_ollama(self) -> list[ModelInfo]:
        """Detecta modelos do Ollama."""
        models = []
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Lista modelos instalados
                resp = await client.get("http://localhost:11434/api/tags", timeout=3.0)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("models", []):
                        model_id = item.get("name", "unknown")
                        model_info_resp = await client.post(
                            "http://localhost:11434/api/show",
                            json={"name": model_id},
                            timeout=5.0,
                        )
                        info = model_info_resp.json() if model_info_resp.status_code == 200 else {}
                        parameters = info.get("parameters", "")
                        context_length = self._extract_context_from_params(parameters)
                        capacity = self._infer_capabilities(info)

                        models.append(ModelInfo(
                            id=model_id,
                            name=model_id,
                            provider=ModelProvider.OLLAMA,
                            is_loaded=self._is_ollama_loaded(model_id),
                            context_length=context_length,
                            capabilities=capacity,
                            supports_function_calling="chat" in str(info.get("template", "")).lower() or
                                                      "function" in str(info.get("parameters", "")).lower(),
                            supports_embeddings="embedding" in model_id.lower(),
                            gpu_layers=item.get("details", {}).get("gpu_layers", 0),
                            total_layers=item.get("details", {}).get("total_layers", 0),
                            vram_usage_mb=item.get("size", 0) / (1024 * 1024),
                            metadata={
                                "original_data": item,
                                "show_info": info,
                            },
                        ))
        except Exception:
            pass
        return models

    async def _detect_openai(self) -> list[ModelInfo]:
        """Detecta modelos do OpenAI (se API key configurada)."""
        models = []
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            return models

        try:
            import httpx
            headers = {"Authorization": f"Bearer {api_key}"}
            async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
                resp = await client.get("https://api.openai.com/v1/models", timeout=5.0)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("data", []):
                        model_id = item.get("id", "")
                        if not model_id:
                            continue
                        capabilities = [ModelCapability.TEXT]
                        if "vision" in model_id or "multimodal" in model_id:
                            capabilities.append(ModelCapability.IMAGE)
                        if "gpt-4o" in model_id or "gpt-4" in model_id:
                            capabilities.append(ModelCapability.FUNCTION_CALLING)

                        models.append(ModelInfo(
                            id=model_id,
                            name=model_id,
                            provider=ModelProvider.OPENAI,
                            context_length=item.get("context_length", 0),
                            capabilities=capabilities,
                            is_multimodal=ModelCapability.IMAGE in capabilities,
                            supports_function_calling=ModelCapability.FUNCTION_CALLING in capabilities,
                            metadata={"original_data": item},
                        ))
        except Exception:
            pass
        return models

    def _parse_backend_model(self, data: dict) -> ModelInfo:
        """Parseia um modelo vindo da API do backend."""
        caps = data.get("capabilities", [])
        if isinstance(caps, str):
            caps = [caps]
        return ModelInfo(
            id=data.get("id", data.get("model_id", "unknown")),
            name=data.get("name", data.get("model_name", data.get("id", "Unknown"))),
            provider=ModelProvider(data.get("provider", "local")),
            context_length=data.get("context_length", 0),
            capabilities=caps,
            is_multimodal=data.get("is_multimodal", False),
            supports_function_calling=data.get("supports_function_calling", False),
            supports_embeddings=data.get("supports_embeddings", False),
            gpu_layers=data.get("gpu_layers", 0),
            total_layers=data.get("total_layers", 0),
            vram_usage_mb=data.get("vram_usage_mb", 0.0),
            vram_total_mb=data.get("vram_total_mb", 0.0),
            tokens_per_second=data.get("tokens_per_second", 0.0),
            is_loaded=data.get("is_loaded", False),
            is_default=data.get("is_default", False),
            metadata=data.get("metadata", {}),
        )

    def _parse_v1_model(self, data: dict) -> ModelInfo:
        """Parseia um modelo no formato OpenAI v1."""
        model_id = data.get("id", "unknown")
        name = model_id.split("/")[-1] if "/" in model_id else model_id
        caps = [ModelCapability.TEXT]
        if "vision" in model_id.lower() or "multimodal" in model_id.lower():
            caps.append(ModelCapability.IMAGE)
        if "gpt-4" in model_id:
            caps.append(ModelCapability.FUNCTION_CALLING)

        return ModelInfo(
            id=model_id,
            name=name,
            provider=ModelProvider.OPENAI,
            context_length=data.get("context_length", 0),
            capabilities=caps,
            is_multimodal=ModelCapability.IMAGE in caps,
            supports_function_calling=ModelCapability.FUNCTION_CALLING in caps,
            metadata={"original_data": data},
        )

    def _extract_context_from_params(self, params: str) -> int:
        """Extrai context_length de parâmetros do modelo."""
        if not params:
            return 0
        import re
        match = re.search(r"num_ctx\s*[:=]\s*(\d+)", params)
        if match:
            return int(match.group(1))
        return 0

    def _infer_capabilities(self, info: dict) -> list[str]:
        """Infere capacidades a partir das informações do modelo."""
        caps = [ModelCapability.TEXT]
        template = str(info.get("template", "")).lower()
        if "image" in template or "visual" in template:
            caps.append(ModelCapability.IMAGE)
        if "function" in template or "tool" in template:
            caps.append(ModelCapability.FUNCTION_CALLING)
        return caps

    def _is_ollama_loaded(self, model_name: str) -> bool:
        """Verifica se um modelo Ollama está carregado."""
        try:
            import httpx
            async def _check():
                async with httpx.AsyncClient(timeout=3.0) as client:
                    resp = await client.get("http://localhost:11434/api/ps", timeout=2.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        processes = data.get("models", [])
                        for p in processes:
                            if model_name in p.get("name", ""):
                                return True
                    return False
            return asyncio.run(_check())
        except Exception:
            return False

    def get_model_by_id(self, model_id: str) -> ModelInfo | None:
        """Busca um modelo por ID."""
        for m in self._models:
            if m.id == model_id:
                return m
        return None

    def switch_model(self, model_id: str) -> bool:
        """Solicita troca de modelo (via API do backend)."""
        try:
            import httpx
            httpx.Client().post(
                f"{self._api_url}/models/switch",
                json={"model_id": model_id},
                timeout=10.0,
            )
            return True
        except Exception:
            return False


# Singleton
_detector_instance: ModelDetector | None = None


def get_detector() -> ModelDetector:
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = ModelDetector()
    return _detector_instance
