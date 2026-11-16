import json
import asyncio
import uuid
import pytest
import httpx
from pydantic import SecretStr
from sqlalchemy import select, func
from app.main import app
from app.core import settings
from app.models import Message, AITurn, ContextNode, Hypothesis
from app.schemas.ai import SafetyDecision, ChatOutput, AnalysisOutput
from app.services.model_gateway import get_gateway, HostedGateway, ModelError
from app.services.ai_workflow import _active, _requests
from conftest import register
from test_integration import conversation, message, P


class FakeGateway:
    def __init__(self):
        self.calls = []
        self.risk = "ordinary"
        self.fail = False
        self.chat = "That sounds like a demanding day. You can take your time putting it into words."
        self.analysis = {"nodes": [], "edges": [], "patterns": []}
        self.before_chat = None

    async def generate(self, instruction, data, schema, max_tokens=None):
        self.calls.append((instruction, data, schema))
        if self.fail:
            raise ModelError("Provider unavailable", 503)
        if schema is SafetyDecision:
            return SafetyDecision(risk=self.risk)
        if schema is AnalysisOutput:
            return AnalysisOutput.model_validate(self.analysis)
        if self.before_chat:
            await self.before_chat()
        return ChatOutput(reply=self.chat)


@pytest.fixture
def gateway():
    _active.clear(); _requests.clear()
    fake = FakeGateway()
    app.dependency_overrides[get_gateway] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_gateway, None)


async def ask(client, cid, mid, **kwargs):
    return await client.post(P+f"/conversations/{cid}/reply", json={"message_id": mid, "consent": True, **kwargs})


async def permissions(client):
    response = await client.patch(P+"/users/me/preferences", json={"memory_allowed": True, "save_context_allowed": True, "reflection_allowed": True})
    assert response.status_code == 200


async def test_explicit_consent_privacy_modes_and_idempotency(client, account, gateway):
    cid = await conversation(client)
    await message(client, cid, "Legacy unshared private message")
    mid = (await message(client, cid, "I had a demanding day", False)).json()["id"]
    assert (await client.post(P+f"/conversations/{cid}/reply", json={"message_id": mid})).status_code == 422
    assert not gateway.calls
    first = await ask(client, cid, mid, use_memory=True)
    assert first.status_code == 200, first.text
    assert len(gateway.calls) == 1
    assert gateway.calls[-1][2] is SafetyDecision
    assert gateway.calls[-1][1] == {"current": "I had a demanding day", "recent": [], "photo_data": None}
    again = await ask(client, cid, mid)
    assert again.json()["message"]["id"] == first.json()["message"]["id"]
    assert len(gateway.calls) == 1
    second = await client.post(P+f"/conversations/{cid}/messages", json={"content": "Help me reflect", "active_mode": "reflection", "memory_allowed": False})
    response = await ask(client, cid, second.json()["id"])
    assert response.status_code == 200
    assert "Deep Reflection" in gateway.calls[-1][0]
    recent = json.dumps(gateway.calls[-1][1]["recent"])
    assert "demanding day" in recent and "Legacy unshared" not in recent


async def test_provider_failure_retry_keeps_writing(client, account, gateway, database):
    cid = await conversation(client)
    mid = (await message(client, cid)).json()["id"]
    gateway.fail = True
    assert (await ask(client, cid, mid)).status_code == 503
    async with database() as db:
        assert (await db.get(AITurn, uuid.UUID(mid))).status == "failed"
        assert await db.scalar(select(func.count()).select_from(Message)) == 1
    gateway.fail = False
    assert (await ask(client, cid, mid)).status_code == 200


async def test_safety_routes_and_rejects_bad_output(client, account, gateway):
    cid = await conversation(client)
    mid = (await message(client, cid, "I am going to kill myself tonight")).json()["id"]
    result = await ask(client, cid, mid)
    assert result.status_code == 200 and result.json()["safety_routed"]
    assert "emergency" in result.json()["message"]["content"] and not gateway.calls
    gateway.risk = "urgent"
    mid = (await message(client, cid, "I cannot keep myself safe")).json()["id"]
    assert (await ask(client, cid, mid)).json()["safety_routed"]
    assert len(gateway.calls) == 1
    gateway.risk = "ordinary"; gateway.chat = "You clearly have bipolar disorder."
    mid = (await message(client, cid, "What does this mean?", mode="reflection")).json()["id"]
    assert (await ask(client, cid, mid)).status_code == 502


async def test_cross_account_read_only_and_revocation(client, account, gateway, database):
    cid = await conversation(client)
    mid = (await message(client, cid, mode="reflection")).json()["id"]
    await register(client, "bob")
    assert (await ask(client, cid, mid)).status_code == 404
    assert not gateway.calls
    await client.post(P+"/auth/login", json={"email": "alice@example.com", "password": "Bridge-Test-42!"})
    async def revoke():
        from app.models import UserPreferences
        async with database() as db:
            pref = await db.get(UserPreferences, uuid.UUID(account["id"]))
            pref.save_history = False
            await db.commit()
    await permissions(client)
    gateway.before_chat = revoke
    assert (await ask(client, cid, mid)).status_code == 409
    rows = (await client.get(P+f"/conversations/{cid}/messages")).json()
    assert len(rows) == 1


async def eligible_sources(client):
    await permissions(client)
    c1, c2 = await conversation(client), await conversation(client)
    ids = [(await message(client, c, f"Work deadlines made me feel tense {i}")).json()["id"] for i,c in enumerate([c1,c1,c2])]
    await message(client, c2, "Never share this", False)
    return c1,c2,ids


async def test_analysis_evidence_review_rejection_and_deletion(client, account, gateway):
    assert (await client.post(P+"/ai/analyze", json={"consent": True})).status_code == 409
    c1,c2,ids = await eligible_sources(client)
    gateway.analysis = {"nodes": [{"kind": "reported_emotion", "label": "Reports tension around work deadlines", "source_ids": ids}],
        "edges": [], "patterns": [{"statement": "Work deadlines may coincide with feeling tense.", "source_ids": ids}]}
    response = await client.post(P+"/ai/analyze", json={"consent": True})
    assert response.status_code == 200, response.text
    assert response.json()["patterns_created"] == 1
    assert "Never share this" not in json.dumps(gateway.calls[-1][1])
    memories = (await client.get(P+"/ai/memories")).json()
    node = memories[0]
    assert node["review_status"] == "unreviewed" and len(node["sources"]) == 3
    assert (await client.patch(P+f"/ai/memories/{node['id']}", json={"label": "Work deadlines feel tense", "review_status": "confirmed"})).status_code == 200
    patterns = (await client.get(P+"/patterns")).json()
    assert len(patterns[0]["evidence"]) == 3
    await client.patch(P+f"/patterns/{patterns[0]['id']}", json={"status": "rejected", "correction": "This was just one busy week."})
    result = await client.post(P+"/ai/analyze", json={"consent": True})
    assert result.json()["patterns_created"] == 0
    assert "just one busy week" in json.dumps(gateway.calls[-1][1])
    # Confirmed context can be retrieved only under both account and turn permission.
    mid = (await message(client, c2, "Work deadlines again", mode="reflection")).json()["id"]
    assert (await ask(client, c2, mid, use_memory=True)).status_code == 200
    assert gateway.calls[-1][1]["reviewed_memory"][0]["text"] == "Work deadlines feel tense"
    await register(client, "bob")
    assert (await client.delete(P+f"/ai/memories/{node['id']}")).status_code == 404
    await client.post(P+"/auth/login", json={"email":"alice@example.com","password":"Bridge-Test-42!"})
    assert (await client.delete(P+f"/conversations/{c1}")).status_code == 204
    assert (await client.get(P+"/ai/memories")).json() == []
    assert (await client.get(P+"/patterns")).json() == []


async def test_analysis_rejects_invented_sources_and_sparse_patterns(client, account, gateway):
    _,_,ids = await eligible_sources(client)
    gateway.analysis["patterns"] = [{"statement":"A tentative idea", "source_ids":[str(uuid.uuid4())]}]
    assert (await client.post(P+"/ai/analyze", json={"consent":True})).status_code == 502
    assert (await client.get(P+"/patterns")).json() == []
    gateway.analysis["patterns"] = [{"statement":"A tentative idea", "source_ids":ids[:2]}]
    result = await client.post(P+"/ai/analyze", json={"consent":True})
    assert result.status_code == 200 and result.json()["patterns_created"] == 0


async def test_gemini_wire_format_validation_and_secret_redaction(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", SecretStr("test-secret-never-log"))
    real_client = httpx.AsyncClient
    requests = []
    def respond(request):
        requests.append(request)
        return httpx.Response(200, json={"candidates":[{"finishReason":"STOP","content":{"parts":[{"thought":True,"text":"do not expose reasoning"},{"text":'{"reply":"A brief acknowledgement."}'}]}}]})
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: real_client(transport=httpx.MockTransport(respond), **kwargs))
    result = await HostedGateway().generate("Listen", {"current":"test"}, ChatOutput)
    assert result.reply == "A brief acknowledgement."
    body = json.loads(requests[0].content)
    assert str(requests[0].url) == "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent"
    assert body["generationConfig"]["responseMimeType"] == "application/json"
    assert requests[0].headers["x-goog-api-key"] == "test-secret-never-log"
    assert "test-secret" not in str(requests[0].url)
    assert json.loads(body["contents"][0]["parts"][0]["text"]) == {"current":"test"}
    assert not any(k in body for k in ["tools", "cachedContent", "safetySettings"])

@pytest.mark.parametrize("body,status", [
    ({"candidates":[{"finishReason":"MAX_TOKENS","content":{"parts":[{"text":'{"reply":"truncated"}'}]}}]},502),
    ({"candidates":[{"finishReason":"STOP","content":{"parts":[{"text":'{"reply":"ok","unexpected":true}'}]}}]},502),
    ({"promptFeedback":{"blockReason":"SAFETY"}},422),
    ({"candidates":[{"finishReason":"SAFETY"}]},422),
    ({"candidates":[]},502),
])
async def test_gemini_invalid_or_blocked_output_not_saved(monkeypatch, body, status):
    monkeypatch.setattr(settings,"gemini_api_key",SecretStr("test"))
    real_client=httpx.AsyncClient
    monkeypatch.setattr(httpx,"AsyncClient",lambda **kwargs: real_client(transport=httpx.MockTransport(lambda request:httpx.Response(200,json=body)),**kwargs))
    with pytest.raises(ModelError) as caught:
        await HostedGateway().generate("Listen",{},ChatOutput)
    assert caught.value.status == status


async def test_duplicate_inflight_request_and_memory_edit(client, account, gateway):
    cid = await conversation(client)
    mid = (await message(client, cid, mode="reflection")).json()["id"]
    started, release = asyncio.Event(), asyncio.Event()
    async def hold():
        started.set()
        await release.wait()
    gateway.before_chat = hold
    task = asyncio.create_task(ask(client, cid, mid))
    try:
        await asyncio.wait_for(started.wait(), 5)
        assert (await ask(client, cid, mid)).status_code == 409
    finally:
        release.set()
    assert (await task).status_code == 200
    assert len(gateway.calls) == 2


async def test_no_key_and_provider_timeout(monkeypatch):
    monkeypatch.setattr(settings,"gemini_api_key",SecretStr(""))
    with pytest.raises(ModelError) as caught:
        await HostedGateway().generate("Listen",{},ChatOutput)
    assert caught.value.status == 503
    monkeypatch.setattr(settings,"gemini_api_key",SecretStr("test"))
    real_client = httpx.AsyncClient
    def timeout(request):
        raise httpx.ReadTimeout("private provider details",request=request)
    monkeypatch.setattr(httpx,"AsyncClient",lambda **kwargs:real_client(transport=httpx.MockTransport(timeout),**kwargs))
    with pytest.raises(ModelError) as caught:
        await HostedGateway().generate("Listen",{},ChatOutput)
    assert caught.value.status == 504 and "private provider details" not in str(caught.value)

async def test_photo_is_sent_as_gemini_image_part(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", SecretStr("test"))
    real_client = httpx.AsyncClient
    captured = {}
    def respond(request):
        captured.update(json.loads(request.content))
        return httpx.Response(200, json={"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": '{"reply":"I see the photo."}'}]}}]})
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: real_client(transport=httpx.MockTransport(respond), **kwargs))
    output = await HostedGateway().generate("Reflect", {"current": "A photo", "photo_data": "data:image/png;base64,cGhvdG8="}, ChatOutput)
    parts = captured["contents"][0]["parts"]
    assert output.reply == "I see the photo."
    assert parts[1]["inlineData"] == {"mimeType": "image/png", "data": "cGhvdG8="}
    assert "photo_data" not in parts[0]["text"]

@pytest.mark.parametrize('upstream,expected', [(400,503),(401,503),(403,503),(404,503),(429,429),(503,502)])
async def test_gemini_provider_errors_redact_secrets(monkeypatch, upstream, expected):
    monkeypatch.setattr(settings, 'gemini_api_key', SecretStr('test-secret-never-log'))
    real_client = httpx.AsyncClient
    requests=[]
    def reject(request):
        requests.append(request)
        return httpx.Response(upstream, json={'error': {'message':'test-secret-never-log'}})
    monkeypatch.setattr(httpx, 'AsyncClient', lambda **kwargs: real_client(transport=httpx.MockTransport(reject), **kwargs))
    with pytest.raises(ModelError) as caught:
        await HostedGateway().generate('Listen', {}, ChatOutput)
    assert caught.value.status == expected
    assert 'test-secret-never-log' not in str(caught.value)
    assert len(requests)==1  # No silent provider fallback or paid retry.
