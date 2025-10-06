"""Topic patterns and suggestions for topic inference."""

from dataclasses import dataclass, field


@dataclass
class TopicPattern:
    """Pattern learned for a specific topic."""

    topic: str
    common_features: list[str] = field(default_factory=list)  # e.g., ["has_tests", "python"]
    common_keywords: list[str] = field(default_factory=list)  # e.g., ["async", "framework"]
    example_repos: list[str] = field(default_factory=list)  # repos that have this topic
    confidence_threshold: float = 0.5

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "topic": self.topic,
            "common_features": self.common_features,
            "common_keywords": self.common_keywords,
            "example_repos": self.example_repos,
            "confidence_threshold": self.confidence_threshold,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TopicPattern":
        """Create from dictionary."""
        return cls(
            topic=data["topic"],
            common_features=data.get("common_features", []),
            common_keywords=data.get("common_keywords", []),
            example_repos=data.get("example_repos", []),
            confidence_threshold=data.get("confidence_threshold", 0.5),
        )


@dataclass
class SimilarRepo:
    """A repository similar to target."""

    full_name: str
    similarity_score: float
    topics: list[str] = field(default_factory=list)
    shared_features: list[str] = field(default_factory=list)


@dataclass
class TopicSuggestion:
    """A suggested topic with metadata."""

    topic: str
    confidence: float  # 0.0 to 1.0
    reasoning: str  # why this topic was suggested
    sources: list[str] = field(
        default_factory=list
    )  # e.g., ["similar_repos", "pattern_match", "llm_inference"]
    already_assigned: bool = False  # if repo already has this topic

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "topic": self.topic,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "sources": self.sources,
            "already_assigned": self.already_assigned,
        }
