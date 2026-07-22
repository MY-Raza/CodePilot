import asyncio
import logging
import random
import time
from collections.abc import AsyncIterator

from groq import AsyncGroq, Groq
from groq import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    GroqError,
    InternalServerError,
    NotFoundError,
    RateLimitError,
    UnprocessableEntityError,
)

from backend.llm.base import LLMProviderBase
from backend.llm.exceptions import (
    GenerationError,
    InvalidModelError,
    LLMConnectionError,
    ProviderUnavailableError,
    StreamingError,
    TokenLimitExceededError,
)
from backend.llm.models import LLMProvider, get_model_definition, list_models
from backend.llm.schemas import ChatMessage, LLMRequest, LLMResponse, ModelInfo, StreamingChunk, TokenUsage
from backend.llm.tokenizer import Tokenizer

logger = logging.getLogger(__name__)

# Exceptions retried per this module's retry policy: rate limits,
# temporary server errors, and network-level failures. Explicitly
# excludes AuthenticationError and request-validation errors
# (BadRequestError, UnprocessableEntityError, NotFoundError) — those
# will not succeed on retry and are raised immediately instead.
_RETRYABLE_EXCEPTIONS = (RateLimitError, APIConnectionError, APITimeoutError, InternalServerError)

_MAX_BACKOFF_SECONDS = 30.0
_BASE_BACKOFF_SECONDS = 1.0


def _backoff_delay(attempt: int) -> float:
    """Compute an exponential backoff delay with jitter.

    Args:
        attempt: The retry attempt number (1-indexed).

    Returns:
        A delay in seconds, capped at `_MAX_BACKOFF_SECONDS`, with up to
        0.5s of random jitter added to reduce thundering-herd retries
        across concurrent requests.
    """
    delay = min(_BASE_BACKOFF_SECONDS * (2 ** (attempt - 1)), _MAX_BACKOFF_SECONDS)
    return delay + random.uniform(0, 0.5)


def _to_provider_messages(messages: list[ChatMessage]) -> list[dict[str, str]]:
    """Convert provider-agnostic `ChatMessage` objects into Groq's message format.

    Args:
        messages: The conversation history.

    Returns:
        A list of `{"role": ..., "content": ...}` dicts, as the Groq SDK
        expects.
    """
    return [{"role": message.role.value, "content": message.content} for message in messages]


class GroqProvider(LLMProviderBase):
    """`LLMProviderBase` implementation backed by the Groq API."""

    def __init__(
        self,
        api_key: str,
        default_model: str,
        default_temperature: float = 0.7,
        default_max_tokens: int = 2048,
        default_top_p: float = 1.0,
        timeout: float = 60.0,
        max_retries: int = 3,
    ) -> None:
        """Initialize the Groq provider.

        Args:
            api_key: The Groq API key.
            default_model: Model identifier used when a request doesn't
                specify one.
            default_temperature: Sampling temperature used when a
                request doesn't specify one.
            default_max_tokens: Maximum output tokens used when a
                request doesn't specify one.
            default_top_p: Nucleus sampling parameter used when a
                request doesn't specify one.
            timeout: Per-request timeout, in seconds.
            max_retries: Maximum retry attempts for retryable failures
                (rate limits, temporary server errors, network failures).

        Raises:
            LLMConnectionError: If the SDK clients cannot be constructed.
        """
        try:
            # max_retries=0: this provider implements its own retry loop
            # (see module docstring) rather than relying on the SDK's.
            self._sync_client = Groq(api_key=api_key, timeout=timeout, max_retries=0)
            self._async_client = AsyncGroq(api_key=api_key, timeout=timeout, max_retries=0)
        except Exception as exc:
            raise LLMConnectionError(f"Failed to initialize Groq client: {exc}") from exc

        self._default_model = default_model
        self._default_temperature = default_temperature
        self._default_max_tokens = default_max_tokens
        self._default_top_p = default_top_p
        self._max_retries = max_retries
        self._tokenizer = Tokenizer()
        logger.info("Connection established: Groq (default_model=%s)", default_model)

    def _resolve_model(self, request: LLMRequest) -> str:
        """Determine which model a request should use.

        Args:
            request: The generation request.

        Returns:
            `request.model` if set, otherwise this provider's configured
            default model.
        """
        return request.model or self._default_model

    def _build_create_kwargs(self, request: LLMRequest, model: str) -> dict[str, object]:
        """Build the keyword arguments passed to the Groq SDK's `create` call.

        Args:
            request: The generation request.
            model: The resolved model identifier.

        Returns:
            Keyword arguments for `chat.completions.create`, with
            per-request values falling back to this provider's
            configured defaults.
        """
        kwargs: dict[str, object] = {
            "model": model,
            "messages": _to_provider_messages(request.messages),
            "temperature": request.temperature
            if request.temperature is not None
            else self._default_temperature,
            "max_tokens": request.max_tokens or self._default_max_tokens,
            "top_p": request.top_p if request.top_p is not None else self._default_top_p,
        }
        if request.stop:
            kwargs["stop"] = request.stop
        if request.response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}
        return kwargs

    def _validate_context_window(self, request: LLMRequest, model: str) -> None:
        """Validate a request against its target model's context window.

        Silently skips validation if the model isn't in this provider's
        registry (e.g. a caller-supplied model string this provider
        doesn't have static limits for) rather than blocking the
        request — Groq's API is still the final authority and will
        reject an oversized request on its own.

        Args:
            request: The generation request.
            model: The resolved model identifier.

        Raises:
            TokenLimitExceededError: If the request would exceed the
                model's known context window.
        """
        definition = get_model_definition(LLMProvider.GROQ, model)
        if definition is None:
            return
        prompt_tokens = self._tokenizer.estimate_prompt_tokens(request.messages)
        max_output = request.max_tokens or self._default_max_tokens
        self._tokenizer.validate_context_window(
            prompt_tokens, max_output, definition.context_window
        )

    @staticmethod
    def _map_non_retryable_exception(exc: Exception, model: str) -> Exception:
        """Translate a non-retryable Groq SDK exception into this module's exceptions.

        Args:
            exc: The exception raised by the Groq SDK.
            model: The model that was requested, for error messages.

        Returns:
            The exception to raise instead of `exc`.
        """
        if isinstance(exc, AuthenticationError):
            return LLMConnectionError(f"Groq authentication failed: {exc}")
        if isinstance(exc, NotFoundError):
            return InvalidModelError(f"Groq does not recognize model '{model}': {exc}")
        if isinstance(exc, (BadRequestError, UnprocessableEntityError)):
            return GenerationError(f"Groq rejected the request: {exc}")
        return GenerationError(f"Groq request failed: {exc}")

    def _to_llm_response(self, response, latency_seconds: float) -> LLMResponse:
        """Convert a Groq `ChatCompletion` into the provider-agnostic `LLMResponse`.

        Args:
            response: The Groq SDK's `ChatCompletion` object.
            latency_seconds: Measured wall-clock request duration.

        Returns:
            The normalized response.
        """
        choice = response.choices[0]
        usage = response.usage
        return LLMResponse(
            id=response.id,
            provider=LLMProvider.GROQ.value,
            model=response.model,
            content=choice.message.content or "",
            finish_reason=choice.finish_reason,
            usage=TokenUsage(
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
                total_tokens=usage.total_tokens if usage else 0,
            ),
            latency_seconds=latency_seconds,
        )

    def _to_streaming_chunk(self, chunk, model: str) -> StreamingChunk:
        """Convert a Groq `ChatCompletionChunk` into the provider-agnostic `StreamingChunk`.

        Args:
            chunk: The Groq SDK's `ChatCompletionChunk` object.
            model: The model generating this stream (Groq's chunk
                objects also carry `.model`, used preferentially when
                present).

        Returns:
            The normalized streaming chunk.
        """
        choice = chunk.choices[0] if chunk.choices else None
        delta_content = choice.delta.content if choice and choice.delta else None
        finish_reason = choice.finish_reason if choice else None
        return StreamingChunk(
            id=chunk.id,
            provider=LLMProvider.GROQ.value,
            model=chunk.model or model,
            delta=delta_content or "",
            finish_reason=finish_reason,
            is_final=finish_reason is not None,
        )

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a complete chat response asynchronously, with retries."""
        model = self._resolve_model(request)
        self._validate_context_window(request, model)
        kwargs = self._build_create_kwargs(request, model)

        logger.info("Request started: model=%s, provider=groq", model)
        start_time = time.perf_counter()
        last_exc: Exception | None = None

        for attempt in range(1, self._max_retries + 2):
            try:
                response = await self._async_client.chat.completions.create(
                    stream=False, **kwargs
                )
                latency_seconds = time.perf_counter() - start_time
                result = self._to_llm_response(response, latency_seconds)
                logger.info(
                    "Request completed: model=%s, latency=%.3fs", model, latency_seconds
                )
                logger.info(
                    "Token usage: prompt=%s completion=%s total=%s",
                    result.usage.prompt_tokens,
                    result.usage.completion_tokens,
                    result.usage.total_tokens,
                )
                return result
            except _RETRYABLE_EXCEPTIONS as exc:
                last_exc = exc
                if attempt > self._max_retries:
                    break
                delay = _backoff_delay(attempt)
                logger.warning(
                    "Retry attempt %s/%s for model=%s after %s: %s",
                    attempt,
                    self._max_retries,
                    model,
                    type(exc).__name__,
                    exc,
                )
                await asyncio.sleep(delay)
            except GroqError as exc:
                logger.error("Request failed (non-retryable): %s", exc)
                raise self._map_non_retryable_exception(exc, model) from exc

        logger.error("Request failed after %s retries: %s", self._max_retries, last_exc)
        raise ProviderUnavailableError(
            f"Groq is unavailable after {self._max_retries} retries: {last_exc}"
        ) from last_exc

    def generate_sync(self, request: LLMRequest) -> LLMResponse:
        """Generate a complete chat response synchronously, with retries."""
        model = self._resolve_model(request)
        self._validate_context_window(request, model)
        kwargs = self._build_create_kwargs(request, model)

        logger.info("Request started: model=%s, provider=groq", model)
        start_time = time.perf_counter()
        last_exc: Exception | None = None

        for attempt in range(1, self._max_retries + 2):
            try:
                response = self._sync_client.chat.completions.create(stream=False, **kwargs)
                latency_seconds = time.perf_counter() - start_time
                result = self._to_llm_response(response, latency_seconds)
                logger.info(
                    "Request completed: model=%s, latency=%.3fs", model, latency_seconds
                )
                logger.info(
                    "Token usage: prompt=%s completion=%s total=%s",
                    result.usage.prompt_tokens,
                    result.usage.completion_tokens,
                    result.usage.total_tokens,
                )
                return result
            except _RETRYABLE_EXCEPTIONS as exc:
                last_exc = exc
                if attempt > self._max_retries:
                    break
                delay = _backoff_delay(attempt)
                logger.warning(
                    "Retry attempt %s/%s for model=%s after %s: %s",
                    attempt,
                    self._max_retries,
                    model,
                    type(exc).__name__,
                    exc,
                )
                time.sleep(delay)
            except GroqError as exc:
                logger.error("Request failed (non-retryable): %s", exc)
                raise self._map_non_retryable_exception(exc, model) from exc

        logger.error("Request failed after %s retries: %s", self._max_retries, last_exc)
        raise ProviderUnavailableError(
            f"Groq is unavailable after {self._max_retries} retries: {last_exc}"
        ) from last_exc

    async def stream(self, request: LLMRequest) -> AsyncIterator[StreamingChunk]:
        """Generate a chat response as a stream of incremental chunks.

        Retries apply only to establishing the initial stream connection
        — once the first chunk has been received and could have been
        yielded to a caller, silently retrying would risk duplicating
        already-delivered output, so a mid-stream failure is raised
        immediately as a `StreamingError` instead of retried.
        """
        model = self._resolve_model(request)
        self._validate_context_window(request, model)
        kwargs = self._build_create_kwargs(request, model)

        logger.info("Streaming started: model=%s, provider=groq", model)
        last_exc: Exception | None = None
        raw_stream = None

        for attempt in range(1, self._max_retries + 2):
            try:
                raw_stream = await self._async_client.chat.completions.create(
                    stream=True, **kwargs
                )
                break
            except _RETRYABLE_EXCEPTIONS as exc:
                last_exc = exc
                if attempt > self._max_retries:
                    break
                delay = _backoff_delay(attempt)
                logger.warning(
                    "Retry attempt %s/%s for streaming model=%s after %s: %s",
                    attempt,
                    self._max_retries,
                    model,
                    type(exc).__name__,
                    exc,
                )
                await asyncio.sleep(delay)
            except GroqError as exc:
                logger.error("Streaming request failed (non-retryable): %s", exc)
                raise self._map_non_retryable_exception(exc, model) from exc

        if raw_stream is None:
            logger.error(
                "Streaming failed to start after %s retries: %s", self._max_retries, last_exc
            )
            raise ProviderUnavailableError(
                f"Groq is unavailable after {self._max_retries} retries: {last_exc}"
            ) from last_exc

        chunk_count = 0
        try:
            async for raw_chunk in raw_stream:
                chunk_count += 1
                yield self._to_streaming_chunk(raw_chunk, model)
        except GroqError as exc:
            logger.error("Streaming failed after %s chunks: %s", chunk_count, exc)
            raise StreamingError(f"Groq streaming failed mid-stream: {exc}") from exc

        logger.info("Streaming completed: model=%s, chunks=%s", model, chunk_count)

    def count_tokens(self, text: str) -> int:
        """Count (or estimate) the number of tokens in a piece of text."""
        return self._tokenizer.count_tokens(text)

    async def health_check(self) -> bool:
        """Check whether the Groq API is currently reachable.

        Uses the lightweight `models.list` endpoint rather than issuing
        a real generation request, to avoid unnecessary cost/latency.
        """
        try:
            await self._async_client.models.list()
            return True
        except Exception as exc:
            logger.error("Groq health check failed: %s", exc)
            return False

    def list_models(self) -> list[ModelInfo]:
        """List the models this provider supports."""
        return [definition.to_model_info() for definition in list_models(LLMProvider.GROQ)]