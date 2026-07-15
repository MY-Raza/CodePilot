import logging
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path

from backend.repository_indexer.exceptions import (
    EncodingError,
    FileTooLargeError,
    InvalidRepositoryError,
    RepositoryNotFoundError,
)
from backend.repository_indexer.file_filters import (
    BINARY_SNIFF_SAMPLE_SIZE,
    DEFAULT_MAX_FILE_SIZE_BYTES,
    is_ignored_directory,
    should_skip_file,
)
from backend.repository_indexer.schemas import RepositoryFile

logger = logging.getLogger(__name__)

# Text encodings attempted in order when decoding a file's raw bytes.
# UTF-8 covers the overwhelming majority of source files; the Windows-1252
# and Latin-1 fallbacks handle older/Windows-authored text files without
# failing the whole file. Latin-1 never raises on decode (every byte
# value is valid), so it acts as a guaranteed-success final fallback.
CANDIDATE_ENCODINGS: tuple[str, ...] = ("utf-8", "utf-8-sig", "cp1252", "latin-1")


class RepositoryLoader:
    """Safely scans a repository directory and yields readable text files."""

    def __init__(
        self,
        max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
        include_hidden: bool = False,
    ) -> None:
        """Initialize the loader.

        Args:
            max_file_size_bytes: Files larger than this are skipped rather
                than read into memory.
            include_hidden: Whether hidden dotfiles should be indexed.
        """
        self._max_file_size_bytes = max_file_size_bytes
        self._include_hidden = include_hidden
        self.files_scanned = 0
        self.files_ignored = 0

    def _validate_root(self, root_path: Path) -> Path:
        """Resolve and validate the repository root path.

        Args:
            root_path: The candidate repository root.

        Returns:
            The fully resolved (symlink-expanded, absolute) root path.

        Raises:
            RepositoryNotFoundError: If the path does not exist.
            InvalidRepositoryError: If the path exists but is not a
                directory.
        """
        if not root_path.exists():
            raise RepositoryNotFoundError(
                f"Repository path does not exist: {root_path}"
            )
        resolved = root_path.resolve(strict=True)
        if not resolved.is_dir():
            raise InvalidRepositoryError(
                f"Repository path is not a directory: {root_path}"
            )
        return resolved

    def _is_safe_path(self, path: Path, repository_root: Path) -> bool:
        """Verify a (possibly symlinked) path resolves inside the repository root.

        Prevents both directory-traversal and unsafe-symlink attacks: a
        symlink inside the repository that points outside of it (e.g. to
        `/etc/passwd`) is rejected rather than followed.

        Args:
            path: The path to check, as encountered during traversal.
            repository_root: The resolved repository root boundary.

        Returns:
            True if the path's resolved, real location is within the
            repository root.
        """
        try:
            resolved = path.resolve(strict=True)
        except (OSError, RuntimeError):
            # Broken symlink or unresolvable path — treat as unsafe.
            return False
        return resolved == repository_root or repository_root in resolved.parents

    def _decode_bytes(self, raw_bytes: bytes, relative_path: str) -> str:
        """Attempt to decode raw file bytes as text.

        Args:
            raw_bytes: The file's raw byte content.
            relative_path: The file's path, for error messages only.

        Returns:
            The decoded text content.

        Raises:
            EncodingError: If no candidate encoding can decode the content
                (in practice, only reachable if all fallbacks including
                latin-1 fail, which should not occur for genuine text).
        """
        for encoding in CANDIDATE_ENCODINGS:
            try:
                return raw_bytes.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise EncodingError(
            f"Could not decode '{relative_path}' using any of the "
            f"candidate encodings: {', '.join(CANDIDATE_ENCODINGS)}."
        )

    def scan_repository(self, root_path: Path) -> Iterator[RepositoryFile]:
        """Lazily traverse a repository and yield readable text files.

        Traversal is streamed (a generator) rather than collected into a
        list up front, so memory usage stays flat regardless of
        repository size. Ignored directories are pruned during the walk
        itself, so their contents are never even stat'd.

        Args:
            root_path: The repository's root directory on local disk.

        Yields:
            A `RepositoryFile` for each file that passes safety and
            filtering checks.

        Raises:
            RepositoryNotFoundError: If `root_path` does not exist.
            InvalidRepositoryError: If `root_path` is not a directory.
        """
        repository_root = self._validate_root(root_path)
        logger.info("Repository scan started: %s", repository_root)

        self.files_scanned = 0
        self.files_ignored = 0

        for current_dir, subdirectories, filenames in _walk(repository_root):
            # Prune ignored directories in-place so os.walk never descends
            # into them — critical for skipping large trees like
            # node_modules efficiently rather than filtering after the fact.
            subdirectories[:] = [
                name for name in subdirectories if not is_ignored_directory(name)
            ]

            for filename in filenames:
                file_path = current_dir / filename
                self.files_scanned += 1

                if file_path.is_symlink() and not self._is_safe_path(
                    file_path, repository_root
                ):
                    logger.warning(
                        "Skipping unsafe symlink outside repository root: %s",
                        file_path,
                    )
                    self.files_ignored += 1
                    continue

                try:
                    file_stat = file_path.stat()
                except OSError:
                    self.files_ignored += 1
                    continue

                try:
                    with file_path.open("rb") as handle:
                        sample = handle.read(BINARY_SNIFF_SAMPLE_SIZE)
                except OSError:
                    self.files_ignored += 1
                    continue

                skip, reason = should_skip_file(
                    filename=filename,
                    size_bytes=file_stat.st_size,
                    sample=sample,
                    max_size_bytes=self._max_file_size_bytes,
                    include_hidden=self._include_hidden,
                )
                if skip:
                    logger.debug("Ignoring file %s: %s", file_path, reason)
                    self.files_ignored += 1
                    continue

                try:
                    repository_file = self.read_file(file_path, repository_root)
                except (FileTooLargeError, EncodingError, OSError) as exc:
                    logger.warning("Failed to read %s: %s", file_path, exc)
                    self.files_ignored += 1
                    continue

                yield repository_file

        logger.info(
            "Repository scan finished: %s files scanned, %s files ignored",
            self.files_scanned,
            self.files_ignored,
        )

    def read_file(self, file_path: Path, repository_root: Path) -> RepositoryFile:
        """Safely read a single file's contents.

        Args:
            file_path: Absolute path to the file to read.
            repository_root: The repository's resolved root, used to
                compute the relative path.

        Returns:
            A `RepositoryFile` containing the decoded content and metadata.

        Raises:
            FileTooLargeError: If the file exceeds the configured maximum
                size (re-checked here in case of a TOCTOU race).
            EncodingError: If the file's content cannot be decoded as text.
            OSError: If the file cannot be read from disk.
        """
        file_stat = file_path.stat()
        if file_stat.st_size > self._max_file_size_bytes:
            raise FileTooLargeError(
                f"File exceeds maximum size of {self._max_file_size_bytes} "
                f"bytes: {file_path}"
            )

        raw_bytes = file_path.read_bytes()
        relative_path = file_path.relative_to(repository_root).as_posix()
        content = self._decode_bytes(raw_bytes, relative_path)

        return RepositoryFile(
            relative_path=relative_path,
            absolute_path=str(file_path),
            content=content,
            size_bytes=file_stat.st_size,
            last_modified=datetime.fromtimestamp(file_stat.st_mtime, tz=timezone.utc),
        )


def _walk(root: Path) -> Iterator[tuple[Path, list[str], list[str]]]:
    """Thin wrapper around `os.walk` operating on and yielding `Path` objects.

    Args:
        root: The directory to walk.

    Yields:
        Tuples of `(current_directory, subdirectory_names, filenames)`,
        matching `os.walk` semantics but with the first element as a
        `Path` for convenience.
    """
    import os

    for current_dir, subdirectories, filenames in os.walk(root):
        yield Path(current_dir), subdirectories, filenames