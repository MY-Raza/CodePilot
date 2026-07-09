import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.database.models.agent_run import AgentRun
    from backend.database.models.user import User


class Conversation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A chat conversation between a user and the AI assistant.

    Attributes:
        user_id: Foreign key to the `User` who owns this conversation.
        title: Short, human-readable title for the conversation.
        user: The `User` who owns this conversation.
        agent_runs: AI agent executions performed within this conversation.
    """

    __tablename__ = "conversations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="New Conversation")

    # ---------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------
    user: Mapped["User"] = relationship(back_populates="conversations")
    agent_runs: Mapped[list["AgentRun"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Return a debug-friendly representation of the conversation."""
        return f"<Conversation id={self.id} title={self.title!r}>"