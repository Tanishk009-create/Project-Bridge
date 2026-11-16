import uuid
from datetime import UTC, datetime
from typing import Annotated
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from app.api.deps import CurrentUserDep, WorkspaceRepoDep, UserRepoDep
from app.models import Capture, PassportItem, Reflection, Hypothesis, DEFAULT_PREFERENCES, UserPreferences
from app.schemas.workspace import (CaptureInput, CaptureResponse, PassportInput, PassportResponse,
    ReflectionInput, ReflectionResponse, PatternReview, PatternResponse, HistoryResponse)

router = APIRouter(tags=["workspace"])
Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0)]

class OnboardingInput(BaseModel):
    primer: str = Field(default="", max_length=500)

@router.post("/onboarding")
async def onboarding(payload: OnboardingInput, user: CurrentUserDep, repo: WorkspaceRepoDep, users: UserRepoDep):
    prefs = await users.get_preferences(user.id)
    if prefs and prefs.onboarding_complete:
        return {"complete": True}
    if payload.primer.strip():
        await repo.save(PassportItem(user_id=user.id, section="support", title="My context primer", description=payload.primer.strip(),
                       use_in_conversations=False, use_for_patterns=False, allow_reflections=False))
    prefs = prefs or UserPreferences(user_id=user.id, **DEFAULT_PREFERENCES)
    prefs.onboarding_complete = True
    await users.save_preferences(prefs)
    return {"complete": True}

async def own(repo, model, record_id, user_id):
    record = await repo.own(model, record_id, user_id)
    if record is None:
        raise HTTPException(404, "Item not found")
    return record

@router.get("/capabilities")
async def capabilities():
    from app.services.model_gateway import configured
    from app.core import settings
    return {"ai_responses": configured(), "pattern_generation": configured(), "attachments": True,
            "email_verification": settings.mail_mode != "disabled",
            "password_recovery": settings.mail_mode != "disabled",
            "notification_delivery": settings.mail_mode == "smtp",
            "mail_delivery_mode": settings.mail_mode,
            "scheduled_reflection_preview": True}

@router.get("/history", response_model=HistoryResponse)
async def history(user: CurrentUserDep, repo: WorkspaceRepoDep, q: str = "", offset: Offset = 0, limit: Limit = 50, kind: str = ""):
    if kind not in {"", "conversation", "quick-capture", "reflection"}:
        raise HTTPException(422,"Unknown history type")
    return await repo.history(user.id, q[:500], offset, limit, kind)

@router.post("/captures", response_model=CaptureResponse, status_code=201)
async def create_capture(payload: CaptureInput, user: CurrentUserDep, repo: WorkspaceRepoDep, users: UserRepoDep):
    prefs = await users.get_preferences(user.id)
    permitted = bool(prefs and prefs.memory_allowed and prefs.save_context_allowed and prefs.reflection_allowed)
    return await repo.save(Capture(user_id=user.id, **{**payload.model_dump(), "analysis_allowed": payload.analysis_allowed and permitted}))

@router.get("/captures", response_model=list[CaptureResponse])
async def captures(user: CurrentUserDep, repo: WorkspaceRepoDep, offset: Offset = 0, limit: Limit = 50):
    return await repo.list(Capture, user.id, limit, offset)

@router.get("/captures/{record_id}", response_model=CaptureResponse)
async def capture(record_id: uuid.UUID, user: CurrentUserDep, repo: WorkspaceRepoDep):
    return await own(repo, Capture, record_id, user.id)

@router.patch("/captures/{record_id}", response_model=CaptureResponse)
async def edit_capture(record_id: uuid.UUID, payload: CaptureInput, user: CurrentUserDep, repo: WorkspaceRepoDep, users: UserRepoDep):
    record = await own(repo, Capture, record_id, user.id)
    prefs = await users.get_preferences(user.id)
    for key, value in payload.model_dump().items():
        setattr(record, key, value)
    record.analysis_allowed = bool(payload.analysis_allowed and prefs and prefs.memory_allowed and prefs.save_context_allowed and prefs.reflection_allowed)
    return await repo.save(record)

@router.delete("/captures/{record_id}", status_code=204)
async def delete_capture(record_id: uuid.UUID, user: CurrentUserDep, repo: WorkspaceRepoDep):
    await repo.delete(await own(repo, Capture, record_id, user.id))

@router.get("/passport", response_model=list[PassportResponse])
async def passport(user: CurrentUserDep, repo: WorkspaceRepoDep, offset: Offset = 0, limit: Limit = 100):
    return await repo.list(PassportItem, user.id, limit, offset)

@router.post("/passport", response_model=PassportResponse, status_code=201)
async def create_passport_item(payload: PassportInput, user: CurrentUserDep, repo: WorkspaceRepoDep):
    return await repo.save(PassportItem(user_id=user.id, **payload.model_dump()))

@router.patch("/passport/{record_id}", response_model=PassportResponse)
async def edit_passport_item(record_id: uuid.UUID, payload: PassportInput, user: CurrentUserDep, repo: WorkspaceRepoDep):
    record = await own(repo, PassportItem, record_id, user.id)
    for key, value in payload.model_dump().items():
        setattr(record, key, value)
    return await repo.save(record)

@router.delete("/passport/{record_id}", status_code=204)
async def delete_passport_item(record_id: uuid.UUID, user: CurrentUserDep, repo: WorkspaceRepoDep):
    await repo.delete(await own(repo, PassportItem, record_id, user.id))

@router.post("/reflections", response_model=ReflectionResponse, status_code=201)
async def create_reflection(payload: ReflectionInput, user: CurrentUserDep, repo: WorkspaceRepoDep):
    if payload.hypothesis_id:
        await own(repo, Hypothesis, payload.hypothesis_id, user.id)
    return await repo.save(Reflection(user_id=user.id, **payload.model_dump(), status="saved"))

@router.get("/reflections/{record_id}", response_model=ReflectionResponse)
async def reflection(record_id: uuid.UUID, user: CurrentUserDep, repo: WorkspaceRepoDep):
    return await own(repo, Reflection, record_id, user.id)

@router.patch("/reflections/{record_id}", response_model=ReflectionResponse)
async def edit_reflection(record_id: uuid.UUID, payload: ReflectionInput, user: CurrentUserDep, repo: WorkspaceRepoDep):
    record = await own(repo, Reflection, record_id, user.id)
    if record.status == "generated":
        raise HTTPException(409, "Generated reflections are read-only. Save a personal response instead.")
    if payload.hypothesis_id:
        await own(repo, Hypothesis, payload.hypothesis_id, user.id)
    record.content_text, record.hypothesis_id = payload.content_text, payload.hypothesis_id
    return await repo.save(record)

@router.delete("/reflections/{record_id}", status_code=204)
async def delete_reflection(record_id: uuid.UUID, user: CurrentUserDep, repo: WorkspaceRepoDep):
    await repo.delete(await own(repo, Reflection, record_id, user.id))

@router.get("/patterns", response_model=list[PatternResponse])
async def patterns(user: CurrentUserDep, repo: WorkspaceRepoDep):
    return await repo.patterns(user.id)

@router.patch("/patterns/{record_id}")
async def review_pattern(record_id: uuid.UUID, payload: PatternReview, user: CurrentUserDep, repo: WorkspaceRepoDep):
    record = await own(repo, Hypothesis, record_id, user.id)
    record.status, record.user_correction = payload.status, payload.correction
    record.reviewed_at = datetime.now(UTC)
    await repo.save(record)
    return {"id": record.id, "status": record.status, "correction": record.user_correction}
