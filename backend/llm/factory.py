import os
from collections.abc import Callable

from backend.core.config import get_settings
from backend.llm.base import LLMProviderBase
from backend.llm.exceptions import ProviderUnavailableError
from backend.llm.groq import GroqProvider

# -----------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------
# Read once here (the composition root for this module) with sensible
# defaults. GROQ_API_KEY and DEFAULT_MODEL already live in
# backend.core.config.Settings (Module 2) and are read from there below
# rather than duplicated here; the rest are specific enough to this
# module that they're read directly, consistent with prior modules in
# this codebase — consider formalizing them into Settings if other
# modules end up needing them too.
DEFAULT_PROVIDER: str = os.getenv("DEFAULT_PROVIDER", "groq").strip().lower()
TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2048"))
TOP_P: float = float(os.getenv("TOP_P", "1.0"))
REQUEST_TIMEOUT: float = float(os.getenv("REQUEST_TIMEOUT", "60"))
MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
ENABLE_STREAMING: bool = os.getenv("ENABLE_STREAMING", "true").strip().lower() == "true"

ProviderBuilder = Callable[[], LLMProviderBase]


class LLMFactory:
    """Selects, constructs, and caches the active `LLMProviderBase` provider.

    The resolved provider is cached as a process-wide singleton after
    first use, since provider clients hold persistent HTTP connection
    pools that are expensive to reconstruct per request.
    """

    _instance: LLMProviderBase | None = None
    _custom_providers: dict[str, ProviderBuilder] = {}

    @classmethod
    def register_provider(cls, name: str, builder: ProviderBuilder) -> None:
        """Register a builder for a provider not built into this module.

        Args:
            name: The provider identifier to match against
                `DEFAULT_PROVIDER` (case-insensitive).
            builder: A zero-argument callable returning an
                `LLMProviderBase` implementation.
        """
        cls._custom_providers[name.strip().lower()] = builder

    @classmethod
    def get_provider(cls) -> LLMProviderBase:
        """Return the active LLM provider, constructing it on first use.

        Returns:
            The process-wide `LLMProviderBase` singleton.

        Raises:
            ProviderUnavailableError: If the resolved provider name has
                no registered builder, or if required configuration
                (e.g. `GROQ_API_KEY`) is missing.
        """
        if cls._instance is not None:
            return cls._instance

        provider_name = DEFAULT_PROVIDER
        builder = cls._custom_providers.get(provider_name) or cls._builtin_builders().get(
            provider_name
        )
        if builder is None:
            raise ProviderUnavailableError(
                f"No LLM provider registered for '{provider_name}'. Set "
                f"DEFAULT_PROVIDER to one of: "
                f"{', '.join(sorted({*cls._builtin_builders(), *cls._custom_providers}))}."
            )

        cls._instance = builder()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Clear the cached singleton instance.

        Primarily useful for tests, or for explicitly reconnecting after
        a configuration change without restarting the process.
        """
        cls._instance = None

    @classmethod
    def _builtin_builders(cls) -> dict[str, ProviderBuilder]:
        """Return the built-in provider name -> builder mapping.

        Returns:
            A mapping covering Groq. Future providers register
            themselves via `register_provider` rather than being added
            here, keeping this factory closed for modification.
        """
        return {"groq": cls._build_groq}

    @staticmethod
    def _build_groq() -> GroqProvider:
        """Construct the Groq provider from application configuration.

        Returns:
            A configured `GroqProvider`.

        Raises:
            ProviderUnavailableError: If `GROQ_API_KEY` is not set.
        """
        settings = get_settings()
        if not settings.groq_api_key:
            raise ProviderUnavailableError(
                "GROQ_API_KEY is not configured; cannot construct the Groq "
                "LLM provider."
            )
        return GroqProvider(
            api_key=settings.groq_api_key,
            default_model=settings.default_model,
            default_temperature=TEMPERATURE,
            default_max_tokens=MAX_TOKENS,
            default_top_p=TOP_P,
            timeout=REQUEST_TIMEOUT,
            max_retries=MAX_RETRIES,
        )


def get_llm_provider() -> LLMProviderBase:
    """FastAPI-dependency-compatible accessor for the active LLM provider.

    Usage:
        from fastapi import Depends
        from backend.llm.factory import get_llm_provider

        def some_endpoint(llm: LLMProviderBase = Depends(get_llm_provider)):
            ...

    Returns:
        The process-wide `LLMProviderBase` singleton.
    """
    return LLMFactory.get_provider()