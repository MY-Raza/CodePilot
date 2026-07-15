from langchain_text_splitters import Language as LCLanguage
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.repository_indexer.language_detector import Language

DEFAULT_CHUNK_SIZE: int = 1000
DEFAULT_CHUNK_OVERLAP: int = 200

# Maps our normalized language identifiers to LangChain's `Language` enum,
# which provides language-specific separator hierarchies (e.g. splitting
# Python on class/def boundaries before falling back to blank lines).
# Only languages LangChain has dedicated separator support for appear
# here; everything else uses the generic fallback splitter.
_LANGCHAIN_LANGUAGE_MAP: dict[str, LCLanguage] = {
    Language.PYTHON: LCLanguage.PYTHON,
    Language.JAVASCRIPT: LCLanguage.JS,
    Language.TYPESCRIPT: LCLanguage.TS,
    Language.JAVA: LCLanguage.JAVA,
    Language.CPP: LCLanguage.CPP,
    Language.C: LCLanguage.CPP,  # LangChain has no dedicated C splitter; C++ separators are a close superset.
    Language.GO: LCLanguage.GO,
    Language.RUST: LCLanguage.RUST,
    Language.CSHARP: LCLanguage.CSHARP,
    Language.PHP: LCLanguage.PHP,
    Language.KOTLIN: LCLanguage.KOTLIN,
    Language.SWIFT: LCLanguage.SWIFT,
    Language.HTML: LCLanguage.HTML,
    Language.MARKDOWN: LCLanguage.MARKDOWN,
}


def _build_splitter(
    language: str, chunk_size: int, chunk_overlap: int
) -> RecursiveCharacterTextSplitter:
    """Construct the appropriate splitter for a given language.

    Args:
        language: A normalized language identifier from `language_detector`.
        chunk_size: Target maximum chunk size, in characters.
        chunk_overlap: Overlap between consecutive chunks, in characters,
            used to preserve context across a chunk boundary.

    Returns:
        A configured `RecursiveCharacterTextSplitter`. Uses
        language-specific separators when available (preserving function/
        class boundaries where possible), otherwise a generic
        paragraph/line/word separator hierarchy.
    """
    lc_language = _LANGCHAIN_LANGUAGE_MAP.get(language)
    if lc_language is not None:
        return RecursiveCharacterTextSplitter.from_language(
            language=lc_language,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    # Generic fallback for languages LangChain has no dedicated separator
    # set for (JSON, YAML, XML, CSS, SQL, Shell, plaintext, requirements.txt,
    # package.json, README-without-markdown-extension, etc.). Prioritizes
    # splitting on blank lines and newlines before falling back to words,
    # which keeps most logical blocks (e.g. YAML top-level keys) intact.
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )


def split_content(
    content: str,
    language: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """Split a file's text content into context-preserving chunks.

    Args:
        content: The file's full decoded text content.
        language: A normalized language identifier from `language_detector`.
        chunk_size: Target maximum chunk size, in characters. Configurable
            per call to allow different chunk sizes for code vs. docs.
        chunk_overlap: Overlap between consecutive chunks, in characters.

    Returns:
        An ordered list of text chunks. Returns an empty list for empty
        input rather than a list containing one empty string.
    """
    if not content.strip():
        return []

    splitter = _build_splitter(language, chunk_size, chunk_overlap)
    return splitter.split_text(content)