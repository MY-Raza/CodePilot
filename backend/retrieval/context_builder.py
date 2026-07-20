import logging
from collections.abc import Callable

from backend.retrieval.exceptions import ContextTooLargeError, NoResultsFoundError
from backend.retrieval.schemas import Citation, ContextChunk, ContextResponse, RetrievedChunk

logger = logging.getLogger(__name__)

DEFAULT_MAX_CONTEXT_TOKENS = 4000

# Characters-per-token approximation used when no real tokenizer is
# injected. This is a coarse, provider-agnostic heuristic (commonly
# cited for English prose with GPT-style BPE tokenizers); it is not
# exact for any particular model, and deliberately not tied to a
# specific tokenizer library (e.g. tiktoken) so this module has no
# dependency on which LLM provider ends up consuming its output. Inject
# a real tokenizer via `token_counter` wherever precise budgeting matters.
_CHARS_PER_TOKEN_ESTIMATE = 4


def estimate_tokens(text: str) -> int:
    """Approximate a text's token count using a characters-per-token heuristic.

    Args:
        text: The text to estimate.

    Returns:
        An approximate token count. Always at least 1 for non-empty text.
    """
    if not text:
        return 0
    return max(1, len(text) // _CHARS_PER_TOKEN_ESTIMATE)


def _document_name(file_path: str) -> str:
    """Extract a file's base name from its (possibly nested) path.

    Args:
        file_path: A relative or absolute file path.

    Returns:
        The final path component.
    """
    return file_path.rsplit("/", 1)[-1]


def _build_citation(chunk: RetrievedChunk, repository_name: str, chunk_number: int) -> Citation:
    """Build a `Citation` for a single retrieved chunk.

    Args:
        chunk: The chunk to cite.
        repository_name: Human-readable repository name.
        chunk_number: This chunk's position within the assembled context
            (1-indexed), used as a simple, stable per-context chunk
            number since a chunk's position within its own source
            document isn't tracked at this layer.

    Returns:
        The chunk's citation. `source_url` is left as None — this module
        has no knowledge of repository host/URL conventions.
    """
    return Citation(
        repository_name=repository_name,
        document_name=_document_name(chunk.file_path),
        relative_file_path=chunk.file_path,
        chunk_number=chunk_number,
        similarity_score=chunk.score,
        language=chunk.language,
        branch=chunk.branch,
        start_line=chunk.start_line,
        end_line=chunk.end_line,
        source_url=None,
    )


def _format_chunk_block(text: str, citation: Citation) -> str:
    """Format a single chunk's text with a citation header for prompt injection.

    Preserves the chunk's original formatting verbatim (code and
    Markdown are never rewritten), wrapping it in a fenced block tagged
    with the detected language so downstream Markdown/code rendering
    behaves correctly.

    Args:
        text: The chunk's source text.
        citation: The chunk's citation, used to build the header.

    Returns:
        A formatted block combining a citation header and the fenced
        chunk text.
    """
    location = citation.relative_file_path
    if citation.start_line is not None and citation.end_line is not None:
        location = f"{location}:{citation.start_line}-{citation.end_line}"

    header = f"[Source: {citation.repository_name} — {location}]"
    fence_tag = citation.language or ""
    return f"{header}\n```{fence_tag}\n{text}\n```"


class ContextBuilder:
    """Merges retrieved chunks into a single, token-budgeted LLM context."""

    def __init__(
        self,
        max_context_tokens: int = DEFAULT_MAX_CONTEXT_TOKENS,
        token_counter: Callable[[str], int] = estimate_tokens,
    ) -> None:
        """Initialize the context builder.

        Args:
            max_context_tokens: The token budget the assembled `context`
                string must fit within.
            token_counter: A function estimating the token count of a
                string. Defaults to a coarse characters-per-token
                heuristic; inject a real tokenizer for precise budgeting.
        """
        self._max_context_tokens = max_context_tokens
        self._token_counter = token_counter

    def build_context(
        self, chunks: list[RetrievedChunk], repository_name: str = "repository"
    ) -> ContextResponse:
        """Merge retrieved chunks into a single, deduplicated, budgeted context.

        Chunks are processed in the order given (callers should pass
        already-reranked chunks for best results) and preserved in that
        order in the output — this module does not re-sort. Chunks are
        added until the next chunk would exceed `max_context_tokens`, at
        which point assembly stops and `truncated=True` is set.

        Args:
            chunks: The chunks to merge, in priority order (most
                relevant first).
            repository_name: Human-readable repository name used in
                citations. Callers with access to multiple repositories'
                chunks in one context should prefer chunks already
                carrying this information, or call this method once per
                repository and merge results themselves.

        Returns:
            The assembled context, its per-chunk breakdown, and citations.

        Raises:
            NoResultsFoundError: If `chunks` is empty.
            ContextTooLargeError: If even the single highest-priority
                chunk exceeds `max_context_tokens` on its own.
        """
        if not chunks:
            raise NoResultsFoundError(
                "Cannot build context: no chunks were provided."
            )

        deduplicated = self._remove_duplicate_chunks(chunks)

        first_citation = _build_citation(deduplicated[0], repository_name, chunk_number=1)
        first_block = _format_chunk_block(deduplicated[0].text, first_citation)
        first_tokens = self._token_counter(first_block)
        if first_tokens > self._max_context_tokens:
            raise ContextTooLargeError(
                f"The single highest-priority chunk alone requires an "
                f"estimated {first_tokens} tokens, exceeding the "
                f"configured budget of {self._max_context_tokens} tokens."
            )

        context_chunks: list[ContextChunk] = []
        citations: list[Citation] = []
        blocks: list[str] = []
        total_tokens = 0
        truncated = False

        for index, chunk in enumerate(deduplicated, start=1):
            citation = _build_citation(chunk, repository_name, chunk_number=index)
            block = _format_chunk_block(chunk.text, citation)
            block_tokens = self._token_counter(block)

            if total_tokens + block_tokens > self._max_context_tokens:
                truncated = True
                logger.debug(
                    "Context builder stopped at chunk %s/%s: token budget reached.",
                    index,
                    len(deduplicated),
                )
                break

            blocks.append(block)
            context_chunks.append(
                ContextChunk(text=chunk.text, citation=citation, token_estimate=block_tokens)
            )
            citations.append(citation)
            total_tokens += block_tokens

        context_text = "\n\n".join(blocks)
        logger.info(
            "Context built: %s chunks, ~%s tokens, truncated=%s",
            len(context_chunks),
            total_tokens,
            truncated,
        )

        return ContextResponse(
            context=context_text,
            chunks=context_chunks,
            citations=citations,
            total_tokens_estimate=total_tokens,
            truncated=truncated,
        )

    @staticmethod
    def _remove_duplicate_chunks(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        """Remove exact-text duplicate chunks, preserving first occurrence order.

        A final safety net independent of reranking — `build_context`
        may be called directly with un-reranked results.

        Args:
            chunks: The chunks to deduplicate.

        Returns:
            The deduplicated chunk list, original order preserved.
        """
        seen_text: set[str] = set()
        deduplicated: list[RetrievedChunk] = []
        for chunk in chunks:
            if chunk.text in seen_text:
                continue
            seen_text.add(chunk.text)
            deduplicated.append(chunk)
        return deduplicated