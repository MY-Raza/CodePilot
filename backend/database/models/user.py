import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.database.models.conversation import Conversation
    from backend.database.models.project import Project
    from backend.database.models.repository import Repository


class UserRole(str, enum.Enum):
    """Authorization role assigned to a user account."""

    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """A registered platform user.

    Attributes:
        username: Unique handle used for display and login.
        email: Unique, verified contact/login email address.
        hashed_password: Bcrypt/argon2 password hash. Never store plaintext.
        first_name: Optional given name.
        last_name: Optional family name.
        avatar_url: Optional URL to a profile image.
        role: Authorization role controlling access to platform features.
        is_active: Whether the account can currently authenticate.
        is_verified: Whether the user's email has been verified.
        last_login: Timestamp of the user's most recent successful login.
        repositories: Repositories owned/added by this user.
        conversations: Chat conversations initiated by this user.
        projects: Projects created by this user.
    """

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(
            UserRole,
            name="user_role",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=UserRole.DEVELOPER,
        server_default=UserRole.DEVELOPER.value,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ---------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------
    repositories: Mapped[list["Repository"]] = relationship(
        back_populates="owner_user",
        cascade="all, delete-orphan",
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    projects: Mapped[list["Project"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Return a debug-friendly representation of the user."""
        return f"<User id={self.id} username={self.username!r}>"