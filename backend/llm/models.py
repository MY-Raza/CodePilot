import logging
from dataclasses import dataclass
from enum import Enum

from backend.llm.schemas import ModelInfo

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Identifiers for supported and future-planned LLM providers.

    Only `GROQ` has a working implementation in this module (see
    `groq.py`); the rest are declared here so `LLMFactory` and calling
    code can reference them ahead of their implementations landing,
    without a breaking rename later.
    """

    GROQ = "groq"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE_GEMINI = "google_gemini"
    AZURE_OPENAI = "azure_openai"
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"


@dataclass(frozen=True)
class ModelDefinition:
    """Static capability/limits information about a single model.

    Attributes:
        provider: Which provider hosts this model.
        model_name: The model's identifier, as passed to the provider's
            API.
        context_window: Maximum combined prompt + completion tokens.
        max_output_tokens: Maximum tokens the model can generate in a
            single response.
        supports_streaming: Whether this model supports streaming.
        supports_json_mode: Whether this model supports structured JSON
            output mode.
        supports_tool_calling: Whether this model supports function/tool
            calling.
        supports_vision: Whether this model supports image inputs.
    """

    provider: LLMProvider
    model_name: str
    context_window: int
    max_output_tokens: int
    supports_streaming: bool = True
    supports_json_mode: bool = False
    supports_tool_calling: bool = False
    supports_vision: bool = False

    def to_model_info(self) -> ModelInfo:
        """Convert this definition into the public `ModelInfo` schema.

        Returns:
            The equivalent `ModelInfo`.
        """
        return ModelInfo(
            provider=self.provider.value,
            model_name=self.model_name,
            context_window=self.context_window,
            max_output_tokens=self.max_output_tokens,
            supports_streaming=self.supports_streaming,
            supports_json_mode=self.supports_json_mode,
            supports_tool_calling=self.supports_tool_calling,
            supports_vision=self.supports_vision,
        )


# -----------------------------------------------------------------------
# Groq-hosted models
# -----------------------------------------------------------------------
# NOTE on figures below: context window / max output token limits are
# set by the provider and can change as Groq updates its hosted model
# catalog. Verify current values against https://console.groq.com/docs/models
# before relying on these for strict production limit enforcement.
#
# NOTE on DeepSeek R1: as of this module's authoring, Groq's currently
# installed SDK model catalog type hints do not list a DeepSeek R1
# variant, suggesting it may not be actively hosted on Groq at this
# time (Groq's hosted model lineup changes over time). The definition
# below is kept so `qwen3`/`llama-3.3` selection code has a consistent
# sibling to test against and so the identifier is ready to use the
# moment it (or an equivalent) becomes available — but confirm
# availability before depending on it in production.
GROQ_LLAMA_3_3_70B = ModelDefinition(
    provider=LLMProvider.GROQ,
    model_name="llama-3.3-70b-versatile",
    context_window=128_000,
    max_output_tokens=32_768,
    supports_streaming=True,
    supports_json_mode=True,
    supports_tool_calling=True,
)

GROQ_DEEPSEEK_R1 = ModelDefinition(
    provider=LLMProvider.GROQ,
    model_name="deepseek-r1-distill-llama-70b",
    context_window=128_000,
    max_output_tokens=16_384,
    supports_streaming=True,
    supports_json_mode=False,
    supports_tool_calling=False,
)

GROQ_QWEN3_32B = ModelDefinition(
    provider=LLMProvider.GROQ,
    model_name="qwen/qwen3-32b",
    context_window=131_072,
    max_output_tokens=40_960,
    supports_streaming=True,
    supports_json_mode=True,
    supports_tool_calling=True,
)

_GROQ_MODELS: dict[str, ModelDefinition] = {
    definition.model_name: definition
    for definition in (GROQ_LLAMA_3_3_70B, GROQ_DEEPSEEK_R1, GROQ_QWEN3_32B)
}

# Registry of provider -> {model_name: ModelDefinition}. Populated with
# built-in providers at import time; extended at runtime via
# `register_model` for future providers, with no change required here.
_MODEL_REGISTRY: dict[LLMProvider, dict[str, ModelDefinition]] = {
    LLMProvider.GROQ: _GROQ_MODELS,
}


def register_model(definition: ModelDefinition) -> None:
    """Register a model definition, for a built-in or future provider.

    Args:
        definition: The model definition to register. Overwrites any
            existing definition for the same (provider, model_name) pair.
    """
    provider_models = _MODEL_REGISTRY.setdefault(definition.provider, {})
    provider_models[definition.model_name] = definition
    logger.debug(
        "Model registered: provider=%s, model=%s",
        definition.provider.value,
        definition.model_name,
    )


def get_model_definition(provider: LLMProvider, model_name: str) -> ModelDefinition | None:
    """Look up a registered model definition.

    Args:
        provider: The provider to look up the model under.
        model_name: The model's identifier.

    Returns:
        The matching `ModelDefinition`, or None if not registered.
    """
    return _MODEL_REGISTRY.get(provider, {}).get(model_name)


def list_models(provider: LLMProvider) -> list[ModelDefinition]:
    """List all registered model definitions for a provider.

    Args:
        provider: The provider to list models for.

    Returns:
        The provider's registered model definitions.
    """
    return list(_MODEL_REGISTRY.get(provider, {}).values())