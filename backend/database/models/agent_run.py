import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.constants import AgentName, ApplicationStatus
from backend.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.database.models.conversation import Conversation


class AgentRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A single AI agent execution within a conversation.

    Attributes:
        conversation_id: Foreign key to the owning `Conversation`.
        agent_name: Identifier of the agent that was executed.
        model_name: Identifier of the LLM used for this run (e.g. Groq model).
        status: Current lifecycle status of the agent run.
        input_tokens: Number of prompt tokens consumed.
        output_tokens: Number of completion tokens generated.
        execution_time: Wall-clock execution time, in seconds.
        conversation: The `Conversation` this agent run belongs to.
    """

    __tablename__ = "agent_runs"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_name: Mapped[AgentName] = mapped_column(
        SAEnum(
            AgentName,
            name="agent_name",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        index=True,
    )
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ApplicationStatus] = mapped_column(
        SAEnum(
            ApplicationStatus,
            name="agent_run_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=ApplicationStatus.PENDING,
        server_default=ApplicationStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    input_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    execution_time: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ---------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------
    conversation: Mapped["Conversation"] = relationship(back_populates="agent_runs")

    def __repr__(self) -> str:
        """Return a debug-friendly representation of the agent run."""
        return f"<AgentRun id={self.id} agent_name={self.agent_name}>"