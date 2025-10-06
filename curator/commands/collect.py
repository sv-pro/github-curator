"""Collect command implementation for building knowledge base corpus."""

import re
from datetime import datetime
from typing import Any, Optional

import click

from curator.github.api_client import GitHubAPIClient
from curator.github.repo_analyzer import RepositoryAnalyzer
from curator.knowledge import KnowledgeStore


def parse_repo_spec(repo_spec: str) -> str:
    """Parse repository specification.

    Supports:
    - owner/repo
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git

    Returns owner/repo format.
    """
    # Already in owner/repo format
    if "/" in repo_spec and not repo_spec.startswith("http"):
        return repo_spec

    # Parse GitHub URL
    match = re.match(r"https?://github\.com/([^/]+/[^/]+?)(?:\.git)?/?$", repo_spec)
    if match:
        return match.group(1)

    raise ValueError(f"Invalid repository specification: {repo_spec}")


def collect_repositories(
    topics: Optional[list[str]] = None,
    specific_repos: Optional[list[str]] = None,
    limit: int = 100,
    min_stars: int = 50,
    language: Optional[str] = None,
    knowledge_base_path: str = ".curator/knowledge",
    refresh_existing: bool = False,
    use_git_clone: bool = False,
    config_path: str = "config/curator.yaml",
) -> dict[str, Any]:
    """Collect repositories and add to knowledge base.

    Args:
        topics: List of GitHub topics to search for
        specific_repos: List of specific repos to add (owner/repo or URLs)
        limit: Maximum number of repos per topic to collect
        min_stars: Minimum star count for topic search
        language: Filter by programming language
        knowledge_base_path: Path to knowledge base directory
        refresh_existing: If True, update existing repos
        use_git_clone: If True, clone repos for deeper analysis
        config_path: Path to config file

    Returns:
        Result dict with counts and errors
    """
    # Initialize components
    github_client = GitHubAPIClient(config_path)
    analyzer = RepositoryAnalyzer(github_client, config_path, use_git_clone=use_git_clone)
    knowledge_store = KnowledgeStore(base_path=knowledge_base_path)

    # Track statistics
    initial_count = len(knowledge_store.list_repositories())
    collected_count = 0
    updated_count = 0
    skipped_count = 0
    errors = []

    repos_to_process = []

    # Handle specific repositories
    if specific_repos:
        click.echo("🔍 Fetching specific repositories...")

        for repo_spec in specific_repos:
            try:
                # Parse repo spec
                repo_name = parse_repo_spec(repo_spec)
                click.echo(f"   • {repo_name}")

                # Fetch repository from GitHub
                gh_repo = github_client.get_repository(repo_name)

                # Convert to SearchResult-like dict
                repo_data = {
                    "full_name": gh_repo.full_name,
                    "name": gh_repo.name,
                    "owner": gh_repo.owner.login,
                    "description": gh_repo.description,
                    "url": gh_repo.html_url,
                    "stars": gh_repo.stargazers_count,
                    "language": gh_repo.language,
                    "topics": list(gh_repo.get_topics()),
                }
                repos_to_process.append(repo_data)

            except Exception as e:
                click.echo(f"     ⚠️  Failed to fetch: {e}")
                errors.append({"repo": repo_spec, "error": str(e)})

        click.echo("")

    # Handle topic search
    if topics:
        for topic in topics:
            click.echo(f"🔍 Searching GitHub for topic:{topic}...")

            # Build search query
            query_parts = [f"topic:{topic}"]
            if min_stars:
                query_parts.append(f"stars:>={min_stars}")
            if language:
                query_parts.append(f"language:{language}")

            query = " ".join(query_parts)
            click.echo(f"   Query: {query}")

            try:
                # Search repositories
                search_results = github_client.search_repositories(query, limit=limit)
                click.echo(f"   Found {len(search_results)} repositories")

                # Convert search results to dict format
                for result in search_results:
                    # Check if we already have this repo from another topic
                    if not any(r["full_name"] == result.full_name for r in repos_to_process):
                        repos_to_process.append(
                            {
                                "full_name": result.full_name,
                                "name": result.name,
                                "owner": result.owner,
                                "description": result.description,
                                "url": result.url,
                                "stars": result.stars,
                                "language": result.language,
                                "topics": result.topics,
                            }
                        )

            except Exception as e:
                click.echo(f"   ⚠️  Search failed: {e}", err=True)
                errors.append({"topic": topic, "error": str(e)})

            click.echo("")

    # Process repositories
    total = len(repos_to_process)
    for i, repo_data in enumerate(repos_to_process, 1):
        full_name = repo_data["full_name"]

        # Check if already in knowledge base
        exists = knowledge_store.has_repository(full_name)

        if exists and not refresh_existing:
            skipped_count += 1
            continue

        # Determine if this is an update or new addition
        is_update = exists
        status_icon = "🔄" if is_update else "📊"
        click.echo(f"{status_icon} [{i}/{total}] {full_name} ({repo_data['stars']}⭐)")

        try:
            # Analyze repository
            # Create a minimal SearchResult-like object for the analyzer
            from curator.github.api_client import SearchResult

            search_result = SearchResult(
                name=repo_data["name"],
                owner=repo_data["owner"],
                full_name=repo_data["full_name"],
                description=repo_data["description"] or "",
                url=repo_data["url"],
                stars=repo_data["stars"],
                last_updated=datetime.now(),  # Use current time
                language=repo_data["language"],
                license_name=None,  # Not critical
                topics=repo_data["topics"],
            )

            context = analyzer.analyze_repository(search_result)
            features = analyzer.extract_key_features(context)

            # Add or update in knowledge base
            if is_update:
                knowledge_store.update_repository(
                    full_name=full_name,
                    topics=repo_data["topics"],
                    features=features,
                    language=repo_data["language"],
                    stars=repo_data["stars"],
                )
                updated_count += 1
            else:
                knowledge_store.add_repository(
                    full_name=full_name,
                    topics=repo_data["topics"],
                    features=features,
                    language=repo_data["language"],
                    stars=repo_data["stars"],
                )
                collected_count += 1

            action = "Refreshed" if is_update else "Added"
            click.echo(f"   ✓ {action} ({len(repo_data['topics'])} topics)")

        except Exception as e:
            click.echo(f"   ⚠️  Failed: {e}")
            errors.append({"repo": full_name, "error": str(e)})
            continue

    # Learn patterns and save
    if collected_count > 0 or updated_count > 0:
        click.echo("")
        click.echo("📈 Learning patterns from collected data...")
        pattern_stats = knowledge_store.learn_patterns()

        click.echo("")
        click.echo("✓ Collection complete!")
        if collected_count > 0:
            click.echo(f"   Added: {collected_count} repositories")
        if updated_count > 0:
            click.echo(f"   Refreshed: {updated_count} repositories")
        if skipped_count > 0:
            click.echo(f"   Skipped (duplicates): {skipped_count}")

        stats = knowledge_store.get_stats()
        click.echo(f"   Total in KB: {stats['total_repositories']} (was {initial_count})")
        click.echo(f"   Patterns learned: {pattern_stats.get('patterns', 0)}")
        click.echo(f"   Unique topics: {stats['total_topics']}")
    else:
        click.echo("")
        click.echo("⚠️  No repositories added or updated")

    return {
        "collected_count": collected_count,
        "updated_count": updated_count,
        "skipped_count": skipped_count,
        "new_topics_count": knowledge_store.get_stats()["total_topics"],
        "errors": errors,
    }
