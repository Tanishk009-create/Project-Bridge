"""Owner-scoped AI context queries. Transactions belong to the service/routes."""
from sqlalchemy import select, delete
from app.models import (Conversation, Message, UserPreferences, AITurn, ContextNode,
                        NodeSource, Hypothesis, HypothesisEvidence, PassportItem, Reflection, ReflectionSource)


class AIRepository:
    def __init__(self, db):
        self.db = db

    async def preferences(self, user_id):
        return await self.db.get(UserPreferences, user_id, populate_existing=True)

    async def message(self, user_id, conversation_id, message_id):
        return await self.db.scalar(select(Message).join(Conversation).where(
            Conversation.user_id == user_id, Conversation.id == conversation_id,
            Message.id == message_id, Message.sender == "user").execution_options(populate_existing=True))

    async def eligible(self, user_id):
        return list(await self.db.scalars(select(Message).join(Conversation).where(
            Conversation.user_id == user_id, Message.sender == "user", Message.memory_allowed.is_(True))
            .order_by(Message.created_at.desc(), Message.id).limit(30)))

    async def recent(self, user_id, conversation_id, before):
        turns = (await self.db.execute(select(Message, AITurn.assistant_id).join(AITurn, AITurn.message_id == Message.id)
            .where(AITurn.user_id == user_id, AITurn.status == "completed", Message.conversation_id == conversation_id,
                   Message.id != before.id, Message.created_at <= before.created_at)
            .order_by(Message.created_at.desc(), Message.id).limit(6))).all()
        result = []
        for message, assistant_id in reversed(turns):
            result.append({"role": "user", "text": message.content[:4000]})
            assistant = await self.db.get(Message, assistant_id) if assistant_id else None
            if assistant and message.active_mode != "mind-dump":
                result.append({"role": "assistant", "text": assistant.content[:2000]})
        return result

    async def memory(self, user_id, current):
        nodes = list(await self.db.scalars(select(ContextNode).where(ContextNode.user_id == user_id,
            ContextNode.review_status == "confirmed").order_by(ContextNode.id).limit(200)))
        # Small lexical retrieval, with a deterministic cap; never submit an entire history.
        words = set(current.casefold().split())
        nodes.sort(key=lambda n: len(words & set(n.label.casefold().split())), reverse=True)
        valid = []
        for node in nodes:
            source = await self.db.scalar(select(Message.id).join(NodeSource, NodeSource.message_id == Message.id)
                .join(Conversation).where(NodeSource.node_id == node.id, Conversation.user_id == user_id,
                    Message.memory_allowed.is_(True)).limit(1))
            if source and words & set(node.label.casefold().split()):
                valid.append({"kind": node.node_type, "text": node.label})
            if len(valid) == 8:
                break
        passport = list(await self.db.scalars(select(PassportItem).where(PassportItem.user_id == user_id,
            PassportItem.use_in_conversations.is_(True)).order_by(PassportItem.created_at.desc()).limit(8)))
        reviews = await self.hypotheses(user_id)
        return {"reviewed_memory": valid, "passport": [{"title": p.title, "text": p.description} for p in passport],
                "interpretation_corrections": [{"statement": h.statement_text, "review": h.status, "correction": h.user_correction}
                    for h in reviews if h.status in {"rejected", "partly", "unsure"}]}

    async def hypotheses(self, user_id):
        return list(await self.db.scalars(select(Hypothesis).where(Hypothesis.user_id == user_id)
                    .order_by(Hypothesis.created_at.desc()).limit(200)))

    async def memories(self, user_id):
        nodes = list(await self.db.scalars(select(ContextNode).where(ContextNode.user_id == user_id)
                    .order_by(ContextNode.id).limit(200)))
        result = []
        for node in nodes:
            sources = (await self.db.execute(select(Message.id, Message.content, Message.conversation_id)
                .join(NodeSource, NodeSource.message_id == Message.id).join(Conversation)
                .where(NodeSource.node_id == node.id, Conversation.user_id == user_id))).mappings()
            result.append({"id": node.id, "kind": node.node_type, "label": node.label,
                           "review_status": node.review_status, "sources": [dict(s) for s in sources]})
        return result

    async def forget_conversation(self, user_id, conversation_id):
        messages = select(Message.id).where(Message.conversation_id == conversation_id)
        nodes = select(NodeSource.node_id).where(NodeSource.message_id.in_(messages))
        patterns = select(HypothesisEvidence.hypothesis_id).where(
            HypothesisEvidence.message_id.in_(messages) | HypothesisEvidence.node_id.in_(nodes))
        reflections = select(ReflectionSource.reflection_id).where(ReflectionSource.message_id.in_(messages))
        await self.db.execute(delete(Reflection).where(Reflection.user_id == user_id, Reflection.id.in_(reflections)))
        await self.db.execute(delete(Hypothesis).where(Hypothesis.user_id == user_id, Hypothesis.id.in_(patterns)))
        await self.db.execute(delete(ContextNode).where(ContextNode.user_id == user_id, ContextNode.id.in_(nodes)))
