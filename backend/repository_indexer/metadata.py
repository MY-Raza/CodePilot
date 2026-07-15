import hashlib
import re
from pathlib import Path

from backend.repository_indexer.language_detector import Language, detect_language
from backend.repository_indexer.schemas import FileMetadata, RepositoryFile

# -----------------------------------------------------------------------
# Heuristic Regex Patterns
# -----------------------------------------------------------------------
# Deliberately conservative (favor false negatives over false positives)
# since these counts are metadata signals, not exact figures.
_FUNCTION_PATTERNS: dict[str, re.Pattern[str]] = {
    Language.PYTHON: re.compile(r"^\s*(async\s+def|def)\s+\w+\s*\(", re.MULTILINE),
    Language.JAVASCRIPT: re.compile(
        r"\bfunction\s*\w*\s*\(|\b\w+\s*=\s*(async\s*)?\([^)]*\)\s*=>", re.MULTILINE
    ),
    Language.TYPESCRIPT: re.compile(
        r"\bfunction\s*\w*\s*\(|\b\w+\s*=\s*(async\s*)?\([^)]*\)\s*=>", re.MULTILINE
    ),
    Language.JAVA: re.compile(
        r"\b(public|private|protected|static)\s+[\w<>\[\]]+\s+\w+\s*\([^;]*\)\s*\{",
        re.MULTILINE,
    ),
    Language.GO: re.compile(r"^\s*func\s+\w*\s*\(", re.MULTILINE),
    Language.RUST: re.compile(r"^\s*(pub\s+)?fn\s+\w+\s*\(", re.MULTILINE),
    Language.CSHARP: re.compile(
        r"\b(public|private|protected|internal|static)\s+[\w<>\[\]]+\s+\w+\s*\([^;]*\)\s*\{",
        re.MULTILINE,
    ),
    Language.CPP: re.compile(r"^\s*[\w:<>\*&\s]+\s+\w+\s*\([^;{]*\)\s*\{", re.MULTILINE),
    Language.C: re.compile(r"^\s*[\w\*\s]+\s+\w+\s*\([^;{]*\)\s*\{", re.MULTILINE),
    Language.PHP: re.compile(r"^\s*function\s+\w+\s*\(", re.MULTILINE),
}

_CLASS_PATTERNS: dict[str, re.Pattern[str]] = {
    Language.PYTHON: re.compile(r"^\s*class\s+\w+", re.MULTILINE),
    Language.JAVASCRIPT: re.compile(r"^\s*class\s+\w+", re.MULTILINE),
    Language.TYPESCRIPT: re.compile(r"^\s*(export\s+)?class\s+\w+", re.MULTILINE),
    Language.JAVA: re.compile(r"^\s*(public|private)?\s*class\s+\w+", re.MULTILINE),
    Language.GO: re.compile(r"^\s*type\s+\w+\s+struct\b", re.MULTILINE),
    Language.RUST: re.compile(r"^\s*(pub\s+)?struct\s+\w+", re.MULTILINE),
    Language.CSHARP: re.compile(
        r"^\s*(public|private|internal)?\s*class\s+\w+", re.MULTILINE
    ),
    Language.CPP: re.compile(r"^\s*class\s+\w+", re.MULTILINE),
    Language.KOTLIN: re.compile(r"^\s*(data\s+)?class\s+\w+", re.MULTILINE),
    Language.SWIFT: re.compile(r"^\s*class\s+\w+", re.MULTILINE),
    Language.PHP: re.compile(r"^\s*class\s+\w+", re.MULTILINE),
}

_IMPORT_PATTERNS: dict[str, re.Pattern[str]] = {
    Language.PYTHON: re.compile(r"^\s*(import\s+\w|from\s+[\w.]+\s+import)", re.MULTILINE),
    Language.JAVASCRIPT: re.compile(
        r"^\s*(import\s+.+\s+from|const\s+.+=\s*require\()", re.MULTILINE
    ),
    Language.TYPESCRIPT: re.compile(
        r"^\s*(import\s+.+\s+from|const\s+.+=\s*require\()", re.MULTILINE
    ),
    Language.JAVA: re.compile(r"^\s*import\s+[\w.]+;", re.MULTILINE),
    Language.GO: re.compile(r'^\s*import\s+(\(|"[^"]+")', re.MULTILINE),
    Language.RUST: re.compile(r"^\s*use\s+[\w:]+", re.MULTILINE),
    Language.CSHARP: re.compile(r"^\s*using\s+[\w.]+;", re.MULTILINE),
    Language.CPP: re.compile(r'^\s*#include\s+[<"][\w./]+[>"]', re.MULTILINE),
    Language.C: re.compile(r'^\s*#include\s+[<"][\w./]+[>"]', re.MULTILINE),
    Language.PHP: re.compile(r"^\s*(require|include)(_once)?\s*\(", re.MULTILINE),
}


def _count_matches(pattern: re.Pattern[str] | None, content: str) -> int:
    """Count regex matches, tolerating an absent pattern.

    Args:
        pattern: A compiled regex, or None if no heuristic is defined for
            the file's language.
        content: The file's text content.

    Returns:
        The number of matches, or 0 if `pattern` is None.
    """
    if pattern is None:
        return 0
    return len(pattern.findall(content))


def compute_checksum(content: str) -> str:
    """Compute a SHA-256 checksum of a file's text content.

    Args:
        content: The file's decoded text content.

    Returns:
        The hex-encoded SHA-256 digest.
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def extract_metadata(
    repository_file: RepositoryFile,
    repository_name: str,
    repository_branch: str | None = None,
) -> FileMetadata:
    """Extract structural and file-system metadata for a repository file.

    Args:
        repository_file: The file to analyze, as produced by
            `RepositoryLoader`.
        repository_name: Name of the repository this file belongs to.
        repository_branch: Branch the repository was indexed from, if known.

    Returns:
        The extracted `FileMetadata`.
    """
    path = Path(repository_file.relative_path)
    language = detect_language(path)
    content = repository_file.content

    return FileMetadata(
        repository_name=repository_name,
        repository_branch=repository_branch,
        relative_path=repository_file.relative_path,
        absolute_path=repository_file.absolute_path,
        language=language,
        extension=path.suffix,
        lines_of_code=content.count("\n") + (1 if content and not content.endswith("\n") else 0),
        function_count=_count_matches(_FUNCTION_PATTERNS.get(language), content),
        class_count=_count_matches(_CLASS_PATTERNS.get(language), content),
        import_count=_count_matches(_IMPORT_PATTERNS.get(language), content),
        file_size_bytes=repository_file.size_bytes,
        checksum_sha256=compute_checksum(content),
        last_modified=repository_file.last_modified,
    )