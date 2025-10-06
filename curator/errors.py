"""Custom error hierarchy for GitHub Curator.

This module provides a structured error hierarchy to distinguish between
different error types and provide better diagnostics.
"""

from typing import Optional


class CuratorError(Exception):
    """Base exception for all curator errors."""

    def __init__(self, message: str, details: Optional[dict] = None):
        """Initialize curator error.

        Args:
            message: Human-readable error message
            details: Additional error context
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """Format error message with details."""
        if self.details:
            details_str = "\n".join(f"  {k}: {v}" for k, v in self.details.items())
            return f"{self.message}\nDetails:\n{details_str}"
        return self.message


# GitHub API Errors


class GitHubError(CuratorError):
    """Base class for GitHub API errors."""

    pass


class GitHubAuthenticationError(GitHubError):
    """GitHub authentication failed (invalid token, expired, etc)."""

    def __init__(
        self, message: str = "GitHub authentication failed", details: Optional[dict] = None
    ):
        super().__init__(message, details)


class GitHubRateLimitError(GitHubError):
    """GitHub API rate limit exceeded."""

    def __init__(self, reset_time: Optional[str] = None, details: Optional[dict] = None):
        message = "GitHub API rate limit exceeded"
        if reset_time:
            message += f" (resets at {reset_time})"
        super().__init__(message, details)


class GitHubNotFoundError(GitHubError):
    """GitHub resource not found (repository, file, etc)."""

    def __init__(self, resource: str, details: Optional[dict] = None):
        message = f"GitHub resource not found: {resource}"
        super().__init__(message, details)


class GitHubAPIError(GitHubError):
    """Generic GitHub API error (server error, network issue, etc)."""

    def __init__(
        self, message: str, status_code: Optional[int] = None, details: Optional[dict] = None
    ):
        details = details or {}
        if status_code:
            details["status_code"] = status_code
        super().__init__(message, details)


# LLM Provider Errors


class LLMError(CuratorError):
    """Base class for LLM provider errors."""

    pass


class LLMAuthenticationError(LLMError):
    """LLM authentication failed (invalid API key, etc)."""

    def __init__(
        self,
        provider: str,
        message: str = "LLM authentication failed",
        details: Optional[dict] = None,
    ):
        details = details or {}
        details["provider"] = provider
        super().__init__(message, details)


class LLMRateLimitError(LLMError):
    """LLM API rate limit exceeded."""

    def __init__(
        self, provider: str, retry_after: Optional[int] = None, details: Optional[dict] = None
    ):
        message = f"{provider} API rate limit exceeded"
        if retry_after:
            message += f" (retry after {retry_after}s)"
        details = details or {}
        details["provider"] = provider
        super().__init__(message, details)


class LLMTimeoutError(LLMError):
    """LLM API request timed out."""

    def __init__(self, provider: str, timeout: int, details: Optional[dict] = None):
        message = f"{provider} API request timed out after {timeout}s"
        details = details or {}
        details["provider"] = provider
        details["timeout"] = timeout
        super().__init__(message, details)


class LLMModelError(LLMError):
    """LLM model error (model not found, context length exceeded, etc)."""

    def __init__(self, provider: str, model: str, message: str, details: Optional[dict] = None):
        details = details or {}
        details["provider"] = provider
        details["model"] = model
        super().__init__(message, details)


class LLMAPIError(LLMError):
    """Generic LLM API error."""

    def __init__(
        self,
        provider: str,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[dict] = None,
    ):
        details = details or {}
        details["provider"] = provider
        if status_code:
            details["status_code"] = status_code
        super().__init__(message, details)


# Configuration Errors


class ConfigurationError(CuratorError):
    """Configuration-related errors."""

    pass


class MissingConfigError(ConfigurationError):
    """Required configuration missing."""

    def __init__(self, key: str, details: Optional[dict] = None):
        message = f"Missing required configuration: {key}"
        super().__init__(message, details)


class InvalidConfigError(ConfigurationError):
    """Configuration value is invalid."""

    def __init__(self, key: str, value: str, reason: str, details: Optional[dict] = None):
        message = f"Invalid configuration for {key}={value}: {reason}"
        super().__init__(message, details)


# Validation Errors


class ValidationError(CuratorError):
    """Data validation errors."""

    pass


class IntentValidationError(ValidationError):
    """Intent structure validation failed."""

    pass


class EvaluationValidationError(ValidationError):
    """Evaluation result validation failed."""

    pass


# Knowledge Base Errors


class KnowledgeBaseError(CuratorError):
    """Knowledge base operation errors."""

    pass


class CorpusNotFoundError(KnowledgeBaseError):
    """Knowledge corpus doesn't exist or is empty."""

    def __init__(self, details: Optional[dict] = None):
        message = "Knowledge corpus not found. Run 'curator collect' first."
        super().__init__(message, details)


# Pipeline Errors


class PipelineError(CuratorError):
    """Pipeline execution errors."""

    pass


class TaskFailedError(PipelineError):
    """Pipeline task failed."""

    def __init__(self, task_name: str, reason: str, details: Optional[dict] = None):
        message = f"Task '{task_name}' failed: {reason}"
        super().__init__(message, details)
