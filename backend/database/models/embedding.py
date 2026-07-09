import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.database.models.embedding import Embedding
    from backend.database.models.repository import Repository


class Document(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A single source file tracked within a repository.

    Attributes:
        repository_id: Foreign key to the owning `Repository`.
        file_path: Path of the file relative to the repository root.
        file_name: Base name of the file (e.g. "main.py").
        language: Detected programming language of the file.
        file_extension: File extension, including the leading dot.
        checksum: Content hash used to detect changes between sync runs.
        chunk_count: Number of RAG chunks produced from this file.
        repository: The `Repository` this document belongs to.
        embeddings: Vector embeddings generated from this document's chunks.
    """

    __tablename__ = "documents"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_extension: Mapped[str | None] = mapped_column(String(20), nullable=True)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ---------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------
    repository: Mapped["Repository"] = relationship(back_populates="documents")
    embeddings: Mapped[list["Embedding"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        # A given file path should only appear once per repository.
        UniqueConstraint(
            "repository_id", "file_path", name="uq_documents_repository_file_path"
        ),
    )

    def __repr__(self) -> str:
        """Return a debug-friendly representation of the document."""
        return f"<Document id={self.id} file_path={self.file_path!r}>"