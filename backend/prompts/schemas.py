from typing import Any, Literal

from pydantic import BaseModel, Field


class PromptVariable(BaseModel):
    """Metadata describing a single variable a prompt accepts.

    Distinct from `variables.PromptVariableName` (an enum of canonical
    placeholder name strings) — this is a richer, introspectable
    description of one such variable's role in a specific prompt, useful
    for documentation or a future UI that generates input forms from a
    prompt's declared variables.

    Attributes:
        name: The variable's canonical name (a `PromptVariableName` value).
        description: Human-readable explanation of what this variable
            should contain.
        required: Whether the prompt fails to build without this
            variable being provided.
        example: An example value, for documentation purposes.
    """

    name: str
    description: str
    required: bool = True
    example: str | None = None


class PromptVersion(BaseModel):
    """A single registered version of a prompt.

    Attributes:
        version: The semantic version string (e.g. "1.0.0").
        changelog: Human-readable summary of what changed in this
            version, if any.
    """

    version: str
    changelog: str | None = None


class PromptMetadata(BaseModel):
    """Introspectable metadata about a registered prompt template.

    Returned by `PromptFactory.list_prompts()` so callers (e.g. a future
    admin UI or the AI agents module deciding which prompt to use) can
    discover available prompts without instantiating them.

    Attributes:
        name: The prompt's unique name.
        description: Human-readable summary of what the prompt does.
        category: The prompt's category (e.g. "code_review").
        version: The prompt's version string.
        required_variables: Names of variables that must be provided to
            build this prompt.
        supported_models: Model identifiers this prompt has been
            designed/tested against. Empty means no specific restriction.
        default_temperature: The temperature used unless overridden.
        default_output_format: The output format used unless overridden.
    """

    name: str
    description: str
    category: str
    version: str
    required_variables: list[str]
    supported_models: list[str]
    default_temperature: float
    default_output_format: str


class PromptRequest(BaseModel):
    """A request to build a rendered prompt from the library.

    Attributes:
        prompt_name: The registered name of the prompt to build.
        version: A specific version to use. Falls back to the latest
            registered version for `prompt_name` when omitted.
        variables: Values for the prompt's placeholders, keyed by
            variable name.
        temperature: Overrides the prompt's default temperature.
        output_format: Overrides the prompt's default output format.
    """

    prompt_name: str
    version: str | None = None
    variables: dict[str, Any] = Field(default_factory=dict)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    output_format: Literal["markdown", "json"] | None = None


class PromptResponse(BaseModel):
    """A fully rendered, ready-to-send prompt.

    Attributes:
        prompt_name: The prompt's name.
        version: The prompt version used.
        system_prompt: The rendered system prompt text.
        user_prompt: The rendered user prompt text, including any
            appended RAG context / conversation history sections.
        variables_used: Names of variables that were actually
            incorporated into the rendered output.
        temperature: The resolved temperature to use for generation.
        output_format: The resolved output format ("markdown" or "json").
    """

    prompt_name: str
    version: str
    system_prompt: str
    user_prompt: str
    variables_used: list[str]
    temperature: float
    output_format: str