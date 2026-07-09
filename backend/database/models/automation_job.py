import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.constants import ApplicationStatus
from backend.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.database.models.project import Project


class AutomationJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A scheduled automation job belonging to a project.

    Attributes:
        project_id: Foreign key to the owning `Project`.
        job_name: Human-readable name identifying the job's purpose.
        status: Current lifecycle status of the job.
        cron_expression: Standard cron expression controlling the schedule.
        last_run: Timestamp of the job's most recent execution.
        next_run: Timestamp of the job's next scheduled execution.
        project: The `Project` this automation job belongs to.
    """

    __tablename__ = "automation_jobs"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ApplicationStatus] = mapped_column(
        SAEnum(ApplicationStatus, name="automation_job_status"),
        default=ApplicationStatus.PENDING,
        server_default=ApplicationStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False)
    last_run: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_run: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ---------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------
    project: Mapped["Project"] = relationship(back_populates="automation_jobs")

    def __repr__(self) -> str:
        """Return a debug-friendly representation of the automation job."""
        return f"<AutomationJob id={self.id} job_name={self.job_name!r}>"