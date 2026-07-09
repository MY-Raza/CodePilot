import os

# ---------------------------------------------------------------------------
# Project Metadata
# ---------------------------------------------------------------------------
PROJECT_NAME: str = "CodePilot"
PROJECT_VERSION: str = "1.0.0"

# ---------------------------------------------------------------------------
# API Routing
# ---------------------------------------------------------------------------
API_PREFIX: str = "/api"
API_V1_PREFIX: str = f"{API_PREFIX}/v1"

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
# Comma-separated origins may be supplied via the ALLOWED_ORIGINS
# environment variable (e.g. "https://app.example.com,https://foo.com").
# Falls back to common local frontend dev servers when unset.
_DEFAULT_ALLOWED_ORIGINS: list[str] = [
    "http://localhost:3000",
    "http://localhost:5173",
]

ALLOWED_ORIGINS: list[str] = (
    [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "").split(",") if origin.strip()]
    or _DEFAULT_ALLOWED_ORIGINS
)

CORS_HEADERS: list[str] = ["*"]

# ---------------------------------------------------------------------------
# Request Limits
# ---------------------------------------------------------------------------
# Maximum accepted request body size, in bytes (default: 10 MB).
MAX_REQUEST_SIZE: int = 10 * 1024 * 1024

# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------
DEFAULT_PAGE_SIZE: int = 20
MAX_PAGE_SIZE: int = 100

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# ---------------------------------------------------------------------------
# AI / RAG Defaults
# ---------------------------------------------------------------------------
DEFAULT_EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_LLM_MODEL: str = "llama-3.3-70b-versatile"

# Text chunking for the RAG ingestion pipeline.
CHUNK_SIZE: int = 1000
CHUNK_OVERLAP: int = 200

# Retrieval behavior.
TOP_K_RESULTS: int = 5

# LLM generation behavior.
TEMPERATURE: float = 0.2
MAX_TOKENS: int = 4096