from enum import Enum


# =============================================================================
# Application Status
# =============================================================================
class ApplicationStatus(str, Enum):
    """Generic lifecycle status shared across multiple domain entities."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    FAILED = "failed"
    SUCCESS = "success"


# =============================================================================
# Repository Status
# =============================================================================
class RepositoryStatus(str, Enum):
    """Lifecycle status of a repository undergoing RAG indexing."""

    INDEXING = "indexing"
    INDEXED = "indexed"
    SYNCING = "syncing"
    ERROR = "error"


# =============================================================================
# Agent Names
# =============================================================================
class AgentName(str, Enum):
    """Identifiers for the specialized AI agents available in the system."""

    CODE_ANALYSIS = "code_analysis"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    DEBUGGING = "debugging"
    PLANNING = "planning"
    AUTOMATION = "automation"


# =============================================================================
# Supported LLM Model Families
# =============================================================================
class SupportedModel(str, Enum):
    """LLM model families supported by the AI layer."""

    LLAMA = "llama"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"


# =============================================================================
# Supported Programming Languages
# =============================================================================
class SupportedLanguage(str, Enum):
    """Programming languages supported by repository analysis and agents."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    GO = "go"
    CSHARP = "csharp"


# =============================================================================
# File Extensions
# =============================================================================
class FileExtension(str, Enum):
    """File extensions recognized by the repository ingestion pipeline."""

    PYTHON = ".py"
    TYPESCRIPT = ".ts"
    TYPESCRIPT_REACT = ".tsx"
    JAVASCRIPT = ".js"
    JAVA = ".java"
    CPP = ".cpp"
    GO = ".go"
    MARKDOWN = ".md"
    JSON = ".json"
    YAML = ".yaml"
    YML = ".yml"
    SQL = ".sql"


# =============================================================================
# API Tags (OpenAPI grouping)
# =============================================================================
class ApiTag(str, Enum):
    """Tags used to group endpoints in the OpenAPI/Swagger documentation."""

    AUTHENTICATION = "Authentication"
    USERS = "Users"
    REPOSITORIES = "Repositories"
    RAG = "RAG"
    AGENTS = "Agents"
    AUTOMATION = "Automation"
    INTEGRATIONS = "Integrations"


# =============================================================================
# HTTP Status Messages
# =============================================================================
class HttpStatusMessage(str, Enum):
    """Human-readable messages paired with common HTTP response outcomes."""

    UNAUTHORIZED = "Unauthorized access. Please authenticate and try again."
    FORBIDDEN = "You do not have permission to perform this action."
    NOT_FOUND = "The requested resource could not be found."
    SUCCESS = "Request completed successfully."
    INTERNAL_ERROR = "An unexpected error occurred. Please try again later."