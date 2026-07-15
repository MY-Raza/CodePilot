from pathlib import Path


class Language:
    """Normalized language identifier constants.

    Plain string constants rather than a `str` Enum so the identifiers
    can be freely extended without a migration, and so they interop
    cleanly with `backend.core.constants.SupportedLanguage` where the two
    overlap without forcing a hard dependency between modules.
    """

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    C = "c"
    GO = "go"
    RUST = "rust"
    CSHARP = "csharp"
    PHP = "php"
    KOTLIN = "kotlin"
    SWIFT = "swift"
    MARKDOWN = "markdown"
    JSON = "json"
    YAML = "yaml"
    XML = "xml"
    HTML = "html"
    CSS = "css"
    SQL = "sql"
    SHELL = "shell"
    DOCKERFILE = "dockerfile"
    REQUIREMENTS_TXT = "requirements_txt"
    PACKAGE_JSON = "package_json"
    README = "readme"
    PLAINTEXT = "plaintext"
    UNKNOWN = "unknown"


# -----------------------------------------------------------------------
# Extension -> Language Mapping
# -----------------------------------------------------------------------
EXTENSION_LANGUAGE_MAP: dict[str, str] = {
    ".py": Language.PYTHON,
    ".pyi": Language.PYTHON,
    ".js": Language.JAVASCRIPT,
    ".jsx": Language.JAVASCRIPT,
    ".mjs": Language.JAVASCRIPT,
    ".cjs": Language.JAVASCRIPT,
    ".ts": Language.TYPESCRIPT,
    ".tsx": Language.TYPESCRIPT,
    ".java": Language.JAVA,
    ".cpp": Language.CPP,
    ".cc": Language.CPP,
    ".cxx": Language.CPP,
    ".hpp": Language.CPP,
    ".hxx": Language.CPP,
    ".c": Language.C,
    ".h": Language.C,
    ".go": Language.GO,
    ".rs": Language.RUST,
    ".cs": Language.CSHARP,
    ".php": Language.PHP,
    ".kt": Language.KOTLIN,
    ".kts": Language.KOTLIN,
    ".swift": Language.SWIFT,
    ".md": Language.MARKDOWN,
    ".markdown": Language.MARKDOWN,
    ".json": Language.JSON,
    ".yaml": Language.YAML,
    ".yml": Language.YAML,
    ".xml": Language.XML,
    ".html": Language.HTML,
    ".htm": Language.HTML,
    ".css": Language.CSS,
    ".scss": Language.CSS,
    ".sql": Language.SQL,
    ".sh": Language.SHELL,
    ".bash": Language.SHELL,
    ".zsh": Language.SHELL,
}

# -----------------------------------------------------------------------
# Special Filename -> Language Mapping
# -----------------------------------------------------------------------
# Matched against the lowercased bare filename (no extension stripping),
# for extensionless or conventionally-named files.
SPECIAL_FILENAME_LANGUAGE_MAP: dict[str, str] = {
    "dockerfile": Language.DOCKERFILE,
    "makefile": Language.SHELL,
    "readme": Language.README,
    "readme.md": Language.README,
    "readme.rst": Language.README,
    "readme.txt": Language.README,
    "license": Language.PLAINTEXT,
    "license.md": Language.PLAINTEXT,
    "license.txt": Language.PLAINTEXT,
    "requirements.txt": Language.REQUIREMENTS_TXT,
    "package.json": Language.PACKAGE_JSON,
}


def detect_language(path: Path) -> str:
    """Detect a file's normalized language identifier.

    Detection order: exact special filename match first (e.g.
    "Dockerfile", "README.md"), then file extension, then a plaintext
    fallback for anything unrecognized.

    Args:
        path: The file path to classify. Only `path.name` and
            `path.suffix` are inspected — the file's content is not read.

    Returns:
        A normalized language identifier from `Language`. Falls back to
        `Language.PLAINTEXT` for unrecognized text-like files rather than
        raising, since indexing should be resilient to unknown file types.
    """
    lowered_name = path.name.lower()

    if lowered_name in SPECIAL_FILENAME_LANGUAGE_MAP:
        return SPECIAL_FILENAME_LANGUAGE_MAP[lowered_name]

    suffix = path.suffix.lower()
    if suffix in EXTENSION_LANGUAGE_MAP:
        return EXTENSION_LANGUAGE_MAP[suffix]

    return Language.PLAINTEXT


def is_supported_language(language: str) -> bool:
    """Check whether a language identifier is one this module recognizes.

    Args:
        language: A normalized language identifier.

    Returns:
        True if the identifier is a known `Language` value (including the
        `PLAINTEXT` fallback, which is always considered indexable).
    """
    known_values = {
        value
        for name, value in vars(Language).items()
        if not name.startswith("_") and isinstance(value, str)
    }
    return language in known_values