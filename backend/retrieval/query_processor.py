import logging
import re
import unicodedata
from abc import ABC, abstractmethod

from backend.retrieval.exceptions import InvalidSearchQueryError

logger = logging.getLogger(__name__)

MAX_QUERY_LENGTH = 2000

# A small, extensible starter set of common software-engineering
# abbreviations expanded to improve semantic search recall. Deliberately
# conservative — only whole-word matches are expanded, and only for
# terms unlikely to also be meaningful identifiers on their own (e.g.
# "id" is intentionally excluded, since expanding it inside natural
# queries like "user id" is more likely to help, but as a standalone
# code identifier it's extremely common and expansion could hurt exact
# recall). Extend this mapping as real query patterns are observed.
ABBREVIATION_EXPANSIONS: dict[str, str] = {
    "auth": "authentication",
    "db": "database",
    "config": "configuration",
    "env": "environment",
    "func": "function",
    "impl": "implementation",
    "repo": "repository",
    "async": "asynchronous",
    "sync": "synchronous",
    "arg": "argument",
    "args": "arguments",
    "param": "parameter",
    "params": "parameters",
    "req": "request",
    "res": "response",
    "err": "error",
    "msg": "message",
    "ctx": "context",
}

_WHITESPACE_PATTERN = re.compile(r"\s+")


class QueryRewriter(ABC):
    """Interface for future query-rewriting strategies.

    Implementations may expand a query with synonyms, decompose it into
    sub-queries, or otherwise transform it before embedding. This
    interface intentionally does not require or imply calling an LLM —
    the retrieval engine must never do so directly — but it accommodates
    an LLM-backed implementation being plugged in from outside this
    module later (e.g. from the AI layer, injected here as a dependency).
    """

    @abstractmethod
    def rewrite(self, query: str) -> str:
        """Rewrite a normalized query.

        Args:
            query: The already-normalized query text.

        Returns:
            The rewritten query text.
        """
        raise NotImplementedError


class IdentityQueryRewriter(QueryRewriter):
    """Default no-op rewriter; returns the query unchanged."""

    def rewrite(self, query: str) -> str:
        """Return the query unchanged.

        Args:
            query: The already-normalized query text.

        Returns:
            The same query text, unmodified.
        """
        return query


class QueryProcessor:
    """Prepares raw user queries for embedding and search."""

    def __init__(
        self,
        rewriter: QueryRewriter | None = None,
        max_query_length: int = MAX_QUERY_LENGTH,
        expand_abbreviations: bool = True,
    ) -> None:
        """Initialize the query processor.

        Args:
            rewriter: A query-rewriting strategy applied after
                normalization and abbreviation expansion. Defaults to a
                no-op identity rewriter.
            max_query_length: Maximum allowed query length, in
                characters, after normalization.
            expand_abbreviations: Whether to expand known abbreviations
                as part of `prepare_for_embedding`.
        """
        self._rewriter = rewriter or IdentityQueryRewriter()
        self._max_query_length = max_query_length
        self._expand_abbreviations = expand_abbreviations

    def normalize_query(self, raw_query: str) -> str:
        """Trim whitespace and normalize Unicode representation.

        Deliberately does not lowercase the query — this is a code
        search assistant, and identifiers are frequently case-sensitive
        (e.g. `HttpClient` vs `httpclient`), so preserving case gives the
        embedding model the most faithful signal.

        Args:
            raw_query: The raw, unprocessed query text.

        Returns:
            The trimmed, whitespace-collapsed, Unicode-normalized query.
        """
        normalized = unicodedata.normalize("NFKC", raw_query)
        normalized = _WHITESPACE_PATTERN.sub(" ", normalized).strip()
        return normalized

    def expand_query_abbreviations(self, query: str) -> str:
        """Expand known whole-word abbreviations to improve search recall.

        Args:
            query: The normalized query text.

        Returns:
            The query with recognized abbreviations expanded. Original
            casing of the surrounding text is preserved; matches are
            case-insensitive but expansions are inserted in lowercase.
        """

        def _expand(match: re.Match[str]) -> str:
            word = match.group(0)
            expansion = ABBREVIATION_EXPANSIONS.get(word.lower())
            return expansion if expansion else word

        pattern = r"\b(" + "|".join(re.escape(term) for term in ABBREVIATION_EXPANSIONS) + r")\b"
        return re.sub(pattern, _expand, query, flags=re.IGNORECASE)

    def validate_query(self, query: str) -> None:
        """Validate a normalized query before it is embedded.

        Args:
            query: The normalized query text.

        Raises:
            InvalidSearchQueryError: If the query is empty or exceeds
                `max_query_length`.
        """
        if not query:
            raise InvalidSearchQueryError("Search query cannot be empty.")
        if len(query) > self._max_query_length:
            raise InvalidSearchQueryError(
                f"Search query exceeds the maximum allowed length of "
                f"{self._max_query_length} characters."
            )

    def prepare_for_embedding(self, raw_query: str) -> str:
        """Run the full query preparation pipeline.

        Normalizes, validates, optionally expands abbreviations, and
        applies the configured rewriter, in that order.

        Args:
            raw_query: The raw, unprocessed query text.

        Returns:
            The fully prepared query text, ready to be embedded.

        Raises:
            InvalidSearchQueryError: If the query fails validation at
                any point in the pipeline.
        """
        normalized = self.normalize_query(raw_query)
        self.validate_query(normalized)

        prepared = normalized
        if self._expand_abbreviations:
            prepared = self.expand_query_abbreviations(prepared)

        prepared = self._rewriter.rewrite(prepared)
        # Re-validate after rewriting, since a rewriter could in
        # principle produce an empty or oversized result.
        self.validate_query(prepared)

        if prepared != raw_query:
            logger.debug("Query prepared: %r -> %r", raw_query, prepared)

        return prepared