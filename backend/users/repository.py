import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models.user import User
from backend.database.session import get_db


class UserRepository:
    """Persistence operations for managing an existing `User` record."""

    def __init__(self, db: Session) -> None:
        """Initialize the repository with a database session.

        Args:
            db: An active SQLAlchemy session, typically injected via
                `Depends(get_db)`.
        """
        self._db = db

    def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """Fetch a user by their unique ID.

        Args:
            user_id: The UUID of the user to look up.

        Returns:
            The matching `User`, or None if no user has this ID.
        """
        statement = select(User).where(User.id == user_id)
        return self._db.execute(statement).scalar_one_or_none()

    def update_user(self, user: User, fields: dict[str, Any]) -> User:
        """Apply a partial set of field updates to a user and persist them.

        Args:
            user: The `User` instance to update.
            fields: A mapping of attribute names to new values. Only keys
                present in this mapping are modified.

        Returns:
            The updated, persisted `User` instance.
        """
        for field_name, value in fields.items():
            setattr(user, field_name, value)
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def update_password(self, user: User, hashed_password: str) -> User:
        """Persist a new password hash for a user.

        Args:
            user: The `User` instance whose password is being changed.
            hashed_password: The new bcrypt hash to store.

        Returns:
            The updated, persisted `User` instance.
        """
        user.hashed_password = hashed_password
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def soft_delete_user(self, user: User) -> User:
        """Mark a user as deleted without removing the database row.

        Sets `is_deleted`, `deleted_at`, and deactivates the account
        (`is_active = False`) so it can no longer authenticate.

        Args:
            user: The `User` instance to soft-delete.

        Returns:
            The updated, persisted `User` instance.
        """
        user.is_deleted = True
        user.deleted_at = datetime.now(timezone.utc)
        user.is_active = False
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def check_email_exists(
        self, email: str, exclude_user_id: uuid.UUID | None = None
    ) -> bool:
        """Check whether an email address is already registered.

        Args:
            email: The email address to check.
            exclude_user_id: A user ID to exclude from the check (used
                when validating a user's own unchanged email during an
                update).

        Returns:
            True if the email is already in use by a different user.
        """
        statement = select(User.id).where(User.email == email)
        if exclude_user_id is not None:
            statement = statement.where(User.id != exclude_user_id)
        return self._db.execute(statement).scalar_one_or_none() is not None

    def check_username_exists(
        self, username: str, exclude_user_id: uuid.UUID | None = None
    ) -> bool:
        """Check whether a username is already taken.

        Args:
            username: The username to check.
            exclude_user_id: A user ID to exclude from the check (used
                when validating a user's own unchanged username during an
                update).

        Returns:
            True if the username is already in use by a different user.
        """
        statement = select(User.id).where(User.username == username)
        if exclude_user_id is not None:
            statement = statement.where(User.id != exclude_user_id)
        return self._db.execute(statement).scalar_one_or_none() is not None


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Provide a `UserRepository` bound to the current request's session.

    Args:
        db: The request-scoped database session.

    Returns:
        A `UserRepository` instance.
    """
    return UserRepository(db)