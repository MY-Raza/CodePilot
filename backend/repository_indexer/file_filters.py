import mimetypes

# -----------------------------------------------------------------------
# Ignored Directories
# -----------------------------------------------------------------------
# Directory names skipped entirely during traversal — never descended
# into, regardless of depth.
IGNORED_DIRECTORIES: frozenset[str] = frozenset(
    {
        ".git",
        ".github",
        ".idea",
        ".vscode",
        "node_modules",
        "dist",
        "build",
        "coverage",
        ".next",
        ".nuxt",
        "target",
        "bin",
        "obj",
        "venv",
        ".venv",
        "env",
        "__pycache__",
        ".cache",
        "tmp",
        "logs",
        "vendor",
    }
)

# -----------------------------------------------------------------------
# Ignored File Extensions
# -----------------------------------------------------------------------
# Media, archive, document, and compiled-binary extensions that are never
# useful as RAG source text, even if small enough to pass size filtering.
IGNORED_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".bmp",
        ".ico",
        ".svg",
        ".mp4",
        ".avi",
        ".mov",
        ".zip",
        ".rar",
        ".7z",
        ".pdf",
        ".docx",
        ".pptx",
        ".xlsx",
        ".exe",
        ".dll",
        ".so",
        ".class",
        ".jar",
    }
)

# -----------------------------------------------------------------------
# Size Limits
# -----------------------------------------------------------------------
# Files larger than this are skipped outright rather than read into
# memory, protecting against large-file memory/DoS attacks.
DEFAULT_MAX_FILE_SIZE_BYTES: int = 2 * 1024 * 1024  # 2 MB

# Number of leading bytes sampled to make a binary/text determination
# without reading the entire file into memory.
BINARY_SNIFF_SAMPLE_SIZE: int = 8192


def is_ignored_directory(directory_name: str) -> bool:
    """Check whether a directory name should be skipped during traversal.

    Args:
        directory_name: The bare directory name (not a full path).

    Returns:
        True if this directory should never be descended into.
    """
    return directory_name in IGNORED_DIRECTORIES


def is_hidden(name: str) -> bool:
    """Check whether a file or directory name is a hidden dotfile.

    Args:
        name: The bare file or directory name (not a full path).

    Returns:
        True if the name starts with a dot (e.g. ".env"), excluding the
        special "." and ".." path segments.
    """
    return name.startswith(".") and name not in {".", ".."}


def is_ignored_extension(filename: str) -> bool:
    """Check whether a file's extension is in the ignore list.

    Args:
        filename: The bare file name (not a full path).

    Returns:
        True if the file's extension matches a known non-text/binary type.
    """
    lowered = filename.lower()
    for extension in IGNORED_EXTENSIONS:
        if lowered.endswith(extension):
            return True
    return False


def exceeds_max_size(
    size_bytes: int, max_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES
) -> bool:
    """Check whether a file's size exceeds the configured maximum.

    Args:
        size_bytes: The file's size, in bytes.
        max_size_bytes: The configured maximum allowed size, in bytes.

    Returns:
        True if the file is too large to index.
    """
    return size_bytes > max_size_bytes


def is_binary_content(sample: bytes) -> bool:
    """Heuristically determine whether a byte sample is binary content.

    Uses the classic null-byte heuristic: text files essentially never
    contain a NUL byte, while most binary formats do within their first
    few kilobytes.

    Args:
        sample: A leading sample of the file's raw bytes (see
            `BINARY_SNIFF_SAMPLE_SIZE`).

    Returns:
        True if the sample appears to be binary rather than text.
    """
    return b"\x00" in sample


def guess_is_binary_by_mimetype(filename: str) -> bool:
    """Fall back to mimetypes guessing when byte-sniffing is inconclusive.

    Args:
        filename: The bare file name (not a full path).

    Returns:
        True if the guessed MIME type is confidently non-text.
    """
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type is None:
        return False
    return not (
        mime_type.startswith("text/")
        or mime_type
        in {
            "application/json",
            "application/xml",
            "application/x-yaml",
            "application/javascript",
            "application/x-sh",
        }
    )


def should_skip_file(
    filename: str,
    size_bytes: int,
    sample: bytes,
    max_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
    include_hidden: bool = False,
) -> tuple[bool, str | None]:
    """Apply all file-level filtering rules in one pass.

    Args:
        filename: The bare file name (not a full path).
        size_bytes: The file's size, in bytes.
        sample: A leading byte sample of the file's content, used for
            binary detection.
        max_size_bytes: The configured maximum allowed file size, in bytes.
        include_hidden: Whether hidden dotfiles should be indexed.

    Returns:
        A tuple of `(should_skip, reason)`. `reason` is None when
        `should_skip` is False.
    """
    if not include_hidden and is_hidden(filename):
        return True, "hidden file"
    if is_ignored_extension(filename):
        return True, "ignored extension"
    if exceeds_max_size(size_bytes, max_size_bytes):
        return True, "exceeds maximum file size"
    if is_binary_content(sample) or guess_is_binary_by_mimetype(filename):
        return True, "binary content"
    return False, None