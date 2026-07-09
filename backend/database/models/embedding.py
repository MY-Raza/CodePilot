import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.database.models.document import Document


class Embedding(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A vector-embedded chunk of a source document.

    Attributes:
        document_id: Foreign key to the owning `Document`.
        chunk_index: Zero-based position of this chunk within the document.
        embedding_model: Identifier of the model used to generate the vector.
        vector_id: ID referencing the corresponding vector in ChromaDB/Qdrant.
        text: The raw text content of this chunk.
        embedding_metadata: Arbitrary JSON metadata (e.g. line ranges, tags).
        document: The `Document` this embedding was derived from.
    """

    __tablename__ = "embeddings"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(255), nullable=False)
    vector_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    # NOTE: Mapped as `embedding_metadata` in Python to avoid colliding with
    # SQLAlchemy's reserved `Base.metadata` attribute; the underlying column
    # name remains "metadata" for schema/API clarity.
    embedding_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )

    # ---------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------
    document: Mapped["Document"] = relationship(back_populates="embeddings")

    def __repr__(self) -> str:
        """Return a debug-friendly representation of the embedding."""
        return f"<Embedding id={self.id} chunk_index={self.chunk_index}>"