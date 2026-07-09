from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.authentication import auth_router
from backend.core.settings import API_V1_PREFIX

# ---------------------------------------------------------------------------
# CORS Configuration
# ---------------------------------------------------------------------------
# Centralized list of allowed origins. This can later be moved to a
# settings/config module (e.g. backend/core/config.py) and loaded from
# environment variables for different deployment environments.
ALLOWED_ORIGINS: list[str] = [
    "http://localhost:3000",
    "http://localhost:5173",
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown events.

    This replaces the deprecated `@app.on_event("startup")` and
    `@app.on_event("shutdown")` decorators with the recommended
    lifespan context manager approach.

    Args:
        app: The FastAPI application instance.

    Yields:
        None. Control is yielded back to the running application between
        startup and shutdown phases.
    """
    # -----------------------------------------------------------------
    # STARTUP LOGIC
    # -----------------------------------------------------------------
    # Future startup tasks will be added here, e.g.:
    #   - Initialize database connection pool
    #   - Initialize ChromaDB / Qdrant client
    #   - Warm up LLM clients (Groq, LangChain, LangGraph)
    #   - Load configuration / secrets validation
    print("Starting CodePilot Backend...")

    yield

    # -----------------------------------------------------------------
    # SHUTDOWN LOGIC
    # -----------------------------------------------------------------
    # Future shutdown tasks will be added here, e.g.:
    #   - Close database connections
    #   - Close vector store connections
    #   - Flush background worker queues
    print("Shutting down CodePilot Backend...")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application instance.

    Returns:
        A fully configured FastAPI application object.
    """
    app = FastAPI(
        title="CodePilot",

        version="1.0.0",
        description=(
            "Enterprise-grade backend powering an AI Software Engineering "
            "Assistant. Provides authentication, repository management, "
            "RAG-based code intelligence, AI agents, integrations, and "
            "automation capabilities."
        ),
        lifespan=lifespan,
        # ---------------------------------------------------------------
        # OpenAPI Metadata
        # ---------------------------------------------------------------
        openapi_tags=[
            {"name": "System", "description": "Health and status endpoints."},
        ],
        contact={
            "name": "AI Software Engineering Assistant Team",
            "email": "support@example.com",
        },
        license_info={
            "name": "Proprietary",
        },
    )

    # -----------------------------------------------------------------
    # CORS Middleware
    # -----------------------------------------------------------------
    # Allows the frontend (running on localhost during development) to
    # communicate with this backend. ALLOWED_ORIGINS should be extended
    # or replaced with environment-driven configuration in production.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -----------------------------------------------------------------
    # Middleware Placeholders
    # -----------------------------------------------------------------
    # NOTE: The following middleware will be implemented in later modules.
    # They are intentionally left as comments to preserve intended
    # execution order (outer to inner):
    #
    #   1. Request Logging Middleware
    #      app.add_middleware(RequestLoggingMiddleware)
    #      -> Logs incoming requests/responses for observability.
    #
    #   2. Authentication Middleware
    #      app.add_middleware(AuthenticationMiddleware)
    #      -> Validates JWT tokens and attaches user context to requests.
    #
    #   3. Rate Limiting Middleware
    #      app.add_middleware(RateLimitingMiddleware)
    #      -> Throttles requests per user/IP to prevent abuse.

    register_routes(app)

    return app


def register_routes(app: FastAPI) -> None:
    """Register root-level routes and API routers on the application.

    Args:
        app: The FastAPI application instance to attach routes to.
    """

    @app.get("/", tags=["System"], summary="Root endpoint")
    async def root() -> dict[str, str]:
        """Return basic backend status information.

        Returns:
            A dictionary containing a welcome message, current status,
            and API version.
        """
        return {
            "message": "CodePilot Backend",
            "status": "running",
            "version": "1.0.0",
        }

    @app.get("/health", tags=["System"], summary="Health check endpoint")
    async def health_check() -> dict[str, str]:
        """Return the health status of the backend service.

        Used by orchestration platforms (e.g. Railway, Docker, Kubernetes)
        to verify the service is alive and ready to accept traffic.

        Returns:
            A dictionary indicating the health status.
        """
        return {"status": "healthy"}

    # -------------------------------------------------------------------
    # API Router Placeholder
    # -------------------------------------------------------------------
    app.include_router(auth_router, prefix=API_V1_PREFIX)


# ---------------------------------------------------------------------------
# Application Instance
# ---------------------------------------------------------------------------
# This is the ASGI application object referenced by uvicorn:
#   uvicorn backend.main:app --host 0.0.0.0 --port 8000
app: FastAPI = create_application()