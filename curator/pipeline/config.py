"""Prefect configuration management for GitHub Curator pipeline."""

from pathlib import Path
from typing import Any

import yaml


class PrefectConfig:
    """Configuration manager for Prefect pipeline settings."""

    def __init__(self, config_path: str = "config/prefect.yaml"):
        """Initialize with configuration file."""
        self.config_path = Path(config_path)
        self._config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            # Return default config if file doesn't exist
            return self._default_config()

        with open(self.config_path) as f:
            return yaml.safe_load(f)

    def _default_config(self) -> dict[str, Any]:
        """Return default configuration."""
        return {
            "results": {
                "persist_by_default": True,
                "storage": {"type": "local", "path": ".prefect-results/"},
            },
            "tasks": {
                "default_cache_expiration": 604800,  # 7 days
                "default_retry_delay": 10,
                "max_retries": 3,
            },
            "task_runner": {"type": "concurrent", "max_workers": 10},
            "cache": {
                "enabled": True,
                "type": "local",
                "path": ".prefect-cache/",
                "max_size_mb": 1000,
            },
        }

    def get_task_config(self, task_name: str) -> dict[str, Any]:
        """Get configuration for a specific task."""
        task_configs = self._config.get("task_configs", {})
        task_config = task_configs.get(task_name, {})

        # Merge with defaults
        defaults = {
            "cache_expiration": self._config["tasks"]["default_cache_expiration"],
            "retries": self._config["tasks"]["max_retries"],
            "retry_delay": self._config["tasks"]["default_retry_delay"],
        }

        return {**defaults, **task_config}

    def get_cache_path(self) -> Path:
        """Get cache directory path."""
        cache_path = Path(self._config["cache"]["path"])
        cache_path.mkdir(parents=True, exist_ok=True)
        return cache_path

    def get_results_path(self) -> Path:
        """Get results directory path."""
        results_path = Path(self._config["results"]["storage"]["path"])
        results_path.mkdir(parents=True, exist_ok=True)
        return results_path

    def get_max_workers(self) -> int:
        """Get maximum number of concurrent workers."""
        return self._config["task_runner"]["max_workers"]

    @property
    def cache_enabled(self) -> bool:
        """Check if caching is enabled."""
        return self._config["cache"]["enabled"]
