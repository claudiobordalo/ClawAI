"""
Model manager for ClawAI.
Handles model discovery, selection and management across different providers.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

from clawaii.core.config.settings import Settings


logger = logging.getLogger(__name__)


class ModelManager:
    """
    Manages models for ClawAI application. Handles discovery and selection 
    of available models from different providers (Ollama, LM Studio, etc).
    
    This class is responsible for detecting which model providers are available
    on the system and managing their respective models.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        
        # Available providers with their capabilities 
        self._providers: Dict[str, ProviderInfo] = {}
        
        # Cache of discovered models for each provider  
        self._models_cache: Dict[str, List[ModelInfo]] = {}

    def discover_models(self) -> None:
        """
        Discover available models from all configured providers.
        This method should be called at startup to populate the model cache.
        """
        logger.info("Discovering available models...")
        
        # Clear existing cache
        self._models_cache.clear()
        
        # Check what providers are enabled/configured  
        if self.settings.default_provider == "ollama":
            try:
                ollama_models = self._discover_ollama_models() 
                self._models_cache["ollama"] = ollama_models
                logger.info(f"Found {len(ollama_models)} models from Ollama")
                
            except Exception as e:
                logger.warning(f"Failed to discover Ollama models: {e}")
        
        if self.settings.default_provider == "lmstudio":
            try:
                lmstudio_models = self._discover_lmstudio_models()
                self._models_cache["lmstudio"] = lmstudio_models
                logger.info(f"Found {len(lmstudio_models)} models from LM Studio")
                
            except Exception as e:
                logger.warning(f"Failed to discover LM Studio models: {e}")

    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """
        Get information about a specific model by name.
        
        Args:
            model_name (str): Name of the model
            
        Returns:
            ModelInfo or None if not found
        """
        # Search through all providers for this model 
        for provider, models in self._models_cache.items():
            for model_info in models:
                if model_info.name == model_name:
                    return model_info
                    
        logger.warning(f"Model '{model_name}' not found")
        return None

    def get_available_models(self) -> List[ModelInfo]:
        """
        Get list of all available models from all providers.
        
        Returns:
            List[ModelInfo]: All discovered models
        """
        all_models = []
        for provider, models in self._models_cache.items():
            # Add provider info to each model 
            for model in models:
                if not hasattr(model, 'provider'):
                    model.provider = provider  # Attach provider name  
                all_models.append(model)
                
        return sorted(all_models, key=lambda m: (m.provider, m.name))

    def get_provider_model(self, model_name: str) -> Optional[str]:
        """
        Get the full qualified name of a model including its provider.
        
        Args:
            model_name (str): Name of the model
            
        Returns:
            str or None if not found
        """ 
        for provider, models in self._models_cache.items():
            for model_info in models:
                if model_info.name == model_name:
                    return f"{provider}:{model_name}"
                    
        # If we don't have a qualified name yet but the user specified one like "ollama:gemma4:latest"
        # then try to extract just the base model name
        parts = model_name.split(":")
        if len(parts) > 1:
            provider_part, *name_parts = parts  
            
            for models in self._models_cache.values():
                for model_info in models:
                    if model_info.name == ":".join(name_parts):
                        return f"{provider_part}:{model_info.name}"
        
        logger.warning(f"Provider not found for model '{model_name}'")
        return None

    def get_default_model(self) -> str: 
        """
        Get the default configured model name.
        
        Returns:
            str: The default model
        """  
        # This should be expanded to handle different providers better,
        # but for now we'll just use settings.default_model directly
        
        return self.settings.default_model

    def _discover_ollama_models(self) -> List[ModelInfo]:
        """
        Discover models from Ollama.
        
        Returns:
            List[ModelInfo]: Discovered models
        """ 
        try:  
            # This is a placeholder - actual implementation would use ollama API or CLI
            
            logger.debug("Discovering Ollama models...")
            
            import subprocess
            result = subprocess.run(
                ["ollama", "list"], 
                capture_output=True, 
                text=True,
                timeout=30  # Prevent hanging
            )
            
            if result.returncode == 0:
                lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                
                models = []
                current_model_name = None
                
                for line in lines[1:]:  # Skip header row  
                    parts = line.split()
                    
                    if len(parts) >= 2 and not (parts[0].startswith('NAME') or 
                                               parts[0] == 'ollama'):
                        model_info = ModelInfo(
                            name=parts[0],
                            provider="ollama",
                            size=int(parts[1]) if parts[1].isdigit() else None,
                            modified_at=None,  # Could parse this from output
                            digest="",         # Could extract this 
                        )
                        
                        models.append(model_info)
                
                return models
            
            logger.warning("Ollama command failed or returned empty result")
            
        except Exception as e:
            logger.error(f"Error discovering Ollama models: {e}")
        
        # Fallback - just use configured defaults
        fallback_models = [
            ModelInfo(name="gemma4:latest", provider="ollama"),
            ModelInfo(name="qwen3:8b", provider="ollama"), 
            ModelInfo(name="deepseek-r1:8b", provider="ollama")
        ]
        
        return fallback_models

    def _discover_lmstudio_models(self) -> List[ModelInfo]:
        """
        Discover models from LM Studio.
        
        Returns:
            List[ModelInfo]: Discovered models
        """ 
        try:
            # This is a placeholder - actual implementation would use LM Studio API
            
            logger.debug("Discovering LM Studio models...")
            
            import subprocess  
            result = subprocess.run(
                ["curl", "-s", self.settings.lmstudio_base_url.replace("/v1", "/models")], 
                capture_output=True, 
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse JSON response - this is a simplified approach  
                
                import json
                
                try:    
                    data = json.loads(result.stdout)
                    
                    models = []
                    for model_data in data.get("data", []):
                        name = model_data.get("id")
                        
                        if name:
                            model_info = ModelInfo(
                                name=name,
                                provider="lmstudio",
                                size=None,  # Size not available from API
                                modified_at=model_data.get("created"),
                                digest="", 
                            )
                            
                            models.append(model_info)
                    
                    return models
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse LM Studio JSON response: {e}")
            
            else:
                logger.warning("LM Studio model discovery command failed")
                
        except Exception as e:
            logger.error(f"Error discovering LM Studio models: {e}")

        # Fallback - use configured default  
        fallback_models = [
            ModelInfo(name=self.settings.lmstudio_default_model, provider="lmstudio") 
        ] if self.settings.lmstudio_default_model else []
        
        return fallback_models


class ProviderInfo:
    """Information about a model provider."""
    
    def __init__(self, name: str):
        self.name = name
        # Add more properties as needed for each provider
        
    def __repr__(self) -> str:
        return f"Provider(name='{self.name}')"


class ModelInfo:
    """
    Information about an AI model.
    """ 
    
    def __init__(
        self, 
        name: str,
        provider: str = "unknown",
        size: int | None = None,
        modified_at: Any | None = None,
        digest: str = "",
        context_length: Optional[int] = None,
        vision_capable: bool = False,
        tool_capabilities: List[str] = [],
    ):
        self.name = name
        self.provider = provider  
        self.size = size  # Size in bytes if available 
        self.modified_at = modified_at  # When model was last modified
        self.digest = digest
        
        # Additional capabilities metadata that can be used for selection logic
        self.context_length = context_length or 0
        self.vision_capable = vision_capable  
        self.tool_capabilities = tool_capabilities

    def __repr__(self) -> str:
        return f"Model(name='{self.name}', provider='{self.provider}')"