"""Per-message consent and a durable reply lease, independent of memory permission."""
import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class AITurn(Base):
    __tablename__ = "ai_turns"
    message_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    assistant_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="pending")
    lease_id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4)
    consent_version: Mapped[str] = mapped_column(String(24), default="ai-sharing-v1")
    safety_routed: Mapped[bool] = mapped_column(default=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
