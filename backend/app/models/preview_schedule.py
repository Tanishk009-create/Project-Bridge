"""Opt-in cadence for evidence-linked Reflection Previews."""
import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class PreviewSchedule(Base):
    __tablename__ = "preview_schedules"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    enabled: Mapped[bool] = mapped_column(default=False)
    cadence_days: Mapped[int] = mapped_column(default=7)
    next_run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_status: Mapped[str] = mapped_column(String(24), default="scheduled")
    last_reflection_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("reflections.id", ondelete="SET NULL"), nullable=True)
