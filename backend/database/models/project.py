import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.database.models.automation_job import AutomationJob
    from backend.database.models.user import User


class Project(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A user-defined project, optionally linked to a repository.

    Attributes:
        user_id: Foreign key to the `User` who owns this project.
        repository_id: Optional foreign key to an associated `Repository`.
        name: Project name.
        description: Optional project description.
        user: The `User` who owns this project.
        automation_jobs: Automation jobs scheduled under this project.
    """

    __tablename__ = "projects"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    repository_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # ---------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------
    user: Mapped["User"] = relationship(back_populates="projects")
    automation_jobs: Mapped[list["AutomationJob"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Return a debug-friendly representation of the project."""
        return f"<Project id={self.id} name={self.name!r}>"