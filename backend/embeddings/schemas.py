from pydantic import BaseModel, ConfigDict, Field


class EmbeddingMetadata(BaseModel):
    """Metadata describing how an embedding vector was produced.

    Attributes:
        model_name: Identifier of the embedding model used.
        dimension: Length of the embedding vector.
        generation_time_seconds: Wall-clock time spent generating this
            embedding. Zero for cache hits, since no computation occurred.
        device: Compute device the model ran on ("cpu", "cuda", "mps").
        normalized: Whether the vector was L2-normalized (cosine-ready).
        cached: Whether this embedding was served from cache rather than
            freshly computed.
    """

    model_name: str
    dimension: int
    generation_time_seconds: float
    device: str
    normalized: bool = True
    cached: bool = False


class EmbeddingRequest(BaseModel):
    """Request to generate a single embedding.

    Attributes:
        text: The text to embed. Validated for emptiness/size/encoding by
            the service layer, not by this schema alone.
    """

    text: str = Field(..., min_length=1)


class EmbeddingResponse(BaseModel):
    """Result of generating a single embedding.

    Attributes:
        text: The original input text (or, for query embeddings, the
            original un-prefixed query).
        embedding: The generated embedding vector.
        metadata: Details about how the embedding was produced.
    """

    model_config = ConfigDict(frozen=True)

    text: str
    embedding: list[float]
    metadata: EmbeddingMetadata


class BatchEmbeddingRequest(BaseModel):
    """Request to generate embeddings for multiple texts at once.

    Attributes:
        texts: The texts to embed, in order. Order is preserved in the
            corresponding `BatchEmbeddingResponse`.
    """

    texts: list[str] = Field(..., min_length=1)


class BatchEmbeddingResponse(BaseModel):
    """Result of a batch embedding generation request.

    Attributes:
        embeddings: Per-text results, in the same order as the request.
        total_texts: Total number of texts processed.
        total_time_seconds: Total wall-clock time for the whole batch.
        cache_hits: Number of texts served from cache.
        cache_misses: Number of texts that required fresh computation.
    """

    embeddings: list[EmbeddingResponse]
    total_texts: int
    total_time_seconds: float
    cache_hits: int
    cache_misses: int


class QueryEmbeddingRequest(BaseModel):
    """Request to generate an embedding for a search query.

    Kept distinct from `EmbeddingRequest` because query embeddings may
    receive a different model-specific instruction prefix than document
    embeddings do (asymmetric embedding models such as BGE and Nomic
    expect this).

    Attributes:
        query: The raw search query text, without any model-specific
            prefix applied — the service layer handles that.
    """

    query: str = Field(..., min_length=1)