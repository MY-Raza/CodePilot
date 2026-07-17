from abc import ABC, abstractmethod

from backend.vectorstore.schemas import (
    CollectionResponse,
    DistanceMetric,
    EmbeddingRecord,
    HealthResponse,
    SearchRequest,
    SearchResult,
)


class VectorStoreBase(ABC):
    """Provider-agnostic interface for storing and retrieving embeddings.

    Implementations must be safe to use as request-scoped or
    application-scoped objects; `VectorStoreFactory` is responsible for
    deciding the actual lifecycle (typically a process-wide singleton,
    since providers hold network/persistent connections).
    """

    @abstractmethod
    def create_collection(
        self,
        collection_name: str,
        dimension: int,
        distance_metric: DistanceMetric = DistanceMetric.COSINE,
    ) -> CollectionResponse:
        """Create a new collection, if it does not already exist.

        Args:
            collection_name: Name of the collection to create.
            dimension: Vector dimension every record in this collection
                must match (determined by the embedding model used).
            distance_metric: Similarity metric the collection is indexed
                for.

        Returns:
            A summary of the created (or already-existing) collection.

        Raises:
            InsertFailedError: If collection creation fails.
        """
        raise NotImplementedError

    @abstractmethod
    def delete_collection(self, collection_name: str) -> None:
        """Permanently delete a collection and all vectors within it.

        Args:
            collection_name: Name of the collection to delete.

        Raises:
            CollectionNotFoundError: If the collection does not exist.
            DeleteFailedError: If deletion fails for another reason.
        """
        raise NotImplementedError

    @abstractmethod
    def collection_exists(self, collection_name: str) -> bool:
        """Check whether a collection currently exists.

        Args:
            collection_name: Name of the collection to check.

        Returns:
            True if the collection exists, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def upsert_embeddings(
        self, collection_name: str, records: list[EmbeddingRecord]
    ) -> int:
        """Insert or update a small set of vectors in a single call.

        For large sets, prefer `batch_upsert`, which chunks records to
        bound peak request size and memory usage.

        Args:
            collection_name: The target collection.
            records: The vectors to upsert.

        Returns:
            The number of records successfully upserted.

        Raises:
            CollectionNotFoundError: If the collection does not exist.
            InsertFailedError: If the upsert fails.
        """
        raise NotImplementedError

    @abstractmethod
    def batch_upsert(
        self,
        collection_name: str,
        records: list[EmbeddingRecord],
        batch_size: int = 100,
    ) -> int:
        """Insert or update a large set of vectors in bounded-size chunks.

        Args:
            collection_name: The target collection.
            records: The vectors to upsert.
            batch_size: Maximum number of records sent per underlying
                provider call.

        Returns:
            The total number of records successfully upserted.

        Raises:
            CollectionNotFoundError: If the collection does not exist.
            InsertFailedError: If any chunk fails to upsert.
        """
        raise NotImplementedError

    @abstractmethod
    def delete_embeddings(self, collection_name: str, ids: list[str]) -> int:
        """Delete specific vectors by their record IDs.

        Args:
            collection_name: The target collection.
            ids: The vector record IDs to delete.

        Returns:
            The number of records deleted.

        Raises:
            CollectionNotFoundError: If the collection does not exist.
            DeleteFailedError: If deletion fails.
        """
        raise NotImplementedError

    @abstractmethod
    def delete_document(self, collection_name: str, document_id: str) -> int:
        """Delete every vector belonging to a single source document.

        Used when a file is removed or changed during re-indexing, to
        clear out its previous chunks before inserting fresh ones.

        Args:
            collection_name: The target collection.
            document_id: ID of the source document whose vectors should
                be removed.

        Returns:
            The number of records deleted.

        Raises:
            CollectionNotFoundError: If the collection does not exist.
            DeleteFailedError: If deletion fails.
        """
        raise NotImplementedError

    @abstractmethod
    def delete_repository(self, collection_name: str, repository_id: str) -> int:
        """Delete every vector belonging to a repository.

        Used when a repository is disconnected/removed from the platform.

        Args:
            collection_name: The target collection.
            repository_id: ID of the repository whose vectors should be
                removed.

        Returns:
            The number of records deleted.

        Raises:
            CollectionNotFoundError: If the collection does not exist.
            DeleteFailedError: If deletion fails.
        """
        raise NotImplementedError

    @abstractmethod
    def similarity_search(
        self, collection_name: str, request: SearchRequest
    ) -> list[SearchResult]:
        """Search a collection for vectors similar to a query vector.

        Args:
            collection_name: The collection to search.
            request: The query vector, result limit, and any metadata
                filters to apply.

        Returns:
            Matching records, ordered from most to least similar.

        Raises:
            CollectionNotFoundError: If the collection does not exist.
            SearchFailedError: If the search fails.
        """
        raise NotImplementedError

    @abstractmethod
    def count_documents(self, collection_name: str) -> int:
        """Count the total number of vectors stored in a collection.

        Args:
            collection_name: The collection to count.

        Returns:
            The number of vectors currently stored.

        Raises:
            CollectionNotFoundError: If the collection does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> HealthResponse:
        """Check whether the underlying vector database is reachable.

        Returns:
            A health status summary. Implementations should catch their
            own connection errors and return `healthy=False` with a
            descriptive message rather than raising, so this method is
            always safe to call (e.g. from an application `/health`
            endpoint).
        """
        raise NotImplementedError