"""Knowledge store for repository corpus management."""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


@dataclass
class RepositoryEntry:
    """Repository entry in knowledge base."""

    full_name: str
    topics: list[str]
    features: dict[str, Any]
    language: Optional[str]
    stars: int
    added: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RepositoryEntry":
        """Create from dictionary."""
        return cls(**data)


class KnowledgeStore:
    """File-based knowledge store for repository corpus.

    Manages knowledge base with the following structure:
    - repositories.jsonl: One repo per line (streaming format)
    - metadata.json: Stats and metadata
    - topic_patterns.json: Topic → features/keywords/examples
    - topic_cooccurrence.json: Topic co-occurrence matrix

    This is Phase 1 implementation using file storage only.
    Future phases will add ChromaDB and NetworkX.
    """

    def __init__(self, base_path: str = ".curator/knowledge"):
        """Initialize knowledge store.

        Args:
            base_path: Base directory for knowledge base files
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        # File paths
        self.repos_file = self.base_path / "repositories.jsonl"
        self.metadata_file = self.base_path / "metadata.json"
        self.patterns_file = self.base_path / "topic_patterns.json"
        self.cooccurrence_file = self.base_path / "topic_cooccurrence.json"

        # Initialize metadata if doesn't exist
        if not self.metadata_file.exists():
            self._save_metadata(
                {
                    "version": "1.0",
                    "last_updated": datetime.now().isoformat(),
                    "total_repositories": 0,
                    "total_topics": 0,
                }
            )

    def add_repository(
        self,
        full_name: str,
        topics: list[str],
        features: dict[str, Any],
        language: Optional[str] = None,
        stars: int = 0,
    ) -> str:
        """Add repository to knowledge base.

        Args:
            full_name: Repository full name (owner/repo)
            topics: List of GitHub topics
            features: Extracted features dict
            language: Primary programming language
            stars: Star count

        Returns:
            Repository ID (full_name)
        """
        entry = RepositoryEntry(
            full_name=full_name,
            topics=topics,
            features=features,
            language=language,
            stars=stars,
            added=datetime.now().isoformat(),
        )

        # Append to JSONL file
        with open(self.repos_file, "a") as f:
            json.dump(entry.to_dict(), f)
            f.write("\n")

        # Update metadata
        self._increment_repository_count()

        return full_name

    def get_repository(self, full_name: str) -> Optional[RepositoryEntry]:
        """Get repository by full name.

        Args:
            full_name: Repository full name (owner/repo)

        Returns:
            Repository entry if found, None otherwise
        """
        if not self.repos_file.exists():
            return None

        with open(self.repos_file) as f:
            for line in f:
                data = json.loads(line)
                if data["full_name"] == full_name:
                    return RepositoryEntry.from_dict(data)

        return None

    def has_repository(self, full_name: str) -> bool:
        """Check if repository exists in knowledge base.

        Args:
            full_name: Repository full name (owner/repo)

        Returns:
            True if exists, False otherwise
        """
        return self.get_repository(full_name) is not None

    def update_repository(
        self,
        full_name: str,
        topics: list[str],
        features: dict[str, Any],
        language: Optional[str] = None,
        stars: int = 0,
    ) -> bool:
        """Update existing repository.

        Args:
            full_name: Repository full name (owner/repo)
            topics: Updated topics
            features: Updated features
            language: Updated language
            stars: Updated stars

        Returns:
            True if updated, False if not found
        """
        if not self.repos_file.exists():
            return False

        # Read all entries
        entries = []
        found = False
        with open(self.repos_file) as f:
            for line in f:
                data = json.loads(line)
                if data["full_name"] == full_name:
                    # Update this entry
                    data["topics"] = topics
                    data["features"] = features
                    data["language"] = language
                    data["stars"] = stars
                    data["added"] = datetime.now().isoformat()  # Update timestamp
                    found = True
                entries.append(data)

        if not found:
            return False

        # Rewrite file
        with open(self.repos_file, "w") as f:
            for entry in entries:
                json.dump(entry, f)
                f.write("\n")

        return True

    def list_repositories(self, limit: Optional[int] = None) -> list[RepositoryEntry]:
        """List all repositories.

        Args:
            limit: Maximum number to return

        Returns:
            List of repository entries
        """
        if not self.repos_file.exists():
            return []

        repos = []
        with open(self.repos_file) as f:
            for i, line in enumerate(f):
                if limit and i >= limit:
                    break
                data = json.loads(line)
                repos.append(RepositoryEntry.from_dict(data))

        return repos

    def get_stats(self) -> dict[str, Any]:
        """Get knowledge base statistics.

        Returns:
            Statistics dict with counts and metadata
        """
        metadata = self._load_metadata()

        # Count unique topics
        unique_topics = set()
        if self.repos_file.exists():
            with open(self.repos_file) as f:
                for line in f:
                    data = json.loads(line)
                    unique_topics.update(data.get("topics", []))

        metadata["total_topics"] = len(unique_topics)

        return metadata

    def learn_patterns(self) -> dict[str, Any]:
        """Learn patterns from repository data.

        Analyzes repositories to extract:
        - Topic → features mapping
        - Topic co-occurrence matrix
        - Common keywords per topic

        Returns:
            Pattern statistics
        """
        if not self.repos_file.exists():
            return {"patterns": 0, "topics": 0}

        # Collect topic data
        topic_features: dict[str, list[dict[str, Any]]] = {}
        topic_repos: dict[str, list[str]] = {}
        topic_cooccurrence: dict[str, dict[str, int]] = {}

        with open(self.repos_file) as f:
            for line in f:
                data = json.loads(line)
                topics = data.get("topics", [])
                features = data.get("features", {})

                for topic in topics:
                    # Collect features for this topic
                    if topic not in topic_features:
                        topic_features[topic] = []
                        topic_repos[topic] = []
                    topic_features[topic].append(features)
                    topic_repos[topic].append(data["full_name"])

                    # Build co-occurrence matrix
                    if topic not in topic_cooccurrence:
                        topic_cooccurrence[topic] = {}
                    for other_topic in topics:
                        if other_topic != topic:
                            topic_cooccurrence[topic][other_topic] = (
                                topic_cooccurrence[topic].get(other_topic, 0) + 1
                            )

        # Build topic patterns
        patterns = {}
        for topic, feature_list in topic_features.items():
            # Find common features for this topic
            patterns[topic] = {
                "count": len(feature_list),
                "examples": topic_repos[topic][:5],  # First 5 examples
                "common_features": self._extract_common_features(feature_list),
            }

        # Save patterns
        with open(self.patterns_file, "w") as f:
            json.dump(patterns, f, indent=2)

        # Save co-occurrence matrix
        with open(self.cooccurrence_file, "w") as f:
            json.dump(topic_cooccurrence, f, indent=2)

        # Update metadata
        metadata = self._load_metadata()
        metadata["total_patterns"] = len(patterns)
        metadata["last_updated"] = datetime.now().isoformat()
        self._save_metadata(metadata)

        return {"patterns": len(patterns), "topics": len(topic_features)}

    def _extract_common_features(self, feature_list: list[dict[str, Any]]) -> dict[str, Any]:
        """Extract common features from list of feature dicts.

        Args:
            feature_list: List of feature dictionaries

        Returns:
            Common features summary
        """
        if not feature_list:
            return {}

        # Count boolean features
        bool_counts: dict[str, int] = {}
        for features in feature_list:
            for key, value in features.items():
                if isinstance(value, bool) and value:
                    bool_counts[key] = bool_counts.get(key, 0) + 1

        # Return features present in >50% of repos
        threshold = len(feature_list) * 0.5
        common = {
            key: count / len(feature_list)
            for key, count in bool_counts.items()
            if count >= threshold
        }

        return common

    def _load_metadata(self) -> dict[str, Any]:
        """Load metadata from file."""
        if not self.metadata_file.exists():
            return {}

        with open(self.metadata_file) as f:
            return json.load(f)

    def _save_metadata(self, metadata: dict[str, Any]) -> None:
        """Save metadata to file."""
        with open(self.metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

    def _increment_repository_count(self) -> None:
        """Increment repository count in metadata."""
        metadata = self._load_metadata()
        metadata["total_repositories"] = metadata.get("total_repositories", 0) + 1
        metadata["last_updated"] = datetime.now().isoformat()
        self._save_metadata(metadata)
