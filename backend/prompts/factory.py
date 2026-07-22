import logging

from backend.prompts.base import PromptTemplate
from backend.prompts.schemas import PromptMetadata

logger = logging.getLogger(__name__)


class PromptNotFoundError(KeyError):
    """Raised when a requested prompt name/version has not been registered."""


class PromptFactory:
    """Process-wide registry of prompt templates, keyed by (name, version).

    Implemented as a singleton via class-level state and classmethods —
    consistent with `LLMFactory`/`VectorStoreFactory`/`EmbeddingFactory`
    elsewhere in this codebase — rather than requiring callers to
    construct and pass around an instance.
    """

    _templates: dict[tuple[str, str], PromptTemplate] = {}
    _latest_version: dict[str, str] = {}

    @classmethod
    def register(cls, template: PromptTemplate) -> None:
        """Register a prompt template.

        Registering a name/version pair that already exists overwrites
        the previous registration (useful for hot-reloading a prompt
        during development). The most recently registered version for a
        given name becomes that name's "latest" — see `get()`.

        Args:
            template: The prompt template to register.
        """
        key = (template.name, template.version)
        cls._templates[key] = template
        cls._latest_version[template.name] = template.version
        logger.debug("Prompt registered: %s (v%s)", template.name, template.version)

    @classmethod
    def get(cls, name: str, version: str | None = None) -> PromptTemplate:
        """Retrieve a registered prompt template.

        Args:
            name: The prompt's registered name.
            version: A specific version to retrieve. Defaults to the
                most recently registered version for `name`.

        Returns:
            The matching prompt template.

        Raises:
            PromptNotFoundError: If `name` has no registered prompts, or
                `version` was specified but does not match a
                registration.
        """
        resolved_version = version or cls._latest_version.get(name)
        if resolved_version is None:
            raise PromptNotFoundError(f"No prompt is registered under the name '{name}'.")

        template = cls._templates.get((name, resolved_version))
        if template is None:
            raise PromptNotFoundError(
                f"Prompt '{name}' has no registered version '{resolved_version}'. "
                f"Available versions: {', '.join(cls.list_versions(name)) or 'none'}."
            )
        return template

    @classmethod
    def list_versions(cls, name: str) -> list[str]:
        """List every registered version for a prompt name.

        Args:
            name: The prompt name to list versions for.

        Returns:
            The registered version strings, in registration order.
        """
        return [version for (registered_name, version) in cls._templates if registered_name == name]

    @classmethod
    def list_prompts(cls, category: str | None = None) -> list[PromptMetadata]:
        """List metadata for every registered prompt's latest version.

        Args:
            category: If provided, only prompts in this category are
                returned.

        Returns:
            Metadata for each registered prompt name's latest version,
            sorted by name.
        """
        results: list[PromptMetadata] = []
        for name, version in sorted(cls._latest_version.items()):
            template = cls._templates[(name, version)]
            if isinstance(template, PromptTemplate) and hasattr(template, "metadata"):
                metadata = template.metadata()
            else:
                metadata = PromptMetadata(
                    name=template.name,
                    description=template.description,
                    category="unknown",
                    version=template.version,
                    required_variables=template.required_variables(),
                    supported_models=template.supported_models(),
                    default_temperature=0.3,
                    default_output_format="markdown",
                )
            if category is None or metadata.category == category:
                results.append(metadata)
        return results

    @classmethod
    def reset(cls) -> None:
        """Clear every registration.

        Primarily useful for tests.
        """
        cls._templates.clear()
        cls._latest_version.clear()