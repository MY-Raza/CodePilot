class RetrievalError(Exception):
    """Base exception for all retrieval engine failures."""


class SearchFailedError(RetrievalError):
    """Raised when a vector database search fails.

    Wraps lower-level `backend.vectorstore.exceptions` failures so
    callers of this module depend only on retrieval-layer exceptions,
    never on which vector database provider is active underneath.
    """


class ContextTooLargeError(RetrievalError):
    """Raised when context cannot be built within the configured token budget.

    Specifically raised when even a single retrieved chunk exceeds the
    maximum context size on its own — not raised for the normal case of
    truncating a longer chunk list to fit, which is signaled instead via
    `ContextResponse.truncated`.
    """


class NoResultsFoundError(RetrievalError):
    """Raised when context is requested from an empty set of retrieved chunks."""


class InvalidSearchQueryError(RetrievalError):
    """Raised when a search query fails validation (empty, oversized, etc.)."""


class RerankingFailedError(RetrievalError):
    """Raised when a reranking step fails.

    Callers in `search.py` catch this internally and fall back to the
    original similarity-ranked order rather than failing the whole
    search — see `search.py` for that resilience behavior. This
    exception exists so reranker implementations have a well-defined
    failure signal to raise, and so direct callers of a reranker (e.g.
    in tests) can assert on failure explicitly.
    """