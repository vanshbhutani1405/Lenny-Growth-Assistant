from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, JSON, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


UUID_TYPE = UUID(as_uuid=False).with_variant(String(36), "sqlite")
JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


class ConversationSession(Base):
    """Durable conversation metadata; transcript data is stored separately."""

    __tablename__ = "conversation_sessions"

    id: Mapped[str] = mapped_column(UUID_TYPE, primary_key=True, default=lambda: str(uuid4()))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    user_metadata: Mapped[dict | None] = mapped_column(JSON_TYPE, nullable=True)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    workflow: Mapped[str | None] = mapped_column(String(64), nullable=True)

    messages: Mapped[list["ConversationMessage"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="ConversationMessage.sequence"
    )
