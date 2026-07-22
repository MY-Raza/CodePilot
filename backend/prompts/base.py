from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

from backend.prompts.schemas import PromptMetadata, PromptResponse
from backend.prompts.variables import (
    CITATION_INSTRUCTIONS,
    JSON_OUTPUT_INSTRUCTIONS,
    MARKDOWN_OUTPUT_INSTRUCTIONS,
    PromptVariableName,
    format_conversation_history,
    format_retrieved_chunks,
    render_template,
)


class MissingVariableError(ValueError):
    """Raised when building a prompt without one of its required variables."""


class PromptTemplate(ABC):
    """Interface every prompt in the library must implement.

    Every concrete prompt — in practice, every `StandardPromptTemplate`
    instance declared across `code_review.py`, `documentation.py`,
    `planning.py`, `debugging.py`, and `architecture.py` — satisfies this
    interface.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """The prompt's unique, stable identifier."""
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable summary of what this prompt does."""
        raise NotImplementedError

    @property
    @abstractmethod
    def version(self) -> str:
        """This prompt's version string."""
        raise NotImplementedError

    @abstractmethod
    def system_prompt(self) -> str:
        """Return this prompt's fully-composed system prompt text.

        Returns:
            The system prompt, including any shared formatting/citation
            instructions.
        """
        raise NotImplementedError

    @abstractmethod
    def build_prompt(
        self,
        variables: dict[str, Any],
        temperature: float | None = None,
        output_format: str | None = None,
    ) -> PromptResponse:
        """Render this prompt with the given variables.

        Args:
            variables: Values for this prompt's placeholders, keyed by
                variable name. Must include every name returned by
                `required_variables()`.
            temperature: Overrides this prompt's default temperature.
            output_format: Overrides this prompt's default output format
                ("markdown" or "json").

        Returns:
            The rendered system/user prompt pair, ready to send to an
            LLM provider.

        Raises:
            MissingVariableError: If a required variable is absent.
        """
        raise NotImplementedError

    @abstractmethod
    def required_variables(self) -> list[str]:
        """List the variable names that must be provided to build this prompt.

        Returns:
            Required variable names, matching `PromptVariableName` values.
        """
        raise NotImplementedError

    @abstractmethod
    def supported_models(self) -> list[str]:
        """List model identifiers this prompt is designed/tested for.

        Returns:
            Supported model identifiers. An empty list means the prompt
            has no specific model restriction.
        """
        raise NotImplementedError


class StandardPromptTemplate(PromptTemplate):
    """Data-driven `PromptTemplate` implementation shared by every prompt.

    Handles safe placeholder substitution, uniform RAG context/citation
    injection, and Markdown/JSON output instruction composition — see
    `build_prompt` — so individual prompt definitions only need to
    supply their task-specific system/user prompt text and variable
    requirements.
    """

    def __init__(
        self,
        name: str,
        description: str,
        version: str,
        category: str,
        system_prompt_text: str,
        user_prompt_template: str,
        required_variables: Sequence[str],
        supported_models: Sequence[str] = (),
        default_temperature: float = 0.3,
        default_output_format: str = "markdown",
    ) -> None:
        """Initialize a prompt definition.

        Args:
            name: Unique, stable identifier for this prompt (e.g.
                "code_review.security").
            description: Human-readable summary of what this prompt does.
            version: This prompt's version string (e.g. "1.0.0").
            category: This prompt's category (e.g. "code_review").
            system_prompt_text: The task-specific system prompt. Shared
                Markdown/citation instructions are appended automatically
                by `system_prompt()` — do not repeat them here.
            user_prompt_template: The user prompt template, using
                `{{variable_name}}` placeholders (see
                `variables.render_template`). Should NOT reference
                `context`/`retrieved_chunks`/`conversation_history` —
                those are appended automatically by `build_prompt` when
                provided, uniformly across every prompt.
            required_variables: Names of variables that must be present
                to build this prompt. Should not include
                `context`/`retrieved_chunks`/`conversation_history`,
                which are always optional.
            supported_models: Model identifiers this prompt is
                designed/tested for. Empty means no restriction.
            default_temperature: Temperature used unless a caller
                overrides it in `build_prompt`.
            default_output_format: Output format used unless a caller
                overrides it in `build_prompt`.
        """
        self._name = name
        self._description = description
        self._version = version
        self._category = category
        self._system_prompt_text = system_prompt_text
        self._user_prompt_template = user_prompt_template
        self._required_variables = tuple(required_variables)
        self._supported_models = tuple(supported_models)
        self._default_temperature = default_temperature
        self._default_output_format = default_output_format

    @property
    def name(self) -> str:
        """This prompt's unique, stable identifier."""
        return self._name

    @property
    def description(self) -> str:
        """Human-readable summary of what this prompt does."""
        return self._description

    @property
    def version(self) -> str:
        """This prompt's version string."""
        return self._version

    @property
    def category(self) -> str:
        """This prompt's category (e.g. "code_review")."""
        return self._category

    def system_prompt(self) -> str:
        """Return the task-specific system prompt plus shared formatting instructions."""
        return (
            f"{self._system_prompt_text}\n\n"
            f"{MARKDOWN_OUTPUT_INSTRUCTIONS}\n\n"
            f"{CITATION_INSTRUCTIONS}"
        )

    def required_variables(self) -> list[str]:
        """List the variable names that must be provided to build this prompt."""
        return list(self._required_variables)

    def supported_models(self) -> list[str]:
        """List model identifiers this prompt is designed/tested for."""
        return list(self._supported_models)

    def metadata(self) -> PromptMetadata:
        """Build this prompt's introspectable metadata.

        Returns:
            The prompt's `PromptMetadata`, as surfaced by
            `PromptFactory.list_prompts()`.
        """
        return PromptMetadata(
            name=self._name,
            description=self._description,
            category=self._category,
            version=self._version,
            required_variables=self.required_variables(),
            supported_models=self.supported_models(),
            default_temperature=self._default_temperature,
            default_output_format=self._default_output_format,
        )

    def build_prompt(
        self,
        variables: dict[str, Any],
        temperature: float | None = None,
        output_format: str | None = None,
    ) -> PromptResponse:
        """Render this prompt, injecting RAG context/history uniformly.

        Args:
            variables: Values for this prompt's placeholders, keyed by
                variable name. Every key except `context`,
                `retrieved_chunks`, and `conversation_history` is
                available for `{{name}}` substitution in the template —
                not only the names returned by `required_variables()` —
                so optional placeholders work too. Must include every
                name returned by `required_variables()`. May also
                include `context` and/or `retrieved_chunks` (RAG
                context — a pre-formatted string or list of chunk
                dicts, see `variables.format_retrieved_chunks`) and/or
                `conversation_history`, all optional and handled the
                same way regardless of which concrete prompt this is.
            temperature: Overrides this prompt's default temperature.
            output_format: Overrides this prompt's default output
                format ("markdown" or "json").

        Returns:
            The rendered system/user prompt pair.

        Raises:
            MissingVariableError: If a required variable is absent or
                empty.
        """
        missing = [name for name in self._required_variables if not variables.get(name)]
        if missing:
            raise MissingVariableError(
                f"Prompt '{self._name}' (v{self._version}) is missing "
                f"required variables: {', '.join(missing)}."
            )

        reserved_keys = {
            PromptVariableName.CONTEXT.value,
            PromptVariableName.RETRIEVED_CHUNKS.value,
            PromptVariableName.CONVERSATION_HISTORY.value,
        }
        # Every provided variable except the three reserved/cross-cutting
        # ones is available for substitution — not just the required
        # ones — so prompts can reference optional placeholders (e.g. an
        # optional `file_path` alongside required `code`/`language`)
        # without every optional variable needing to be declared required.
        core_variables = {
            key: value for key, value in variables.items() if key not in reserved_keys
        }
        user_prompt = render_template(self._user_prompt_template, core_variables)
        variables_used = list(core_variables.keys())

        extra_sections: list[str] = []
        retrieved_chunks = variables.get(PromptVariableName.RETRIEVED_CHUNKS.value)
        context_value = variables.get(PromptVariableName.CONTEXT.value)
        conversation_history = variables.get(PromptVariableName.CONVERSATION_HISTORY.value)

        if retrieved_chunks:
            extra_sections.append(format_retrieved_chunks(retrieved_chunks))
            variables_used.append(PromptVariableName.RETRIEVED_CHUNKS.value)
        elif context_value:
            extra_sections.append(f"## Additional Context\n\n{context_value}")
            variables_used.append(PromptVariableName.CONTEXT.value)

        if conversation_history:
            extra_sections.append(format_conversation_history(conversation_history))
            variables_used.append(PromptVariableName.CONVERSATION_HISTORY.value)

        if extra_sections:
            user_prompt = f"{user_prompt}\n\n" + "\n\n".join(extra_sections)

        resolved_temperature = (
            temperature if temperature is not None else self._default_temperature
        )
        resolved_output_format = output_format or self._default_output_format

        system_prompt_text = self.system_prompt()
        if resolved_output_format == "json":
            system_prompt_text = f"{system_prompt_text}\n\n{JSON_OUTPUT_INSTRUCTIONS}"

        return PromptResponse(
            prompt_name=self._name,
            version=self._version,
            system_prompt=system_prompt_text,
            user_prompt=user_prompt,
            variables_used=variables_used,
            temperature=resolved_temperature,
            output_format=resolved_output_format,
        )