from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SearchFilter(BaseModel):
    """Metadata filters that can be combined and applied to a search.

    All fields are optional and combine with logical AND. Fields not
    natively indexed by the underlying vector store (see field-level
    notes) are applied best-effort — see `filters.py` for exactly how
    each is handled.

    Attributes:
        repository_id: Restrict results to a single repository.
        branch: Restrict results to a single repository branch.
        language: Restrict results to a single detected language.
        file_extension: Restrict results to files with this extension
            (e.g. ".py"). Applied client-side after retrieval, since
            extension is not a separately indexed field in the vector
            store — derived from each result's file path instead.
        document_id: Restrict results to a single source document.
        author: Restrict results to a single author. NOTE: no stage of
            the current pipeline (repository indexer, embeddings, or
            vector store) captures author metadata yet, so this filter
            is prepared but will not match anything until that metadata
            is populated upstream.
        created_after: Only include chunks indexed at or after this time.
        created_before: Only include chunks indexed at or before this time.
        metadata: Additional arbitrary equality filters, merged into the
            underlying vector store query as exact-match conditions.
    """

    repository_id: str | None = None
    branch: str | None = None
    language: str | None = None
    file_extension: str | None = None
    document_id: str | None = None
    author: str | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None
    metadata: dict[str, Any] | None = None


class SearchRequest(BaseModel):
    """A retrieval-layer search request.

    Attributes:
        query: The raw, user-supplied search query text.
        top_k: Maximum number of results to return. Falls back to the
            configured default (`TOP_K_RESULTS`) when omitted.
        similarity_threshold: Minimum similarity score a result must
            meet to be included. Falls back to the configured default
            (`SIMILARITY_THRESHOLD`) when omitted.
        filters: Metadata filters to apply.
        enable_hybrid_search: Override the configured default for
            whether to blend in keyword matching alongside semantic
            search.
        enable_reranking: Override the configured default for whether
            to rerank results after initial retrieval.
    """

    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, gt=0, le=100)
    similarity_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    filters: SearchFilter | None = None
    enable_hybrid_search: bool | None = None
    enable_reranking: bool | None = None


class RetrievedChunk(BaseModel):
    """A single raw chunk retrieved from the vector store.

    Represents the pre-context-building result of search + (optional)
    reranking — see `ContextChunk` for the post-context-building shape.

    Attributes:
        id: The vector record's unique identifier.
        text: The chunk's source text.
        score: Similarity score (higher is more similar), possibly
            adjusted by hybrid search blending and/or reranking.
        repository_id: ID of the repository this chunk belongs to.
        document_id: ID of the source document this chunk belongs to.
        chunk_id: ID of this specific chunk within the document.
        file_path: Path of the source file, relative to the repository
            root.
        language: Detected language of the source file, if known.
        branch: The repository branch this chunk was indexed from.
        start_line: Starting line number of this chunk within the source
            file, if available. NOTE: not currently populated —
            `backend.vectorstore.schemas.VectorDocument` does not carry
            line-number metadata yet; see this module's README notes.
        end_line: Ending line number of this chunk, under the same
            availability caveat as `start_line`.
    """

    id: str
    text: str
    score: float
    repository_id: str
    document_id: str
    chunk_id: str
    file_path: str
    language: str | None = None
    branch: str | None = None
    start_line: int | None = None
    end_line: int | None = None


class SearchResponse(BaseModel):
    """The result of a retrieval-layer search.

    Attributes:
        query: The (possibly normalized) query text that was searched.
        results: The retrieved chunks, ordered from most to least
            relevant.
        total_results: Number of chunks returned.
        search_type: Which search strategy produced these results
            ("semantic" or "hybrid").
        reranked: Whether reranking was applied to these results.
    """

    query: str
    results: list[RetrievedChunk]
    total_results: int
    search_type: str
    reranked: bool


class Citation(BaseModel):
    """A source citation for a chunk included in an assembled context.

    Attributes:
        repository_name: Human-readable repository name.
        document_name: The source file's base name (e.g. "main.py").
        relative_file_path: Path of the source file, relative to the
            repository root.
        chunk_number: This chunk's index within its source document.
        similarity_score: The chunk's similarity score at time of
            retrieval.
        language: Detected language of the source file, if known.
        branch: The repository branch this chunk was indexed from.
        start_line: Starting line number, if available (see
            `RetrievedChunk.start_line`'s availability caveat).
        end_line: Ending line number, if available.
        source_url: Placeholder for a deep link to the source location
            (e.g. a GitHub blob URL). Not populated by this module —
            this module has no knowledge of repository host/URL
            conventions; a caller with that context (e.g. the API layer)
            can fill this in.
    """

    repository_name: str
    document_name: str
    relative_file_path: str
    chunk_number: int
    similarity_score: float
    language: str | None = None
    branch: str | None = None
    start_line: int | None = None
    end_line: int | None = None
    source_url: str | None = None


class ContextChunk(BaseModel):
    """A chunk included in the final, assembled LLM-ready context.

    Attributes:
        text: The chunk's source text, unmodified (code formatting and
            Markdown are preserved as-is).
        citation: This chunk's source citation.
        token_estimate: Estimated token count for this chunk's text.
    """

    text: str
    citation: Citation
    token_estimate: int


class ContextResponse(BaseModel):
    """The result of building an LLM-ready context from retrieved chunks.

    This module never calls an LLM itself — `context` is prepared text
    intended for a caller (the AI layer) to inject into a prompt.

    Attributes:
        context: The assembled, prompt-ready text block, with chunks
            separated and each preceded by a short citation header.
        chunks: The individual chunks included in `context`, in order.
        citations: Citations for every included chunk, in the same order
            as `chunks`.
        total_tokens_estimate: Estimated total token count of `context`.
        truncated: True if one or more retrieved chunks were dropped to
            stay within the configured token budget.
    """

    context: str
    chunks: list[ContextChunk]
    citations: list[Citation]
    total_tokens_estimate: int
    truncated: bool