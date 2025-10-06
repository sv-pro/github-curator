"""Prefect pipeline for GitHub Curator.

This module provides declarative, build-system-like pipeline execution with:
- Automatic caching based on content
- Parallel task execution
- Incremental computation
- Resumable workflows
"""

from curator.pipeline.cache import (  # noqa: E402
    analysis_cache_key,
    evaluation_cache_key,
    intent_cache_key,
    reflection_cache_key,
    search_cache_key,
)
from curator.pipeline.config import PrefectConfig
from curator.pipeline.flows import test_intent_flow
from curator.pipeline.tasks import structure_intent_task

__all__ = [
    "PrefectConfig",
    "structure_intent_task",
    "test_intent_flow",
    "intent_cache_key",
    "search_cache_key",
    "analysis_cache_key",
    "evaluation_cache_key",
    "reflection_cache_key",
]
