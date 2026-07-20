import logging
import os

from backend.embeddings import EmbeddingService, QueryEmbeddingRequest
from backend.retrieval.context_builder import ContextBuilder
from backend.retrieval.exceptions import SearchFailedError
from backend.retrieval.filters import apply_client_side_filters, apply_to_vector_store_request
from backend.retrieval.query_processor import QueryProcessor
from backend.retrieval.reranker import HeuristicReranker, Reranker
from backend.retrieval.schemas import (
    ContextResponse,
    RetrievedChunk,
    SearchFilter,
    SearchRequest,
    SearchResponse,
)
from backend.vectorstore import DEFAULT_COLLECTION_NAME, DEFAULT_TOP_K, VectorStoreBase, get_vector_store
from backend.vectorstore.exceptions import VectorStoreError
from backend.vectorstore.schemas import SearchResult as VectorSearchResult

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------
# Read once here (the composition root) and injected into collaborators
# via constructor defaults, rather than each submodule reading
# environment variables independently. Consider formalizing these into
# backend.core.settings if other modules end up needing them too.
TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS", str(DEFAULT_TOP_K)))
MAX_CONTEXT_TOKENS: int = int(os.getenv("MAX_CONTEXT_TOKENS", "4000"))
SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.0"))
ENABLE_HYBRID_SEARCH: bool = os.getenv("ENABLE_HYBRID_SEARCH", "false").strip().lower() == "true"
ENABLE_RERANKING: bool = os.getenv("ENABLE_RERANKING", "true").strip().lower() == "true"
# Weight given to semantic similarity vs. keyword overlap when hybrid
# search is enabled; see `_keyword_overlap_score` for why this is a
# lexical-overlap heuristic rather than a real BM25/full-text engine.
HYBRID_SEARCH_SEMANTIC_WEIGHT: float = float(
    os.getenv("HYBRID_SEARCH_SEMANTIC_WEIGHT", "0.7")
)


def _vector_result_to_chunk(result: VectorSearchResult) -> RetrievedChunk:
    """Convert a vector-store-layer search result into a retrieval-layer chunk.

    Args:
        result: A single result from `VectorStoreBase.similarity_search`.

    Returns:
        The equivalent `RetrievedChunk`. `start_line`/`end_line` are
        always None today — `backend.vectorstore.schemas.VectorDocument`
        does not carry line-number metadata yet (a gap introduced
        upstream, not something this module can fill in).
    """
    metadata = result.metadata
    return RetrievedChunk(
        id=result.id,
        text=result.text or "",
        score=result.score,
        repository_id=metadata.repository_id,
        document_id=metadata.document_id,
        chunk_id=metadata.chunk_id,
        file_path=metadata.file_path,
        language=metadata.language,
        branch=metadata.branch,
        start_line=None,
        end_line=None,
    )


def _keyword_overlap_score(query: str, text: str) -> float:
    """Approximate lexical overlap between a query and a chunk's text.

    A pragmatic stand-in for a real keyword/BM25 search engine, which
    this application does not currently have configured. Computes the
    fraction of distinct query terms (longer than 2 characters, to skip
    trivial noise words) that appear as a case-insensitive substring in
    the chunk text.

    This is intentionally simple. If hybrid search quality becomes a
    priority, swapping this for a proper inverted-index/BM25 engine
    would be a meaningful upgrade without changing this function's
    single call site in `_apply_hybrid_scoring`.

    Args:
        query: The (prepared) query text.
        text: The candidate chunk text.

    Returns:
        A score in [0, 1]: the fraction of matched query terms.
    """
    terms = {term.lower() for term in query.split() if len(term) > 2}
    if not terms:
        return 0.0
    text_lower = text.lower()
    matched = sum(1 for term in terms if term in text_lower)
    return matched / len(terms)


class RetrievalSearchService:
    """Orchestrates the full retrieval pipeline for a query.

    Depends only on `EmbeddingService` (to embed queries) and
    `VectorStoreBase` (to search vectors) — never on a concrete
    embedding model or vector database provider, and never on an LLM.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        vector_store: VectorStoreBase | None = None,
        query_processor: QueryProcessor | None = None,
        reranker: Reranker | None = None,
        context_builder: ContextBuilder | None = None,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        top_k: int = TOP_K_RESULTS,
        similarity_threshold: float = SIMILARITY_THRESHOLD,
        enable_hybrid_search: bool = ENABLE_HYBRID_SEARCH,
        enable_reranking: bool = ENABLE_RERANKING,
        hybrid_semantic_weight: float = HYBRID_SEARCH_SEMANTIC_WEIGHT,
    ) -> None:
        """Initialize the retrieval search service.

        Args:
            embedding_service: The embedding service used to embed
                queries. Defaults to a new `EmbeddingService` using the
                application's configured default model.
            vector_store: The vector store to search. Defaults to the
                application's configured active provider.
            query_processor: The query preparation pipeline. Defaults to
                a standard `QueryProcessor`.
            reranker: The reranking strategy. Defaults to the built-in
                `HeuristicReranker` (no external model call).
            context_builder: The context assembly component used by
                `search_and_build_context`. Defaults to a
                `ContextBuilder` using `MAX_CONTEXT_TOKENS`.
            collection_name: The vector store collection to search.
            top_k: Default maximum number of results per search, used
                when a `SearchRequest` doesn't specify one.
            similarity_threshold: Default minimum similarity score,
                used when a `SearchRequest` doesn't specify one.
            enable_hybrid_search: Default hybrid search toggle, used
                when a `SearchRequest` doesn't specify one.
            enable_reranking: Default reranking toggle, used when a
                `SearchRequest` doesn't specify one.
            hybrid_semantic_weight: Weight (0-1) given to semantic
                similarity vs. keyword overlap during hybrid scoring.
        """
        self._embedding_service = embedding_service or EmbeddingService()
        self._vector_store = vector_store or get_vector_store()
        self._query_processor = query_processor or QueryProcessor()
        self._reranker = reranker or HeuristicReranker()
        self._context_builder = context_builder or ContextBuilder(
            max_context_tokens=MAX_CONTEXT_TOKENS
        )
        self._collection_name = collection_name
        self._top_k_default = top_k
        self._similarity_threshold_default = similarity_threshold
        self._enable_hybrid_search_default = enable_hybrid_search
        self._enable_reranking_default = enable_reranking
        self._hybrid_semantic_weight = hybrid_semantic_weight

    def search(self, request: SearchRequest) -> SearchResponse:
        """Run the full retrieval pipeline for a single query.

        Pipeline: prepare query -> embed -> vector search -> client-side
        filters -> (optional) hybrid scoring -> similarity threshold ->
        (optional) reranking -> top_k truncation.

        Args:
            request: The search request.

        Returns:
            The search results and metadata about how they were produced.

        Raises:
            InvalidSearchQueryError: If the query fails validation.
            SearchFailedError: If the underlying vector store search fails.
        """
        top_k = request.top_k or self._top_k_default
        similarity_threshold = (
            request.similarity_threshold
            if request.similarity_threshold is not None
            else self._similarity_threshold_default
        )
        use_hybrid = (
            request.enable_hybrid_search
            if request.enable_hybrid_search is not None
            else self._enable_hybrid_search_default
        )
        use_reranking = (
            request.enable_reranking
            if request.enable_reranking is not None
            else self._enable_reranking_default
        )

        prepared_query = self._query_processor.prepare_for_embedding(request.query)
        logger.info(
            "Search started: query=%r, top_k=%s, hybrid=%s, reranking=%s",
            prepared_query,
            top_k,
            use_hybrid,
            use_reranking,
        )

        try:
            query_embedding = self._embedding_service.generate_query_embedding(
                QueryEmbeddingRequest(query=prepared_query)
            )
            vector_request = apply_to_vector_store_request(
                query_vector=query_embedding.embedding,
                top_k=top_k,
                search_filter=request.filters,
            )
            raw_results = self._vector_store.similarity_search(
                self._collection_name, vector_request
            )
        except VectorStoreError as exc:
            logger.error("Search failed: %s", exc)
            raise SearchFailedError(f"Vector store search failed: {exc}") from exc

        chunks = [_vector_result_to_chunk(result) for result in raw_results]
        logger.info("Chunks retrieved: %s", len(chunks))
        chunks = apply_client_side_filters(chunks, request.filters)

        search_type = "semantic"
        if use_hybrid:
            chunks = self._apply_hybrid_scoring(prepared_query, chunks)
            search_type = "hybrid"

        chunks = [chunk for chunk in chunks if chunk.score >= similarity_threshold]

        reranked = False
        if use_reranking and chunks:
            chunks = self._safe_rerank(prepared_query, chunks)
            reranked = True

        chunks = chunks[:top_k]

        logger.info(
            "Search completed: query=%r, results=%s, type=%s, reranked=%s",
            prepared_query,
            len(chunks),
            search_type,
            reranked,
        )
        return SearchResponse(
            query=prepared_query,
            results=chunks,
            total_results=len(chunks),
            search_type=search_type,
            reranked=reranked,
        )

    def search_and_build_context(
        self, request: SearchRequest, repository_name: str = "repository"
    ) -> ContextResponse:
        """Run `search()` and immediately assemble the results into context.

        Convenience method chaining retrieval and context assembly for
        the common case where a caller (e.g. the AI layer) wants
        LLM-ready context directly, without manually wiring the two
        steps together.

        Args:
            request: The search request.
            repository_name: Human-readable repository name for citations.

        Returns:
            The assembled context, ready for prompt injection.

        Raises:
            InvalidSearchQueryError: If the query fails validation.
            SearchFailedError: If the underlying vector store search fails.
            NoResultsFoundError: If the search returns no chunks.
            ContextTooLargeError: If even the top result alone exceeds
                the configured token budget.
        """
        response = self.search(request)
        return self._context_builder.build_context(
            response.results, repository_name=repository_name
        )

    def _apply_hybrid_scoring(
        self, query: str, chunks: list[RetrievedChunk]
    ) -> list[RetrievedChunk]:
        """Blend semantic similarity with keyword overlap and re-sort.

        Args:
            query: The prepared query text.
            chunks: The semantically-retrieved chunks.

        Returns:
            The chunks with blended scores, re-sorted descending.
        """
        blended: list[RetrievedChunk] = []
        for chunk in chunks:
            keyword_score = _keyword_overlap_score(query, chunk.text)
            blended_score = (
                self._hybrid_semantic_weight * chunk.score
                + (1 - self._hybrid_semantic_weight) * keyword_score
            )
            blended.append(chunk.model_copy(update={"score": blended_score}))
        return sorted(blended, key=lambda chunk: chunk.score, reverse=True)

    def _safe_rerank(
        self, query: str, chunks: list[RetrievedChunk]
    ) -> list[RetrievedChunk]:
        """Rerank chunks, falling back to the original order on failure.

        A reranking failure (e.g. a future cross-encoder call erroring
        out) should degrade search quality, not break it outright — this
        wrapper logs the failure and returns the pre-rerank order rather
        than propagating the error to the caller.

        Args:
            query: The prepared query text.
            chunks: The chunks to rerank.

        Returns:
            The reranked chunks, or the original chunks if reranking
            failed.
        """
        try:
            reranked = self._reranker.rerank(query, chunks)
            logger.info("Chunks reranked: %s -> %s", len(chunks), len(reranked))
            return reranked
        except Exception as exc:
            logger.warning(
                "Reranking failed (%s); falling back to similarity-ranked order.",
                exc,
            )
            return chunks

    # -------------------------------------------------------------------
    # Convenience wrappers for the spec's named search "types" — thin
    # sugar over search() with the corresponding filter field pre-set.
    # -------------------------------------------------------------------
    def repository_search(
        self, query: str, repository_id: str, **kwargs: object
    ) -> SearchResponse:
        """Search restricted to a single repository.

        Args:
            query: The raw search query.
            repository_id: The repository to restrict results to.
            **kwargs: Additional `SearchRequest` fields (e.g. `top_k`).

        Returns:
            The search results.
        """
        return self._search_with_filter_field(query, "repository_id", repository_id, **kwargs)

    def document_search(
        self, query: str, document_id: str, **kwargs: object
    ) -> SearchResponse:
        """Search restricted to a single source document.

        Args:
            query: The raw search query.
            document_id: The document to restrict results to.
            **kwargs: Additional `SearchRequest` fields.

        Returns:
            The search results.
        """
        return self._search_with_filter_field(query, "document_id", document_id, **kwargs)

    def language_search(
        self, query: str, language: str, **kwargs: object
    ) -> SearchResponse:
        """Search restricted to a single detected language.

        Args:
            query: The raw search query.
            language: The language to restrict results to.
            **kwargs: Additional `SearchRequest` fields.

        Returns:
            The search results.
        """
        return self._search_with_filter_field(query, "language", language, **kwargs)

    def branch_search(self, query: str, branch: str, **kwargs: object) -> SearchResponse:
        """Search restricted to a single repository branch.

        Args:
            query: The raw search query.
            branch: The branch to restrict results to.
            **kwargs: Additional `SearchRequest` fields.

        Returns:
            The search results.
        """
        return self._search_with_filter_field(query, "branch", branch, **kwargs)

    def _search_with_filter_field(
        self, query: str, field_name: str, value: str, **kwargs: object
    ) -> SearchResponse:
        """Shared implementation for the single-field convenience search methods.

        Args:
            query: The raw search query.
            field_name: The `SearchFilter` field to set.
            value: The value to set it to.
            **kwargs: Additional `SearchRequest` fields.

        Returns:
            The search results.
        """
        search_filter = SearchFilter(**{field_name: value})
        return self.search(SearchRequest(query=query, filters=search_filter, **kwargs))

    def batch_search(self, queries: list[str], **kwargs: object) -> list[SearchResponse]:
        """Run `search()` sequentially for a list of queries.

        A convenience wrapper, not true parallel/batched retrieval — the
        `VectorStoreBase` interface (Module 9) searches one query vector
        at a time, so this issues one full pipeline run per query.

        Args:
            queries: The raw search queries.
            **kwargs: Additional `SearchRequest` fields applied to every
                query in the batch.

        Returns:
            One `SearchResponse` per input query, in the same order.
        """
        return [self.search(SearchRequest(query=query, **kwargs)) for query in queries]


def get_search_service() -> RetrievalSearchService:
    """FastAPI-dependency-compatible accessor for a `RetrievalSearchService`.

    Usage:
        from fastapi import Depends
        from backend.retrieval.search import get_search_service

        def some_endpoint(
            search_service: RetrievalSearchService = Depends(get_search_service),
        ):
            ...

    Returns:
        A new `RetrievalSearchService` wired with the application's
        default embedding service and vector store. Unlike
        `VectorStoreFactory`/`EmbeddingFactory`, this is not cached as a
        singleton — construction is cheap, since the expensive
        resources it wires together (the loaded embedding model, the
        vector store connection) are already singletons themselves.
    """
    return RetrievalSearchService()