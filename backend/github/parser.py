from backend.github.schemas import (
    BranchResponse,
    CommitResponse,
    IssueResponse,
    PullRequestResponse,
    RepositoryResponse,
)


def parse_repository(data: dict) -> RepositoryResponse:
    """Normalize a raw GitHub repository object.

    Args:
        data: The raw GitHub API repository object (optionally enriched
            with a "languages" key by `get_repository_metadata`).

    Returns:
        The normalized repository representation.
    """
    return RepositoryResponse(
        github_repository_id=data["id"],
        name=data["name"],
        full_name=data["full_name"],
        owner=data["owner"]["login"],
        description=data.get("description"),
        default_branch=data.get("default_branch", "main"),
        is_private=data.get("private", False),
        language=data.get("language"),
        html_url=data["html_url"],
        stargazers_count=data.get("stargazers_count"),
        forks_count=data.get("forks_count"),
        open_issues_count=data.get("open_issues_count"),
        updated_at=data.get("updated_at"),
    )


def parse_branch(data: dict) -> BranchResponse:
    """Normalize a raw GitHub branch object.

    Args:
        data: The raw GitHub API branch object.

    Returns:
        The normalized branch representation.
    """
    return BranchResponse(
        name=data["name"],
        commit_sha=data["commit"]["sha"],
        protected=data.get("protected", False),
    )


def parse_branches(items: list[dict]) -> list[BranchResponse]:
    """Normalize a list of raw GitHub branch objects.

    Args:
        items: Raw GitHub API branch objects.

    Returns:
        The normalized branch representations.
    """
    return [parse_branch(item) for item in items]


def parse_commit(data: dict) -> CommitResponse:
    """Normalize a raw GitHub commit object.

    Args:
        data: The raw GitHub API commit object.

    Returns:
        The normalized commit representation.
    """
    commit_detail = data.get("commit", {})
    author_detail = commit_detail.get("author", {})
    return CommitResponse(
        sha=data["sha"],
        message=commit_detail.get("message", ""),
        author_name=author_detail.get("name"),
        author_email=author_detail.get("email"),
        authored_at=author_detail.get("date"),
        url=data["html_url"],
    )


def parse_commits(items: list[dict]) -> list[CommitResponse]:
    """Normalize a list of raw GitHub commit objects.

    Args:
        items: Raw GitHub API commit objects.

    Returns:
        The normalized commit representations.
    """
    return [parse_commit(item) for item in items]


def parse_pull_request(data: dict) -> PullRequestResponse:
    """Normalize a raw GitHub pull request object.

    Args:
        data: The raw GitHub API pull request object.

    Returns:
        The normalized pull request representation.
    """
    return PullRequestResponse(
        number=data["number"],
        title=data["title"],
        state=data["state"],
        author=(data.get("user") or {}).get("login"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
        merged=bool(data.get("merged_at")),
        url=data["html_url"],
    )


def parse_pull_requests(items: list[dict]) -> list[PullRequestResponse]:
    """Normalize a list of raw GitHub pull request objects.

    Args:
        items: Raw GitHub API pull request objects.

    Returns:
        The normalized pull request representations.
    """
    return [parse_pull_request(item) for item in items]


def parse_issue(data: dict) -> IssueResponse:
    """Normalize a raw GitHub issue object.

    Args:
        data: The raw GitHub API issue object.

    Returns:
        The normalized issue representation.
    """
    return IssueResponse(
        number=data["number"],
        title=data["title"],
        state=data["state"],
        author=(data.get("user") or {}).get("login"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
        url=data["html_url"],
    )


def parse_issues(items: list[dict]) -> list[IssueResponse]:
    """Normalize a list of raw GitHub issue objects.

    Args:
        items: Raw GitHub API issue objects.

    Returns:
        The normalized issue representations.
    """
    return [parse_issue(item) for item in items]