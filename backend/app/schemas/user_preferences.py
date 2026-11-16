import uuid
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, field_validator

class UserPreferencesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: uuid.UUID
    default_mode: str
    memory_allowed: bool
    reflection_allowed: bool
    notification_enabled: bool
    notification_email_enabled: bool
    save_history: bool
    save_context_allowed: bool
    dark_mode: bool
    reduced_motion: bool
    text_size: str
    onboarding_complete: bool

class UserPreferencesUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    default_mode: Literal["mind-dump", "reflection"] | None = None
    memory_allowed: bool | None = None
    reflection_allowed: bool | None = None
    notification_enabled: bool | None = None
    notification_email_enabled: bool | None = None
    save_history: bool | None = None
    save_context_allowed: bool | None = None
    dark_mode: bool | None = None
    reduced_motion: bool | None = None
    text_size: Literal["small", "comfortable", "large"] | None = None
    onboarding_complete: bool | None = None

    @field_validator("*")
    @classmethod
    def not_null(cls, value: Any) -> Any:
        if value is None:
            raise ValueError("Can't be null")
        return value
