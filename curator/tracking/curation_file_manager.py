"""Manages CURATION.md file formatting and content."""

from datetime import datetime
from typing import Any


class CurationFileManager:
    """Formats and manages CURATION.md content."""

    @staticmethod
    def format_entry(
        theme: str,
        overall_score: float,
        confidence: float,
        dimensions: dict[str, dict[str, Any]],
        evidence: list[str],
        repo_commit: str = "unknown",
    ) -> str:
        """Format a curation evaluation entry for CURATION.md.

        Args:
            theme: Curation theme
            overall_score: Overall evaluation score (0-10)
            confidence: Overall confidence (0-1)
            dimensions: Dict of dimension_name -> {score, confidence}
            evidence: List of evidence strings
            repo_commit: Git commit hash of evaluated code

        Returns:
            Formatted markdown entry
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        tag_num = CurationFileManager._generate_tag_suffix()

        # Header
        lines = [
            f"## [{timestamp}] Theme: {theme}",
            "",
            f"**Tag**: curation-{tag_num}",
            f"**Overall Score**: {overall_score:.1f}/10",
            f"**Confidence**: {CurationFileManager._confidence_label(confidence)} ({confidence:.2f})",
            f"**Repository Commit**: {repo_commit[:7]}",
            "",
        ]

        # Dimensions
        if dimensions:
            lines.append("### Evaluation Dimensions")
            lines.append("")
            for dim_name, dim_data in dimensions.items():
                score = dim_data.get("score", 0.0)
                conf = dim_data.get("confidence", 0.0)
                lines.append(
                    f"- **{dim_name}**: {score:.1f}/10 "
                    f"(confidence: {CurationFileManager._confidence_label(conf)} {conf:.2f})"
                )
            lines.append("")

        # Evidence
        if evidence:
            lines.append("### Key Evidence")
            lines.append("")
            for item in evidence:
                lines.append(f"- {item}")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _confidence_label(confidence: float) -> str:
        """Convert confidence score to human label."""
        if confidence >= 0.8:
            return "High"
        elif confidence >= 0.6:
            return "Medium"
        elif confidence >= 0.4:
            return "Low"
        else:
            return "Very Low"

    @staticmethod
    def _generate_tag_suffix() -> str:
        """Generate tag suffix (timestamp-based)."""
        return datetime.utcnow().strftime("%Y%m%d")
