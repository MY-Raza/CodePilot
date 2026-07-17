class VectorStoreError(Exception):
    """Base exception for all vector database failures."""


class CollectionNotFoundError(VectorStoreError):
    """Raised when an operation references a collection that does not exist."""


class VectorDatabaseUnavailableError(VectorStoreError):
    """Raised when the configured vector database cannot be reached at all."""


class InsertFailedError(VectorStoreError):
    """Raised when an upsert/insert operation fails."""


class DeleteFailedError(VectorStoreError):
    """Raised when a delete operation fails."""


class SearchFailedError(VectorStoreError):
    """Raised when a similarity search operation fails."""


class ConnectionFailedError(VectorStoreError):
    """Raised when establishing a connection to the vector database fails."""