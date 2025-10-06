"""Custom cache key functions for Prefect tasks."""

import hashlib
import json
from pathlib import Path
from typing import Any, Optional

from prefect import get_run_logger
from prefect.context import TaskRunContext


def _hash_dict(data: dict[str, Any]) -> str:
    """Create deterministic hash from dictionary."""
    json_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_str.encode()).hexdigest()


def _get_config_version(config_path: str) -> str:
    """Get version hash of configuration file."""
    config_file = Path(config_path)
    if not config_file.exists():
        return "default"

    with open(config_file) as f:
        config_content = f.read()
    return hashlib.sha256(config_content.encode()).hexdigest()[:8]


def intent_cache_key(context: TaskRunContext, parameters: dict) -> str:
    """Custom cache key for intent structuring.

    Cache based on:
    - Theme text
    - Focus areas
    - Exclusions
    - Config version (to invalidate when config changes)
    """
    cache_data = {
        "theme": parameters.get("theme", ""),
        "focus_areas": sorted(parameters.get("focus_areas") or []),
        "exclusions": sorted(parameters.get("exclusions") or []),
        "config_version": _get_config_version(parameters.get("config_path", "config/curator.yaml")),
    }

    cache_key = _hash_dict(cache_data)

    # Log cache key for debugging
    logger = get_run_logger()
    logger.debug(f"Intent cache key: {cache_key[:12]}... (theme: {cache_data['theme'][:50]}...)")

    return cache_key


def search_cache_key(context: TaskRunContext, parameters: dict) -> str:
    """Custom cache key for GitHub repository search.

    Cache based on:
    - Intent ID (represents the search criteria)
    - Constraint parameters (stars, age, etc.)
    """
    intent = parameters.get("intent")
    if not intent:
        return "no-intent"

    cache_data = {
        "intent_id": intent.intent_id,
        "min_stars": intent.constraints.min_stars,
        "max_age_months": intent.constraints.max_age_months,
        "requires_license": intent.constraints.requires_license,
    }

    cache_key = _hash_dict(cache_data)

    logger = get_run_logger()
    logger.debug(f"Search cache key: {cache_key[:12]}... (intent: {intent.intent_id[:8]}...)")

    return cache_key


def analysis_cache_key(context: TaskRunContext, parameters: dict) -> str:
    """Custom cache key for repository analysis.

    Cache based on:
    - Repository full name
    - Last push date (to detect updates)
    """
    repo = parameters.get("repo")
    if not repo:
        context_obj = parameters.get("context")
        if context_obj:
            repo_name = context_obj.full_name
            updated_at = getattr(context_obj, "updated_at", "unknown")
        else:
            return "no-repo"
    else:
        repo_name = repo.full_name
        updated_at = getattr(repo, "updated_at", "unknown")

    cache_data = {
        "repo": repo_name,
        "updated_at": str(updated_at),
    }

    cache_key = _hash_dict(cache_data)

    logger = get_run_logger()
    logger.debug(f"Analysis cache key: {cache_key[:12]}... (repo: {repo_name})")

    return cache_key


def evaluation_cache_key(context: TaskRunContext, parameters: dict) -> str:
    """Custom cache key for repository evaluation.

    Cache based on:
    - Repository name
    - Intent ID
    - Model version (to invalidate when model changes)
    """
    repo_context = parameters.get("context")
    intent = parameters.get("intent")

    if not repo_context or not intent:
        return "incomplete"

    cache_data = {
        "repo": repo_context.full_name,
        "intent_id": intent.intent_id,
        "model_version": "claude-sonnet-4-5-20250929",  # Update when changing models
    }

    cache_key = _hash_dict(cache_data)

    logger = get_run_logger()
    logger.debug(
        f"Evaluation cache key: {cache_key[:12]}... (repo: {repo_context.full_name}, intent: {intent.intent_id[:8]}...)"
    )

    return cache_key


def validation_cache_key(context: TaskRunContext, parameters: dict) -> Optional[str]:
    """Custom cache key for validation tasks.

    Validation is typically not cached as it's fast and depends on current state.
    """
    return None  # Don't cache by returning None


def reflection_cache_key(context: TaskRunContext, parameters: dict) -> str:
    """Custom cache key for reflection tasks.

    Cache based on:
    - Number of evaluations
    - Intent ID
    - Evaluation IDs (to detect changes)
    """
    evaluations = parameters.get("evaluations", [])
    intent = parameters.get("intent")

    if not evaluations or not intent:
        return "incomplete"

    # Create hash of evaluation repos and scores
    eval_summary = {
        "intent_id": intent.intent_id,
        "eval_count": len(evaluations),
        "eval_repos": sorted([e.repo for e in evaluations]),
    }

    cache_key = _hash_dict(eval_summary)

    logger = get_run_logger()
    logger.debug(f"Reflection cache key: {cache_key[:12]}... ({len(evaluations)} evaluations)")

    return cache_key
