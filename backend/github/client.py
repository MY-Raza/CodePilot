import asyncio
import logging

import httpx

from backend.core.config import get_settings
from backend.github.exceptions import (
    AuthenticationFailedError,
    GitHubIntegrationError,
    GitHubRateLimitError,
    RepositoryNotFoundError,
)

logger = logging.getLogger(__name__)

GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_API_VERSION = "2022-11-28"
DEFAULT_TIMEOUT_SECONDS = 15.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_PAGE_SIZE = 100
MAX_PAGES = 5


class GitHubClient:
    """Async client for the GitHub REST API.

    Intended for use as an async context manager so the underlying HTTP
    connection pool is properly closed:

        async with GitHubClient() as client:
            repo = await client.get_repository("octocat", "hello-world")
    """

    def __init__(
        self,
        token: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        """Initialize the client.

        Args:
            token: A GitHub Personal Access Token. Falls back to
                `Settings.github_token` when omitted, supporting both
                public (unauthenticated) and private (authenticated)
                repository access.
            timeout: Per-request timeout, in seconds.
            max_retries: Maximum retry attempts for transient failures
                (timeouts and 5xx responses).
        """
        settings = get_settings()
        self._token = token or settings.github_token
        self._timeout = timeout
        self._max_retries = max_retries
        self._http_client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "GitHubClient":
        """Open the underlying HTTP connection pool."""
        self._http_client = httpx.AsyncClient(
            base_url=GITHUB_API_BASE_URL,
            timeout=self._timeout,
            headers=self._default_headers(),
        )
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Close the underlying HTTP connection pool."""
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    def _default_headers(self) -> dict[str, str]:
        """Build the default headers sent with every request.

        Returns:
            A headers mapping including the Accept, API version, and (if
            configured) Authorization headers. The token itself is never
            logged.
        """
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def _request(
        self, method: str, path: str, params: dict[str, str | int] | None = None
    ) -> httpx.Response:
        """Issue an authenticated request with retry and error mapping.

        Args:
            method: The HTTP method (e.g. "GET").
            path: The API path, relative to the GitHub API base URL.
            params: Optional query parameters.

        Returns:
            The successful `httpx.Response`.

        Raises:
            AuthenticationFailedError: On a 401 response.
            RepositoryNotFoundError: On a 404 response.
            GitHubRateLimitError: On a 403/429 rate-limit response.
            GitHubIntegrationError: On repeated timeouts or other
                unrecoverable HTTP errors.
        """
        if self._http_client is None:
            raise GitHubIntegrationError(
                "GitHubClient must be used as an async context manager "
                "(e.g. 'async with GitHubClient() as client: ...')."
            )

        attempt = 0
        while True:
            attempt += 1
            try:
                response = await self._http_client.request(method, path, params=params)
            except httpx.TimeoutException as exc:
                if attempt >= self._max_retries:
                    logger.error("GitHub API request timed out: %s %s", method, path)
                    raise GitHubIntegrationError(
                        f"GitHub API request to '{path}' timed out after "
                        f"{self._max_retries} attempts."
                    ) from exc
                await asyncio.sleep(0.5 * (2**attempt))
                continue

            if response.status_code == 401:
                raise AuthenticationFailedError(
                    "GitHub rejected the configured credentials. Verify "
                    "GITHUB_TOKEN is set and has not expired."
                )
            if response.status_code == 404:
                raise RepositoryNotFoundError(
                    f"GitHub resource not found: {path}"
                )
            if response.status_code == 403 and response.headers.get(
                "X-RateLimit-Remaining"
            ) == "0":
                raise GitHubRateLimitError(
                    "GitHub API rate limit exceeded.",
                    reset_at=response.headers.get("X-RateLimit-Reset"),
                )
            if response.status_code == 429:
                raise GitHubRateLimitError(
                    "GitHub API secondary rate limit exceeded.",
                    reset_at=response.headers.get("Retry-After"),
                )
            if response.status_code >= 500 and attempt < self._max_retries:
                logger.warning(
                    "GitHub API returned %s for %s %s; retrying (attempt %s/%s).",
                    response.status_code,
                    method,
                    path,
                    attempt,
                    self._max_retries,
                )
                await asyncio.sleep(0.5 * (2**attempt))
                continue

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "GitHub API error: %s %s -> %s",
                    method,
                    path,
                    response.status_code,
                )
                raise GitHubIntegrationError(
                    f"GitHub API request to '{path}' failed with status "
                    f"{response.status_code}."
                ) from exc

            return response

    async def _paginated_get(
        self,
        path: str,
        params: dict[str, str | int] | None = None,
        max_pages: int = MAX_PAGES,
    ) -> list[dict]:
        """Fetch and concatenate all pages of a paginated list endpoint.

        Args:
            path: The API path, relative to the GitHub API base URL.
            params: Optional query parameters merged with pagination
                parameters.
            max_pages: Safety cap on the number of pages fetched.

        Returns:
            The concatenated list of items across all fetched pages.
        """
        items: list[dict] = []
        page = 1
        base_params = dict(params or {})
        base_params.setdefault("per_page", DEFAULT_PAGE_SIZE)

        while page <= max_pages:
            page_params = {**base_params, "page": page}
            response = await self._request("GET", path, params=page_params)
            page_items = response.json()
            if not page_items:
                break
            items.extend(page_items)
            if len(page_items) < int(base_params["per_page"]):
                break
            page += 1

        return items

    async def get_repository(self, owner: str, repo: str) -> dict:
        """Fetch core repository metadata.

        Args:
            owner: The repository owner's GitHub login.
            repo: The repository's short name.

        Returns:
            The raw GitHub API repository object.
        """
        response = await self._request("GET", f"/repos/{owner}/{repo}")
        return response.json()

    async def get_repository_metadata(self, owner: str, repo: str) -> dict:
        """Fetch repository metadata enriched with detected languages.

        Args:
            owner: The repository owner's GitHub login.
            repo: The repository's short name.

        Returns:
            The raw repository object with an added "languages" key
            mapping language name to byte count.
        """
        repository = await self.get_repository(owner, repo)
        languages_response = await self._request(
            "GET", f"/repos/{owner}/{repo}/languages"
        )
        repository["languages"] = languages_response.json()
        return repository

    async def validate_repository(self, owner: str, repo: str) -> bool:
        """Check whether a repository exists and is accessible.

        Args:
            owner: The repository owner's GitHub login.
            repo: The repository's short name.

        Returns:
            True if the repository is accessible with the configured
            credentials, False if it does not exist or access is denied.

        Raises:
            GitHubRateLimitError: If the rate limit is exceeded while
                validating.
        """
        try:
            await self.get_repository(owner, repo)
            return True
        except (RepositoryNotFoundError, AuthenticationFailedError):
            return False

    async def list_branches(self, owner: str, repo: str) -> list[dict]:
        """List all branches of a repository.

        Args:
            owner: The repository owner's GitHub login.
            repo: The repository's short name.

        Returns:
            A list of raw GitHub API branch objects.
        """
        return await self._paginated_get(f"/repos/{owner}/{repo}/branches")

    async def get_pull_requests(
        self, owner: str, repo: str, state: str = "open"
    ) -> list[dict]:
        """List pull requests for a repository.

        Args:
            owner: The repository owner's GitHub login.
            repo: The repository's short name.
            state: Filter by state — "open", "closed", or "all".

        Returns:
            A list of raw GitHub API pull request objects.
        """
        return await self._paginated_get(
            f"/repos/{owner}/{repo}/pulls", params={"state": state}
        )

    async def get_commits(
        self, owner: str, repo: str, branch: str | None = None
    ) -> list[dict]:
        """List commits for a repository.

        Args:
            owner: The repository owner's GitHub login.
            repo: The repository's short name.
            branch: Optional branch (GitHub's `sha` parameter) to list
                commits from; defaults to the repository's default branch.

        Returns:
            A list of raw GitHub API commit objects.
        """
        params: dict[str, str | int] = {"sha": branch} if branch else {}
        return await self._paginated_get(
            f"/repos/{owner}/{repo}/commits", params=params
        )

    async def get_issues(self, owner: str, repo: str, state: str = "open") -> list[dict]:
        """List issues for a repository, excluding pull requests.

        GitHub's issues endpoint includes pull requests in its results;
        this method filters those out so only genuine issues remain.

        Args:
            owner: The repository owner's GitHub login.
            repo: The repository's short name.
            state: Filter by state — "open", "closed", or "all".

        Returns:
            A list of raw GitHub API issue objects, excluding pull
            requests.
        """
        raw_items = await self._paginated_get(
            f"/repos/{owner}/{repo}/issues", params={"state": state}
        )
        return [item for item in raw_items if "pull_request" not in item]