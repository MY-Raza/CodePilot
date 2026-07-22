class LLMServiceError(Exception):
    """Base exception for all LLM service failures."""


class LLMConnectionError(LLMServiceError):
    """Raised when the provider rejects credentials or cannot be reached.

    Covers authentication failures specifically (never retried — see
    `groq.py`'s retry policy) as well as lower-level connection setup
    failures.
    """


class InvalidModelError(LLMServiceError):
    """Raised when a requested model is unknown to the provider."""


class TokenLimitExceededError(LLMServiceError):
    """Raised when a request's prompt plus requested output would exceed
    a model's context window.
    """


class StreamingError(LLMServiceError):
    """Raised when a streaming response fails mid-stream."""


class GenerationError(LLMServiceError):
    """Raised when a non-streaming generation request fails."""


class ProviderUnavailableError(LLMServiceError):
    """Raised when a provider is unreachable after exhausting retries,
    or when the requested provider has no registered implementation.
    """