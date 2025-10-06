"""Knowledge base for storing and retrieving repository patterns and topics."""

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from curator.github.repo_analyzer import RepositoryContext
from curator.knowledge.topic_pattern import SimilarRepo, TopicPattern


@dataclass
class RepositoryRecord:
    """A repository record in the knowledge base."""

    full_name: str
    topics: list[str] = field(default_factory=list)
    features: dict[str, Any] = field(default_factory=dict)
    language: Optional[str] = None
    stars: int = 0
    added: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            "full_name": self.full_name,
            "topics": self.topics,
            "features": self.features,
            "language": self.language,
            "stars": self.stars,
            "added": self.added,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RepositoryRecord":
        """Create from dictionary."""
        return cls(
            full_name=data["full_name"],
            topics=data.get("topics", []),
            features=data.get("features", {}),
            language=data.get("language"),
            stars=data.get("stars", 0),
            added=data.get("added", datetime.utcnow().isoformat()),
        )


class KnowledgeBase:
    """Stores and retrieves learned patterns from curation history."""

    def __init__(self, base_path: str = ".curator/knowledge"):
        """Initialize knowledge base.

        Args:
            base_path: Directory for knowledge base storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        self.repos_file = self.base_path / "repositories.jsonl"
        self.patterns_file = self.base_path / "topic_patterns.json"
        self.cooccurrence_file = self.base_path / "topic_cooccurrence.json"
        self.metadata_file = self.base_path / "metadata.json"

        # In-memory cache
        self.repositories: list[RepositoryRecord] = []
        self.topic_patterns: dict[str, TopicPattern] = {}
        self.topic_cooccurrence: dict[tuple[str, str], float] = {}

        # Load existing data
        self._load()

    def _load(self) -> None:
        """Load knowledge base from disk."""
        # Load repositories
        if self.repos_file.exists():
            with open(self.repos_file) as f:
                for line in f:
                    if line.strip():
                        repo_data = json.loads(line)
                        self.repositories.append(RepositoryRecord.from_dict(repo_data))

        # Load patterns
        if self.patterns_file.exists():
            with open(self.patterns_file) as f:
                patterns_data = json.load(f)
                self.topic_patterns = {
                    topic: TopicPattern.from_dict({**pattern_data, "topic": topic})
                    for topic, pattern_data in patterns_data.items()
                }

        # Load co-occurrence
        if self.cooccurrence_file.exists():
            with open(self.cooccurrence_file) as f:
                cooccur_data = json.load(f)
                # Convert string keys back to tuples
                self.topic_cooccurrence = {
                    tuple(key.split("|")): score for key, score in cooccur_data.items()
                }

    def save(self) -> None:
        """Save knowledge base to disk."""
        # Save repositories (JSONL format)
        with open(self.repos_file, "w") as f:
            for repo in self.repositories:
                f.write(json.dumps(repo.to_dict()) + "\n")

        # Save patterns
        patterns_dict = {topic: pattern.to_dict() for topic, pattern in self.topic_patterns.items()}
        with open(self.patterns_file, "w") as f:
            json.dump(patterns_dict, f, indent=2)

        # Save co-occurrence (convert tuple keys to strings)
        cooccur_dict = {f"{t1}|{t2}": score for (t1, t2), score in self.topic_cooccurrence.items()}
        with open(self.cooccurrence_file, "w") as f:
            json.dump(cooccur_dict, f, indent=2)

        # Save metadata
        metadata = {
            "version": "1.0",
            "last_updated": datetime.utcnow().isoformat(),
            "total_repositories": len(self.repositories),
            "total_topics": len(self.topic_patterns),
        }
        with open(self.metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

    def add_repository(self, context: RepositoryContext, features: dict[str, Any]) -> None:
        """Add a repository to the knowledge base.

        Args:
            context: Repository context from analysis
            features: Extracted features from analyzer
        """
        record = RepositoryRecord(
            full_name=context.full_name,
            topics=context.metadata.topics,
            features=features,
            language=context.metadata.language,
            stars=context.metadata.stars,
        )
        self.repositories.append(record)

    def load_from_curation(self, curation_output_dir: Path) -> None:
        """Load knowledge from curation output.

        Args:
            curation_output_dir: Path to curation output directory
        """
        # Load evaluations
        evaluations_dir = curation_output_dir / "evaluations"
        if not evaluations_dir.exists():
            return

        # This is a placeholder - actual implementation would need to
        # reload the evaluation contexts or store them separately
        # For now, we'll load from summary if available
        summary_file = curation_output_dir / "summary.json"
        if summary_file.exists():
            with open(summary_file) as f:
                summary = json.load(f)

            for repo_data in summary.get("top_repositories", []):
                # Create minimal record from summary
                # In a full implementation, we'd have more data
                record = RepositoryRecord(
                    full_name=repo_data["repo"],
                    topics=[],  # Would need to fetch these
                    features={},
                    stars=0,
                )
                self.repositories.append(record)

    def learn_patterns(self) -> None:
        """Learn topic patterns from stored repositories."""
        # Group repos by topic
        topic_repos: dict[str, list[RepositoryRecord]] = defaultdict(list)
        for repo in self.repositories:
            for topic in repo.topics:
                topic_repos[topic].append(repo)

        # Learn pattern for each topic
        for topic, repos in topic_repos.items():
            if len(repos) < 2:  # Need at least 2 examples
                continue

            # Collect features and keywords
            all_features = []
            all_keywords = []

            for repo in repos:
                # Features
                for feature, value in repo.features.items():
                    if value is True:  # Boolean features
                        all_features.append(feature)

                # Keywords from repo name and topics
                name_parts = repo.full_name.lower().split("/")[-1].split("-")
                all_keywords.extend(name_parts)
                all_keywords.extend([t for t in repo.topics if t != topic])

            # Find most common features
            feature_counts = Counter(all_features)
            common_features = [
                feat for feat, count in feature_counts.most_common(10) if count >= len(repos) * 0.3
            ]

            # Find most common keywords
            keyword_counts = Counter(all_keywords)
            common_keywords = [
                kw for kw, count in keyword_counts.most_common(10) if count >= len(repos) * 0.3
            ]

            # Create pattern
            self.topic_patterns[topic] = TopicPattern(
                topic=topic,
                common_features=common_features,
                common_keywords=common_keywords,
                example_repos=[r.full_name for r in repos[:5]],
                confidence_threshold=0.5,
            )

        # Learn topic co-occurrence
        self._learn_cooccurrence()

    def _learn_cooccurrence(self) -> None:
        """Learn which topics commonly appear together."""
        topic_pairs: dict[tuple[str, str], int] = Counter()

        for repo in self.repositories:
            topics = sorted(repo.topics)  # Sort for consistent ordering
            for i, t1 in enumerate(topics):
                for t2 in topics[i + 1 :]:
                    topic_pairs[(t1, t2)] += 1

        # Convert counts to probabilities
        total_repos = len(self.repositories)
        if total_repos > 0:
            self.topic_cooccurrence = {
                pair: count / total_repos for pair, count in topic_pairs.items()
            }

    def find_similar_repos(
        self, target_features: dict[str, Any], language: Optional[str] = None, limit: int = 10
    ) -> list[SimilarRepo]:
        """Find similar repositories in knowledge base.

        Args:
            target_features: Features of target repository
            language: Primary language (for filtering)
            limit: Maximum number of similar repos to return

        Returns:
            List of similar repositories ranked by similarity
        """
        similar: list[tuple[RepositoryRecord, float, list[str]]] = []

        for repo in self.repositories:
            # Skip if language doesn't match (if specified)
            if language and repo.language != language:
                continue

            # Calculate feature similarity
            shared_features = []
            for feature, value in target_features.items():
                if feature in repo.features and repo.features[feature] == value:
                    shared_features.append(feature)

            if not shared_features:
                continue

            # Similarity score = proportion of matching features
            total_features = len(set(target_features.keys()) | set(repo.features.keys()))
            similarity = len(shared_features) / total_features if total_features > 0 else 0

            similar.append((repo, similarity, shared_features))

        # Sort by similarity
        similar.sort(key=lambda x: x[1], reverse=True)

        # Convert to SimilarRepo objects
        return [
            SimilarRepo(
                full_name=repo.full_name,
                similarity_score=score,
                topics=repo.topics,
                shared_features=features,
            )
            for repo, score, features in similar[:limit]
        ]

    def get_topic_patterns(self) -> dict[str, TopicPattern]:
        """Get learned patterns for each topic."""
        return self.topic_patterns.copy()

    def get_topic_cooccurrence(self) -> dict[tuple[str, str], float]:
        """Get topic co-occurrence statistics."""
        return self.topic_cooccurrence.copy()

    def get_stats(self) -> dict[str, Any]:
        """Get knowledge base statistics."""
        return {
            "total_repositories": len(self.repositories),
            "total_topics": len({t for r in self.repositories for t in r.topics}),
            "total_patterns": len(self.topic_patterns),
            "languages": list({r.language for r in self.repositories if r.language}),
        }
