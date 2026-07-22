import logging
from collections.abc import AsyncIterator, Callable

from backend.llm.exceptions import StreamingError
from backend.llm.schemas import StreamingChunk

logger = logging.getLogger(__name__)


class StreamController:
    """A cancellation flag shared between a stream consumer and its caller.

    Usage:
        controller = StreamController()
        stream = consume_stream(provider.stream(request), controller=controller)
        # ... elsewhere, e.g. on client disconnect ...
        controller.cancel()
    """

    def __init__(self) -> None:
        """Initialize the controller in the not-cancelled state."""
        self._cancelled = False

    def cancel(self) -> None:
        """Request cancellation of the associated stream.

        Takes effect before the next chunk is yielded — any chunk
        already in flight when this is called is still delivered.
        """
        self._cancelled = True

    @property
    def is_cancelled(self) -> bool:
        """Whether cancellation has been requested."""
        return self._cancelled


class StreamAggregator:
    """Accumulates streaming chunks into a single complete text and outcome."""

    def __init__(self) -> None:
        """Initialize an empty aggregator."""
        self._parts: list[str] = []
        self.chunk_count: int = 0
        self.finish_reason: str | None = None

    def add(self, chunk: StreamingChunk) -> None:
        """Record a single streaming chunk.

        Args:
            chunk: The chunk to accumulate.
        """
        if chunk.delta:
            self._parts.append(chunk.delta)
        self.chunk_count += 1
        if chunk.finish_reason is not None:
            self.finish_reason = chunk.finish_reason

    @property
    def text(self) -> str:
        """The full text accumulated so far, in chunk order."""
        return "".join(self._parts)


async def consume_stream(
    raw_stream: AsyncIterator[StreamingChunk],
    controller: StreamController | None = None,
    on_chunk: Callable[[StreamingChunk], None] | None = None,
    aggregator: StreamAggregator | None = None,
) -> AsyncIterator[StreamingChunk]:
    """Wrap a provider's raw chunk stream with aggregation/cancellation/callbacks.

    Args:
        raw_stream: The provider's normalized chunk stream (e.g. from
            `GroqProvider.stream()`).
        controller: An optional cancellation controller. If its
            `cancel()` is called from another task, iteration stops
            before the next chunk is yielded.
        on_chunk: An optional callback invoked with each chunk as it is
            yielded. Exceptions raised by the callback are logged and
            swallowed — a broken callback should never break the stream
            itself.
        aggregator: An optional `StreamAggregator` to accumulate chunks
            into. If omitted, chunks are still yielded but nothing
            accumulates them — pass one explicitly if you need the full
            text afterward.

    Yields:
        Each chunk from `raw_stream`, in order, until exhaustion or
        cancellation.

    Raises:
        StreamingError: If iterating `raw_stream` raises.
    """
    logger.info("Streaming started.")
    chunk_count = 0
    try:
        async for chunk in raw_stream:
            if controller is not None and controller.is_cancelled:
                logger.info("Streaming cancelled after %s chunks.", chunk_count)
                return

            if aggregator is not None:
                aggregator.add(chunk)

            if on_chunk is not None:
                try:
                    on_chunk(chunk)
                except Exception:
                    logger.warning(
                        "Streaming on_chunk callback raised; continuing stream.",
                        exc_info=True,
                    )

            chunk_count += 1
            yield chunk
    except StreamingError:
        raise
    except Exception as exc:
        logger.error("Streaming failed after %s chunks: %s", chunk_count, exc)
        raise StreamingError(f"Streaming failed: {exc}") from exc

    logger.info("Streaming completed: %s chunks.", chunk_count)


async def to_sse_stream(chunks: AsyncIterator[StreamingChunk]) -> AsyncIterator[str]:
    """Adapt a chunk stream into Server-Sent-Events-formatted strings.

    Directly usable as the `content` argument of
    `fastapi.responses.StreamingResponse` (with
    `media_type="text/event-stream"`) without this module importing
    FastAPI itself.

    Args:
        chunks: The chunk stream to adapt, typically the output of
            `consume_stream`.

    Yields:
        SSE-formatted strings, one JSON-encoded chunk per event, ending
        with a terminal `data: [DONE]` event.
    """
    async for chunk in chunks:
        yield f"data: {chunk.model_dump_json()}\n\n"
    yield "data: [DONE]\n\n"