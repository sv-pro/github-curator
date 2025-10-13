"""Adaptive search strategy with automatic query generation and constraint adjustment."""

import json
from dataclasses import dataclass
from typing import Any, Optional

import yaml

from curator.llm import create_llm_provider_from_config
from curator.llm.base import LLMMessage


@dataclass
class SearchConstraints:
    """Dynamic search constraints that can be adjusted."""

    min_stars: int
    max_age_months: int
    requires_license: bool

    def loosen(self, stars_adj: int, age_adj: int):
        """Loosen constraints to get more results."""
        self.min_stars = max(0, self.min_stars - stars_adj)
        self.max_age_months += age_adj

    def tighten(self, stars_adj: int, age_adj: int):
        """Tighten constraints to get fewer results."""
        self.min_stars += stars_adj
        self.max_age_months = max(1, self.max_age_months - age_adj)


class AdaptiveSearchStrategy:
    """Adaptive search that adjusts queries and constraints based on result counts."""

    def __init__(self, config_path: str = "config/curator.yaml"):
        """Initialize adaptive search strategy."""
        self.config = self._load_config(config_path)
        self.config_path = config_path
        # Use fallback-enabled LLM provider from config
        self.llm_provider = create_llm_provider_from_config(config_path)

        adaptive_config = self.config["github"]["adaptive_search"]
        self.enabled = adaptive_config.get("enabled", False)
        self.target_count = adaptive_config.get("target_repo_count", 30)
        self.min_count = adaptive_config.get("min_repo_count", 20)
        self.max_count = adaptive_config.get("max_repo_count", 50)
        self.max_iterations = adaptive_config.get("max_iterations", 5)
        self.initial_queries_count = adaptive_config.get("initial_queries_count", 3)
        self.stars_adj = adaptive_config.get("stars_adjustment", 10)
        self.age_adj = adaptive_config.get("age_adjustment_months", 2)

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        with open(config_path) as f:
            return yaml.safe_load(f)

    def generate_search_queries(
        self, theme: str, style: str = "balanced", count: int = 3
    ) -> list[str]:
        """Generate search queries using LLM with fallback support.

        Args:
            theme: Main curation theme
            style: "narrow", "balanced", or "broad"
            count: Number of queries to generate

        Returns:
            List of search query strings
        """
        style_instructions = {
            "narrow": "Generate very specific, focused queries that closely match the theme",
            "balanced": "Generate queries with moderate specificity",
            "broad": "Generate diverse, exploratory queries that capture different aspects",
        }

        prompt = f"""Generate {count} GitHub search queries for finding repositories about: "{theme}"

{style_instructions.get(style, style_instructions["balanced"])}

Requirements:
- Each query should be 2-5 words
- Queries should be diverse and complementary
- Use terminology developers would use in repo names/descriptions
- Include both general and specific terms

Return ONLY a JSON array of query strings, nothing else.
Example: ["query one", "query two", "query three"]"""

        # Use LLM provider with fallback support
        response = self.llm_provider.complete(
            messages=[LLMMessage(role="user", content=prompt)],
            max_tokens=500,
        )

        # Extract JSON array from response content
        response_text = response.content
        start = response_text.find("[")
        end = response_text.rfind("]") + 1
        queries = json.loads(response_text[start:end])

        return queries

    def adaptive_search(
        self,
        theme: str,
        github_client,
        initial_constraints: SearchConstraints,
        limit: Optional[int] = None,
    ) -> list:
        """Execute adaptive search with automatic query and constraint adjustment.

        Args:
            theme: Main curation theme
            github_client: GitHubAPIClient instance
            initial_constraints: Starting search constraints
            limit: Maximum total results to return

        Returns:
            Deduplicated list of search results
        """
        if not self.enabled:
            # Fall back to single query search
            queries = [theme]
            return self._search_with_queries(queries, github_client, initial_constraints, limit)

        print(f"🔄 Adaptive search enabled (target: {self.target_count} repos)")
        print("")

        constraints = SearchConstraints(
            min_stars=initial_constraints.min_stars,
            max_age_months=initial_constraints.max_age_months,
            requires_license=initial_constraints.requires_license,
        )

        all_results: dict[str, Any] = {}  # Use dict for deduplication by full_name
        iteration = 0
        query_style = "balanced"

        while iteration < self.max_iterations:
            iteration += 1
            result_count = len(all_results)

            print(f"Iteration {iteration}/{self.max_iterations}: {result_count} repos found")

            # Decide on strategy based on current count
            if result_count < self.min_count:
                if iteration > 1:
                    print(
                        f"  → Too few results, loosening constraints (stars: {constraints.min_stars} → {constraints.min_stars - self.stars_adj})"
                    )
                    constraints.loosen(self.stars_adj, self.age_adj)
                query_style = "broad"
                query_count = self.initial_queries_count + 1
            elif result_count > self.max_count:
                print(
                    f"  → Too many results, tightening constraints (stars: {constraints.min_stars} → {constraints.min_stars + self.stars_adj})"
                )
                constraints.tighten(self.stars_adj, self.age_adj)
                query_style = "narrow"
                query_count = max(2, self.initial_queries_count - 1)
            elif self.min_count <= result_count <= self.max_count:
                print(f"  ✓ Target range achieved ({self.min_count}-{self.max_count})")
                break
            else:
                query_count = self.initial_queries_count

            # Generate queries
            print(f"  → Generating {query_count} {query_style} queries...")
            queries = self.generate_search_queries(theme, query_style, query_count)

            for idx, query in enumerate(queries, 1):
                print(f"    {idx}. '{query}'")

            # Search with generated queries
            print(
                f"  → Searching with constraints: stars≥{constraints.min_stars}, age≤{constraints.max_age_months}mo"
            )

            for query in queries:
                results = github_client.search_repositories(
                    query=query,
                    min_stars=constraints.min_stars,
                    max_age_months=constraints.max_age_months,
                    requires_license=constraints.requires_license,
                    limit=limit,
                )

                # Deduplicate by full_name
                for result in results:
                    if result.full_name not in all_results:
                        all_results[result.full_name] = result

            print(f"  → Total unique repos: {len(all_results)}")
            print("")

        final_results = list(all_results.values())

        # Apply final limit if specified
        if limit and len(final_results) > limit:
            final_results = final_results[:limit]

        print(f"✓ Adaptive search complete: {len(final_results)} repos")
        print("")

        return final_results

    def _search_with_queries(
        self,
        queries: list[str],
        github_client,
        constraints: SearchConstraints,
        limit: Optional[int],
    ) -> list:
        """Helper to search with multiple queries and deduplicate."""
        all_results = {}

        for query in queries:
            results = github_client.search_repositories(
                query=query,
                min_stars=constraints.min_stars,
                max_age_months=constraints.max_age_months,
                requires_license=constraints.requires_license,
                limit=limit,
            )

            for result in results:
                if result.full_name not in all_results:
                    all_results[result.full_name] = result

        return list(all_results.values())
