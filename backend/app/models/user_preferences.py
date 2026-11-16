import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User

# Used until the user saves their own preferences: every pipeline is opt-in.
DEFAULT_PREFERENCES = {
    "default_mode": "mind-dump",
    "memory_allowed": False,
    "reflection_allowed": False,
    "notification_enabled": False,
    "notification_email_enabled": False,
    "save_history": True,
    "save_context_allowed": False,
    "dark_mode": False,
    "reduced_motion": False,
    "text_size": "comfortable",
    "onboarding_complete": False,
}


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    # 1:1 with User, so the FK is also the primary key.
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    default_mode: Mapped[str] = mapped_column(String(32))
    memory_allowed: Mapped[bool]
    reflection_allowed: Mapped[bool]
    notification_enabled: Mapped[bool]
    notification_email_enabled: Mapped[bool] = mapped_column(default=False, server_default="0")
    save_history: Mapped[bool] = mapped_column(default=True, server_default="1")
    save_context_allowed: Mapped[bool] = mapped_column(default=False, server_default="0")
    dark_mode: Mapped[bool] = mapped_column(default=False, server_default="0")
    reduced_motion: Mapped[bool] = mapped_column(default=False, server_default="0")
    text_size: Mapped[str] = mapped_column(String(32), default="comfortable", server_default="comfortable")
    onboarding_complete: Mapped[bool] = mapped_column(default=False, server_default="0")

    user: Mapped["User"] = relationship(back_populates="preferences")
