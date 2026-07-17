import logging
import os
import time
from collections.abc import Callable

from backend.embeddings.cache import DEFAULT_CACHE_SIZE, EmbeddingCache
from backend.embeddings.exceptions import (
    BatchEmbeddingError,
    EmbeddingGenerationError,
    InvalidEmbeddingInputError,
)
from backend.embeddings.factory import EmbeddingFactory
from backend.embeddings.models import DOCUMENT_PREFIXES, QUERY_PREFIXES
from backend.embeddings.schemas import (
    BatchEmbeddingRequest,
    BatchEmbeddingResponse,
    EmbeddingMetadata,
    EmbeddingRequest,
    EmbeddingResponse,
    QueryEmbeddingRequest,
)

logger = logging.getLogger(__name__)

# Configuration, read from environment with sensible defaults. Consider
# formalizing these into backend.core.settings if other modules end up
# needing them too.
MAX_TEXT_LENGTH: int = int(os.getenv("EMBEDDING_MAX_TEXT_LENGTH", "20000"))
DEFAULT_BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))

# Invoked with (texts_processed, total_texts) after each internal batch
# completes during batch embedding generation. Optional.
ProgressCallback = Callable[[int, int], None]


def _validate_text(text: str) -> str:
    """Validate a single text input before embedding.

    Args:
        text: The candidate text to validate.

    Returns:
        The validated text, unchanged.

    Raises:
        InvalidEmbeddingInputError: If the text is null, not a string,
            empty/whitespace-only, oversized, or contains undecodable
            byte sequences.
    """
    if text is None:
        raise InvalidEmbeddingInputError("Text cannot be null.")
    if not isinstance(text, str):
        raise InvalidEmbeddingInputError("Text must be a string.")
    if not text.strip():
        raise InvalidEmbeddingInputError("Text cannot be empty or whitespace-only.")
    if len(text) > MAX_TEXT_LENGTH:
        raise InvalidEmbeddingInputError(
            f"Text exceeds maximum length of {MAX_TEXT_LENGTH} characters "
            f"(got {len(text)})."
        )
    try:
        text.encode("utf-8").decode("utf-8")
    except UnicodeError as exc:
        raise InvalidEmbeddingInputError("Text contains invalid encoding.") from exc
    return text


class EmbeddingService:
    """Generates embeddings for text, backed by a cached model provider.

    Each `EmbeddingService` instance is bound to a single model/device
    pair for its lifetime; the underlying model itself is loaded once
    (via `EmbeddingFactory`) and shared across every service instance
    that requests the same (model_name, device) combination.
    """

    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
        cache: EmbeddingCache | None = None,
    ) -> None:
        """Initialize the service.

        Args:
            model_name: A supported embedding model identifier. Falls
                back to the `EMBEDDING_MODEL` environment variable (via
                `EmbeddingFactory`) when omitted.
            device: The compute device to run on. Falls back to the
                `EMBEDDING_DEVICE` environment variable / auto-detection
                when omitted.
            batch_size: Number of texts encoded per internal forward
                pass during batch generation. Falls back to the
                `EMBEDDING_BATCH_SIZE` environment variable.
            cache: An `EmbeddingCache` instance. A new one is constructed
                (sized via `EMBEDDING_CACHE_SIZE`) when omitted, allowing
                dependency injection for testing or cache sharing.
        """
        self._provider = EmbeddingFactory.get_model(model_name, device)
        self._batch_size = batch_size
        self._cache = cache or EmbeddingCache(
            max_size=int(os.getenv("EMBEDDING_CACHE_SIZE", str(DEFAULT_CACHE_SIZE)))
        )

    @property
    def model_name(self) -> str:
        """The identifier of the currently loaded embedding model."""
        return self._provider.model_name

    @property
    def dimension(self) -> int:
        """The vector dimension produced by the currently loaded model."""
        return self._provider.dimension

    @property
    def cache_stats(self):
        """Current cache hit/miss/eviction statistics."""
        return self._cache.stats

    def _embed_single(self, model_input_text: str, response_text: str) -> EmbeddingResponse:
        """Cache-check, encode, and build a response for one piece of text.

        Shared by `generate_embedding` and `generate_query_embedding` so
        model-specific instruction prefixes can differ between the two
        while the caching/encoding/response-construction logic stays in
        one place.

        Args:
            model_input_text: The exact text sent to the model and used
                as the cache key — this is the (possibly prefixed) text.
            response_text: The text surfaced back to the caller in the
                response's `text` field — the original, un-prefixed text.

        Returns:
            The generated (or cache-served) embedding and its metadata.

        Raises:
            EmbeddingGenerationError: If the underlying model fails to
                produce an embedding.
        """
        cached_vector = self._cache.get(model_input_text, self._provider.model_name)
        if cached_vector is not None:
            return EmbeddingResponse(
                text=response_text,
                embedding=cached_vector,
                metadata=EmbeddingMetadata(
                    model_name=self._provider.model_name,
                    dimension=self._provider.dimension,
                    generation_time_seconds=0.0,
                    device=self._provider.device,
                    normalized=True,
                    cached=True,
                ),
            )

        start_time = time.perf_counter()
        try:
            vectors = self._provider.encode(
                [model_input_text], batch_size=1, normalize=True
            )
        except Exception as exc:
            logger.error("Embedding generation failed: %s", exc)
            raise EmbeddingGenerationError(
                f"Failed to generate embedding: {exc}"
            ) from exc
        elapsed_seconds = time.perf_counter() - start_time

        vector = vectors[0]
        self._cache.set(model_input_text, self._provider.model_name, vector)
        logger.info(
            "Embedding generated in %.4fs (model=%s, dimension=%s)",
            elapsed_seconds,
            self._provider.model_name,
            self._provider.dimension,
        )

        return EmbeddingResponse(
            text=response_text,
            embedding=vector,
            metadata=EmbeddingMetadata(
                model_name=self._provider.model_name,
                dimension=self._provider.dimension,
                generation_time_seconds=elapsed_seconds,
                device=self._provider.device,
                normalized=True,
                cached=False,
            ),
        )

    def generate_embedding(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate an embedding for a single piece of document/chunk text.

        Automatically applies the model-specific document instruction
        prefix, if any (see `document_prefix`), so callers never need to
        remember to do this themselves — symmetric with how
        `generate_query_embedding` handles the query-side prefix.

        Args:
            request: The text to embed.

        Returns:
            The generated (or cache-served) embedding and its metadata.
            The response's `text` field contains the original,
            un-prefixed input text.

        Raises:
            InvalidEmbeddingInputError: If the text fails validation.
            EmbeddingGenerationError: If the underlying model fails to
                produce an embedding.
        """
        text = _validate_text(request.text)
        prefix = DOCUMENT_PREFIXES.get(self._provider.model_name, "")
        return self._embed_single(f"{prefix}{text}", text)

    def generate_batch_embeddings(
        self,
        request: BatchEmbeddingRequest,
        on_progress: ProgressCallback | None = None,
    ) -> BatchEmbeddingResponse:
        """Generate embeddings for multiple texts, batching and caching efficiently.

        Cache lookups happen first for every text; only cache misses are
        sent to the model, and those are encoded in `batch_size`-sized
        chunks to bound peak memory usage regardless of how many texts
        are requested. Duplicate texts within the same batch — common
        when re-indexing a repository with repeated boilerplate — are
        encoded at most once each, regardless of how many times they
        occur in `request.texts`.

        Args:
            request: The texts to embed, in order.
            on_progress: Optional callback invoked as `(processed, total)`
                after each internal batch completes.

        Returns:
            Per-text results in the same order as the request, plus
            aggregate timing and cache statistics for the batch.

        Raises:
            InvalidEmbeddingInputError: If any text fails validation.
            BatchEmbeddingError: If encoding the batch fails.
        """
        logger.info("Batch started: %s texts", len(request.texts))
        start_time = time.perf_counter()

        try:
            validated_texts = [_validate_text(text) for text in request.texts]
        except InvalidEmbeddingInputError as exc:
            raise BatchEmbeddingError(f"Invalid text in batch: {exc}") from exc

        responses: list[EmbeddingResponse | None] = [None] * len(validated_texts)
        cache_hits = 0
        cache_misses = 0
        document_prefix = DOCUMENT_PREFIXES.get(self._provider.model_name, "")

        # Group indices by their exact (prefixed) model-input text so that
        # duplicate texts within this single batch — a common occurrence
        # when re-indexing a repository with repeated boilerplate — are
        # only ever encoded once, regardless of how many times they occur
        # or whether they were already in the persistent cache.
        indices_by_text: dict[str, list[int]] = {}
        for index, text in enumerate(validated_texts):
            model_input_text = f"{document_prefix}{text}"
            indices_by_text.setdefault(model_input_text, []).append(index)

        texts_to_encode: list[str] = []

        for model_input_text, indices in indices_by_text.items():
            cached_vector = self._cache.get(model_input_text, self._provider.model_name)
            if cached_vector is not None:
                cache_hits += len(indices)
                for index in indices:
                    responses[index] = EmbeddingResponse(
                        text=validated_texts[index],
                        embedding=cached_vector,
                        metadata=EmbeddingMetadata(
                            model_name=self._provider.model_name,
                            dimension=self._provider.dimension,
                            generation_time_seconds=0.0,
                            device=self._provider.device,
                            normalized=True,
                            cached=True,
                        ),
                    )
            else:
                # Only the first occurrence requires real computation; any
                # duplicate occurrences in this batch are satisfied by that
                # same computation without a separate model call, so they
                # count toward hits rather than misses.
                cache_misses += 1
                cache_hits += len(indices) - 1
                texts_to_encode.append(model_input_text)

        if texts_to_encode:
            try:
                vectors = self._encode_in_batches(texts_to_encode, on_progress)
            except Exception as exc:
                logger.error("Batch embedding generation failed: %s", exc)
                raise BatchEmbeddingError(
                    f"Failed to generate batch embeddings: {exc}"
                ) from exc

            per_text_time = (time.perf_counter() - start_time) / len(texts_to_encode)
            for model_input_text, vector in zip(texts_to_encode, vectors):
                self._cache.set(model_input_text, self._provider.model_name, vector)
                for index in indices_by_text[model_input_text]:
                    responses[index] = EmbeddingResponse(
                        text=validated_texts[index],
                        embedding=vector,
                        metadata=EmbeddingMetadata(
                            model_name=self._provider.model_name,
                            dimension=self._provider.dimension,
                            generation_time_seconds=per_text_time,
                            device=self._provider.device,
                            normalized=True,
                            cached=False,
                        ),
                    )

        total_time_seconds = time.perf_counter() - start_time
        logger.info(
            "Batch finished: %s texts, %s cache hits, %s cache misses, %.4fs total",
            len(validated_texts),
            cache_hits,
            cache_misses,
            total_time_seconds,
        )

        return BatchEmbeddingResponse(
            embeddings=[response for response in responses if response is not None],
            total_texts=len(validated_texts),
            total_time_seconds=total_time_seconds,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
        )

    def _encode_in_batches(
        self, texts: list[str], on_progress: ProgressCallback | None = None
    ) -> list[list[float]]:
        """Encode texts in configurable-size batches for memory efficiency.

        Args:
            texts: The texts to encode (already validated, already
                filtered to cache misses only).
            on_progress: Optional callback invoked as `(processed, total)`
                after each batch.

        Returns:
            One embedding vector per input text, in the same order.
        """
        all_vectors: list[list[float]] = []
        total = len(texts)

        for start_index in range(0, total, self._batch_size):
            batch = texts[start_index : start_index + self._batch_size]
            batch_vectors = self._provider.encode(
                batch, batch_size=self._batch_size, normalize=True
            )
            all_vectors.extend(batch_vectors)

            if on_progress is not None:
                on_progress(min(start_index + len(batch), total), total)

        return all_vectors

    def generate_query_embedding(self, request: QueryEmbeddingRequest) -> EmbeddingResponse:
        """Generate an embedding for a search query.

        Applies the model-specific query instruction prefix, if any
        (asymmetric retrieval models such as BGE and Nomic expect
        different prefixes for queries vs. indexed documents to produce
        well-calibrated similarity scores). The returned response's
        `text` field contains the original, un-prefixed query for
        clarity to the caller.

        Args:
            request: The raw search query.

        Returns:
            The generated embedding and its metadata.

        Raises:
            InvalidEmbeddingInputError: If the query fails validation.
            EmbeddingGenerationError: If the underlying model fails to
                produce an embedding.
        """
        query = _validate_text(request.query)
        prefix = QUERY_PREFIXES.get(self._provider.model_name, "")
        return self._embed_single(f"{prefix}{query}", query)

    def document_prefix(self) -> str:
        """Return the model-specific document instruction prefix, if any.

        Applied automatically by `generate_embedding` and
        `generate_batch_embeddings` — exposed here only for introspection
        or testing, not because callers need to apply it themselves.

        Returns:
            The prefix string for the currently loaded model, or an empty
            string if the model does not use one.
        """
        return DOCUMENT_PREFIXES.get(self._provider.model_name, "")