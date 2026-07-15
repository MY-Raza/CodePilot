import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RepositoryFile(BaseModel):
    """A single file read from a repository, prior to language detection.

    Attributes:
        relative_path: Path relative to the repository root, using
            forward slashes regardless of host OS.
        absolute_path: Fully resolved absolute path on local disk.
        content: The file's decoded text content.
        size_bytes: File size, in bytes.
        last_modified: Timestamp the file was last modified on disk.
    """

    model_config = ConfigDict(frozen=True)

    relative_path: str
    absolute_path: str
    content: str
    size_bytes: int
    last_modified: datetime


class FileMetadata(BaseModel):
    """Extracted metadata describing a single indexed file.

    Attributes:
        repository_name: Name of the repository this file belongs to.
        repository_branch: Branch the repository was indexed from, if known.
        relative_path: Path relative to the repository root.
        absolute_path: Fully resolved absolute path on local disk.
        language: Detected programming/markup language identifier.
        extension: File extension, including the leading dot (empty string
            for extensionless special files like "Dockerfile").
        lines_of_code: Total line count of the file's content.
        function_count: Best-effort count of function/method definitions.
        class_count: Best-effort count of class/type definitions.
        import_count: Best-effort count of import/include statements.
        file_size_bytes: File size, in bytes.
        checksum_sha256: SHA-256 hex digest of the file's content.
        last_modified: Timestamp the file was last modified on disk.
    """

    model_config = ConfigDict(frozen=True)

    repository_name: str
    repository_branch: str | None = None
    relative_path: str
    absolute_path: str
    language: str
    extension: str
    lines_of_code: int
    function_count: int
    class_count: int
    import_count: int
    file_size_bytes: int
    checksum_sha256: str
    last_modified: datetime


class Chunk(BaseModel):
    """A single structured chunk produced from a source file.

    Deliberately contains no embedding vector or vector-store identifier
    — this module stops at producing chunk text plus metadata; embedding
    generation and storage belong to the RAG engine module.

    Attributes:
        id: Unique identifier for this chunk.
        repository_name: Name of the repository this chunk belongs to.
        relative_path: Path of the source file, relative to repository root.
        language: Detected language of the source file.
        chunk_index: Zero-based position of this chunk within its file.
        content: The chunk's text content.
        start_line: Best-effort starting line number within the source
            file, if determinable.
        end_line: Best-effort ending line number within the source file,
            if determinable.
        metadata: The full file-level metadata this chunk was derived from.
    """

    model_config = ConfigDict(frozen=True)

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    repository_name: str
    relative_path: str
    language: str
    chunk_index: int
    content: str
    start_line: int | None = None
    end_line: int | None = None
    metadata: FileMetadata


class RepositoryIndex(BaseModel):
    """Summary of a repository's scanned/indexed file set.

    Attributes:
        repository_name: Name of the indexed repository.
        repository_branch: Branch the repository was indexed from, if known.
        root_path: Absolute local path to the repository root.
        total_files_scanned: Count of files encountered during traversal.
        total_files_indexed: Count of files that passed filtering and were
            successfully processed.
        total_files_ignored: Count of files skipped by filtering rules.
        languages: Distinct languages detected across indexed files.
        indexed_at: Timestamp the indexing run completed.
    """

    repository_name: str
    repository_branch: str | None = None
    root_path: str
    total_files_scanned: int
    total_files_indexed: int
    total_files_ignored: int
    languages: list[str]
    indexed_at: datetime


class PipelineResult(BaseModel):
    """Final output of a full repository indexing pipeline run.

    Attributes:
        index: Summary statistics for the indexing run.
        chunks: All structured chunks produced across all indexed files.
        errors: Human-readable descriptions of any non-fatal errors
            encountered for individual files (e.g. a single unreadable
            file does not necessarily abort the whole run).
    """

    index: RepositoryIndex
    chunks: list[Chunk]
    errors: list[str] = Field(default_factory=list)