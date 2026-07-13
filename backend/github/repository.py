import uuid
from datetime import datetime
from typing import Any

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models.repository import Repository
from backend.database.session import get_db


class GitHubRepositoryRepository:
    """Persistence operations for connected `Repository` records."""

    def __init__(self, db: Session) -> None:
        """Initialize the repository with a database session.

        Args:
            db: An active SQLAlchemy session, typically injected via
                `Depends(get_db)`.
        """
        self._db = db

    def save_repository(self, user_id: uuid.UUID, fields: dict[str, Any]) -> Repository:
        """Persist a newly connected repository.

        Args:
            user_id: The ID of the user connecting the repository.
            fields: Column values for the new `Repository` row (e.g.
                `github_repository_id`, `name`, `full_name`, `owner`,
                `branch`, `description`, `language`, `default_branch`,
                `is_private`).

        Returns:
            The newly created, persisted `Repository`.
        """
        repository = Repository(user_id=user_id, **fields)
        self._db.add(repository)
        self._db.commit()
        self._db.refresh(repository)
        return repository

    def update_repository(self, repository: Repository, fields: dict[str, Any]) -> Repository:
        """Apply a partial set of field updates to a repository.

        Args:
            repository: The `Repository` instance to update.
            fields: A mapping of attribute names to new values.

        Returns:
            The updated, persisted `Repository`.
        """
        for field_name, value in fields.items():
            setattr(repository, field_name, value)
        self._db.add(repository)
        self._db.commit()
        self._db.refresh(repository)
        return repository

    def repository_exists(self, github_repository_id: int) -> bool:
        """Check whether a GitHub repository has already been connected.

        Args:
            github_repository_id: The repository's numeric ID on GitHub.

        Returns:
            True if a `Repository` row already references this GitHub
            repository ID.
        """
        statement = select(Repository.id).where(
            Repository.github_repository_id == github_repository_id
        )
        return self._db.execute(statement).scalar_one_or_none() is not None

    def delete_repository(self, repository: Repository) -> None:
        """Permanently remove a connected repository record.

        The `Repository` model has no soft-delete support, so this is a
        hard delete. Associated `Document`/`Embedding` rows cascade per
        the foreign key relationships defined on the model.

        Args:
            repository: The `Repository` instance to delete.
        """
        self._db.delete(repository)
        self._db.commit()

    def update_last_sync(
        self, repository: Repository, indexed_at: datetime, status: Any
    ) -> Repository:
        """Update a repository's sync timestamp and status.

        Args:
            repository: The `Repository` instance to update.
            indexed_at: Timestamp of the sync attempt.
            status: The resulting `RepositoryStatus` value.

        Returns:
            The updated, persisted `Repository`.
        """
        repository.indexed_at = indexed_at
        repository.status = status
        self._db.add(repository)
        self._db.commit()
        self._db.refresh(repository)
        return repository

    def find_repository(self, repository_id: uuid.UUID) -> Repository | None:
        """Fetch a connected repository by its internal ID.

        Args:
            repository_id: The platform's internal repository UUID.

        Returns:
            The matching `Repository`, or None if not found.
        """
        statement = select(Repository).where(Repository.id == repository_id)
        return self._db.execute(statement).scalar_one_or_none()

    def find_by_github_id(self, github_repository_id: int) -> Repository | None:
        """Fetch a connected repository by its GitHub numeric ID.

        Args:
            github_repository_id: The repository's numeric ID on GitHub.

        Returns:
            The matching `Repository`, or None if not found.
        """
        statement = select(Repository).where(
            Repository.github_repository_id == github_repository_id
        )
        return self._db.execute(statement).scalar_one_or_none()


def get_github_repository_repository(
    db: Session = Depends(get_db),
) -> GitHubRepositoryRepository:
    """Provide a `GitHubRepositoryRepository` bound to the request's session.

    Args:
        db: The request-scoped database session.

    Returns:
        A `GitHubRepositoryRepository` instance.
    """
    return GitHubRepositoryRepository(db)