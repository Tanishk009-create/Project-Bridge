"""User-authored records, separate from AI-extracted context and hypotheses."""
import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class Capture(Base):
    __tablename__ = "captures"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    content: Mapped[str] = mapped_column(Text)
    photo_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(32))
    analysis_allowed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class PassportItem(Base):
    __tablename__ = "passport_items"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    section: Mapped[str] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(Text)
    use_in_conversations: Mapped[bool] = mapped_column(default=False)
    use_for_patterns: Mapped[bool] = mapped_column(default=False)
    allow_reflections: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
