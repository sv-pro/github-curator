"""Research workspace management."""

import logging
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class ResearchInfo:
    """Information about a research workspace."""

    name: str
    query: str
    created: datetime
    local_path: Path
    repo_count: int
    snapshot_count: int
    last_updated: datetime


class ResearchConfig:
    """Research workspace configuration."""

    def __init__(
        self,
        name: str,
        query: str,
        created: Optional[datetime] = None,
        theme: Optional[dict[str, Any]] = None,
        search: Optional[dict[str, Any]] = None,
        snapshots: Optional[list[dict[str, Any]]] = None,
    ):
        """Initialize research configuration.

        Args:
            name: Research name (must be filesystem-safe)
            query: Search query/theme
            created: Creation timestamp
            theme: Theme configuration (focus, exclude)
            search: Search parameters (min_stars, language, etc.)
            snapshots: List of snapshot metadata
        """
        self.name = name
        self.query = query
        self.created = created or datetime.utcnow()
        self.theme = theme or {}
        self.search = search or {}
        self.snapshots = snapshots or []

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {
            "name": self.name,
            "query": self.query,
            "created": self.created.isoformat(),
            "theme": self.theme,
            "search": self.search,
            "snapshots": self.snapshots,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResearchConfig":
        """Create from dictionary (YAML deserialization)."""
        return cls(
            name=data["name"],
            query=data["query"],
            created=datetime.fromisoformat(data["created"]),
            theme=data.get("theme", {}),
            search=data.get("search", {}),
            snapshots=data.get("snapshots", []),
        )


class ResearchManager:
    """Manages research workspaces."""

    def __init__(self, base_path: Optional[Path] = None):
        """Initialize research manager.

        Args:
            base_path: Base directory for research workspaces
                      (default: ~/.github-curator/research)
        """
        if base_path is None:
            base_path = Path.home() / ".github-curator" / "research"
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def get_research_path(self, name: str) -> Path:
        """Get path to research workspace."""
        return self.base_path / self._sanitize_name(name)

    def exists(self, name: str) -> bool:
        """Check if research workspace exists."""
        research_path = self.get_research_path(name)
        return research_path.exists() and (research_path / "config.yaml").exists()

    def create(
        self,
        name: str,
        query: str,
        focus: Optional[str] = None,
        exclude: Optional[str] = None,
        min_stars: Optional[int] = None,
        language: Optional[str] = None,
        max_age_days: Optional[int] = None,
    ) -> ResearchInfo:
        """Create new research workspace.

        Args:
            name: Research name (will be sanitized for filesystem)
            query: Search query/theme
            focus: Focus areas (comma-separated)
            exclude: Exclusion criteria (comma-separated)
            min_stars: Minimum GitHub stars
            language: Programming language filter
            max_age_days: Maximum days since last update

        Returns:
            ResearchInfo about created workspace

        Raises:
            ValueError: If research already exists
        """
        if self.exists(name):
            raise ValueError(f"Research '{name}' already exists")

        # Create workspace structure
        research_path = self.get_research_path(name)
        research_path.mkdir(parents=True, exist_ok=True)
        (research_path / "repos").mkdir(exist_ok=True)
        (research_path / "snapshots").mkdir(exist_ok=True)
        (research_path / "reports").mkdir(exist_ok=True)

        # Build configuration
        theme: dict[str, Any] = {}
        if focus:
            theme["focus"] = focus
        if exclude:
            theme["exclude"] = exclude

        search: dict[str, Any] = {}
        if min_stars is not None:
            search["min_stars"] = min_stars
        if language:
            search["language"] = language
        if max_age_days is not None:
            search["max_age_days"] = max_age_days

        config = ResearchConfig(name=name, query=query, theme=theme, search=search)

        # Save configuration
        self._save_config(research_path, config)

        logger.info(f"Created research workspace: {name} at {research_path}")

        return self._get_research_info(name, config, research_path)

    def load_config(self, name: str) -> ResearchConfig:
        """Load research configuration.

        Args:
            name: Research name

        Returns:
            ResearchConfig

        Raises:
            ValueError: If research doesn't exist
        """
        if not self.exists(name):
            raise ValueError(f"Research '{name}' does not exist")

        research_path = self.get_research_path(name)
        config_file = research_path / "config.yaml"

        with open(config_file) as f:
            data = yaml.safe_load(f)

        return ResearchConfig.from_dict(data)

    def save_config(self, name: str, config: ResearchConfig) -> None:
        """Save research configuration.

        Args:
            name: Research name
            config: Research configuration

        Raises:
            ValueError: If research doesn't exist
        """
        if not self.exists(name):
            raise ValueError(f"Research '{name}' does not exist")

        research_path = self.get_research_path(name)
        self._save_config(research_path, config)

    def list_research(self) -> list[ResearchInfo]:
        """List all research workspaces.

        Returns:
            List of ResearchInfo for all workspaces
        """
        research_list: list[ResearchInfo] = []

        if not self.base_path.exists():
            return research_list

        for research_dir in self.base_path.iterdir():
            if not research_dir.is_dir():
                continue

            config_file = research_dir / "config.yaml"
            if not config_file.exists():
                continue

            try:
                with open(config_file) as f:
                    data = yaml.safe_load(f)
                config = ResearchConfig.from_dict(data)
                info = self._get_research_info(config.name, config, research_dir)
                research_list.append(info)
            except Exception as e:
                logger.warning(f"Failed to load research {research_dir.name}: {e}")
                continue

        return sorted(research_list, key=lambda x: x.last_updated, reverse=True)

    def delete(self, name: str, confirm: bool = False) -> None:
        """Delete research workspace.

        Args:
            name: Research name
            confirm: Must be True to actually delete

        Raises:
            ValueError: If research doesn't exist or confirm is False
        """
        if not self.exists(name):
            raise ValueError(f"Research '{name}' does not exist")

        if not confirm:
            raise ValueError(
                "Must pass confirm=True to delete research workspace. "
                "This will delete all repos, snapshots, and reports."
            )

        research_path = self.get_research_path(name)
        shutil.rmtree(research_path)
        logger.info(f"Deleted research workspace: {name}")

    def get_repos_path(self, name: str) -> Path:
        """Get path to repos directory."""
        return self.get_research_path(name) / "repos"

    def get_snapshots_path(self, name: str) -> Path:
        """Get path to snapshots directory."""
        return self.get_research_path(name) / "snapshots"

    def get_reports_path(self, name: str) -> Path:
        """Get path to reports directory."""
        return self.get_research_path(name) / "reports"

    def _save_config(self, research_path: Path, config: ResearchConfig) -> None:
        """Save configuration to YAML file."""
        config_file = research_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config.to_dict(), f, default_flow_style=False, sort_keys=False)

    def _get_research_info(
        self, name: str, config: ResearchConfig, research_path: Path
    ) -> ResearchInfo:
        """Build ResearchInfo from config and filesystem."""
        repos_path = research_path / "repos"
        snapshots_path = research_path / "snapshots"

        # Count repos (subdirectories in repos/)
        repo_count = 0
        if repos_path.exists():
            for org_dir in repos_path.iterdir():
                if org_dir.is_dir():
                    repo_count += sum(1 for r in org_dir.iterdir() if r.is_dir())

        # Count snapshots (JSON files in snapshots/)
        snapshot_count = 0
        if snapshots_path.exists():
            snapshot_count = sum(1 for f in snapshots_path.glob("*.json"))

        # Last updated from config or mtime
        last_updated = config.created
        if config.snapshots:
            latest_snapshot = max(config.snapshots, key=lambda s: s.get("date", ""), default=None)
            if latest_snapshot and "date" in latest_snapshot:
                last_updated = datetime.fromisoformat(latest_snapshot["date"])

        return ResearchInfo(
            name=name,
            query=config.query,
            created=config.created,
            local_path=research_path,
            repo_count=repo_count,
            snapshot_count=snapshot_count,
            last_updated=last_updated,
        )

    def _sanitize_name(self, name: str) -> str:
        """Sanitize research name for filesystem.

        Converts to lowercase, replaces spaces with hyphens,
        removes unsafe characters.
        """
        import re

        # Convert to lowercase
        name = name.lower()
        # Replace spaces and underscores with hyphens
        name = re.sub(r"[\s_]+", "-", name)
        # Remove non-alphanumeric characters except hyphens
        name = re.sub(r"[^a-z0-9-]", "", name)
        # Remove leading/trailing hyphens
        name = name.strip("-")
        # Collapse multiple hyphens
        name = re.sub(r"-+", "-", name)

        if not name:
            raise ValueError("Research name must contain alphanumeric characters")

        return name
