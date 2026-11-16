import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from app.api.deps import CurrentUserDep, SessionDep
from app.core import settings
from app.models import ContextNode
from app.repositories.ai import AIRepository
from app.schemas.ai import ReplyRequest, ReplyResponse, AnalysisRequest, MemoryUpdate
from app.services.model_gateway import get_gateway, configured, ModelError
from app.services.ai_workflow import request_slot, reply, analyze

router = APIRouter(tags=["AI"])
GatewayDep = Annotated[object, Depends(get_gateway)]

@router.get("/ai/status")
async def ai_status(user: CurrentUserDep):
    return {"configured": configured(), "provider": "Google Gemini",
            "model": settings.llm_model}

@router.post("/conversations/{conversation_id}/reply", response_model=ReplyResponse)
async def ai_reply(conversation_id: uuid.UUID, payload: ReplyRequest, user: CurrentUserDep, db: SessionDep, gateway: GatewayDep):
    async with request_slot(user.id):
        try:
            return await reply(db, user.id, conversation_id, payload, gateway)
        except ModelError as e:
            raise HTTPException(e.status, str(e)) from None

@router.post("/ai/analyze")
async def ai_analysis(payload: AnalysisRequest, user: CurrentUserDep, db: SessionDep, gateway: GatewayDep):
    async with request_slot(user.id):
        try:
            return await analyze(db, user.id, gateway)
        except ModelError as e:
            raise HTTPException(e.status, str(e)) from None

@router.get("/ai/memories")
async def memories(user: CurrentUserDep, db: SessionDep):
    return await AIRepository(db).memories(user.id)

async def own_node(db, user_id, node_id):
    node = await db.scalar(select(ContextNode).where(ContextNode.id == node_id, ContextNode.user_id == user_id))
    if not node:
        raise HTTPException(404, "Memory not found")
    return node

@router.patch("/ai/memories/{node_id}")
async def edit_memory(node_id: uuid.UUID, payload: MemoryUpdate, user: CurrentUserDep, db: SessionDep):
    node = await own_node(db, user.id, node_id)
    node.label, node.review_status = payload.label.strip(), payload.review_status
    if not node.label:
        raise HTTPException(422, "Memory cannot be empty")
    await db.flush()
    return {"id": node.id, "review_status": node.review_status}

@router.delete("/ai/memories/{node_id}", status_code=204)
async def delete_memory(node_id: uuid.UUID, user: CurrentUserDep, db: SessionDep):
    await db.delete(await own_node(db, user.id, node_id))
    await db.flush()
