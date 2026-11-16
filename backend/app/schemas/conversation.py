import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator
from app.schemas.photo import validate_photo

# Allowed modes aren't decided yet: any stripped, non-empty string that fits String(32).
Mode = Literal["mind-dump", "reflection"]


class ConversationCreateRequest(BaseModel):
    initial_mode: Mode


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    started_at: datetime
    ended_at: datetime | None
    initial_mode: str


class MessageCreateRequest(BaseModel):
    """A message from the user; the server sets `sender`."""

    content: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20000)]
    active_mode: Mode
    memory_allowed: bool
    photo_data: str | None = None

    @field_validator("photo_data")
    @classmethod
    def photo_is_valid(cls, value: str | None) -> str | None:
        return validate_photo(value)


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    sender: str
    content: str
    created_at: datetime
    active_mode: str
    memory_allowed: bool
    photo_data: str | None = None
