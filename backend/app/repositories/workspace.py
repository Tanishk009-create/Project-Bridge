"""Queries for the user's workspace. Every lookup is scoped to its owner."""
import uuid
from sqlalchemy import select, func, literal, union_all, case
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Capture, PassportItem, Reflection, Conversation, Message, Hypothesis
from app.models.hypothesis_evidence import HypothesisEvidence

class WorkspaceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def own(self, model, record_id: uuid.UUID, user_id: uuid.UUID):
        return await self.db.scalar(select(model).where(model.id == record_id, model.user_id == user_id))

    async def list(self, model, user_id: uuid.UUID, limit=100, offset=0):
        return list(await self.db.scalars(select(model).where(model.user_id == user_id)
                    .order_by(model.created_at.desc(), model.id).limit(limit).offset(offset)))

    async def save(self, record):
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)
        return record

    async def delete(self, record):
        await self.db.delete(record)
        await self.db.flush()

    async def history(self, user_id: uuid.UUID, q: str, offset: int, limit: int, kind: str = ""):
        first_message = (select(Message.content).where(Message.conversation_id == Conversation.id)
                         .order_by(Message.created_at, Message.id).limit(1).scalar_subquery())
        rows = union_all(
            select(Conversation.id, literal("conversation").label("type"), Conversation.initial_mode.label("title"),
                   func.coalesce(first_message, "Empty conversation").label("text"), Conversation.started_at.label("created_at"))
                .where(Conversation.user_id == user_id),
            select(Capture.id, literal("quick-capture"), Capture.category, Capture.content, Capture.created_at).where(Capture.user_id == user_id),
            select(Reflection.id, literal("reflection"), case((Reflection.status == "generated", "Conversation reflection"), else_="Personal reflection"), Reflection.content_text, Reflection.created_at).where(Reflection.user_id == user_id),
        ).subquery()
        statement = select(rows)
        if q:
            statement = statement.where(rows.c.text.icontains(q, autoescape=True) | rows.c.title.icontains(q, autoescape=True))
        if kind:
            statement = statement.where(rows.c.type == kind)
        total = await self.db.scalar(select(func.count()).select_from(statement.subquery()))
        counts = dict((await self.db.execute(select(rows.c.type, func.count()).group_by(rows.c.type))).all())
        result = (await self.db.execute(statement.order_by(rows.c.created_at.desc(), rows.c.id).offset(offset).limit(limit))).mappings()
        items = []
        for row in result:
            item = dict(row)
            route = {"conversation": "/conversation", "reflection": "/reflection", "quick-capture": "/notebook"}[item["type"]]
            item["href"] = f"{route}?id={item['id']}"
            items.append(item)
        return {"items": items, "total": total, "counts": counts}

    async def patterns(self, user_id):
        patterns = await self.list(Hypothesis, user_id)
        result = []
        for pattern in patterns:
            evidence = (await self.db.execute(select(Message.id, Message.content, Message.conversation_id)
                .join(HypothesisEvidence, HypothesisEvidence.message_id == Message.id)
                .join(Conversation, Conversation.id == Message.conversation_id)
                .where(HypothesisEvidence.hypothesis_id == pattern.id, Conversation.user_id == user_id,
                       Message.memory_allowed.is_(True)).limit(20))).mappings()
            result.append({"id": pattern.id, "statement_text": pattern.statement_text,
                "status": pattern.status, "created_at": pattern.created_at,
                "user_correction": pattern.user_correction, "evidence": [dict(e) for e in evidence]})
        return result
