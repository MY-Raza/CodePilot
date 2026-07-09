from enum import Enum
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Supported deployment environments.

    Attributes:
        LOCAL: Local developer machine, outside Docker.
        DEVELOPMENT: Shared development/staging environment.
        DOCKER: Running inside a local Docker container.
        RAILWAY: Deployed on Railway.
        RENDER: Deployed on Render.
        PRODUCTION: Production deployment.
    """

    LOCAL = "local"
    DEVELOPMENT = "development"
    DOCKER = "docker"
    RAILWAY = "railway"
    RENDER = "render"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Centralized application configuration.

    All values are sourced from environment variables (or a `.env` file in
    local development). No secrets are hardcoded — sensitive fields such as
    API keys and tokens default to `None` and must be supplied at runtime.

    Attributes:
        app_name: Human-readable application name.
        app_version: Semantic version of the running application.
        app_description: Short description used in OpenAPI metadata.
        debug: Enables verbose debugging behavior when True.
        environment: The current deployment environment.
        host: Network interface the server binds to.
        port: Network port the server listens on.
        jwt_secret: Secret key used to sign/verify JWT tokens.
        jwt_algorithm: Algorithm used for JWT signing (e.g. "HS256").
        access_token_expire_minutes: Access token lifetime, in minutes.
        refresh_token_expire_days: Refresh token lifetime, in days.
        database_url: SQLAlchemy-compatible PostgreSQL connection string.
        groq_api_key: API key for the Groq LLM inference service.
        default_model: Default LLM model identifier used by the AI layer.
        qdrant_url: URL of the Qdrant vector database instance.
        qdrant_api_key: API key for authenticating with Qdrant Cloud.
        github_token: Personal access token for GitHub API integration.
        jira_email: Email address associated with the Jira account.
        jira_api_token: API token for Jira authentication.
        jira_domain: Atlassian domain hosting the Jira instance.
        slack_bot_token: Bot token used to authenticate Slack API calls.
        slack_signing_secret: Secret used to verify Slack request signatures.
        google_client_id: OAuth 2.0 client ID for Google integrations.
        google_client_secret: OAuth 2.0 client secret for Google integrations.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------
    app_name: str = Field(
        default="AI Software Engineering Assistant",
        description="Human-readable name of the application.",
    )
    app_version: str = Field(
        default="1.0.0",
        description="Semantic version of the running application.",
    )
    app_description: str = Field(
        default=(
            "Enterprise-grade backend powering an AI Software Engineering "
            "Assistant."
        ),
        description="Short description used in OpenAPI metadata.",
    )
    debug: bool = Field(
        default=False,
        description="Enables verbose debugging behavior when True.",
    )
    environment: Environment = Field(
        default=Environment.LOCAL,
        description="The current deployment environment.",
    )
    host: str = Field(
        default="0.0.0.0",
        description="Network interface the server binds to.",
    )
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Network port the server listens on.",
    )

    # -------------------------------------------------------------------
    # Security
    # -------------------------------------------------------------------
    jwt_secret: str = Field(
        default=...,
        description="Secret key used to sign/verify JWT tokens.",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="Algorithm used for JWT signing.",
    )
    access_token_expire_minutes: int = Field(
        default=30,
        gt=0,
        description="Access token lifetime, in minutes.",
    )
    refresh_token_expire_days: int = Field(
        default=7,
        gt=0,
        description="Refresh token lifetime, in days.",
    )

    # -------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------
    database_url: str = Field(
        default=...,
        description="SQLAlchemy-compatible PostgreSQL connection string.",
    )

    # -------------------------------------------------------------------
    # AI / LLM
    # -------------------------------------------------------------------
    groq_api_key: str | None = Field(
        default=None,
        description="API key for the Groq LLM inference service.",
    )
    default_model: str = Field(
        default="llama-3.3-70b-versatile",
        description="Default LLM model identifier used by the AI layer.",
    )

    # -------------------------------------------------------------------
    # Qdrant (Production Vector Store)
    # -------------------------------------------------------------------
    qdrant_url: str | None = Field(
        default=None,
        description="URL of the Qdrant vector database instance.",
    )
    qdrant_api_key: str | None = Field(
        default=None,
        description="API key for authenticating with Qdrant Cloud.",
    )

    # -------------------------------------------------------------------
    # GitHub Integration
    # -------------------------------------------------------------------
    github_token: str | None = Field(
        default=None,
        description="Personal access token for GitHub API integration.",
    )

    # -------------------------------------------------------------------
    # Jira Integration
    # -------------------------------------------------------------------
    jira_email: str | None = Field(
        default=None,
        description="Email address associated with the Jira account.",
    )
    jira_api_token: str | None = Field(
        default=None,
        description="API token for Jira authentication.",
    )
    jira_domain: str | None = Field(
        default=None,
        description="Atlassian domain hosting the Jira instance.",
    )

    # -------------------------------------------------------------------
    # Slack Integration
    # -------------------------------------------------------------------
    slack_bot_token: str | None = Field(
        default=None,
        description="Bot token used to authenticate Slack API calls.",
    )
    slack_signing_secret: str | None = Field(
        default=None,
        description="Secret used to verify Slack request signatures.",
    )

    # -------------------------------------------------------------------
    # Google Integration
    # -------------------------------------------------------------------
    google_client_id: str | None = Field(
        default=None,
        description="OAuth 2.0 client ID for Google integrations.",
    )
    google_client_secret: str | None = Field(
        default=None,
        description="OAuth 2.0 client secret for Google integrations.",
    )

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret_strength(cls, value: str) -> str:
        """Ensure the JWT secret meets a minimum security bar.

        Args:
            value: The raw JWT secret provided via environment variable.

        Returns:
            The validated JWT secret.

        Raises:
            ValueError: If the secret is shorter than 32 characters.
        """
        if len(value) < 32:
            raise ValueError(
                "JWT_SECRET must be at least 32 characters long for "
                "adequate cryptographic strength."
            )
        return value

    @property
    def is_production(self) -> bool:
        """Return True if running in a production-like environment."""
        return self.environment in {
            Environment.PRODUCTION,
            Environment.RAILWAY,
            Environment.RENDER,
        }


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton instance of `Settings`.

    Using `lru_cache` ensures environment variables are parsed and
    validated only once per process, and the same validated configuration
    object is reused across the entire application.

    Returns:
        The cached, validated `Settings` instance.
    """
    return Settings()