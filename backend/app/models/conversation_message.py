from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.conversation_session import JSON_TYPE, UUID_TYPE


class ConversationMessage(Base):
    """Durable user/assistant turns, ordered within a conversation."""

    __tablename__ = "conversation_messages"
    __table_args__ = (
        Index("ix_conversation_messages_session_sequence", "session_id", "sequence", unique=True),
    )

    id: Mapped[str] = mapped_column(UUID_TYPE, primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(
        UUID_TYPE, ForeignKey("conversation_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON_TYPE, nullable=True)

    session: Mapped["ConversationSession"] = relationship(back_populates="messages")
