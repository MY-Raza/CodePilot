import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Root declarative base class for all ORM models.

    Alembic's `env.py` should target `Base.metadata` for autogeneration
    to detect all models registered through this base.
    """


class UUIDPrimaryKeyMixin:
    """Adds a UUID primary key column named `id`.

    The UUID is generated client-side via `uuid.uuid4` by default. To
    generate UUIDs server-side instead (e.g. via the `pgcrypto` extension),
    add `server_default=text("gen_random_uuid()")` after enabling the
    extension with `CREATE EXTENSION IF NOT EXISTS pgcrypto;`.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )


class TimestampMixin:
    """Adds `created_at` and `updated_at` timestamp columns.

    Both columns are timezone-aware and populated server-side, ensuring
    consistent values regardless of application server clock drift.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """Adds soft-delete support via `is_deleted` and `deleted_at` columns.

    Records are never physically removed by default; queries should
    filter on `is_deleted == False` to exclude soft-deleted rows.
    """

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class AuditMixin:
    """Adds `created_by` and `updated_by` actor-tracking columns.

    Stores the UUID of the user responsible for creating/last-updating a
    record. Nullable to support system-initiated changes (e.g. background
    workers) with no associated user.
    """

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )