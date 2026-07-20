import logging
from abc import ABC, abstractmethod

from backend.retrieval.exceptions import RerankingFailedError
from backend.retrieval.schemas import RetrievedChunk

logger = logging.getLogger(__name__)


class Reranker(ABC):
    """Interface every reranking strategy must implement.

    `search.py` depends only on this interface via `rerank()` — it never
    knows or cares whether the concrete implementation is the built-in
    heuristic reranker or a future cross-encoder-backed one.
    """

    @abstractmethod
    def rerank(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        """Rerank a list of retrieved chunks for a given query.

        Args:
            query: The (prepared) query text the chunks were retrieved
                for.
            chunks: The initially-retrieved chunks, ordered by vector
                similarity.

        Returns:
            The reranked chunks.

        Raises:
            RerankingFailedError: If reranking cannot be completed.
        """
        raise NotImplementedError


class CrossEncoderReranker(Reranker):
    """Base class for future cross-encoder-backed reranking providers.

    Concrete subclasses (e.g. a BAAI reranker, Cohere Rerank, or Jina AI
    Reranker integration) should implement `_score_pairs`; this class
    handles the shared bookkeeping (normalizing scores back onto
    retrieved chunks, error wrapping) so each provider only needs to
    implement the actual scoring call.

    Not registered as the default reranker — instantiate and pass a
    concrete subclass to `search.py`'s composition root explicitly once
    a provider is implemented and configured.
    """

    def __init__(self, model_name: str) -> None:
        """Initialize the cross-encoder reranker.

        Args:
            model_name: Identifier of the cross-encoder model/provider
                this instance uses.
        """
        self.model_name = model_name

    @abstractmethod
    def _score_pairs(self, query: str, texts: list[str]) -> list[float]:
        """Score each (query, text) pair using the concrete provider.

        Args:
            query: The query text.
            texts: The candidate chunk texts to score against the query.

        Returns:
            A relevance score per text, in the same order as `texts`.
        """
        raise NotImplementedError

    def rerank(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        """Rerank chunks using cross-encoder scores from `_score_pairs`.

        Args:
            query: The query text the chunks were retrieved for.
            chunks: The initially-retrieved chunks.

        Returns:
            The chunks reordered by cross-encoder score, descending.

        Raises:
            RerankingFailedError: If `_score_pairs` raises.
        """
        if not chunks:
            return chunks
        try:
            scores = self._score_pairs(query, [chunk.text for chunk in chunks])
        except Exception as exc:
            raise RerankingFailedError(
                f"Cross-encoder reranking via '{self.model_name}' failed: {exc}"
            ) from exc

        rescored = [
            chunk.model_copy(update={"score": score})
            for chunk, score in zip(chunks, scores)
        ]
        return sorted(rescored, key=lambda chunk: chunk.score, reverse=True)


class HeuristicReranker(Reranker):
    """Default reranker: normalization, dedup, and diversity — no model call.

    Applies four passes over the initially-retrieved chunks, in order:
      1. Score normalization (min-max, onto a 0-1 range).
      2. Duplicate removal (exact text matches).
      3. Per-document diversity capping (limits how many chunks from the
         same source document can appear, so one large or highly
         repetitive file doesn't crowd out the rest of the context).
      4. Final ordering by (adjusted) score, descending.
    """

    def __init__(self, max_chunks_per_document: int = 3) -> None:
        """Initialize the heuristic reranker.

        Args:
            max_chunks_per_document: Maximum number of chunks from any
                single source document allowed to survive reranking.
        """
        self._max_chunks_per_document = max_chunks_per_document

    def rerank(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        """Apply normalization, dedup, and diversity capping.

        Args:
            query: Unused by this implementation — present to satisfy
                the `Reranker` interface, kept for future heuristics
                (e.g. lexical overlap boosting) without a signature
                change.
            chunks: The initially-retrieved chunks, ordered by vector
                similarity.

        Returns:
            The reranked chunks.
        """
        if not chunks:
            return chunks

        normalized = self._normalize_scores(chunks)
        deduplicated = self._remove_duplicates(normalized)
        diversified = self._enforce_diversity(deduplicated)
        return sorted(diversified, key=lambda chunk: chunk.score, reverse=True)

    @staticmethod
    def _normalize_scores(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        """Min-max normalize scores across a chunk list onto [0, 1].

        Args:
            chunks: The chunks to normalize.

        Returns:
            New `RetrievedChunk` instances with normalized scores. If
            all scores are equal (including a single chunk), every score
            is set to 1.0 rather than dividing by zero.
        """
        scores = [chunk.score for chunk in chunks]
        minimum, maximum = min(scores), max(scores)
        spread = maximum - minimum

        if spread == 0:
            return [chunk.model_copy(update={"score": 1.0}) for chunk in chunks]

        return [
            chunk.model_copy(update={"score": (chunk.score - minimum) / spread})
            for chunk in chunks
        ]

    @staticmethod
    def _remove_duplicates(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        """Drop chunks with exactly duplicated text, keeping the first (highest-scored).

        Args:
            chunks: The chunks to deduplicate. Assumed already ordered
                by descending score, so the first occurrence kept is the
                highest-scored one.

        Returns:
            The deduplicated chunk list, order preserved.
        """
        seen_text: set[str] = set()
        deduplicated: list[RetrievedChunk] = []
        for chunk in sorted(chunks, key=lambda c: c.score, reverse=True):
            if chunk.text in seen_text:
                continue
            seen_text.add(chunk.text)
            deduplicated.append(chunk)
        return deduplicated

    def _enforce_diversity(self, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        """Cap the number of chunks retained per source document.

        Args:
            chunks: The chunks to diversify, assumed ordered by
                descending score.

        Returns:
            The diversity-capped chunk list, order preserved.
        """
        counts: dict[str, int] = {}
        diversified: list[RetrievedChunk] = []
        for chunk in sorted(chunks, key=lambda c: c.score, reverse=True):
            count = counts.get(chunk.document_id, 0)
            if count >= self._max_chunks_per_document:
                continue
            counts[chunk.document_id] = count + 1
            diversified.append(chunk)
        return diversified