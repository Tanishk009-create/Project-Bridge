"""Provenance for generated reflections and user-created in-app reminders."""
import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class ReflectionSource(Base):
    __tablename__ = "reflection_sources"
    reflection_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reflections.id", ondelete="CASCADE"), primary_key=True)
    message_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"), primary_key=True)
    quote: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text)

class Reminder(Base):
    __tablename__ = "reminders"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    reflection_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("reflections.id", ondelete="CASCADE"), nullable=True)
    destination: Mapped[str] = mapped_column(String(32), default="reflection")
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(24), default="scheduled")
    delivery_status: Mapped[str] = mapped_column(String(24), default="pending", server_default="pending")
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
