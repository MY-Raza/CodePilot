import logging
import time
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PayloadSchemaType,
    PointIdsList,
    PointStruct,
    VectorParams,
)

from backend.vectorstore.base import VectorStoreBase
from backend.vectorstore.exceptions import (
    CollectionNotFoundError,
    ConnectionFailedError,
    DeleteFailedError,
    InsertFailedError,
    SearchFailedError,
)
from backend.vectorstore.schemas import (
    CollectionResponse,
    DistanceMetric,
    EmbeddingRecord,
    HealthResponse,
    SearchRequest,
    SearchResult,
    VectorDocument,
)

logger = logging.getLogger(__name__)

# Reserved payload key storing the caller-supplied record ID, so it can
# be recovered even though Qdrant's own point ID is a derived UUID.
_ORIGINAL_ID_PAYLOAD_KEY = "__vector_id"

# Metadata fields indexed for efficient server-side filtering. Payload
# indexing is a Qdrant-specific optimization with no ChromaDB equivalent
# needed (ChromaDB filters unindexed metadata efficiently by default at
# this scale), so it lives here rather than in the shared base interface.
_INDEXED_PAYLOAD_FIELDS = ("repository_id", "document_id", "language", "branch")

_DISTANCE_MAP = {
    DistanceMetric.COSINE: Distance.COSINE,
    DistanceMetric.EUCLIDEAN: Distance.EUCLID,
    DistanceMetric.DOT: Distance.DOT,
}


def _to_point_id(record_id: str) -> str:
    """Translate a caller-supplied record ID into a valid Qdrant point ID.

    Args:
        record_id: The caller-supplied `EmbeddingRecord.id`.

    Returns:
        `record_id` unchanged if it is already a valid UUID string,
        otherwise a UUID5 deterministically derived from it (stable
        across calls, so repeated upserts of the same logical record
        remain idempotent).
    """
    try:
        uuid.UUID(record_id)
        return record_id
    except ValueError:
        return str(uuid.uuid5(uuid.NAMESPACE_URL, record_id))


class QdrantVectorStore(VectorStoreBase):
    """`VectorStoreBase` implementation backed by Qdrant."""

    def __init__(self, url: str, api_key: str | None = None) -> None:
        """Initialize a Qdrant client.

        Args:
            url: The Qdrant instance URL (self-hosted or Qdrant Cloud).
            api_key: API key for Qdrant Cloud or a secured self-hosted
                instance. None for an unsecured local instance.

        Raises:
            ConnectionFailedError: If the client cannot be constructed.
        """
        try:
            self._client = QdrantClient(url=url, api_key=api_key)
        except Exception as exc:
            raise ConnectionFailedError(
                f"Failed to initialize Qdrant client for '{url}': {exc}"
            ) from exc
        logger.info("Connection established: Qdrant (url=%s)", url)

    def create_collection(
        self,
        collection_name: str,
        dimension: int,
        distance_metric: DistanceMetric = DistanceMetric.COSINE,
    ) -> CollectionResponse:
        """Create a new collection, if it does not already exist."""
        if self.collection_exists(collection_name):
            return CollectionResponse(
                name=collection_name,
                exists=True,
                vector_count=self.count_documents(collection_name),
                dimension=dimension,
                distance_metric=distance_metric,
            )

        try:
            self._client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=dimension, distance=_DISTANCE_MAP[distance_metric]
                ),
            )
            for field_name in _INDEXED_PAYLOAD_FIELDS:
                self._client.create_payload_index(
                    collection_name=collection_name,
                    field_name=field_name,
                    field_schema=PayloadSchemaType.KEYWORD,
                )
        except Exception as exc:
            raise InsertFailedError(
                f"Failed to create collection '{collection_name}': {exc}"
            ) from exc

        logger.info(
            "Collection created: %s (dimension=%s, metric=%s)",
            collection_name,
            dimension,
            distance_metric.value,
        )
        return CollectionResponse(
            name=collection_name,
            exists=True,
            vector_count=0,
            dimension=dimension,
            distance_metric=distance_metric,
        )

    def delete_collection(self, collection_name: str) -> None:
        """Permanently delete a collection and all vectors within it."""
        if not self.collection_exists(collection_name):
            raise CollectionNotFoundError(
                f"Collection '{collection_name}' does not exist."
            )
        try:
            self._client.delete_collection(collection_name=collection_name)
        except Exception as exc:
            raise DeleteFailedError(
                f"Failed to delete collection '{collection_name}': {exc}"
            ) from exc
        logger.info("Collection deleted: %s", collection_name)

    def collection_exists(self, collection_name: str) -> bool:
        """Check whether a collection currently exists."""
        return self._client.collection_exists(collection_name=collection_name)

    def upsert_embeddings(
        self, collection_name: str, records: list[EmbeddingRecord]
    ) -> int:
        """Insert or update a small set of vectors in a single call."""
        return self.batch_upsert(collection_name, records, batch_size=len(records) or 1)

    def batch_upsert(
        self,
        collection_name: str,
        records: list[EmbeddingRecord],
        batch_size: int = 100,
    ) -> int:
        """Insert or update a large set of vectors in bounded-size chunks."""
        if not self.collection_exists(collection_name):
            raise CollectionNotFoundError(
                f"Collection '{collection_name}' does not exist."
            )

        total_upserted = 0
        for start in range(0, len(records), batch_size):
            chunk = records[start : start + batch_size]
            points = [
                PointStruct(
                    id=_to_point_id(record.id),
                    vector=record.vector,
                    payload={
                        **record.metadata.model_dump(mode="json"),
                        "text": record.text,
                        _ORIGINAL_ID_PAYLOAD_KEY: record.id,
                    },
                )
                for record in chunk
            ]
            try:
                self._client.upsert(collection_name=collection_name, points=points)
            except Exception as exc:
                raise InsertFailedError(
                    f"Failed to upsert batch into collection "
                    f"'{collection_name}': {exc}"
                ) from exc
            total_upserted += len(chunk)

        logger.info(
            "Embeddings inserted: %s vectors into '%s'",
            total_upserted,
            collection_name,
        )
        return total_upserted

    def delete_embeddings(self, collection_name: str, ids: list[str]) -> int:
        """Delete specific vectors by their record IDs."""
        if not self.collection_exists(collection_name):
            raise CollectionNotFoundError(
                f"Collection '{collection_name}' does not exist."
            )
        try:
            self._client.delete(
                collection_name=collection_name,
                points_selector=PointIdsList(
                    points=[_to_point_id(record_id) for record_id in ids]
                ),
            )
        except Exception as exc:
            raise DeleteFailedError(
                f"Failed to delete embeddings from '{collection_name}': {exc}"
            ) from exc
        logger.info("Embeddings deleted: %s vectors from '%s'", len(ids), collection_name)
        return len(ids)

    def delete_document(self, collection_name: str, document_id: str) -> int:
        """Delete every vector belonging to a single source document."""
        return self._delete_by_field(collection_name, "document_id", document_id)

    def delete_repository(self, collection_name: str, repository_id: str) -> int:
        """Delete every vector belonging to a repository."""
        return self._delete_by_field(collection_name, "repository_id", repository_id)

    def _delete_by_field(
        self, collection_name: str, field_name: str, value: str
    ) -> int:
        """Delete every point whose payload matches a single field/value pair.

        Args:
            collection_name: The target collection.
            field_name: The indexed payload field to match on.
            value: The value to match.

        Returns:
            The number of points deleted.

        Raises:
            CollectionNotFoundError: If the collection does not exist.
            DeleteFailedError: If deletion fails.
        """
        if not self.collection_exists(collection_name):
            raise CollectionNotFoundError(
                f"Collection '{collection_name}' does not exist."
            )
        before = self.count_documents(collection_name)
        try:
            self._client.delete(
                collection_name=collection_name,
                points_selector=Filter(
                    must=[FieldCondition(key=field_name, match=MatchValue(value=value))]
                ),
            )
        except Exception as exc:
            raise DeleteFailedError(
                f"Failed to delete points where {field_name}='{value}' from "
                f"'{collection_name}': {exc}"
            ) from exc
        deleted = before - self.count_documents(collection_name)
        logger.info(
            "Embeddings deleted: %s vectors where %s='%s' from '%s'",
            deleted,
            field_name,
            value,
            collection_name,
        )
        return deleted

    def similarity_search(
        self, collection_name: str, request: SearchRequest
    ) -> list[SearchResult]:
        """Search a collection for vectors similar to a query vector."""
        if not self.collection_exists(collection_name):
            raise CollectionNotFoundError(
                f"Collection '{collection_name}' does not exist."
            )
        logger.info(
            "Search started: collection='%s', top_k=%s", collection_name, request.top_k
        )

        query_filter = self._build_filter(request)
        try:
            response = self._client.query_points(
                collection_name=collection_name,
                query=request.query_vector,
                limit=request.top_k,
                query_filter=query_filter,
                with_payload=True,
            )
        except Exception as exc:
            raise SearchFailedError(
                f"Similarity search failed on '{collection_name}': {exc}"
            ) from exc

        results = [self._point_to_result(point) for point in response.points]
        logger.info(
            "Search completed: collection='%s', results=%s", collection_name, len(results)
        )
        return results

    @staticmethod
    def _point_to_result(point) -> SearchResult:
        """Convert a Qdrant `ScoredPoint` into a provider-agnostic `SearchResult`.

        Args:
            point: A `ScoredPoint` returned by `query_points`.

        Returns:
            The normalized search result, with `id` restored to the
            original caller-supplied record ID.
        """
        payload = dict(point.payload or {})
        original_id = payload.pop(_ORIGINAL_ID_PAYLOAD_KEY, str(point.id))
        text = payload.pop("text", None)
        metadata_fields = {
            "repository_id",
            "document_id",
            "chunk_id",
            "language",
            "file_path",
            "branch",
            "embedding_model",
            "created_at",
        }
        metadata = VectorDocument(
            **{key: payload.get(key) for key in metadata_fields if key in payload}
        )
        return SearchResult(id=original_id, score=point.score, metadata=metadata, text=text)

    @staticmethod
    def _build_filter(request: SearchRequest) -> Filter | None:
        """Build a Qdrant `Filter` from a `SearchRequest`.

        Args:
            request: The search request whose repository/document/
                language/custom filters should be combined.

        Returns:
            A `Filter` requiring all present conditions to match, or
            None if no filters were specified.
        """
        conditions = []
        if request.repository_id is not None:
            conditions.append(
                FieldCondition(
                    key="repository_id", match=MatchValue(value=request.repository_id)
                )
            )
        if request.document_id is not None:
            conditions.append(
                FieldCondition(
                    key="document_id", match=MatchValue(value=request.document_id)
                )
            )
        if request.language is not None:
            conditions.append(
                FieldCondition(key="language", match=MatchValue(value=request.language))
            )
        if request.filters:
            for key, value in request.filters.items():
                conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))

        return Filter(must=conditions) if conditions else None

    def count_documents(self, collection_name: str) -> int:
        """Count the total number of vectors stored in a collection."""
        if not self.collection_exists(collection_name):
            raise CollectionNotFoundError(
                f"Collection '{collection_name}' does not exist."
            )
        return self._client.count(collection_name=collection_name, exact=True).count

    def health_check(self) -> HealthResponse:
        """Check whether the underlying Qdrant instance is reachable."""
        start = time.perf_counter()
        try:
            self._client.get_collections()
            latency_ms = (time.perf_counter() - start) * 1000
            return HealthResponse(
                provider="qdrant",
                healthy=True,
                message="Qdrant is reachable.",
                latency_ms=latency_ms,
            )
        except Exception as exc:
            logger.error("Qdrant health check failed: %s", exc)
            return HealthResponse(
                provider="qdrant",
                healthy=False,
                message=f"Qdrant health check failed: {exc}",
                latency_ms=None,
            )