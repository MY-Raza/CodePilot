import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.constants import RepositoryStatus
from backend.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.database.models.document import Document
    from backend.database.models.user import User


class Repository(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A source code repository registered for AI-assisted analysis.

    Attributes:
        user_id: Foreign key to the `User` who registered this repository.
        github_repository_id: The repository's numeric ID on GitHub.
        name: Short repository name (e.g. "my-service").
        full_name: Fully qualified name (e.g. "org-name/my-service").
        owner: GitHub login of the repository's owner/organization.
        branch: The branch currently checked out for analysis.
        description: Optional repository description.
        language: Primary programming language, if known.
        default_branch: The repository's default branch on GitHub.
        status: Current indexing lifecycle status.
        is_private: Whether the repository is private on GitHub.
        indexed_at: Timestamp of the most recent successful indexing run.
        owner_user: The `User` who owns/registered this repository.
        documents: Source files indexed from this repository.
    """

    __tablename__ = "repositories"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    github_repository_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(
        String(512), unique=True, nullable=False, index=True
    )
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    branch: Mapped[str] = mapped_column(String(255), nullable=False, default="main")
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    language: Mapped[str | None] = mapped_column(String(100), nullable=True)
    default_branch: Mapped[str] = mapped_column(
        String(255), nullable=False, default="main"
    )
    status: Mapped[RepositoryStatus] = mapped_column(
        SAEnum(RepositoryStatus, name="repository_status"),
        default=RepositoryStatus.INDEXING,
        server_default=RepositoryStatus.INDEXING.value,
        nullable=False,
        index=True,
    )
    is_private: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    indexed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ---------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------
    owner_user: Mapped["User"] = relationship(back_populates="repositories")
    documents: Mapped[list["Document"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Return a debug-friendly representation of the repository."""
        return f"<Repository id={self.id} full_name={self.full_name!r}>"