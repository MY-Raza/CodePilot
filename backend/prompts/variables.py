import re
from enum import Enum
from typing import Any


class PromptVariableName(str, Enum):
    """Canonical names for every placeholder used across the prompt library.

    Referenced by name (`.value`) inside prompt templates as
    `{{variable_name}}`, and by `StandardPromptTemplate` to know which
    variables a given prompt requires.
    """

    # Repository / project identity
    REPOSITORY_NAME = "repository_name"
    PROJECT_NAME = "project_name"
    BRANCH = "branch"

    # Source content
    CODE = "code"
    LANGUAGE = "language"
    FILE_PATH = "file_path"
    FUNCTION_NAME = "function_name"
    CLASS_NAME = "class_name"

    # System design content
    ARCHITECTURE = "architecture"
    REQUIREMENTS = "requirements"
    API_DEFINITION = "api_definition"
    DATABASE_SCHEMA = "database_schema"
    FOLDER_STRUCTURE = "folder_structure"
    DEPENDENCIES = "dependencies"
    TECH_STACK = "tech_stack"
    ENDPOINT = "endpoint"

    # Debugging content
    ISSUE_DESCRIPTION = "issue_description"
    STACK_TRACE = "stack_trace"
    ERROR_MESSAGE = "error_message"
    PERFORMANCE_METRICS = "performance_metrics"
    PATCH_TARGET = "patch_target"

    # Documentation content
    DOCUMENTATION = "documentation"

    # Planning content
    TICKET_TYPE = "ticket_type"
    SPRINT_GOAL = "sprint_goal"
    TEST_FRAMEWORK = "test_framework"

    # Cross-cutting / RAG (handled centrally by
    # StandardPromptTemplate.build_prompt — see base.py — so these are
    # rarely referenced directly inside an individual template string)
    CONTEXT = "context"
    RETRIEVED_CHUNKS = "retrieved_chunks"
    CONVERSATION_HISTORY = "conversation_history"


# -----------------------------------------------------------------------
# Shared, reusable prompt components
# -----------------------------------------------------------------------
# Appended uniformly by StandardPromptTemplate rather than repeated in
# every individual prompt's system prompt text.
MARKDOWN_OUTPUT_INSTRUCTIONS = (
    "Format your entire response in clean, well-structured Markdown. "
    "Use headings (##, ###) to separate sections, bullet or numbered "
    "lists for enumerable items, and fenced code blocks with language "
    "tags for any code you include. Use tables where a tabular "
    "comparison is clearer than prose."
)

CITATION_INSTRUCTIONS = (
    "When you reference specific code, cite its source using the file "
    "path and line numbers provided in the retrieved context (e.g. "
    "`auth/login.py:12-18`). Do not fabricate file paths, line numbers, "
    "or code that was not provided to you."
)

JSON_OUTPUT_INSTRUCTIONS = (
    "Return ONLY a single valid JSON object with no surrounding prose, "
    "Markdown code fences, or commentary."
)


# -----------------------------------------------------------------------
# Safe template rendering
# -----------------------------------------------------------------------
_PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def render_template(template: str, variables: dict[str, Any]) -> str:
    """Substitute `{{variable_name}}` placeholders in a template string.

    Only exact `{{name}}` matches for names present in `variables` are
    replaced; every other character in `template` — including any stray
    single or double braces from injected source code — is left exactly
    as-is. Unrecognized placeholders (a name not present in `variables`)
    are also left untouched rather than raising, so partially-filled
    templates degrade visibly instead of crashing.

    Args:
        template: The template string, containing zero or more
            `{{variable_name}}` placeholders.
        variables: A mapping of variable name to value. Values are
            converted with `str()` before substitution.

    Returns:
        The rendered string.
    """

    def _substitute(match: re.Match[str]) -> str:
        key = match.group(1)
        if key in variables:
            return str(variables[key])
        return match.group(0)

    return _PLACEHOLDER_PATTERN.sub(_substitute, template)


def format_retrieved_chunks(chunks: "str | list[dict[str, Any]]") -> str:
    """Format RAG-retrieved context into a citation-friendly Markdown section.

    Deliberately decoupled from `backend.retrieval` — this module never
    imports it — so it accepts either a pre-formatted string (e.g. the
    `context` field of a `retrieval.schemas.ContextResponse`, which
    already includes citation headers and fenced code blocks) or a list
    of plain chunk-like dicts for callers that want to pass raw data.

    Args:
        chunks: The RAG context to format. If a string, used as-is
            (assumed already formatted). If a list, each item is
            expected to have at least a `text` key, with optional
            `file_path`/`repository_name`/`language` keys used to build
            a citation header per chunk.

    Returns:
        A Markdown section titled "## Retrieved Code Context".
    """
    if isinstance(chunks, str):
        body = chunks
    else:
        blocks: list[str] = []
        for chunk in chunks:
            source = chunk.get("file_path") or chunk.get("source") or "unknown source"
            repository = chunk.get("repository_name")
            header = f"[Source: {repository} — {source}]" if repository else f"[Source: {source}]"
            text = chunk.get("text", "")
            language = chunk.get("language") or ""
            blocks.append(f"{header}\n```{language}\n{text}\n```")
        body = "\n\n".join(blocks)
    return f"## Retrieved Code Context\n\n{body}"


def format_conversation_history(history: "str | list[dict[str, str]]") -> str:
    """Format prior conversation turns into a Markdown section.

    Args:
        history: The conversation history to format. If a string, used
            as-is. If a list, each item is expected to have `role` and
            `content` keys.

    Returns:
        A Markdown section titled "## Conversation History".
    """
    if isinstance(history, str):
        body = history
    else:
        lines = [f"**{turn.get('role', 'user').capitalize()}:** {turn.get('content', '')}" for turn in history]
        body = "\n\n".join(lines)
    return f"## Conversation History\n\n{body}"