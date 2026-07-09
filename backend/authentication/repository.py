import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.authentication.schemas import UserCreate
from backend.database.models.user import User


class UserRepository:
    """Persistence operations for the `User` model."""

    def __init__(self, db: Session) -> None:
        """Initialize the repository with a database session.

        Args:
            db: An active SQLAlchemy session, typically injected via
                `Depends(get_db)`.
        """
        self._db = db

    def create_user(self, user_data: UserCreate, hashed_password: str) -> User:
        """Persist a new user record.

        Args:
            user_data: Validated user creation data (plaintext password is
                not used here — the caller must supply a pre-hashed value).
            hashed_password: The bcrypt hash of the user's password.

        Returns:
            The newly created, persisted `User` instance.
        """
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
        )
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def get_user_by_email(self, email: str) -> User | None:
        """Fetch a user by their email address.

        Args:
            email: The email address to look up.

        Returns:
            The matching `User`, or None if no user has this email.
        """
        statement = select(User).where(User.email == email)
        return self._db.execute(statement).scalar_one_or_none()

    def get_user_by_username(self, username: str) -> User | None:
        """Fetch a user by their username.

        Args:
            username: The username to look up.

        Returns:
            The matching `User`, or None if no user has this username.
        """
        statement = select(User).where(User.username == username)
        return self._db.execute(statement).scalar_one_or_none()

    def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """Fetch a user by their unique ID.

        Args:
            user_id: The UUID of the user to look up.

        Returns:
            The matching `User`, or None if no user has this ID.
        """
        statement = select(User).where(User.id == user_id)
        return self._db.execute(statement).scalar_one_or_none()