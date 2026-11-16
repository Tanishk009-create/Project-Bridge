import uuid
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.conversation import MessageResponse

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class ReplyRequest(StrictModel):
    message_id: uuid.UUID
    consent: Literal[True]
    use_memory: bool = False

class ReplyResponse(BaseModel):
    message: MessageResponse
    safety_routed: bool

class AnalysisRequest(StrictModel):
    consent: Literal[True]

class SafetyDecision(StrictModel):
    risk: Literal["ordinary", "urgent"]

class ChatOutput(StrictModel):
    reply: str = Field(min_length=1, max_length=6000)

class ExtractedNode(StrictModel):
    kind: Literal["observation", "user_interpretation", "reported_emotion", "person", "event", "behaviour", "physical_reaction", "context", "goal"]
    label: str = Field(min_length=1, max_length=255)
    source_ids: list[uuid.UUID] = Field(min_length=1, max_length=8)

class ExtractedEdge(StrictModel):
    from_index: int = Field(ge=0)
    to_index: int = Field(ge=0)
    relation: Literal["mentioned_with", "followed_by", "associated_with", "contradicted_by"]

class CandidatePattern(StrictModel):
    statement: str = Field(min_length=1, max_length=500)
    source_ids: list[uuid.UUID] = Field(min_length=1, max_length=12)

class AnalysisOutput(StrictModel):
    nodes: list[ExtractedNode] = Field(max_length=12)
    edges: list[ExtractedEdge] = Field(max_length=12)
    patterns: list[CandidatePattern] = Field(max_length=3)

class MemoryUpdate(StrictModel):
    label: str = Field(min_length=1, max_length=255)
    review_status: Literal["confirmed", "rejected"]

class ReflectionCitation(StrictModel):
    message_id: uuid.UUID
    quote: str = Field(min_length=1, max_length=600)
    explanation: str = Field(min_length=1, max_length=400)

class GroundedReflection(StrictModel):
    observation: str = Field(min_length=1, max_length=500)
    reflection: str = Field(min_length=1, max_length=1600)
    question: str = Field(min_length=1, max_length=300)
    evidence: list[ReflectionCitation] = Field(min_length=1, max_length=5)
