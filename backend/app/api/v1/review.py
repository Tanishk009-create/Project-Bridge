import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, AwareDatetime, ConfigDict
from sqlalchemy import select
from app.api.deps import CurrentUserDep, SessionDep
from app.api.v1.ai import GatewayDep
from app.models import Conversation, Message, Reflection, ReflectionSource, Reminder, PreviewSchedule
from app.repositories.ai import AIRepository
from app.schemas.ai import AnalysisRequest, GroundedReflection
from app.services.ai_workflow import request_slot, analysis_allowed
from app.services.ai_policy import BASE_POLICY, urgent_risk, validate_reply
from app.services.model_gateway import ModelError

router = APIRouter(tags=["reflection and reminders"])

async def reflection_view(db, record):
    evidence = (await db.execute(select(ReflectionSource.message_id, ReflectionSource.quote,
        ReflectionSource.explanation, Message.conversation_id, Message.created_at)
        .join(Message, Message.id == ReflectionSource.message_id).join(Conversation)
        .where(ReflectionSource.reflection_id == record.id, Conversation.user_id == record.user_id))).mappings()
    return {"id": record.id, "content_text": record.content_text, "status": record.status,
        "created_at": record.created_at, "hypothesis_id": record.hypothesis_id, "evidence": [dict(e) for e in evidence]}

@router.get("/reflection-review")
async def reflection_reviews(user: CurrentUserDep, db: SessionDep):
    records = list(await db.scalars(select(Reflection).where(Reflection.user_id == user.id)
                    .order_by(Reflection.created_at.desc(), Reflection.id).limit(100)))
    return [await reflection_view(db, record) for record in records]

@router.get("/reflection-review/{record_id}")
async def reflection_detail(record_id:uuid.UUID,user:CurrentUserDep,db:SessionDep):
    record=await db.scalar(select(Reflection).where(Reflection.id==record_id,Reflection.user_id==user.id))
    if not record:raise HTTPException(404,"Reflection not found")
    return await reflection_view(db,record)

@router.post("/conversations/{conversation_id}/reflection", status_code=201)
async def generate_reflection(conversation_id: uuid.UUID, payload: AnalysisRequest,
                              user: CurrentUserDep, db: SessionDep, gateway: GatewayDep, scheduled: bool = False):
    async with request_slot(user.id):
        repo = AIRepository(db)
        own = await db.scalar(select(Conversation.id).where(Conversation.id == conversation_id, Conversation.user_id == user.id))
        if not own:
            raise HTTPException(404, "Conversation not found")
        await analysis_allowed(repo, user.id)
        messages = list(await db.scalars(select(Message).where(Message.conversation_id == conversation_id,
            Message.sender == "user", Message.memory_allowed.is_(True)).order_by(Message.created_at.desc()).limit(20)))
        if not messages:
            raise HTTPException(409, "This conversation has no messages saved with memory and context permission.")
        sources = {m.id: m.content[:4000] for m in messages}
        data = {"sources": [{"id":str(mid), "text":content} for mid,content in sources.items()]}
        await db.commit()
        try:
            if await urgent_risk(gateway, {"current":"", "recent":data["sources"]}):
                raise ModelError("Reflection is paused because this writing may need immediate safety support. If there is immediate danger, contact local emergency services or someone you trust nearby.",409)
            output = await gateway.generate(BASE_POLICY + """
Create one tentative reflection on THIS conversation, not a cross-conversation pattern or diagnosis.
Distinguish what the person reported from possible interpretations. Include one optional open question.
Every substantive interpretation must be supported by the evidence you return. Copy each quote EXACTLY from
the supplied source text and use that source's exact ID. Explain how each quote supports the reflection,
without claiming causation. Do not invent words, facts, identities or emotions. Return between 1 and 5 citations.
""",data,GroundedReflection,max_tokens=8192)
            for citation in output.evidence:
                if citation.message_id not in sources or citation.quote not in sources[citation.message_id]:
                    raise ModelError("The reflection included a quote that did not match your writing. Nothing was saved; please retry.")
                validate_reply(citation.explanation)
            content = "\n\n".join(validate_reply(v) for v in [output.observation,output.reflection,output.question])
            await analysis_allowed(repo,user.id)
            allowed = set(await db.scalars(select(Message.id).join(Conversation).where(Conversation.user_id == user.id,
                Conversation.id == conversation_id, Message.id.in_(sources), Message.memory_allowed.is_(True))))
            if set(sources) != allowed:
                raise ModelError("The source writing changed. The reflection was discarded.",409)
            if scheduled:
                schedule = await db.get(PreviewSchedule, user.id, populate_existing=True)
                if not schedule or not schedule.enabled:
                    raise ModelError("Scheduled previews were turned off. The generated reflection was discarded.",409)
            record=Reflection(user_id=user.id,content_text=content,status="preview" if scheduled else "generated",hypothesis_id=None)
            db.add(record);await db.flush()
            seen=set()
            for citation in output.evidence:
                if citation.message_id in seen:continue
                seen.add(citation.message_id)
                db.add(ReflectionSource(reflection_id=record.id, message_id=citation.message_id,
                    quote=citation.quote,explanation=citation.explanation))
            await db.flush()
            return await reflection_view(db,record)
        except ModelError as e:
            raise HTTPException(e.status,str(e)) from None

class ReminderInput(BaseModel):
    model_config=ConfigDict(extra="forbid")
    scheduled_at: AwareDatetime
    destination: Literal["reflection","notebook","conversation"]="reflection"
    reflection_id: uuid.UUID | None = None

class ReminderUpdate(BaseModel):
    model_config=ConfigDict(extra="forbid")
    status: Literal["completed","scheduled"]

def reminder_view(r):
    return {"id":r.id,"scheduled_at":r.scheduled_at,"status":r.status,"destination":r.destination,"reflection_id":r.reflection_id,
        "title":"A moment for your Bridge space", "delivery_status":r.delivery_status}

@router.get("/reminders")
async def reminders(user: CurrentUserDep,db: SessionDep):
    records=await db.scalars(select(Reminder).where(Reminder.user_id==user.id).order_by(Reminder.scheduled_at).limit(100))
    return [reminder_view(r) for r in records]

@router.post("/reminders",status_code=201)
async def add_reminder(payload: ReminderInput,user: CurrentUserDep,db: SessionDep):
    if payload.scheduled_at <= datetime.now(UTC):
        raise HTTPException(422,"Choose a future date and time.")
    prefs=await AIRepository(db).preferences(user.id)
    if not (prefs and prefs.notification_enabled):
        raise HTTPException(409,"Enable in-app reminders in Settings first.")
    if payload.reflection_id and not await db.scalar(select(Reflection.id).where(Reflection.id==payload.reflection_id,Reflection.user_id==user.id)):
        raise HTTPException(404,"Reflection not found")
    record=Reminder(user_id=user.id,**payload.model_dump(),status="scheduled")
    db.add(record);await db.flush()
    return reminder_view(record)

async def own_reminder(db,user_id,record_id):
    record=await db.scalar(select(Reminder).where(Reminder.id==record_id,Reminder.user_id==user_id))
    if not record:raise HTTPException(404,"Reminder not found")
    return record

@router.patch("/reminders/{record_id}")
async def update_reminder(record_id:uuid.UUID,payload:ReminderUpdate,user:CurrentUserDep,db:SessionDep):
    record=await own_reminder(db,user.id,record_id);record.status=payload.status;await db.flush()
    return reminder_view(record)

@router.delete("/reminders/{record_id}",status_code=204)
async def delete_reminder(record_id:uuid.UUID,user:CurrentUserDep,db:SessionDep):
    await db.delete(await own_reminder(db,user.id,record_id));await db.flush()

@router.post("/reminders/{record_id}/retry-delivery")
async def retry_reminder_delivery(record_id:uuid.UUID,user:CurrentUserDep,db:SessionDep):
    record=await own_reminder(db,user.id,record_id)
    if record.status!="scheduled" or record.delivery_status!="failed":
        raise HTTPException(409,"Only a failed, active email delivery can be retried.")
    record.delivery_status="pending"
    await db.flush()
    return reminder_view(record)

class PreviewScheduleInput(BaseModel):
    model_config=ConfigDict(extra="forbid")
    enabled: bool
    cadence_days: Literal[7,14,30]=7

def preview_schedule_view(record):
    if not record:
        return {"enabled":False,"cadence_days":7,"next_run_at":None,"last_run_at":None,
                "last_status":"not-scheduled","last_reflection_id":None}
    return {"enabled":record.enabled,"cadence_days":record.cadence_days,"next_run_at":record.next_run_at,
            "last_run_at":record.last_run_at,"last_status":record.last_status,
            "last_reflection_id":record.last_reflection_id}

@router.get("/reflection-preview/schedule")
async def get_preview_schedule(user:CurrentUserDep,db:SessionDep):
    return preview_schedule_view(await db.get(PreviewSchedule,user.id))

@router.post("/reflection-preview/{record_id}/keep")
async def keep_preview(record_id:uuid.UUID,user:CurrentUserDep,db:SessionDep):
    record=await db.scalar(select(Reflection).where(Reflection.id==record_id,Reflection.user_id==user.id))
    if not record:raise HTTPException(404,"Reflection Preview not found")
    if record.status!="preview":raise HTTPException(409,"Only a pending preview can be kept.")
    record.status="generated"
    await db.flush()
    return await reflection_view(db,record)

@router.delete("/reflection-preview/{record_id}",status_code=204)
async def dismiss_preview(record_id:uuid.UUID,user:CurrentUserDep,db:SessionDep):
    record=await db.scalar(select(Reflection).where(Reflection.id==record_id,Reflection.user_id==user.id))
    if not record:raise HTTPException(404,"Reflection Preview not found")
    if record.status!="preview":raise HTTPException(409,"Only a pending preview can be dismissed.")
    await db.delete(record)
    await db.flush()

@router.put("/reflection-preview/schedule")
async def set_preview_schedule(payload:PreviewScheduleInput,user:CurrentUserDep,db:SessionDep):
    prefs=await AIRepository(db).preferences(user.id)
    if payload.enabled and not (prefs and prefs.save_history and prefs.memory_allowed and
                                prefs.save_context_allowed and prefs.reflection_allowed):
        raise HTTPException(409,"Enable History, Memory, Context extraction and Reflection before scheduling previews.")
    record=await db.get(PreviewSchedule,user.id)
    if not record:
        record=PreviewSchedule(user_id=user.id,enabled=payload.enabled,cadence_days=payload.cadence_days,
            next_run_at=datetime.now(UTC)+timedelta(days=payload.cadence_days),last_status="scheduled")
        db.add(record)
    else:
        record.enabled=payload.enabled
        record.cadence_days=payload.cadence_days
        record.next_run_at=datetime.now(UTC)+timedelta(days=payload.cadence_days)
        record.last_status="scheduled" if payload.enabled else "paused"
    await db.flush()
    return preview_schedule_view(record)
