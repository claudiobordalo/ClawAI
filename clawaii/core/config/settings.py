"""
Settings management for ClawAI.
Handles configuration loading and access patterns.
"""

import os
from typing import Optional, List

# Import YAML library  
try:
    import yaml 
except ImportError:
    # Fallback if not available - will be used in runtime checks
    pass


class Settings:
    """
    Centralized settings manager for the ClawAI application. 
    
    This class loads configuration from config.yaml and provides access to all 
    application settings with appropriate defaults.
    
    Configuration is loaded once at initialization time, so changes require a restart.
    """

    def __init__(self):
        self._config = {}
        
        # Load default values first
        self._load_defaults()
        
        try:
            config_path = os.path.join(os.getcwd(), "configs", "config.yaml")
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded_config = yaml.safe_load(f) or {}
                    
                    # Merge defaults with actual configuration
                    self._merge_configs(self._config, loaded_config)
                
        except Exception as e:
            print(f"Warning: Failed to load config file {e}")
            
    def _load_defaults(self):
        """Load default settings."""
        
        # Default application settings  
        app_settings = {
            "application": {
                "name": "ClawAI",
                "version": "0.1.0", 
                "debug": False
            },
            "paths": {
                "logs": "./data/logs",
                "memory": "./data/memory", 
                "projects": "./data/projects"
            },  
            "ollama": {
                "host": "http://localhost:11434"  # Default Ollama host/port
            },
            "models": {   # Model configurations with default names and aliases
                "default": "qwen2.5-coder:14b",
                "planner": "qwen3:8b", 
                "coder": "qwen2.5-coder:14b",
                "reviewer": "deepseek-r1:8b",
                "vision": "qwen2.5vl:7b",  
                "embedding": "nomic-embed-text"
            },
            # Resource monitoring settings
            "resources": {
                "cpu_busy_percent": 85,
                "ram_busy_percent": 85, 
                "disk_busy_percent": 95,
                "critical_processes": [
                    "gta5.exe",
                    "dofus.exe",  
                    "ankama launcher.exe",
                    "blender.exe",
                    "unrealeditor.exe",
                    "unity.exe",
                    "cl.exe",
                    "msbuild.exe", 
                    "ninja.exe"
                ]
            }
        }

        self._config = app_settings

    def _merge_configs(self, default_config: dict, override_config: dict):
        """Merge two configuration dictionaries recursively."""
        
        for key, value in override_config.items():
            if isinstance(value, dict) and key in default_config:
                # Recursively merge nested dicts
                self._merge_configs(default_config[key], value)
            else:
                # Override or set new values 
                default_config[key] = value

    @property  
    def application_name(self) -> str:
        """Get the application name."""
        return self._config.get("application", {}).get("name", "ClawAI")

    @property
    def version(self) -> str:  
        """Get the application version.""" 
        return self._config.get("application", {}).get("version", "0.1.0") 

    @property
    def debug_mode(self) -> bool:
        """Check if debugging is enabled."""
        return self._config.get("application", {}).get("debug", False)

    @property  
    def log_path(self) -> str:
        """Get the logs directory path.""" 
        paths = self._config.get("paths", {})
        return os.path.abspath(paths.get("logs", "./data/logs"))

    @property
    def memory_path(self) -> str:  
        """Get the memory storage directory."""
        paths = self._config.get("paths", {})  
        return os.path.abspath(paths.get("memory", "./data/memory")) 

    @property 
    def projects_path(self) -> str:
        """Get the projects data path.""" 
        paths = self._config.get("paths", {})
        return os.path.abspath(paths.get("projects", "./data/projects"))

    @property
    def ollama_host(self) -> str:  
        """Get Ollama server host."""
        ollama_config = self._config.get("ollama", {}) 
        return ollama_config.get("host", "http://localhost:11434")

    # Model settings - these are aliases to specific models
    @property
    def default_model(self) -> str:
        """Get the default model name."""
        models = self._config.get("models", {})
        return models.get("default", "")

    @property  
    def planner_model(self) -> str: 
        """Get the planner model alias.""" 
        models = self._config.get("models", {}) 
        return models.get("planner", "") 

    @property
    def coder_model(self) -> str:
        """Get the code generation model."""
        models = self._config.get("models", {})
        return models.get("coder", "")

    @property  
    def reviewer_model(self) -> str: 
        """Get the review model."""  
        models = self._config.get("models", {})  
        return models.get("reviewer", "") 

    @property
    def vision_model(self) -> str:
        """Get the vision-capable model."""
        models = self._config.get("models", {})
        return models.get("vision", "")

    @property 
    def embedding_model(self) -> str:  
        """Get the embedding model name.""" 
        models = self._config.get("models", {})  
        return models.get("embedding", "") 

    # Resource monitoring settings
    @property
    def cpu_busy_percent(self) -> int:
        """CPU busy threshold percentage."""
        resources = self._config.get("resources", {})
        return resources.get("cpu_busy_percent", 85)

    @property 
    def ram_busy_percent(self) -> int:  
        """RAM busy threshold percentage.""" 
        resources = self._config.get("resources", {})  
        return resources.get("ram_busy_percent", 85)
        
    @property
    def disk_busy_percent(self) -> int:
        """Disk usage threshold."""
        resources = self._config.get("resources", {})
        return resources.get("disk_busy_percent", 95)

    @property 
    def critical_processes(self) -> List[str]:  
        """List of processes that should not be interrupted during AI work.""" 
        resources = self._config.get("resources", {}) 
        return resources.get("critical_processes", [])