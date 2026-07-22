from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from backend.llm.schemas import LLMRequest, LLMResponse, ModelInfo, StreamingChunk


class LLMProviderBase(ABC):
    """Provider-agnostic interface for generating chat completions."""

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a complete chat response asynchronously.

        Args:
            request: The generation request.

        Returns:
            The complete generated response.

        Raises:
            InvalidModelError: If the requested model is not recognized
                by this provider.
            TokenLimitExceededError: If the request would exceed the
                model's context window.
            GenerationError: If the provider rejects the request for
                another reason.
            LLMConnectionError: If authentication fails.
            ProviderUnavailableError: If the provider is unreachable
                after exhausting retries.
        """
        raise NotImplementedError

    @abstractmethod
    def generate_sync(self, request: LLMRequest) -> LLMResponse:
        """Generate a complete chat response synchronously.

        Args:
            request: The generation request.

        Returns:
            The complete generated response.

        Raises:
            InvalidModelError: If the requested model is not recognized
                by this provider.
            TokenLimitExceededError: If the request would exceed the
                model's context window.
            GenerationError: If the provider rejects the request for
                another reason.
            LLMConnectionError: If authentication fails.
            ProviderUnavailableError: If the provider is unreachable
                after exhausting retries.
        """
        raise NotImplementedError

    @abstractmethod
    def stream(self, request: LLMRequest) -> AsyncIterator[StreamingChunk]:
        """Generate a chat response as a stream of incremental chunks.

        Args:
            request: The generation request.

        Yields:
            `StreamingChunk` instances as they become available, with
            the final chunk carrying `is_final=True` and a
            `finish_reason`.

        Raises:
            InvalidModelError: If the requested model is not recognized
                by this provider.
            TokenLimitExceededError: If the request would exceed the
                model's context window.
            StreamingError: If the stream fails after starting.
            LLMConnectionError: If authentication fails.
            ProviderUnavailableError: If the provider is unreachable
                after exhausting retries on the initial connection.
        """
        raise NotImplementedError

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count (or estimate) the number of tokens in a piece of text.

        Args:
            text: The text to count tokens in.

        Returns:
            The token count.
        """
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        """Check whether this provider is currently reachable.

        Returns:
            True if the provider responded successfully, False
            otherwise. Implementations should catch their own
            connection errors and return False rather than raising, so
            this method is always safe to call (e.g. from an
            application `/health` endpoint).
        """
        raise NotImplementedError

    @abstractmethod
    def list_models(self) -> list[ModelInfo]:
        """List the models this provider supports.

        Returns:
            Capability/limits information for every model this provider
            has registered (see `backend.llm.models`).
        """
        raise NotImplementedError