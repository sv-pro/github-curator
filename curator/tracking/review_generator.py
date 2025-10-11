"""Generates human-readable REVIEW.md content with rich LLM-generated narratives."""

from datetime import datetime
from typing import Any, Optional

from anthropic import Anthropic


class ReviewGenerator:
    """Generates publication-ready review content with rich, actual content."""

    def __init__(
        self,
        anthropic_client: Optional[Anthropic] = None,
        model: str = "claude-sonnet-4-5-20250929",
    ):
        """Initialize review generator.

        Args:
            anthropic_client: Anthropic client for LLM-generated content
            model: Model to use for generation
        """
        self.anthropic_client = anthropic_client or Anthropic()
        self.model = model

    def generate_review(
        self,
        org: str,
        repo: str,
        theme: str,
        overall_score: float,
        confidence: float,
        dimensions: dict[str, dict[str, Any]],
        evidence: list[str],
        repo_description: Optional[str] = None,
        readme_excerpt: Optional[str] = None,
        first_reviewed: Optional[datetime] = None,
    ) -> str:
        """Generate rich REVIEW.md content using LLM.

        Args:
            org: Repository organization
            repo: Repository name
            theme: Curation theme
            overall_score: Overall score (0-10)
            confidence: Overall confidence (0-1)
            dimensions: Dimension evaluations with scores, confidence, reasoning
            evidence: List of evidence items
            repo_description: Repository description from GitHub
            readme_excerpt: Excerpt from README for context
            first_reviewed: Optional date of first review

        Returns:
            Rich markdown review with actual content
        """
        # Prepare evaluation context for LLM
        evaluation_context = self._format_evaluation_context(
            org=org,
            repo=repo,
            theme=theme,
            overall_score=overall_score,
            confidence=confidence,
            dimensions=dimensions,
            evidence=evidence,
            repo_description=repo_description,
            readme_excerpt=readme_excerpt,
        )

        # Generate rich narrative using LLM
        prompt = f"""You are writing a publication-ready repository review for a technical blog or documentation site.

Given this repository evaluation data, write a compelling, informative review that goes beyond just restating the scores.

{evaluation_context}

Write a review with these sections:

## At a Glance
A compelling 2-3 paragraph introduction that captures what makes this repository special (or not).
Be specific about actual features, approaches, or characteristics you observed. Don't just restate scores.

## Deep Dive
For each top dimension, write a substantive paragraph explaining:
- What specific aspects were evaluated
- Concrete examples from the evidence
- Why this matters for the theme
- Any standout features or concerns

## Real-World Context
Write about:
- Who should (or shouldn't) use this
- Specific use cases where it excels
- How it compares to alternatives (if evident from the evaluation)
- Production readiness considerations

## Bottom Line
A honest, nuanced conclusion that synthesizes the evaluation. Not just "it's good/bad" but actual insight.

Guidelines:
- Write in engaging, professional prose (not bullet points except where natural)
- Be specific - reference actual evidence, not generic statements
- Be honest - acknowledge weaknesses if score/confidence indicates them
- Write for developers who want substance, not marketing
- Use technical language appropriately
- Avoid phrases like "this project" - use the repo name or "it"
- Don't just restate dimension scores - provide insight

Return ONLY the markdown content for these sections, starting with "## At a Glance"."""

        try:
            response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )

            llm_content = response.content[0].text.strip()

        except Exception:
            # Fallback to template-based generation if LLM fails
            llm_content = self._generate_fallback_content(
                repo=repo,
                theme=theme,
                overall_score=overall_score,
                dimensions=dimensions,
                evidence=evidence,
            )

        # Build final markdown with header and footer
        timestamp = datetime.utcnow().strftime("%Y-%m-%d")
        conf_pct = int(confidence * 100)

        header = f"""# {repo}

> **Last reviewed**: {timestamp} | **Theme**: "{theme}" | **Score**: {overall_score:.1f}/10 | **Confidence**: {conf_pct}%

"""

        # Review history section
        history = "\n\n---\n\n## Review History\n\n"
        if first_reviewed:
            first_date = first_reviewed.strftime("%Y-%m-%d")
            history += f"- **First reviewed**: {first_date}\n"
        history += f"- **Latest review**: {timestamp}\n"

        # Footer
        footer = """\n\n---\n\n*Review generated by [GitHub Curator](https://github.com/IntentHub/github-curator) with metacognitive evaluation*\n"""

        return header + llm_content + history + footer

    def _format_evaluation_context(
        self,
        org: str,
        repo: str,
        theme: str,
        overall_score: float,
        confidence: float,
        dimensions: dict[str, dict[str, Any]],
        evidence: list[str],
        repo_description: Optional[str],
        readme_excerpt: Optional[str],
    ) -> str:
        """Format evaluation data for LLM prompt."""
        lines = [
            f"REPOSITORY: {org}/{repo}",
            f"DESCRIPTION: {repo_description or 'No description'}",
            f"THEME: {theme}",
            f"OVERALL SCORE: {overall_score:.1f}/10",
            f"CONFIDENCE: {confidence:.2f} ({self._confidence_label(confidence)})",
            "",
            "DIMENSION SCORES:",
        ]

        # Sort dimensions by score
        sorted_dims = sorted(dimensions.items(), key=lambda x: x[1].get("score", 0), reverse=True)

        for dim_name, dim_data in sorted_dims:
            score = dim_data.get("score", 0.0)
            conf = dim_data.get("confidence", 0.0)
            reasoning = dim_data.get("reasoning", "")
            lines.append(f"  - {dim_name}: {score:.1f}/10 (confidence: {conf:.2f})")
            if reasoning:
                # Truncate long reasoning
                reasoning_short = reasoning[:200] + "..." if len(reasoning) > 200 else reasoning
                lines.append(f"    Reasoning: {reasoning_short}")

        lines.extend(["", "KEY EVIDENCE:"])
        for item in evidence[:10]:
            lines.append(f"  - {item}")

        if readme_excerpt:
            lines.extend(["", "README EXCERPT:", readme_excerpt[:500]])

        return "\n".join(lines)

    def _generate_fallback_content(
        self,
        repo: str,
        theme: str,
        overall_score: float,
        dimensions: dict[str, dict[str, Any]],
        evidence: list[str],
    ) -> str:
        """Generate fallback content if LLM fails."""
        quality_desc = self._score_description(overall_score)

        lines = [
            "## At a Glance",
            "",
            f'{repo} {quality_desc} when evaluated against the theme "{theme}" '
            f"with an overall score of {overall_score:.1f}/10.",
            "",
            "## Key Dimensions",
            "",
        ]

        sorted_dims = sorted(dimensions.items(), key=lambda x: x[1].get("score", 0), reverse=True)

        for dim_name, dim_data in sorted_dims[:5]:
            score = dim_data.get("score", 0.0)
            reasoning = dim_data.get("reasoning", "No detailed reasoning provided.")
            lines.extend([f"### {dim_name} ({score:.1f}/10)", "", reasoning, ""])

        lines.extend(["## Supporting Evidence", ""])
        for item in evidence[:5]:
            lines.append(f"- {item}")

        lines.extend(["", "## Bottom Line", ""])
        lines.append(
            f'This repository scored {overall_score:.1f}/10 for the theme "{theme}". '
            "Refer to the dimension evaluations above for detailed assessment."
        )

        return "\n".join(lines)

    @staticmethod
    def _score_description(score: float) -> str:
        """Convert score to descriptive phrase."""
        if score >= 9.0:
            return "stands out as exceptional"
        elif score >= 8.0:
            return "demonstrates strong quality"
        elif score >= 7.0:
            return "shows good quality"
        elif score >= 6.0:
            return "presents adequate quality"
        elif score >= 5.0:
            return "shows moderate quality"
        else:
            return "has room for improvement"

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
