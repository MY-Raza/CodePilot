# backend/github/exceptions.py
"""Custom exceptions for the GitHub integration module.

All exceptions raised by `client.py`, `service.py`, and `webhooks.py`
derive from `GitHubIntegrationError`, so callers can catch broadly or
narrowly as needed.
"""


class GitHubIntegrationError(Exception):
    """Base exception for all GitHub integration failures."""


class RepositoryNotFoundError(GitHubIntegrationError):
    """Raised when a repository does not exist or is inaccessible."""


class InvalidRepositoryError(GitHubIntegrationError):
    """Raised when a repository reference is malformed or otherwise invalid."""


class GitHubRateLimitError(GitHubIntegrationError):
    """Raised when the GitHub API rate limit has been exceeded.

    Attributes:
        reset_at: Unix timestamp (as a string) when the rate limit resets,
            if provided by the GitHub API response.
    """

    def __init__(self, message: str, reset_at: str | None = None) -> None:
        """Initialize the error with an optional rate-limit reset time.

        Args:
            message: Human-readable error description.
            reset_at: Unix timestamp string from the `X-RateLimit-Reset`
                response header, if available.
        """
        super().__init__(message)
        self.reset_at = reset_at


class AuthenticationFailedError(GitHubIntegrationError):
    """Raised when GitHub rejects the configured credentials."""


class CloneFailedError(GitHubIntegrationError):
    """Raised when cloning a repository to local storage fails."""


class PullFailedError(GitHubIntegrationError):
    """Raised when pulling the latest changes for a repository fails."""


class WebhookVerificationError(GitHubIntegrationError):
    """Raised when a webhook payload's signature fails verification."""