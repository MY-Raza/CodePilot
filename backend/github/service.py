import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import git
from fastapi import Depends
from git.exc import GitCommandError

from backend.core.constants import RepositoryStatus
from backend.database.models.repository import Repository
from backend.database.models.user import User
from backend.github import parser
from backend.github.client import GitHubClient
from backend.github.exceptions import (
    CloneFailedError,
    InvalidRepositoryError,
    PullFailedError,
)
from backend.github.repository import GitHubRepositoryRepository, get_github_repository_repository
from backend.github.schemas import (
    BranchResponse,
    CommitResponse,
    ConnectRepositoryRequest,
    IssueResponse,
    PullRequestResponse,
    RepositoryResponse,
    RepositorySyncResponse,
)

logger = logging.getLogger(__name__)

# Root directory under which repositories are cloned locally. Configurable
# via the REPOSITORY_CLONE_ROOT environment variable; defaults to a path
# suitable for a mounted Docker volume. Each repository is cloned into a
# subdirectory named after its internal (platform) UUID, not its GitHub
# name, to avoid collisions between repositories of the same name owned
# by different users.
DEFAULT_CLONE_ROOT = Path(os.getenv("REPOSITORY_CLONE_ROOT", "/data/repositories"))


class GitHubService:
    """Coordinates GitHub repository connection, sync, and local cloning."""

    def __init__(
        self,
        repository: GitHubRepositoryRepository,
        clone_root: Path = DEFAULT_CLONE_ROOT,
    ) -> None:
        """Initialize the service.

        Args:
            repository: The data-access layer for connected repositories.
            clone_root: Root directory under which repositories are cloned.
        """
        self._repository = repository
        self._clone_root = clone_root

    def _local_path(self, repository: Repository) -> Path:
        """Compute the local clone path for a connected repository.

        Args:
            repository: The connected repository record.

        Returns:
            The local filesystem path this repository should be cloned to.
        """
        return self._clone_root / str(repository.id)

    def _clone_url(self, owner: str, name: str, token: str | None) -> str:
        """Build an HTTPS clone URL, embedding a token for private access.

        Args:
            owner: The repository owner's GitHub login.
            name: The repository's short name.
            token: A GitHub Personal Access Token, or None for public,
                unauthenticated cloning.

        Returns:
            The HTTPS clone URL. Never logged by callers of this method,
            since it may embed a credential.
        """
        if token:
            return f"https://{token}@github.com/{owner}/{name}.git"
        return f"https://github.com/{owner}/{name}.git"

    async def validate_repository(self, owner: str, name: str) -> bool:
        """Check whether a repository exists and is accessible on GitHub.

        Args:
            owner: The repository owner's GitHub login.
            name: The repository's short name.

        Returns:
            True if the repository is accessible, False otherwise.
        """
        async with GitHubClient() as client:
            return await client.validate_repository(owner, name)

    async def get_repository_details(self, owner: str, name: str) -> RepositoryResponse:
        """Fetch and normalize a repository's metadata from GitHub.

        Args:
            owner: The repository owner's GitHub login.
            name: The repository's short name.

        Returns:
            The normalized repository representation.
        """
        async with GitHubClient() as client:
            raw = await client.get_repository_metadata(owner, name)
        return parser.parse_repository(raw)

    async def connect_repository(
        self, user: User, request: ConnectRepositoryRequest
    ) -> Repository:
        """Validate and persist a new connected repository for a user.

        Args:
            user: The user connecting the repository.
            request: The owner/name (and optional branch) to connect.

        Returns:
            The newly persisted `Repository` record.

        Raises:
            InvalidRepositoryError: If the repository does not exist, is
                inaccessible, or has already been connected.
        """
        async with GitHubClient() as client:
            if not await client.validate_repository(request.owner, request.name):
                raise InvalidRepositoryError(
                    f"Repository '{request.owner}/{request.name}' does not "
                    "exist or is not accessible with the configured "
                    "credentials."
                )
            raw = await client.get_repository_metadata(request.owner, request.name)

        if self._repository.repository_exists(raw["id"]):
            raise InvalidRepositoryError(
                f"Repository '{request.owner}/{request.name}' is already "
                "connected."
            )

        parsed = parser.parse_repository(raw)
        fields = {
            "github_repository_id": parsed.github_repository_id,
            "name": parsed.name,
            "full_name": parsed.full_name,
            "owner": parsed.owner,
            "branch": request.branch or parsed.default_branch,
            "description": parsed.description,
            "language": parsed.language,
            "default_branch": parsed.default_branch,
            "is_private": parsed.is_private,
            "status": RepositoryStatus.INDEXING,
        }

        repository = self._repository.save_repository(user.id, fields)
        logger.info(
            "Repository connected: %s (id=%s, user_id=%s)",
            repository.full_name,
            repository.id,
            user.id,
        )
        return repository

    def clone_repository(self, repository: Repository, token: str | None = None) -> Path:
        """Clone a connected repository to local storage.

        If the target path already contains a valid git repository, this
        is treated as a no-op and the existing path is returned rather
        than raising an error.

        Args:
            repository: The connected repository to clone.
            token: A GitHub Personal Access Token for private repository
                access. Falls back to `Settings.github_token` inside
                `GitHubClient` if omitted here; passed explicitly since
                cloning happens outside the async client context.

        Returns:
            The local filesystem path the repository was cloned to.

        Raises:
            CloneFailedError: If the clone operation fails, or if the
                target path exists but is not a valid git repository.
        """
        target_path = self._local_path(repository)

        if target_path.exists():
            try:
                git.Repo(target_path)
                logger.info(
                    "Repository already cloned, skipping: %s", repository.full_name
                )
                return target_path
            except git.InvalidGitRepositoryError as exc:
                raise CloneFailedError(
                    f"Local path for repository '{repository.full_name}' "
                    "exists but is not a valid git repository. Remove it "
                    "manually before retrying."
                ) from exc

        target_path.parent.mkdir(parents=True, exist_ok=True)
        clone_url = self._clone_url(repository.owner, repository.name, token)

        logger.info("Clone started: %s -> %s", repository.full_name, target_path)
        try:
            git.Repo.clone_from(clone_url, target_path, branch=repository.branch)
        except GitCommandError as exc:
            # Never log `exc` directly here: GitPython includes the failed
            # command line, which would leak the embedded access token.
            logger.error("Clone failed for repository: %s", repository.full_name)
            raise CloneFailedError(
                f"Failed to clone repository '{repository.full_name}'. "
                "Verify the repository exists, the branch is correct, and "
                "GITHUB_TOKEN has access if the repository is private."
            ) from exc

        logger.info("Clone completed: %s -> %s", repository.full_name, target_path)
        return target_path

    def pull_repository(self, repository: Repository) -> None:
        """Pull the latest changes for an already-cloned repository.

        Args:
            repository: The connected repository to pull.

        Raises:
            PullFailedError: If the repository has not been cloned yet,
                or if the pull operation fails.
        """
        target_path = self._local_path(repository)
        if not target_path.exists():
            raise PullFailedError(
                f"Repository '{repository.full_name}' has not been cloned "
                "locally yet. Clone it before attempting to pull."
            )

        logger.info("Pull started: %s", repository.full_name)
        try:
            local_repo = git.Repo(target_path)
            local_repo.remotes.origin.pull()
        except (GitCommandError, git.InvalidGitRepositoryError) as exc:
            logger.error("Pull failed for repository: %s", repository.full_name)
            raise PullFailedError(
                f"Failed to pull latest changes for repository "
                f"'{repository.full_name}'."
            ) from exc

        logger.info("Pull completed: %s", repository.full_name)

    def sync_repository(
        self, repository: Repository, token: str | None = None
    ) -> RepositorySyncResponse:
        """Synchronize a repository's local clone (clone-or-pull).

        Marks the repository as SYNCING for the duration of the operation,
        then INDEXED on success or ERROR on failure.

        Args:
            repository: The connected repository to synchronize.
            token: A GitHub Personal Access Token for private repository
                access, if not relying on the configured default.

        Returns:
            A summary of the sync operation's outcome.
        """
        self._repository.update_repository(
            repository, {"status": RepositoryStatus.SYNCING}
        )

        try:
            target_path = self._local_path(repository)
            if target_path.exists():
                self.pull_repository(repository)
            else:
                self.clone_repository(repository, token=token)
        except (CloneFailedError, PullFailedError) as exc:
            self._repository.update_repository(
                repository, {"status": RepositoryStatus.ERROR}
            )
            return RepositorySyncResponse(
                repository_id=repository.id,
                status=RepositoryStatus.ERROR,
                indexed_at=repository.indexed_at,
                message=str(exc),
            )

        now = datetime.now(timezone.utc)
        updated = self._repository.update_last_sync(
            repository, indexed_at=now, status=RepositoryStatus.INDEXED
        )
        logger.info("Repository synchronized: %s", repository.full_name)
        return RepositorySyncResponse(
            repository_id=updated.id,
            status=RepositoryStatus.INDEXED,
            indexed_at=updated.indexed_at,
            message=f"Repository '{updated.full_name}' synchronized successfully.",
        )

    async def fetch_commits(
        self, owner: str, name: str, branch: str | None = None
    ) -> list[CommitResponse]:
        """Fetch and normalize commits for a repository.

        Args:
            owner: The repository owner's GitHub login.
            name: The repository's short name.
            branch: Optional branch to list commits from.

        Returns:
            The normalized commit representations.
        """
        async with GitHubClient() as client:
            raw = await client.get_commits(owner, name, branch=branch)
        return parser.parse_commits(raw)

    async def fetch_pull_requests(
        self, owner: str, name: str, state: str = "open"
    ) -> list[PullRequestResponse]:
        """Fetch and normalize pull requests for a repository.

        Args:
            owner: The repository owner's GitHub login.
            name: The repository's short name.
            state: Filter by state — "open", "closed", or "all".

        Returns:
            The normalized pull request representations.
        """
        async with GitHubClient() as client:
            raw = await client.get_pull_requests(owner, name, state=state)
        return parser.parse_pull_requests(raw)

    async def fetch_issues(
        self, owner: str, name: str, state: str = "open"
    ) -> list[IssueResponse]:
        """Fetch and normalize issues for a repository.

        Args:
            owner: The repository owner's GitHub login.
            name: The repository's short name.
            state: Filter by state — "open", "closed", or "all".

        Returns:
            The normalized issue representations.
        """
        async with GitHubClient() as client:
            raw = await client.get_issues(owner, name, state=state)
        return parser.parse_issues(raw)

    async def list_branches(self, owner: str, name: str) -> list[BranchResponse]:
        """Fetch and normalize branches for a repository.

        Args:
            owner: The repository owner's GitHub login.
            name: The repository's short name.

        Returns:
            The normalized branch representations.
        """
        async with GitHubClient() as client:
            raw = await client.list_branches(owner, name)
        return parser.parse_branches(raw)


def get_github_service(
    repository: GitHubRepositoryRepository = Depends(get_github_repository_repository),
) -> GitHubService:
    """Provide a `GitHubService` wired with its repository dependency.

    Args:
        repository: The request-scoped connected-repository data layer.

    Returns:
        A `GitHubService` instance.
    """
    return GitHubService(repository)