import logging
import os

import torch

from backend.embeddings.exceptions import EmbeddingModelNotFoundError
from backend.embeddings.models import DEFAULT_MODEL, SUPPORTED_MODELS, EmbeddingModel, EmbeddingProvider

logger = logging.getLogger(__name__)


def resolve_device(preferred: str | None = None) -> str:
    """Resolve the compute device to run embedding inference on.

    Args:
        preferred: An explicit device request ("cpu", "cuda", "mps"), or
            None/"auto" to auto-detect the best available device.

    Returns:
        The resolved device identifier. Auto-detection prefers CUDA, then
        Apple Silicon MPS, falling back to CPU if neither is available.
    """
    if preferred and preferred.lower() != "auto":
        return preferred.lower()
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


class EmbeddingFactory:
    """Singleton factory for loading and caching embedding model instances.

    Adding a new embedding provider (OpenAI, Voyage AI, Cohere) requires
    only a new branch inside `_load_provider` — `EmbeddingService` depends
    solely on the `EmbeddingProvider` protocol, never on this factory's
    internals or on `EmbeddingModel` directly, so no service code changes
    when a provider is added.
    """

    _instances: dict[tuple[str, str], EmbeddingProvider] = {}

    @classmethod
    def get_model(
        cls, model_name: str | None = None, device: str | None = None
    ) -> EmbeddingProvider:
        """Get a cached (or newly loaded) embedding model instance.

        Args:
            model_name: A supported model identifier. Falls back to the
                `EMBEDDING_MODEL` environment variable, then
                `DEFAULT_MODEL`, when omitted.
            device: The compute device to load the model on. Falls back
                to the `EMBEDDING_DEVICE` environment variable (or
                auto-detection) when omitted.

        Returns:
            A loaded, ready-to-use embedding provider.

        Raises:
            EmbeddingModelNotFoundError: If the resolved model name is
                not in `SUPPORTED_MODELS`.
        """
        resolved_name = model_name or os.getenv("EMBEDDING_MODEL", DEFAULT_MODEL)
        resolved_device = resolve_device(device or os.getenv("EMBEDDING_DEVICE"))

        if resolved_name not in SUPPORTED_MODELS:
            raise EmbeddingModelNotFoundError(
                f"Embedding model '{resolved_name}' is not supported. "
                f"Supported models: {', '.join(sorted(SUPPORTED_MODELS))}."
            )

        cache_key = (resolved_name, resolved_device)
        if cache_key not in cls._instances:
            logger.info(
                "Loading embedding model '%s' on device '%s'...",
                resolved_name,
                resolved_device,
            )
            cls._instances[cache_key] = cls._load_provider(resolved_name, resolved_device)

        return cls._instances[cache_key]

    @staticmethod
    def _load_provider(model_name: str, device: str) -> EmbeddingProvider:
        """Instantiate the concrete provider backing a given model name.

        All four currently supported models are served through
        sentence-transformers. Future providers would be dispatched here
        by a naming convention (e.g. an "openai:" prefix on model_name)
        without requiring any change to `EmbeddingService`.

        Args:
            model_name: A supported model identifier.
            device: The resolved compute device.

        Returns:
            A loaded embedding provider implementing `EmbeddingProvider`.
        """
        return EmbeddingModel(model_name=model_name, device=device)

    @classmethod
    def clear_cache(cls) -> None:
        """Evict all cached model instances, freeing their memory.

        Primarily useful for tests or explicit memory reclamation between
        model switches; not required during normal application operation.
        """
        cls._instances.clear()