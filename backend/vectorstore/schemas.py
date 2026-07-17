import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DistanceMetric(str, Enum):
    """Supported vector similarity distance metrics."""

    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT = "dot"


class VectorDocument(BaseModel):
    """Metadata describing the source of a single embedded chunk.

    Attached to every vector stored in the vector database, and returned
    alongside every search result, so callers can trace a vector back to
    the exact repository file and chunk it came from.

    Attributes:
        repository_id: ID of the repository this chunk belongs to.
        document_id: ID of the source file (document) this chunk belongs to.
        chunk_id: ID of the specific chunk within the document.
        language: Detected programming/markup language of the source file.
        file_path: Path of the source file, relative to the repository root.
        branch: The repository branch this chunk was indexed from.
        embedding_model: Identifier of the model used to generate the vector.
        created_at: Timestamp the vector was created/indexed.
    """

    repository_id: str
    document_id: str
    chunk_id: str
    language: str | None = None
    file_path: str
    branch: str | None = None
    embedding_model: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EmbeddingRecord(BaseModel):
    """A single vector ready to be stored in the vector database.

    Attributes:
        id: Unique identifier for this vector record. Callers are
            responsible for generating stable, collision-free IDs (a
            common convention is `f"{document_id}:{chunk_index}"`).
        vector: The embedding vector, typically produced by the
            embeddings module.
        metadata: Structured metadata describing this vector's source.
        text: The original chunk text, optionally stored alongside the
            vector so search results can display it without a separate
            lookup.
    """

    id: str
    vector: list[float]
    metadata: VectorDocument
    text: str | None = None


class SearchRequest(BaseModel):
    """A similarity search request against a collection.

    Attributes:
        query_vector: The embedding vector to search against.
        top_k: Maximum number of results to return.
        repository_id: Optional filter restricting results to a single
            repository.
        document_id: Optional filter restricting results to a single
            source document.
        language: Optional filter restricting results to a single
            detected language.
        filters: Additional arbitrary metadata filters, applied as exact
            matches (e.g. `{"branch": "main"}`).
    """

    query_vector: list[float]
    top_k: int = Field(default=10, gt=0, le=1000)
    repository_id: str | None = None
    document_id: str | None = None
    language: str | None = None
    filters: dict[str, Any] | None = None


class SearchResult(BaseModel):
    """A single ranked result from a similarity search.

    Attributes:
        id: The matched vector record's unique identifier.
        score: Similarity score. Higher is more similar, regardless of
            the underlying distance metric (implementations normalize
            distance-based metrics to a similarity score on this field).
        metadata: The matched vector's source metadata.
        text: The matched vector's original chunk text, if it was stored.
    """

    id: str
    score: float
    metadata: VectorDocument
    text: str | None = None


class BatchInsertRequest(BaseModel):
    """A request to insert or update many vectors at once.

    Attributes:
        collection_name: The target collection.
        records: The vectors to upsert.
        batch_size: Number of records sent to the underlying provider per
            network call, bounding peak memory/payload size regardless of
            how many records are requested in total.
    """

    collection_name: str
    records: list[EmbeddingRecord] = Field(..., min_length=1)
    batch_size: int = Field(default=100, gt=0, le=1000)


class DeleteRequest(BaseModel):
    """A request to delete vectors from a collection.

    Exactly one of `ids`, `document_id`, or `repository_id` should be
    provided to scope the deletion; implementations should treat
    providing more than one as increasingly narrow (all conditions
    apply), and providing none as an error rather than deleting an
    entire collection by accident.

    Attributes:
        collection_name: The target collection.
        ids: Explicit vector record IDs to delete.
        document_id: Delete all vectors belonging to this source document.
        repository_id: Delete all vectors belonging to this repository.
    """

    collection_name: str
    ids: list[str] | None = None
    document_id: str | None = None
    repository_id: str | None = None


class CollectionResponse(BaseModel):
    """Summary information about a collection.

    Attributes:
        name: The collection's name.
        exists: Whether the collection currently exists.
        vector_count: Number of vectors currently stored, if known.
        dimension: The vector dimension the collection was created with,
            if known.
        distance_metric: The distance metric the collection uses, if known.
    """

    name: str
    exists: bool
    vector_count: int | None = None
    dimension: int | None = None
    distance_metric: DistanceMetric | None = None


class HealthResponse(BaseModel):
    """Result of a vector database health check.

    Attributes:
        provider: Identifier of the active provider (e.g. "chroma",
            "qdrant").
        healthy: Whether the provider responded successfully.
        message: Human-readable status detail.
        latency_ms: Round-trip time of the health check call, in
            milliseconds.
    """

    model_config = ConfigDict(protected_namespaces=())

    provider: str
    healthy: bool
    message: str
    latency_ms: float | None = None


def generate_vector_id(document_id: str, chunk_index: int) -> str:
    """Build a stable, collision-resistant vector record ID.

    Provided as a shared convention so every caller (repository
    indexing, re-indexing, deletion) derives the same ID for the same
    logical chunk, making upserts idempotent.

    Args:
        document_id: The source document's ID.
        chunk_index: The chunk's position within the document.

    Returns:
        A deterministic string ID safe to use as a vector record ID
        across all supported providers.
    """
    namespace = uuid.uuid5(uuid.NAMESPACE_URL, f"{document_id}:{chunk_index}")
    return str(namespace)