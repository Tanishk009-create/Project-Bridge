import uuid
from datetime import datetime
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator
from app.schemas.photo import validate_photo

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]

class CaptureInput(BaseModel):
    content: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20000)]
    category: Literal["Thought", "Idea", "Moment", "Note"] = "Thought"
    analysis_allowed: bool = False
    photo_data: str | None = None

    @field_validator("photo_data")
    @classmethod
    def photo_is_valid(cls, value: str | None) -> str | None:
        return validate_photo(value)

class CaptureResponse(CaptureInput):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime

class PassportInput(BaseModel):
    section: Literal["matters", "support"]
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
    description: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
    use_in_conversations: bool = False
    use_for_patterns: bool = False
    allow_reflections: bool = False

class PassportResponse(PassportInput):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime

class ReflectionInput(BaseModel):
    content_text: Text
    hypothesis_id: uuid.UUID | None = None

class ReflectionResponse(ReflectionInput):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    status: str
    created_at: datetime

class PatternReview(BaseModel):
    status: Literal["confirmed", "partly", "rejected", "unsure"]
    correction: str | None = Field(default=None, max_length=2000)

class PatternResponse(BaseModel):
    id: uuid.UUID
    statement_text: str
    status: str
    created_at: datetime
    user_correction: str | None
    evidence: list[dict]

class HistoryEntry(BaseModel):
    id: uuid.UUID
    type: str
    title: str
    text: str
    created_at: datetime
    href: str

class HistoryResponse(BaseModel):
    items: list[HistoryEntry]
    total: int
    counts: dict[str, int]
