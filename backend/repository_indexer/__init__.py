# backend/repository_indexer/__init__.py
"""Repository indexing module.

Prepares a locally-cloned repository for RAG by scanning, filtering,
detecting languages, extracting metadata, and splitting source files
into structured chunks. Deliberately independent of any vector
database — no embeddings are generated and no ChromaDB/Qdrant calls are
made here; that is the responsibility of a separate RAG engine module,
which is expected to consume `Chunk` objects produced by this one.

Typical usage:

    from pathlib import Path
    from backend.repository_indexer import RepositoryIndexingPipeline

    pipeline = RepositoryIndexingPipeline(chunk_size=1000, chunk_overlap=200)
    result = pipeline.run_to_completion(
        repository_root=Path("/data/repositories/<repo-id>"),
        repository_name="octocat/hello-world",
        repository_branch="main",
    )
    # result.chunks -> list[Chunk], ready to hand off to an embedding step
    # result.index  -> RepositoryIndex summary stats
"""

from backend.repository_indexer.exceptions import (
    BinaryFileDetectedError,
    EncodingError,
    FileTooLargeError,
    InvalidRepositoryError,
    RepositoryIndexerError,
    RepositoryNotFoundError,
    UnsupportedLanguageError,
)
from backend.repository_indexer.pipeline import RepositoryIndexingPipeline
from backend.repository_indexer.schemas import (
    Chunk,
    FileMetadata,
    PipelineResult,
    RepositoryFile,
    RepositoryIndex,
)

__all__ = [
    "RepositoryIndexingPipeline",
    "RepositoryFile",
    "FileMetadata",
    "Chunk",
    "RepositoryIndex",
    "PipelineResult",
    "RepositoryIndexerError",
    "RepositoryNotFoundError",
    "InvalidRepositoryError",
    "UnsupportedLanguageError",
    "FileTooLargeError",
    "BinaryFileDetectedError",
    "EncodingError",
]