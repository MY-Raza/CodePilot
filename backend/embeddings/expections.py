class EmbeddingServiceError(Exception):
    """Base exception for all embedding service failures."""


class EmbeddingModelNotFoundError(EmbeddingServiceError):
    """Raised when a requested embedding model is not in the supported registry."""


class EmbeddingGenerationError(EmbeddingServiceError):
    """Raised when generating a single embedding fails unexpectedly."""


class CacheError(EmbeddingServiceError):
    """Raised when an embedding cache operation fails unexpectedly."""


class InvalidEmbeddingInputError(EmbeddingServiceError):
    """Raised when input text fails validation.

    Covers empty text, oversized text, invalid/undecodable encoding, and
    null values.
    """


class BatchEmbeddingError(EmbeddingServiceError):
    """Raised when generating a batch of embeddings fails."""