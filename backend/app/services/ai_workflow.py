"""Consent-aware AI orchestration; owns short transactions around remote calls."""
import uuid
import re
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from difflib import SequenceMatcher
from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from app.core import settings
from app.models import AITurn, Conversation, Message, ContextNode, NodeSource, ContextEdge, Hypothesis, HypothesisEvidence
from app.repositories.ai import AIRepository
from app.schemas.ai import AnalysisOutput
from app.services.ai_policy import BASE_POLICY, generate_reply, urgent_risk, validate_reply
from app.services.model_gateway import ModelError

# Development safeguards per process. Production deployments should use a shared limiter.
_active = set()
_requests = defaultdict(deque)

@asynccontextmanager
async def request_slot(user_id):
    now = time.monotonic()
    for key in list(_requests):
        while _requests[key] and _requests[key][0] < now - 60:
            _requests[key].popleft()
        if not _requests[key]:
            del _requests[key]
    if user_id in _active:
        raise HTTPException(409, "An AI request is already running for your account.")
    if len(_active) >= 4 or len(_requests[user_id]) >= 10:
        raise HTTPException(429, "Too many AI requests. Please wait a minute.")
    _requests[user_id].append(now)
    _active.add(user_id)
    try:
        yield
    finally:
        _active.discard(user_id)

async def reply(db, user_id, conversation_id, payload, gateway):
    repo = AIRepository(db)
    source = await repo.message(user_id, conversation_id, payload.message_id)
    conversation = await db.get(Conversation, conversation_id, populate_existing=True)
    if not source or not conversation or conversation.user_id != user_id:
        raise HTTPException(404, "Message not found")
    prefs = await repo.preferences(user_id)
    if conversation.ended_at or (prefs and not prefs.save_history):
        raise HTTPException(409, "This conversation is read-only.")
    turn = await db.get(AITurn, source.id)
    if turn and turn.status == "completed" and turn.assistant_id:
        assistant = await db.get(Message, turn.assistant_id)
        if assistant:
            return {"message": assistant, "safety_routed": turn.safety_routed}
    latest = await db.scalar(select(Message.id).where(Message.conversation_id == conversation_id, Message.sender == "user")
                            .order_by(Message.created_at.desc(), Message.id.desc()).limit(1))
    if latest != source.id:
        raise HTTPException(409, "Request a reply to the latest message in this conversation.")
    lease = uuid.uuid4()
    now = datetime.now(UTC)
    if turn:
        claimed = await db.execute(update(AITurn).where(AITurn.message_id == source.id,
            (AITurn.status == "failed") | ((AITurn.status == "pending") & (AITurn.started_at < now - timedelta(minutes=3))))
            .values(status="pending", lease_id=lease, started_at=now))
        if not claimed.rowcount:
            raise HTTPException(409, "This reply is already being generated. Please wait.")
    else:
        db.add(AITurn(message_id=source.id, user_id=user_id, status="pending", lease_id=lease, started_at=now))
    try:
        await db.commit()  # Publish idempotency claim, release SQLite write lock before network I/O.
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "This reply is already being generated.") from None
    try:
        use_memory = bool(payload.use_memory and source.memory_allowed and prefs and prefs.memory_allowed and prefs.save_context_allowed)
        data = {"current": source.content, "recent": await repo.recent(user_id, conversation_id, source)}
        if source.photo_data:
            data["photo_data"] = source.photo_data
        if use_memory:
            memory_snapshot = await repo.memory(user_id, source.content)
            data.update(memory_snapshot)
        await db.commit()
        text, safety = await generate_reply(gateway, data, source.active_mode)
        # Re-check consent controls/deletion after awaiting the provider; discard if anything changed.
        existing = await repo.message(user_id, conversation_id, source.id)
        prefs_now = await repo.preferences(user_id)
        conversation = await db.get(Conversation, conversation_id, populate_existing=True)
        if not existing or not conversation or conversation.ended_at or (prefs_now and not prefs_now.save_history):
            raise ModelError("The conversation changed while the reply was generated. The reply was discarded.", 409)
        if use_memory and not (prefs_now and prefs_now.memory_allowed and prefs_now.save_context_allowed and existing.memory_allowed):
            raise ModelError("Memory permissions changed. The generated reply was discarded.", 409)
        if use_memory and memory_snapshot != await repo.memory(user_id, existing.content):
            raise ModelError("Saved context changed. The generated reply was discarded; please retry.", 409)
        claimed = await db.execute(update(AITurn).where(AITurn.message_id == source.id, AITurn.lease_id == lease,
            AITurn.status == "pending").values(status="completed", safety_routed=safety))
        if not claimed.rowcount:
            raise ModelError("The reply request expired. Please retry.", 409)
        assistant = Message(conversation_id=conversation_id, sender="assistant", content=text,
            active_mode=source.active_mode, memory_allowed=False, created_at=datetime.now(UTC))
        db.add(assistant)
        await db.flush()
        await db.execute(update(AITurn).where(AITurn.message_id == source.id).values(assistant_id=assistant.id))
        await db.commit()
        return {"message": assistant, "safety_routed": safety}
    except (ModelError, HTTPException):
        await db.rollback()
        await db.execute(update(AITurn).where(AITurn.message_id == payload.message_id, AITurn.lease_id == lease,
            AITurn.status == "pending").values(status="failed"))
        await db.commit()
        raise

def similar(a, b):
    clean = lambda s: re.sub(r"\W+", " ", s.casefold()).removeprefix("possible pattern ").strip()
    return SequenceMatcher(None, clean(a), clean(b)).ratio() > .78

async def analysis_allowed(repo, user_id):
    prefs = await repo.preferences(user_id)
    if not (prefs and prefs.save_history and prefs.memory_allowed and prefs.save_context_allowed and prefs.reflection_allowed):
        raise HTTPException(409, "Enable History, Memory, Context extraction and Reflection in Settings before analysing saved writing.")

async def analyze(db, user_id, gateway):
    repo = AIRepository(db)
    await analysis_allowed(repo, user_id)
    messages = await repo.eligible(user_id)
    if not messages:
        raise HTTPException(409, "No eligible messages. Allow memory and context when saving new conversation messages first.")
    sources = {m.id: m.conversation_id for m in messages}
    previous = await repo.hypotheses(user_id)
    data = {"sources": [{"id": str(m.id), "conversation": str(m.conversation_id), "text": m.content[:2000]} for m in messages],
            "previous_interpretations": [{"statement": h.statement_text, "review": h.status, "correction": h.user_correction} for h in previous]}
    await db.commit()
    if await urgent_risk(gateway, {"current": "", "recent": data["sources"]}):
        raise ModelError("Pattern analysis was paused because the writing may need immediate safety support. Open a conversation for support, or contact local emergency services if there is immediate danger.", 409)
    output = await gateway.generate(BASE_POLICY + """
Extract only explicitly supported context nodes. Separate observations, user interpretations and reported emotions.
Labels are concise attributed descriptions, not diagnoses. Every node and pattern must cite exact supplied source IDs.
Edges reference zero-based node indices, describe supported associations and never imply causation.
Suggest at most 3 tentative recurring patterns, each supported by at least 3 distinct messages across 2 conversations.
Return no patterns if evidence is insufficient. Never repeat a rejected interpretation, including paraphrases; respect corrections.
Do not duplicate previous interpretations. Empty arrays are a valid result. No clinical conclusions.
""", data, AnalysisOutput, max_tokens=8192)
    for item in [*output.nodes, *output.patterns]:
        if not set(item.source_ids) <= sources.keys():
            raise ModelError("Analysis included an unknown source. Nothing was saved; please retry.")
        validate_reply(item.label if hasattr(item, "label") else item.statement)
    if any(e.from_index >= len(output.nodes) or e.to_index >= len(output.nodes) for e in output.edges):
        raise ModelError("Analysis included an invalid context link. Nothing was saved.")
    await analysis_allowed(repo, user_id)
    now_sources = {m.id for m in await repo.eligible(user_id)}
    if not sources.keys() <= now_sources:
        raise ModelError("Source writing changed during analysis. Nothing was saved; please retry.", 409)
    # Read reviews again: a rejection made during the remote call still applies.
    previous = await repo.hypotheses(user_id)
    old_nodes = list(await db.scalars(select(ContextNode).where(ContextNode.user_id == user_id)))
    nodes = []
    count_nodes = count_patterns = 0
    for candidate in output.nodes:
        node = next((n for n in old_nodes if n.node_type == candidate.kind and similar(n.label, candidate.label)), None)
        if node is None:
            node = ContextNode(user_id=user_id, node_type=candidate.kind, label=candidate.label, review_status="unreviewed")
            db.add(node)
            await db.flush()
            for source_id in set(candidate.source_ids):
                db.add(NodeSource(node_id=node.id, message_id=source_id))
            old_nodes.append(node)
            count_nodes += 1
        nodes.append(node)
    for edge in output.edges:
        a, b = nodes[edge.from_index], nodes[edge.to_index]
        if a.id == b.id or a.review_status == "rejected" or b.review_status == "rejected":
            continue
        exists = await db.scalar(select(ContextEdge.id).where(ContextEdge.from_node_id == a.id,
            ContextEdge.to_node_id == b.id, ContextEdge.relation_type == edge.relation))
        if not exists:
            db.add(ContextEdge(from_node_id=a.id, to_node_id=b.id, relation_type=edge.relation))
            await db.flush()
    for candidate in output.patterns:
        ids = set(candidate.source_ids)
        if len(ids) < settings.pattern_min_messages or len({sources[i] for i in ids}) < settings.pattern_min_conversations:
            continue
        if any(similar(candidate.statement, h.statement_text) for h in previous):
            continue
        pattern = Hypothesis(user_id=user_id, statement_text="Possible pattern: " + candidate.statement, status="pending")
        db.add(pattern)
        await db.flush()
        for source_id in ids:
            db.add(HypothesisEvidence(hypothesis_id=pattern.id, message_id=source_id, evidence_role="supporting"))
        previous.append(pattern)
        count_patterns += 1
    await db.commit()
    return {"nodes_created": count_nodes, "patterns_created": count_patterns,
            "messages_considered": len(sources), "notice": "Review suggestions before using them. No pattern is a diagnosis or established fact."}
