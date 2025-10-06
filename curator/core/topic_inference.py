"""Topic inference engine for suggesting repository topics."""

import re

from anthropic import Anthropic

from curator.github.repo_analyzer import RepositoryContext
from curator.knowledge.knowledge_base import KnowledgeBase
from curator.knowledge.topic_pattern import SimilarRepo, TopicSuggestion


class TopicInferenceEngine:
    """Infers topics for a repository using knowledge base and LLM."""

    def __init__(self, knowledge_base: KnowledgeBase, anthropic_client: Anthropic, model: str):
        """Initialize topic inference engine.

        Args:
            knowledge_base: Knowledge base with learned patterns
            anthropic_client: Anthropic API client
            model: Claude model to use
        """
        self.kb = knowledge_base
        self.client = anthropic_client
        self.model = model

    def infer_topics(
        self,
        target: RepositoryContext,
        features: dict,
        blind_mode: bool = True,
    ) -> list[TopicSuggestion]:
        """Infer topics for target repository.

        Args:
            target: Repository context
            features: Extracted features
            blind_mode: If True, don't look at existing topics (for comparison)

        Returns:
            List of topic suggestions
        """
        # Get existing topics (only for comparison output, not inference)
        existing_topics = set(target.metadata.topics) if not blind_mode else set()

        # Step 1: Find pattern matches
        pattern_topics = self._find_pattern_matches(features)

        # Step 2: Find similar repos
        similar_repos = self.kb.find_similar_repos(
            features, language=target.metadata.language, limit=10
        )

        # Step 3: Infer from similar repos
        similar_topics = self._infer_from_similar(similar_repos)

        # Step 4: Use LLM for final inference
        suggestions = self._infer_with_llm(target, pattern_topics, similar_topics, similar_repos)

        # Mark which topics are already assigned (for comparison mode)
        for suggestion in suggestions:
            suggestion.already_assigned = suggestion.topic in existing_topics

        return suggestions

    def _find_pattern_matches(self, features: dict) -> dict[str, float]:
        """Match target against learned patterns.

        Args:
            features: Repository features

        Returns:
            Dict of topic -> confidence score
        """
        matches: dict[str, float] = {}

        for topic, pattern in self.kb.topic_patterns.items():
            # Count matching features
            matching_features = sum(
                1 for feat in pattern.common_features if features.get(feat, False)
            )

            if matching_features > 0:
                # Confidence based on proportion of pattern features that match
                confidence = (
                    matching_features / len(pattern.common_features)
                    if pattern.common_features
                    else 0
                )
                if confidence >= pattern.confidence_threshold:
                    matches[topic] = confidence

        return matches

    def _infer_from_similar(self, similar_repos: list[SimilarRepo]) -> dict[str, float]:
        """Infer topics from similar repositories.

        Args:
            similar_repos: List of similar repos

        Returns:
            Dict of topic -> confidence score
        """
        if not similar_repos:
            return {}

        # Aggregate topics weighted by similarity
        topic_scores: dict[str, float] = {}
        total_similarity = sum(repo.similarity_score for repo in similar_repos)

        if total_similarity == 0:
            return {}

        for repo in similar_repos:
            weight = repo.similarity_score / total_similarity
            for topic in repo.topics:
                topic_scores[topic] = topic_scores.get(topic, 0) + weight

        return topic_scores

    def _infer_with_llm(
        self,
        context: RepositoryContext,
        pattern_topics: dict[str, float],
        similar_topics: dict[str, float],
        similar_repos: list[SimilarRepo],
    ) -> list[TopicSuggestion]:
        """Use Claude to generate and validate topic suggestions.

        Args:
            context: Repository context
            pattern_topics: Topics from pattern matching
            similar_topics: Topics from similar repos
            similar_repos: Similar repositories

        Returns:
            List of topic suggestions
        """
        # Build prompt
        prompt = self._build_inference_prompt(
            context, pattern_topics, similar_topics, similar_repos
        )

        # Call Claude
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )

        # Parse response
        response_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                response_text += block.text

        return self._parse_llm_response(response_text, pattern_topics, similar_topics)

    def _build_inference_prompt(
        self,
        context: RepositoryContext,
        pattern_topics: dict[str, float],
        similar_topics: dict[str, float],
        similar_repos: list[SimilarRepo],
    ) -> str:
        """Build prompt for LLM topic inference."""
        # Repository info
        repo_info = [
            f"Repository: {context.full_name}",
            f"Description: {context.metadata.description or 'None'}",
            f"Language: {context.metadata.language or 'Unknown'}",
            f"Stars: {context.metadata.stars}",
        ]

        # README excerpt
        if context.readme_content:
            readme_excerpt = context.readme_content[:1000]
            repo_info.append(f"\nREADME excerpt:\n{readme_excerpt}\n...")

        # Pattern matches
        pattern_info = []
        if pattern_topics:
            pattern_info.append("Topics suggested by learned patterns:")
            for topic, conf in sorted(pattern_topics.items(), key=lambda x: x[1], reverse=True)[:5]:
                pattern_info.append(f"  - {topic} (confidence: {conf:.2f})")

        # Similar repos
        similar_info = []
        if similar_repos:
            similar_info.append(f"\nSimilar repositories (found {len(similar_repos)} matches):")
            for repo in similar_repos[:3]:
                similar_info.append(
                    f"  - {repo.full_name} (similarity: {repo.similarity_score:.2f})"
                )
                if repo.topics:
                    similar_info.append(f"    Topics: {', '.join(repo.topics[:5])}")

        # Aggregated topics from similar
        if similar_topics:
            similar_info.append("\nMost common topics in similar repositories:")
            for topic, score in sorted(similar_topics.items(), key=lambda x: x[1], reverse=True)[
                :8
            ]:
                similar_info.append(f"  - {topic} (score: {score:.2f})")

        prompt = f"""Analyze this GitHub repository and suggest 5-10 relevant topics.

{chr(10).join(repo_info)}

{chr(10).join(pattern_info)}

{chr(10).join(similar_info)}

IMPORTANT RULES:
1. Topics must follow GitHub's naming conventions:
   - All lowercase
   - Use hyphens for multi-word topics (e.g., "machine-learning")
   - Maximum 50 characters
   - No spaces or special characters except hyphens

2. Suggest topics in these categories:
   - Primary language/technology (e.g., "python", "rust")
   - Domain/purpose (e.g., "web-framework", "cli-tool")
   - Key features (e.g., "async", "type-checking")
   - Use cases (e.g., "api", "microservices")

3. Provide for EACH topic:
   - Topic name (following rules above)
   - Confidence score (0.0 to 1.0)
   - Brief reasoning (one sentence)

Format your response as:
TOPIC: <topic-name>
CONFIDENCE: <0.0-1.0>
REASONING: <why this topic fits>
---

Suggest 5-10 topics total, ranked by confidence (highest first).
"""

        return prompt

    def _parse_llm_response(
        self, response_text: str, pattern_topics: dict, similar_topics: dict
    ) -> list[TopicSuggestion]:
        """Parse LLM response into topic suggestions."""
        suggestions = []

        # Split by separator
        topic_blocks = response_text.split("---")

        for block in topic_blocks:
            block = block.strip()
            if not block:
                continue

            # Extract fields
            topic_match = re.search(r"TOPIC:\s*(.+)", block, re.IGNORECASE)
            conf_match = re.search(r"CONFIDENCE:\s*([\d.]+)", block, re.IGNORECASE)
            reason_match = re.search(r"REASONING:\s*(.+)", block, re.IGNORECASE | re.DOTALL)

            if not (topic_match and conf_match):
                continue

            topic = topic_match.group(1).strip().lower()
            confidence = float(conf_match.group(1))
            reasoning = reason_match.group(1).strip() if reason_match else "LLM suggestion"

            # Validate topic format
            if not self._validate_topic_format(topic):
                continue

            # Determine sources
            sources = ["llm_inference"]
            if topic in pattern_topics:
                sources.append("pattern_match")
            if topic in similar_topics:
                sources.append("similar_repos")

            suggestions.append(
                TopicSuggestion(
                    topic=topic,
                    confidence=confidence,
                    reasoning=reasoning,
                    sources=sources,
                    already_assigned=False,  # Will be set by caller
                )
            )

        # Sort by confidence
        suggestions.sort(key=lambda s: s.confidence, reverse=True)

        return suggestions[:10]  # Limit to top 10

    def _validate_topic_format(self, topic: str) -> bool:
        """Validate topic follows GitHub's naming conventions."""
        if not topic:
            return False
        if len(topic) > 50:
            return False
        if not re.match(r"^[a-z0-9][a-z0-9-]*$", topic):
            return False
        if topic.startswith("-") or topic.endswith("-"):
            return False
        return True
