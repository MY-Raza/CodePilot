import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.core.constants import RepositoryStatus


class ConnectRepositoryRequest(BaseModel):
    """Request payload to connect a GitHub repository to the platform.

    Attributes:
        owner: The GitHub organization or user that owns the repository.
        name: The repository's short name (not the full "owner/name").
        branch: Optional branch to track; defaults to the repository's
            default branch on GitHub if omitted.
    """

    owner: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)
    branch: str | None = Field(default=None, max_length=255)


class RepositoryResponse(BaseModel):
    """Normalized representation of a GitHub repository.

    Attributes:
        github_repository_id: The repository's numeric ID on GitHub.
        name: Short repository name.
        full_name: Fully qualified name ("owner/name").
        owner: GitHub login of the repository's owner/organization.
        description: Optional repository description.
        default_branch: The repository's default branch on GitHub.
        is_private: Whether the repository is private.
        language: Primary programming language, if known.
        html_url: The repository's web URL on GitHub.
        stargazers_count: Number of stars, if available.
        forks_count: Number of forks, if available.
        open_issues_count: Number of open issues, if available.
        updated_at: Timestamp of the repository's last update on GitHub.
    """

    model_config = ConfigDict(from_attributes=True)

    github_repository_id: int
    name: str
    full_name: str
    owner: str
    description: str | None = None
    default_branch: str
    is_private: bool
    language: str | None = None
    html_url: str
    stargazers_count: int | None = None
    forks_count: int | None = None
    open_issues_count: int | None = None
    updated_at: datetime | None = None


class BranchResponse(BaseModel):
    """Normalized representation of a repository branch.

    Attributes:
        name: The branch name.
        commit_sha: SHA of the commit the branch currently points to.
        protected: Whether the branch has GitHub branch protection rules.
    """

    name: str
    commit_sha: str
    protected: bool = False


class CommitResponse(BaseModel):
    """Normalized representation of a single commit.

    Attributes:
        sha: The commit's SHA hash.
        message: The commit message.
        author_name: Name of the commit author, if available.
        author_email: Email of the commit author, if available.
        authored_at: Timestamp the commit was authored.
        url: The commit's web URL on GitHub.
    """

    sha: str
    message: str
    author_name: str | None = None
    author_email: str | None = None
    authored_at: datetime | None = None
    url: str


class PullRequestResponse(BaseModel):
    """Normalized representation of a pull request.

    Attributes:
        number: The pull request's number within the repository.
        title: The pull request's title.
        state: Current state ("open", "closed").
        author: GitHub login of the pull request's author, if available.
        created_at: Timestamp the pull request was created.
        updated_at: Timestamp the pull request was last updated.
        merged: Whether the pull request has been merged.
        url: The pull request's web URL on GitHub.
    """

    number: int
    title: str
    state: str
    author: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    merged: bool = False
    url: str


class IssueResponse(BaseModel):
    """Normalized representation of an issue.

    Attributes:
        number: The issue's number within the repository.
        title: The issue's title.
        state: Current state ("open", "closed").
        author: GitHub login of the issue's author, if available.
        created_at: Timestamp the issue was created.
        updated_at: Timestamp the issue was last updated.
        url: The issue's web URL on GitHub.
    """

    number: int
    title: str
    state: str
    author: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    url: str


class RepositorySyncResponse(BaseModel):
    """Result of a repository synchronization operation.

    Attributes:
        repository_id: The platform's internal repository ID.
        status: The repository's lifecycle status after the sync attempt.
        indexed_at: Timestamp of the most recent successful sync.
        message: Human-readable summary of the sync outcome.
    """

    repository_id: uuid.UUID
    status: RepositoryStatus
    indexed_at: datetime | None = None
    message: str


class WebhookPayload(BaseModel):
    """Normalized envelope for an inbound GitHub webhook delivery.

    Attributes:
        event: The GitHub event type, from the `X-GitHub-Event` header
            (e.g. "push", "pull_request", "issues", "repository", "ping").
        delivery_id: The unique delivery ID, from the
            `X-GitHub-Delivery` header.
        payload: The raw, parsed JSON body of the webhook request.
    """

    event: str
    delivery_id: str | None = None
    payload: dict[str, Any]