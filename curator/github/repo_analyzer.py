"""Repository content analysis and context gathering."""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from curator.github.api_client import GitHubAPIClient, SearchResult
import yaml


@dataclass
class RepositoryContext:
    """Aggregated context about a repository for evaluation."""
    full_name: str
    metadata: SearchResult
    readme_content: Optional[str] = None
    file_structure: Dict[str, Any] = field(default_factory=dict)
    additional_files: Dict[str, str] = field(default_factory=dict)
    directory_listing: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "full_name": self.full_name,
            "metadata": {
                "name": self.metadata.name,
                "owner": self.metadata.owner,
                "description": self.metadata.description,
                "stars": self.metadata.stars,
                "last_updated": self.metadata.last_updated.isoformat(),
                "language": self.metadata.language,
                "license": self.metadata.license_name,
                "url": self.metadata.url,
                "topics": self.metadata.topics
            },
            "readme_content": self.readme_content,
            "file_structure": self.file_structure,
            "additional_files": self.additional_files,
            "directory_listing": self.directory_listing
        }


class RepositoryAnalyzer:
    """Analyzes repository content and gathers context for evaluation."""

    def __init__(self, github_client: GitHubAPIClient, config_path: str = "config/curator.yaml"):
        """Initialize analyzer.

        Args:
            github_client: GitHub API client instance
            config_path: Path to configuration file
        """
        self.github_client = github_client
        self.config = self._load_config(config_path)
        self.context_files = self.config['github']['context_files']

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def analyze_repository(self, repo: SearchResult) -> RepositoryContext:
        """Gather comprehensive context about a repository.

        Args:
            repo: SearchResult from GitHub search

        Returns:
            RepositoryContext with all gathered information
        """
        context = RepositoryContext(
            full_name=repo.full_name,
            metadata=repo
        )

        # Get README
        context.readme_content = self.github_client.get_readme_content(repo.full_name)

        # Get file structure
        context.file_structure = self.github_client.get_repository_structure(
            repo.full_name,
            max_depth=2
        )

        # Get root directory listing
        context.directory_listing = self.github_client.list_directory(repo.full_name, "")

        # Try to fetch additional context files
        for file_spec in self.context_files:
            if file_spec.endswith('/'):
                # It's a directory - list it
                dir_contents = self.github_client.list_directory(repo.full_name, file_spec.rstrip('/'))
                if dir_contents:
                    context.additional_files[file_spec] = f"Directory contains: {', '.join(dir_contents)}"
            else:
                # It's a file - try to get content
                content = self.github_client.get_file_content(repo.full_name, file_spec)
                if content:
                    # Limit content length to avoid overwhelming context
                    context.additional_files[file_spec] = content[:5000] + ("..." if len(content) > 5000 else "")

        return context

    def extract_key_features(self, context: RepositoryContext) -> Dict[str, Any]:
        """Extract key features from repository context.

        Args:
            context: RepositoryContext object

        Returns:
            Dictionary of extracted features
        """
        features = {
            "has_readme": context.readme_content is not None,
            "readme_length": len(context.readme_content) if context.readme_content else 0,
            "has_license": context.metadata.license_name is not None,
            "primary_language": context.metadata.language,
            "topics": context.metadata.topics,
            "stars": context.metadata.stars,
        }

        # Check for common important files
        important_files = [
            "LICENSE", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md",
            "ARCHITECTURE.md", "DESIGN.md", ".github/", "docs/",
            "examples/", "tests/", "test/"
        ]

        for file_name in important_files:
            if file_name.endswith('/'):
                features[f"has_{file_name.rstrip('/')}"] = file_name.rstrip('/') in context.directory_listing
            else:
                features[f"has_{file_name.lower().replace('.', '_')}"] = file_name in context.directory_listing

        # Analyze directory structure depth
        features["structure_depth"] = self._calculate_structure_depth(context.file_structure)

        # Check for documentation indicators in README
        if context.readme_content:
            readme_lower = context.readme_content.lower()
            features["readme_has_installation"] = "installation" in readme_lower or "install" in readme_lower
            features["readme_has_usage"] = "usage" in readme_lower or "example" in readme_lower
            features["readme_has_api"] = "api" in readme_lower
            features["readme_has_architecture"] = "architecture" in readme_lower or "design" in readme_lower
            features["readme_has_contributing"] = "contributing" in readme_lower

        return features

    def _calculate_structure_depth(self, structure: Dict[str, Any], current_depth: int = 0) -> int:
        """Calculate maximum depth of directory structure."""
        if not structure:
            return current_depth

        max_depth = current_depth
        for value in structure.values():
            if isinstance(value, dict):
                depth = self._calculate_structure_depth(value, current_depth + 1)
                max_depth = max(max_depth, depth)

        return max_depth

    def get_evaluation_context_summary(self, context: RepositoryContext) -> str:
        """Create a text summary of repository context for LLM evaluation.

        Args:
            context: RepositoryContext object

        Returns:
            Formatted string summarizing repository for evaluation
        """
        features = self.extract_key_features(context)

        summary_parts = [
            f"Repository: {context.full_name}",
            f"Description: {context.metadata.description}",
            f"Language: {context.metadata.language}",
            f"Stars: {context.metadata.stars}",
            f"License: {context.metadata.license_name or 'None'}",
            f"Topics: {', '.join(context.metadata.topics) if context.metadata.topics else 'None'}",
            f"Last updated: {context.metadata.last_updated.strftime('%Y-%m-%d')}",
            "",
            "Key Features:",
        ]

        # Add important features
        important_features = [
            ("Documentation", features.get("has_readme", False)),
            ("Architecture docs", features.get("has_architecture_md", False)),
            ("Examples", features.get("has_examples", False)),
            ("Tests", features.get("has_tests", False) or features.get("has_test", False)),
            ("Contributing guide", features.get("has_contributing_md", False)),
        ]

        for feature_name, has_feature in important_features:
            summary_parts.append(f"- {feature_name}: {'Yes' if has_feature else 'No'}")

        # Add README highlights
        if context.readme_content:
            summary_parts.extend([
                "",
                f"README ({len(context.readme_content)} chars):",
                context.readme_content[:2000] + ("..." if len(context.readme_content) > 2000 else "")
            ])

        # Add directory structure
        if context.directory_listing:
            summary_parts.extend([
                "",
                "Root directory:",
                ", ".join(context.directory_listing[:20])
            ])

        # Add additional files
        if context.additional_files:
            summary_parts.append("")
            summary_parts.append("Additional context files:")
            for file_name, content in context.additional_files.items():
                summary_parts.append(f"\n{file_name}:")
                summary_parts.append(content[:1000] + ("..." if len(content) > 1000 else ""))

        return "\n".join(summary_parts)
