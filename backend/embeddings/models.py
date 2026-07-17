import logging
from typing import Protocol, runtime_checkable

import torch
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------
# Supported Models
# -----------------------------------------------------------------------
DEFAULT_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

SUPPORTED_MODELS: frozenset[str] = frozenset(
    {
        "BAAI/bge-large-en-v1.5",
        "BAAI/bge-base-en-v1.5",
        "nomic-ai/nomic-embed-text-v1",
        "sentence-transformers/all-MiniLM-L6-v2",
    }
)

# Models whose sentence-transformers loading requires trust_remote_code=True
# to execute their custom modeling code. Deliberately a fixed, reviewed
# allow-list — never derived from arbitrary/user-supplied model names, to
# avoid executing untrusted remote code.
_TRUST_REMOTE_CODE_MODELS: frozenset[str] = frozenset({"nomic-ai/nomic-embed-text-v1"})

# Some models are trained for asymmetric retrieval and expect different
# instruction prefixes for search queries vs. indexed documents. Models
# not listed default to no prefix (symmetric embedding).
QUERY_PREFIXES: dict[str, str] = {
    "BAAI/bge-large-en-v1.5": "Represent this sentence for searching relevant passages: ",
    "BAAI/bge-base-en-v1.5": "Represent this sentence for searching relevant passages: ",
    "nomic-ai/nomic-embed-text-v1": "search_query: ",
}

DOCUMENT_PREFIXES: dict[str, str] = {
    "nomic-ai/nomic-embed-text-v1": "search_document: ",
}


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Structural interface any embedding backend must satisfy.

    Defined as a `Protocol` rather than an abstract base class so future
    providers (OpenAI, Voyage AI, Cohere) can plug into `EmbeddingFactory`
    by simply matching this shape — no shared base class or import of
    this module is required from a new provider implementation.

    Attributes:
        model_name: Identifier of the loaded model.
        dimension: Length of vectors this model produces.
        device: Compute device the model runs on.
    """

    model_name: str
    dimension: int
    device: str

    def encode(
        self, texts: list[str], batch_size: int, normalize: bool = True
    ) -> list[list[float]]:
        """Encode a list of texts into embedding vectors.

        Args:
            texts: The texts to encode.
            batch_size: Maximum number of texts encoded in a single
                internal forward pass.
            normalize: Whether to L2-normalize output vectors (required
                for cosine-similarity search).

        Returns:
            One embedding vector per input text, in the same order.
        """
        ...


class EmbeddingModel:
    """Sentence-transformers-backed embedding provider.

    Wraps a loaded `SentenceTransformer` instance behind the
    `EmbeddingProvider` protocol. Loading happens once, in `__init__`;
    `EmbeddingFactory` is responsible for ensuring instances are reused
    rather than reconstructed on every call.
    """

    def __init__(self, model_name: str, device: str) -> None:
        """Load a sentence-transformers model.

        Args:
            model_name: A supported model identifier (see
                `SUPPORTED_MODELS`).
            device: The compute device to load the model onto ("cpu",
                "cuda", or "mps").
        """
        self.model_name = model_name
        self.device = device

        trust_remote_code = model_name in _TRUST_REMOTE_CODE_MODELS
        self._model = SentenceTransformer(
            model_name,
            device=device,
            trust_remote_code=trust_remote_code,
        )
        self.dimension: int = int(self._model.get_sentence_embedding_dimension())

        logger.info(
            "Model loaded: %s (dimension=%s, device=%s)",
            model_name,
            self.dimension,
            device,
        )

    def encode(
        self, texts: list[str], batch_size: int, normalize: bool = True
    ) -> list[list[float]]:
        """Encode texts into embedding vectors.

        Wrapped in `torch.no_grad()` since embedding generation is
        inference-only — this avoids building an unnecessary autograd
        graph, reducing memory usage significantly.

        Args:
            texts: The texts to encode.
            batch_size: Internal batch size for the forward pass.
            normalize: Whether to L2-normalize output vectors.

        Returns:
            One embedding vector (as a plain list of floats) per input
            text, in the same order.
        """
        with torch.no_grad():
            vectors = self._model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=normalize,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
        return vectors.tolist()