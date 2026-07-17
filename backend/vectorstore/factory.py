import os
from collections.abc import Callable

from backend.core.config import get_settings
from backend.vectorstore.base import VectorStoreBase
from backend.vectorstore.chroma import ChromaVectorStore
from backend.vectorstore.exceptions import VectorDatabaseUnavailableError
from backend.vectorstore.qdrant import QdrantVectorStore
from backend.vectorstore.schemas import DistanceMetric

# Configuration, read from environment with sensible defaults. Consider
# formalizing these into backend.core.settings if other modules end up
# needing them too — QDRANT_URL/QDRANT_API_KEY already live there and
# are read from Settings below rather than duplicated here.
DEFAULT_COLLECTION_NAME: str = os.getenv("VECTOR_STORE_COLLECTION_NAME", "code_chunks")
DEFAULT_DISTANCE_METRIC: DistanceMetric = DistanceMetric(
    os.getenv("VECTOR_STORE_DISTANCE_METRIC", DistanceMetric.COSINE.value)
)
DEFAULT_TOP_K: int = int(os.getenv("VECTOR_STORE_TOP_K", "10"))
DEFAULT_CHROMA_PERSIST_DIRECTORY: str = os.getenv(
    "CHROMA_PERSIST_DIRECTORY", "/data/chroma"
)

ProviderBuilder = Callable[[], VectorStoreBase]


class VectorStoreFactory:
    """Selects, constructs, and caches the active `VectorStoreBase` provider.

    The resolved provider is cached as a process-wide singleton after
    first use, since both ChromaDB and Qdrant clients hold persistent
    connections/handles that are expensive to reconstruct per request.
    """

    _instance: VectorStoreBase | None = None
    _custom_providers: dict[str, ProviderBuilder] = {}

    @classmethod
    def register_provider(cls, name: str, builder: ProviderBuilder) -> None:
        """Register a builder for a provider not built into this module.

        Args:
            name: The provider identifier to match against
                `VECTOR_DB_PROVIDER` (case-insensitive).
            builder: A zero-argument callable returning a
                `VectorStoreBase` implementation.
        """
        cls._custom_providers[name.strip().lower()] = builder

    @classmethod
    def get_store(cls) -> VectorStoreBase:
        """Return the active vector store, constructing it on first use.

        Returns:
            The process-wide `VectorStoreBase` singleton.

        Raises:
            VectorDatabaseUnavailableError: If the resolved provider name
                has no registered builder, or if required configuration
                (e.g. `QDRANT_URL` when using Qdrant) is missing.
        """
        if cls._instance is not None:
            return cls._instance

        provider_name = cls._resolve_provider_name()
        builder = cls._custom_providers.get(provider_name) or cls._builtin_builders().get(
            provider_name
        )
        if builder is None:
            raise VectorDatabaseUnavailableError(
                f"No vector store provider registered for '{provider_name}'. "
                f"Set VECTOR_DB_PROVIDER to one of: "
                f"{', '.join(sorted({*cls._builtin_builders(), *cls._custom_providers}))}."
            )

        cls._instance = builder()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Clear the cached singleton instance.

        Primarily useful for tests, or for explicitly reconnecting after
        a configuration change without restarting the process.
        """
        cls._instance = None

    @staticmethod
    def _resolve_provider_name() -> str:
        """Determine which provider to use from configuration.

        An explicit `VECTOR_DB_PROVIDER` environment variable always
        wins. Otherwise, the deployment environment decides: production-
        like environments default to Qdrant, everything else (local
        development, Docker) defaults to ChromaDB.

        Returns:
            The resolved, lowercased provider name.
        """
        explicit = os.getenv("VECTOR_DB_PROVIDER")
        if explicit:
            return explicit.strip().lower()

        settings = get_settings()
        return "qdrant" if settings.is_production else "chroma"

    @classmethod
    def _builtin_builders(cls) -> dict[str, ProviderBuilder]:
        """Return the built-in provider name -> builder mapping.

        Returns:
            A mapping covering ChromaDB (under both "chroma" and
            "chromadb") and Qdrant.
        """
        return {
            "chroma": cls._build_chroma,
            "chromadb": cls._build_chroma,
            "qdrant": cls._build_qdrant,
        }

    @staticmethod
    def _build_chroma() -> ChromaVectorStore:
        """Construct the ChromaDB provider from environment configuration.

        Returns:
            A connected `ChromaVectorStore`.
        """
        return ChromaVectorStore(persist_directory=DEFAULT_CHROMA_PERSIST_DIRECTORY)

    @staticmethod
    def _build_qdrant() -> QdrantVectorStore:
        """Construct the Qdrant provider from environment configuration.

        Returns:
            A connected `QdrantVectorStore`.

        Raises:
            VectorDatabaseUnavailableError: If `QDRANT_URL` is not set.
        """
        settings = get_settings()
        if not settings.qdrant_url:
            raise VectorDatabaseUnavailableError(
                "QDRANT_URL is not configured; cannot construct the Qdrant "
                "vector store provider."
            )
        return QdrantVectorStore(url=settings.qdrant_url, api_key=settings.qdrant_api_key)


def get_vector_store() -> VectorStoreBase:
    """FastAPI-dependency-compatible accessor for the active vector store.

    Usage:
        from fastapi import Depends
        from backend.vectorstore.factory import get_vector_store

        def some_endpoint(store: VectorStoreBase = Depends(get_vector_store)):
            ...

    Returns:
        The process-wide `VectorStoreBase` singleton.
    """
    return VectorStoreFactory.get_store()