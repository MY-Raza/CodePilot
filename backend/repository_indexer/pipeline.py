import logging
from collections.abc import Callable, Iterator
from datetime import datetime, timezone
from pathlib import Path

from backend.repository_indexer.exceptions import RepositoryIndexerError
from backend.repository_indexer.file_filters import DEFAULT_MAX_FILE_SIZE_BYTES
from backend.repository_indexer.loader import RepositoryLoader
from backend.repository_indexer.metadata import extract_metadata
from backend.repository_indexer.schemas import (
    Chunk,
    FileMetadata,
    PipelineResult,
    RepositoryIndex,
)
from backend.repository_indexer.splitter import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    split_content,
)

logger = logging.getLogger(__name__)

# Called with (files_processed_so_far, chunks_produced_so_far) after each
# file completes. Optional — pipeline runs identically without one.
ProgressCallback = Callable[[int, int], None]


class RepositoryIndexingPipeline:
    """Orchestrates the full scan -> filter -> metadata -> split flow.

    Exposes both a streaming interface (`run`, a generator yielding
    `Chunk` objects as they're produced — memory-efficient and suitable
    for batch/incremental consumption) and a convenience method
    (`run_to_completion`) that collects the full `PipelineResult` for
    callers that want everything at once.
    """

    def __init__(
        self,
        loader: RepositoryLoader | None = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
    ) -> None:
        """Initialize the pipeline.

        Args:
            loader: A `RepositoryLoader` instance. A default one is
                constructed if omitted, allowing dependency injection for
                testing (e.g. a loader with a custom size limit).
            chunk_size: Target maximum chunk size, in characters.
            chunk_overlap: Overlap between consecutive chunks, in characters.
            max_file_size_bytes: Used only when `loader` is omitted, to
                construct the default loader.
        """
        self._loader = loader or RepositoryLoader(
            max_file_size_bytes=max_file_size_bytes
        )
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def run(
        self,
        repository_root: Path,
        repository_name: str,
        repository_branch: str | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> Iterator[Chunk]:
        """Run the indexing pipeline, streaming chunks as they're produced.

        A single file failing to process (e.g. an encoding edge case that
        slips past the loader) logs a warning and is skipped rather than
        aborting the entire run — repository indexing should be resilient
        to a handful of problematic files.

        Args:
            repository_root: The repository's root directory on local disk.
            repository_name: Name of the repository being indexed.
            repository_branch: Branch being indexed, if known.
            on_progress: Optional callback invoked after each file is
                processed, with `(files_processed, chunks_produced)`.

        Yields:
            `Chunk` objects in the order their source files were
            encountered, and in order within each file.

        Raises:
            RepositoryIndexerError: Propagated from the loader if the
                repository root itself is invalid (a fatal, run-level
                failure, distinct from a single bad file).
        """
        logger.info(
            "Pipeline started for repository '%s' at %s",
            repository_name,
            repository_root,
        )

        files_processed = 0
        chunks_produced = 0

        try:
            for repository_file in self._loader.scan_repository(repository_root):
                try:
                    metadata = extract_metadata(
                        repository_file, repository_name, repository_branch
                    )
                    chunks = self._split_file(repository_file.content, metadata)
                except Exception as exc:  # noqa: BLE001 - isolate per-file failures
                    logger.warning(
                        "Skipping file due to processing error: %s (%s)",
                        repository_file.relative_path,
                        exc,
                    )
                    continue

                files_processed += 1
                chunks_produced += len(chunks)

                for chunk in chunks:
                    yield chunk

                if on_progress is not None:
                    on_progress(files_processed, chunks_produced)

        except RepositoryIndexerError:
            logger.error("Pipeline failed for repository '%s'", repository_name)
            raise

        logger.info(
            "Pipeline completed for repository '%s': %s files processed, "
            "%s chunks generated",
            repository_name,
            files_processed,
            chunks_produced,
        )

    def _split_file(self, content: str, metadata: FileMetadata) -> list[Chunk]:
        """Split a single file's content and wrap the results as `Chunk` objects.

        Args:
            content: The file's decoded text content.
            metadata: The file's previously extracted metadata.

        Returns:
            The ordered list of `Chunk` objects for this file. Empty for
            files with no meaningful content after splitting.
        """
        text_chunks = split_content(
            content,
            language=metadata.language,
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
        )

        chunks: list[Chunk] = []
        cursor_line = 1
        for index, text_chunk in enumerate(text_chunks):
            chunk_line_count = text_chunk.count("\n") + 1
            chunks.append(
                Chunk(
                    repository_name=metadata.repository_name,
                    relative_path=metadata.relative_path,
                    language=metadata.language,
                    chunk_index=index,
                    content=text_chunk,
                    start_line=cursor_line,
                    end_line=cursor_line + chunk_line_count - 1,
                    metadata=metadata,
                )
            )
            # Approximate next start line; overlap means this is a
            # best-effort estimate rather than an exact source mapping.
            cursor_line += max(chunk_line_count - 1, 1)

        return chunks

    def run_to_completion(
        self,
        repository_root: Path,
        repository_name: str,
        repository_branch: str | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> PipelineResult:
        """Run the pipeline and collect the full result in memory.

        Prefer `run()` directly for large repositories where streaming
        consumption (e.g. batching chunks into a vector store as they
        arrive) is preferable to holding every chunk in memory at once.

        Args:
            repository_root: The repository's root directory on local disk.
            repository_name: Name of the repository being indexed.
            repository_branch: Branch being indexed, if known.
            on_progress: Optional progress callback; see `run()`.

        Returns:
            The complete `PipelineResult`, including summary statistics
            and every generated chunk.
        """
        chunks: list[Chunk] = []
        languages: set[str] = set()
        errors: list[str] = []

        try:
            for chunk in self.run(
                repository_root, repository_name, repository_branch, on_progress
            ):
                chunks.append(chunk)
                languages.add(chunk.language)
        except RepositoryIndexerError as exc:
            errors.append(str(exc))

        # NOTE: this counts distinct files that produced at least one
        # chunk. A file read successfully but empty after whitespace
        # stripping (see split_content) contributes zero chunks and is
        # therefore not reflected here, even though the loader did
        # process it. Acceptable for RAG purposes — an empty file has
        # nothing to retrieve — but worth knowing if you need an exact
        # "files successfully read" count elsewhere.
        indexed_relative_paths = {chunk.relative_path for chunk in chunks}

        index = RepositoryIndex(
            repository_name=repository_name,
            repository_branch=repository_branch,
            root_path=str(repository_root),
            total_files_scanned=self._loader.files_scanned,
            total_files_indexed=len(indexed_relative_paths),
            total_files_ignored=self._loader.files_ignored,
            languages=sorted(languages),
            indexed_at=datetime.now(timezone.utc),
        )

        return PipelineResult(index=index, chunks=chunks, errors=errors)