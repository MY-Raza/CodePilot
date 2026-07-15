class RepositoryIndexerError(Exception):
    """Base exception for all repository indexing failures."""


class RepositoryNotFoundError(RepositoryIndexerError):
    """Raised when the target repository path does not exist locally."""


class InvalidRepositoryError(RepositoryIndexerError):
    """Raised when a path exists but is not a valid, safe repository root.

    Covers cases such as the path not being a directory, or resolving
    (after symlink expansion) outside of an expected root.
    """


class UnsupportedLanguageError(RepositoryIndexerError):
    """Raised when a file's language cannot be determined or handled."""


class FileTooLargeError(RepositoryIndexerError):
    """Raised when a file exceeds the configured maximum size limit."""


class BinaryFileDetectedError(RepositoryIndexerError):
    """Raised when a file is detected as binary and cannot be indexed as text."""


class EncodingError(RepositoryIndexerError):
    """Raised when a file's text content cannot be safely decoded."""