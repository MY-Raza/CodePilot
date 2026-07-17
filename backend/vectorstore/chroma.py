import logging
import re
import time

import chromadb
from chromadb.config import Settings as ChromaSettings

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

# ChromaDB collection names must be 3-512 characters from [a-zA-Z0-9._-],
# starting and ending with an alphanumeric character.
_VALID_COLLECTION_NAME = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{1,510}[a-zA-Z0-9]$")

# Metadata keys every stored vector's payload includes, mirroring
# VectorDocument's fields. Centralized so chroma.py and qdrant.py agree
# on the same on-the-wire metadata shape.
_METADATA_FIELDS = (
    "repository_id",
    "document_id",
    "chunk_id",
    "language",
    "file_path",
    "branch",
    "embedding_model",
    "created_at",
)


def _metadata_to_dict(metadata: VectorDocument) -> dict:
    """Flatten a `VectorDocument` into a ChromaDB-compatible metadata dict.

    ChromaDB metadata values must be str/int/float/bool — None values are
    dropped rather than stored, since ChromaDB rejects None.

    Args:
        metadata: The structured metadata to flatten.

    Returns:
        A flat dict suitable for ChromaDB's `metadatas` parameter.
    """
    raw = metadata.model_dump(mode="json")
    return {key: value for key, value in raw.items() if value is not None}


def _dict_to_metadata(data: dict) -> VectorDocument:
    """Reconstruct a `VectorDocument` from a ChromaDB metadata dict.

    Args:
        data: The raw metadata dict returned by ChromaDB.

    Returns:
        The reconstructed structured metadata.
    """
    return VectorDocument(**{key: data.get(key) for key in _METADATA_FIELDS if key in data})


def _distance_to_similarity(distance: float, metric: str) -> float:
    """Convert a ChromaDB distance value into a higher-is-better similarity score.

    ChromaDB always returns "distance" (lower is more similar); this
    module's `SearchResult.score` contract is "higher is more similar"
    regardless of provider, so a conversion is applied based on the
    collection's configured space.

    Args:
        distance: The raw distance value returned by ChromaDB.
        metric: The collection's configured hnsw space ("cosine", "l2",
            or "ip").

    Returns:
        A similarity score where higher means more similar.
    """
    if metric == "cosine":
        return 1.0 - distance
    if metric == "ip":
        # ChromaDB stores inner-product distance as its negation.
        return -distance
    # l2 (squared euclidean): monotonically decreasing transform into (0, 1].
    return 1.0 / (1.0 + distance)


class ChromaVectorStore(VectorStoreBase):
    """`VectorStoreBase` implementation backed by ChromaDB.

    Intended for local development and single-node deployments, per the
    project's Development/Production provider split (ChromaDB / Qdrant).
    """

    def __init__(self, persist_directory: str) -> None:
        """Initialize a persistent ChromaDB client.

        Args:
            persist_directory: Filesystem directory ChromaDB persists
                its data to. Created automatically if it does not exist.

        Raises:
            ConnectionFailedError: If the persistent client cannot be
                initialized (e.g. an unwritable directory).
        """
        try:
            self._client = chromadb.PersistentClient(
                path=persist_directory,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        except Exception as exc:
            raise ConnectionFailedError(
                f"Failed to initialize ChromaDB persistent client at "
                f"'{persist_directory}': {exc}"
            ) from exc
        self._persist_directory = persist_directory
        logger.info(
            "Connection established: ChromaDB (persist_directory=%s)",
            persist_directory,
        )

    def _get_collection(self, collection_name: str):
        """Fetch an existing collection, raising if it does not exist.

        Args:
            collection_name: Name of the collection to fetch.

        Returns:
            The ChromaDB collection handle.

        Raises:
            CollectionNotFoundError: If the collection does not exist.
        """
        if not self.collection_exists(collection_name):
            raise CollectionNotFoundError(
                f"Collection '{collection_name}' does not exist."
            )
        return self._client.get_collection(
            name=collection_name, embedding_function=None
        )

    def create_collection(
        self,
        collection_name: str,
        dimension: int,
        distance_metric: DistanceMetric = DistanceMetric.COSINE,
    ) -> CollectionResponse:
        """Create a new collection, if it does not already exist."""
        if not _VALID_COLLECTION_NAME.match(collection_name):
            raise InsertFailedError(
                f"Invalid collection name '{collection_name}': ChromaDB "
                "requires 3-512 characters from [a-zA-Z0-9._-], starting "
                "and ending with an alphanumeric character."
            )

        space = {
            DistanceMetric.COSINE: "cosine",
            DistanceMetric.EUCLIDEAN: "l2",
            DistanceMetric.DOT: "ip",
        }[distance_metric]

        try:
            self._client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": space},
                embedding_function=None,
            )
        except Exception as exc:
            raise InsertFailedError(
                f"Failed to create collection '{collection_name}': {exc}"
            ) from exc

        logger.info("Collection created: %s (space=%s)", collection_name, space)
        return CollectionResponse(
            name=collection_name,
            exists=True,
            vector_count=self.count_documents(collection_name),
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
            self._client.delete_collection(name=collection_name)
        except Exception as exc:
            raise DeleteFailedError(
                f"Failed to delete collection '{collection_name}': {exc}"
            ) from exc
        logger.info("Collection deleted: %s", collection_name)

    def collection_exists(self, collection_name: str) -> bool:
        """Check whether a collection currently exists."""
        existing_names = {
            collection.name for collection in self._client.list_collections()
        }
        return collection_name in existing_names

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
        collection = self._get_collection(collection_name)
        total_upserted = 0

        for start in range(0, len(records), batch_size):
            chunk = records[start : start + batch_size]
            try:
                collection.upsert(
                    ids=[record.id for record in chunk],
                    embeddings=[record.vector for record in chunk],
                    metadatas=[_metadata_to_dict(record.metadata) for record in chunk],
                    documents=[record.text or "" for record in chunk],
                )
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
        collection = self._get_collection(collection_name)
        try:
            collection.delete(ids=ids)
        except Exception as exc:
            raise DeleteFailedError(
                f"Failed to delete embeddings from '{collection_name}': {exc}"
            ) from exc
        logger.info("Embeddings deleted: %s vectors from '%s'", len(ids), collection_name)
        return len(ids)

    def delete_document(self, collection_name: str, document_id: str) -> int:
        """Delete every vector belonging to a single source document."""
        collection = self._get_collection(collection_name)
        before = collection.count()
        try:
            collection.delete(where={"document_id": document_id})
        except Exception as exc:
            raise DeleteFailedError(
                f"Failed to delete document '{document_id}' from "
                f"'{collection_name}': {exc}"
            ) from exc
        deleted = before - collection.count()
        logger.info(
            "Embeddings deleted: %s vectors for document '%s' from '%s'",
            deleted,
            document_id,
            collection_name,
        )
        return deleted

    def delete_repository(self, collection_name: str, repository_id: str) -> int:
        """Delete every vector belonging to a repository."""
        collection = self._get_collection(collection_name)
        before = collection.count()
        try:
            collection.delete(where={"repository_id": repository_id})
        except Exception as exc:
            raise DeleteFailedError(
                f"Failed to delete repository '{repository_id}' from "
                f"'{collection_name}': {exc}"
            ) from exc
        deleted = before - collection.count()
        logger.info(
            "Embeddings deleted: %s vectors for repository '%s' from '%s'",
            deleted,
            repository_id,
            collection_name,
        )
        return deleted

    def similarity_search(
        self, collection_name: str, request: SearchRequest
    ) -> list[SearchResult]:
        """Search a collection for vectors similar to a query vector."""
        collection = self._get_collection(collection_name)
        logger.info(
            "Search started: collection='%s', top_k=%s", collection_name, request.top_k
        )

        where = self._build_where_filter(request)
        space = collection.metadata.get("hnsw:space", "cosine") if collection.metadata else "cosine"

        try:
            raw = collection.query(
                query_embeddings=[request.query_vector],
                n_results=request.top_k,
                where=where or None,
                include=["metadatas", "documents", "distances"],
            )
        except Exception as exc:
            raise SearchFailedError(
                f"Similarity search failed on '{collection_name}': {exc}"
            ) from exc

        results: list[SearchResult] = []
        ids = raw.get("ids", [[]])[0]
        distances = raw.get("distances", [[]])[0]
        metadatas = raw.get("metadatas", [[]])[0]
        documents = raw.get("documents", [[]])[0]

        for record_id, distance, metadata, document in zip(
            ids, distances, metadatas, documents
        ):
            results.append(
                SearchResult(
                    id=record_id,
                    score=_distance_to_similarity(distance, space),
                    metadata=_dict_to_metadata(metadata or {}),
                    text=document or None,
                )
            )

        logger.info(
            "Search completed: collection='%s', results=%s", collection_name, len(results)
        )
        return results

    @staticmethod
    def _build_where_filter(request: SearchRequest) -> dict:
        """Build a ChromaDB `where` filter from a `SearchRequest`.

        Args:
            request: The search request whose repository/document/
                language/custom filters should be combined.

        Returns:
            A ChromaDB-compatible `where` filter dict. Multiple
            conditions are combined with `$and`; ChromaDB requires this
            explicit combinator when more than one condition is present.
        """
        conditions = []
        if request.repository_id is not None:
            conditions.append({"repository_id": request.repository_id})
        if request.document_id is not None:
            conditions.append({"document_id": request.document_id})
        if request.language is not None:
            conditions.append({"language": request.language})
        if request.filters:
            for key, value in request.filters.items():
                conditions.append({key: value})

        if not conditions:
            return {}
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}

    def count_documents(self, collection_name: str) -> int:
        """Count the total number of vectors stored in a collection."""
        collection = self._get_collection(collection_name)
        return collection.count()

    def health_check(self) -> HealthResponse:
        """Check whether the underlying ChromaDB instance is reachable."""
        start = time.perf_counter()
        try:
            self._client.heartbeat()
            latency_ms = (time.perf_counter() - start) * 1000
            return HealthResponse(
                provider="chroma",
                healthy=True,
                message="ChromaDB is reachable.",
                latency_ms=latency_ms,
            )
        except Exception as exc:
            logger.error("ChromaDB health check failed: %s", exc)
            return HealthResponse(
                provider="chroma",
                healthy=False,
                message=f"ChromaDB health check failed: {exc}",
                latency_ms=None,
            )