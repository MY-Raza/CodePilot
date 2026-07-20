import logging

from backend.retrieval.schemas import RetrievedChunk, SearchFilter
from backend.vectorstore.schemas import SearchRequest as VectorStoreSearchRequest

logger = logging.getLogger(__name__)


def build_vector_store_filters(search_filter: SearchFilter | None) -> dict[str, object]:
    """Build the generic metadata filter dict passed to the vector store.

    Only fields the vector store can index and filter on server-side
    belong here (`repository_id`, `document_id`, and `language` have
    dedicated `VectorStoreSearchRequest` fields and are excluded from
    this dict — see `apply_to_vector_store_request`). Everything else
    that maps onto stored metadata (currently just `branch`, plus any
    caller-supplied `metadata`) goes into the generic equality-filter
    dict.

    `file_extension`, `created_after`/`created_before`, and `author` are
    intentionally NOT included here:
      - `file_extension` has no dedicated indexed field; it's applied
        client-side in `apply_client_side_filters` instead.
      - `created_after`/`created_before` need range comparison, which
        the current vector store abstraction's equality-only `filters`
        dict cannot express.
      - `author` has no corresponding field anywhere upstream (the
        repository indexer, embeddings, and vector store metadata
        schemas don't capture it yet), so it cannot be translated into
        a working filter at all today.

    Args:
        search_filter: The retrieval-layer filter to translate, or None.

    Returns:
        A flat dict of exact-match conditions for
        `VectorStoreSearchRequest.filters`. Empty if there is nothing to
        filter on server-side.
    """
    if search_filter is None:
        return {}

    conditions: dict[str, object] = {}
    if search_filter.branch is not None:
        conditions["branch"] = search_filter.branch
    if search_filter.metadata:
        conditions.update(search_filter.metadata)

    if search_filter.author is not None:
        logger.warning(
            "Author filtering was requested but no stage of the indexing "
            "pipeline currently stores author metadata; this filter will "
            "not match any results until that metadata is populated "
            "upstream."
        )
        conditions["author"] = search_filter.author

    if search_filter.created_after is not None or search_filter.created_before is not None:
        logger.warning(
            "created_after/created_before were requested, but the vector "
            "store's filter interface only supports exact-match "
            "conditions, not date ranges. These filters are not applied "
            "server-side; consider filtering client-side on "
            "RetrievedChunk if this becomes a hard requirement."
        )

    return conditions


def apply_to_vector_store_request(
    query_vector: list[float],
    top_k: int,
    search_filter: SearchFilter | None,
) -> VectorStoreSearchRequest:
    """Build a fully-populated `VectorStoreSearchRequest` from retrieval filters.

    Args:
        query_vector: The embedded query vector to search with.
        top_k: Maximum number of results to request from the vector store.
        search_filter: The retrieval-layer filter to translate.

    Returns:
        A vector-store-layer search request with `repository_id`,
        `document_id`, and `language` mapped to their dedicated fields,
        and everything else folded into `filters`.
    """
    return VectorStoreSearchRequest(
        query_vector=query_vector,
        top_k=top_k,
        repository_id=search_filter.repository_id if search_filter else None,
        document_id=search_filter.document_id if search_filter else None,
        language=search_filter.language if search_filter else None,
        filters=build_vector_store_filters(search_filter) or None,
    )


def apply_client_side_filters(
    chunks: list[RetrievedChunk], search_filter: SearchFilter | None
) -> list[RetrievedChunk]:
    """Apply filter conditions the vector store cannot enforce server-side.

    Currently handles `file_extension` only, matched against each
    chunk's `file_path` suffix.

    Args:
        chunks: Already-retrieved chunks to filter.
        search_filter: The retrieval-layer filter to apply.

    Returns:
        The filtered chunk list, preserving original order.
    """
    if search_filter is None or search_filter.file_extension is None:
        return chunks

    extension = search_filter.file_extension
    if not extension.startswith("."):
        extension = f".{extension}"

    return [chunk for chunk in chunks if chunk.file_path.endswith(extension)]