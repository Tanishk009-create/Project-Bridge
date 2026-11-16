import uuid
import base64
from datetime import UTC, datetime, timedelta
import pytest
from sqlalchemy import select, func, create_engine, text, inspect
from app.models import Message, Hypothesis, HypothesisEvidence, RefreshToken
from app.core import settings
from app.core.jwt import verify_token
from conftest import register
from app.sqlite_upgrade import add_photo_columns, add_account_and_delivery_columns

P = '/api/v1'

def test_existing_sqlite_photo_upgrade_preserves_data():
    engine = create_engine('sqlite:///:memory:')
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE captures (id TEXT PRIMARY KEY, content TEXT NOT NULL)'))
        connection.execute(text('CREATE TABLE messages (id TEXT PRIMARY KEY, content TEXT NOT NULL)'))
        connection.execute(text("INSERT INTO captures VALUES ('first', 'existing writing')"))
        add_photo_columns(connection)
        add_photo_columns(connection)
        assert connection.execute(text("SELECT content FROM captures WHERE id='first'")).scalar_one() == 'existing writing'
        assert 'photo_data' in {column['name'] for column in inspect(connection).get_columns('captures')}
        assert 'photo_data' in {column['name'] for column in inspect(connection).get_columns('messages')}
    engine.dispose()

def test_existing_sqlite_account_upgrade_preserves_users():
    engine = create_engine('sqlite:///:memory:')
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE users (id TEXT PRIMARY KEY, email TEXT NOT NULL)'))
        connection.execute(text('CREATE TABLE user_preferences (user_id TEXT PRIMARY KEY)'))
        connection.execute(text('CREATE TABLE reminders (id TEXT PRIMARY KEY, status TEXT NOT NULL)'))
        connection.execute(text("INSERT INTO users VALUES ('first', 'legacy@example.com')"))
        add_account_and_delivery_columns(connection)
        add_account_and_delivery_columns(connection)
        assert connection.execute(text("SELECT email_verified_at FROM users WHERE id='first'")).scalar_one()
        assert 'notification_email_enabled' in {c['name'] for c in inspect(connection).get_columns('user_preferences')}
        assert 'delivery_status' in {c['name'] for c in inspect(connection).get_columns('reminders')}
    engine.dispose()

async def test_authentication_and_cookie_lifecycle(client):
    assert (await client.get(P + '/users/me')).status_code == 401
    await register(client)
    assert (await client.get(P + '/users/me')).json()['username'] == 'alice'
    response = await client.post(P + '/auth/login', json={'username': 'alice', 'password': 'wrong'})
    assert response.status_code == 401
    response = await client.post(P + '/auth/login', json={'username': 'alice', 'password': 'Bridge-Test-42!'})
    cookies = response.headers.get_list('set-cookie')
    assert all('HttpOnly' in cookie and 'SameSite=lax' in cookie for cookie in cookies)
    assert any('Path=/api/v1/auth' in cookie for cookie in cookies)
    before = client.cookies.get('refresh_token')
    assert (await client.post(P + '/auth/refresh')).status_code == 204
    assert client.cookies.get('refresh_token') != before
    assert (await client.post(P + '/auth/logout')).status_code == 204
    assert (await client.get(P + '/users/me')).status_code == 401
    assert (await client.post(P + '/auth/refresh')).status_code == 401

async def test_signup_validation_and_duplicate(client, account):
    payload = {'username': 'alice', 'email': 'alice@example.com', 'password': 'Bridge-Test-42!'}
    assert (await client.post(P + '/auth/signup', json=payload)).status_code == 409
    payload.update(username='newuser', email='new@example.com', password='weak')
    assert (await client.post(P + '/auth/signup', json=payload)).status_code == 422
    payload.update(username='bad username', password='Bridge-Test-42!')
    assert (await client.post(P + '/auth/signup', json=payload)).status_code == 422

async def test_profile_preferences_and_idempotent_onboarding(client, account):
    prefs = (await client.get(P + '/users/me/preferences')).json()
    assert prefs['save_history'] and not prefs['memory_allowed'] and not prefs['onboarding_complete']
    assert not prefs['reflection_allowed'] and not prefs['notification_enabled']
    assert (await client.patch(P + '/users/me/preferences', json={'dark_mode': True, 'text_size': 'large'})).status_code == 200
    assert (await client.get(P + '/users/me/preferences')).json()['dark_mode']
    assert (await client.patch(P + '/users/me/preferences', json={'memory_allowed': None})).status_code == 422
    assert (await client.patch(P + '/users/me/preferences', json={'unexpected': True})).status_code == 422
    assert (await client.patch(P + '/users/me', json={'display_name': 'My Name'})).json()['display_name'] == 'My Name'
    for _ in range(2):
        assert (await client.post(P + '/onboarding', json={'primer': 'I prefer time to think.'})).status_code == 200
    passport = (await client.get(P + '/passport')).json()
    assert len(passport) == 1 and not passport[0]['use_for_patterns']
    assert (await client.get(P + '/users/me/preferences')).json()['onboarding_complete']

async def conversation(client):
    response = await client.post(P + '/conversations', json={'initial_mode': 'mind-dump'})
    assert response.status_code == 201, response.text
    return response.json()['id']

async def message(client, cid, text='A private thought', allowed=True, mode='mind-dump'):
    return await client.post(P + f'/conversations/{cid}/messages', json={'content': text, 'active_mode': mode, 'memory_allowed': allowed})

async def test_photo_roundtrip_and_validation(client, account):
    photo = 'data:image/png;base64,' + base64.b64encode(b'\x89PNG\r\n\x1a\n' + b'photo').decode()
    capture = await client.post(P + '/captures', json={'content': 'Photo in my notebook', 'category': 'Moment', 'photo_data': photo})
    assert capture.status_code == 201, capture.text
    assert (await client.get(P + f"/captures/{capture.json()['id']}")).json()['photo_data'] == photo
    cid = await conversation(client)
    payload = {'content': 'Photo in my mind dump', 'active_mode': 'mind-dump', 'memory_allowed': False, 'photo_data': photo}
    sent = await client.post(P + f'/conversations/{cid}/messages', json=payload)
    assert sent.status_code == 201, sent.text
    assert (await client.get(P + f'/conversations/{cid}/messages')).json()[0]['photo_data'] == photo
    bad = await client.post(P + '/captures', json={'content': 'Bad photo', 'photo_data': 'data:image/png;base64,' + base64.b64encode(b'not a png').decode()})
    assert bad.status_code == 422

async def test_conversation_history_and_memory_permissions(client, account, database):
    cid = await conversation(client)
    first = await message(client, cid)
    assert first.status_code == 201 and first.json()['memory_allowed'] is False
    await client.patch(P + '/users/me/preferences', json={'memory_allowed': True, 'save_context_allowed': True})
    assert (await message(client, cid, 'Allowed thought')).json()['memory_allowed'] is True
    assert (await message(client, cid, 'Locally denied', False)).json()['memory_allowed'] is False
    stored = (await client.get(P + f'/conversations/{cid}/messages?limit=2')).json()
    assert len(stored) == 2
    history = await client.get(P + '/history?q=private')
    assert history.status_code == 200, history.text
    assert history.json()['total'] == 1
    await client.patch(P + '/users/me/preferences', json={'save_history': False})
    assert (await message(client, cid)).status_code == 409
    assert (await client.post(P + '/conversations', json={'initial_mode': 'reflection'})).status_code == 409
    assert (await client.get(P + f'/conversations/{cid}/messages')).status_code == 200
    await client.patch(P + '/users/me/preferences', json={'save_history': True})
    assert (await client.post(P + f'/conversations/{cid}/end')).status_code == 200
    assert (await message(client, cid)).status_code == 409
    assert (await client.delete(P + f'/conversations/{cid}')).status_code == 204
    async with database() as db:
        assert await db.scalar(select(func.count()).select_from(Message)) == 0

async def test_workspace_crud_and_history(client, account):
    capture = await client.post(P + '/captures', json={'content': 'Remember the presentation', 'analysis_allowed': True})
    assert capture.status_code == 201 and not capture.json()['analysis_allowed']
    capid = capture.json()['id']
    await client.patch(P + '/users/me/preferences', json={'memory_allowed': True, 'save_context_allowed': True, 'reflection_allowed': True})
    assert (await client.patch(P + f'/captures/{capid}', json={'content': 'Edited presentation note', 'analysis_allowed': True})).json()['analysis_allowed']
    passport = await client.post(P + '/passport', json={'section': 'matters', 'title': 'Learning', 'description': 'Time for practice'})
    assert passport.status_code == 201, passport.text
    pid = passport.json()['id']
    assert (await client.patch(P + f'/passport/{pid}', json={'section': 'support', 'title': 'Quiet', 'description': 'A quiet room'})).status_code == 200
    reflection = await client.post(P + '/reflections', json={'content_text': 'Today I made progress.'})
    assert reflection.status_code == 201, reflection.text
    rid = reflection.json()['id']
    assert (await client.patch(P + f'/reflections/{rid}', json={'content_text': 'Updated reflection'})).status_code == 200
    history = (await client.get(P + '/history?limit=1')).json()
    assert len(history['items']) == 1 and history['total'] == 2
    assert (await client.get(P + '/history?q=presentation')).json()['total'] == 1
    assert (await client.get(P + '/history?q=%25')).json()['total'] == 0
    assert (await client.post(P + '/captures', json={'content': '   '})).status_code == 422
    for route, identifier in [('captures', capid), ('passport', pid), ('reflections', rid)]:
        assert (await client.delete(P + f'/{route}/{identifier}')).status_code == 204
    assert (await client.get(P + '/history')).json()['total'] == 0

async def test_cross_account_access_is_denied(client, account, database):
    cid = await conversation(client)
    await message(client, cid, 'Alice-only content')
    capid = (await client.post(P + '/captures', json={'content': 'Alice-only note'})).json()['id']
    pid = (await client.post(P + '/passport', json={'section': 'matters', 'title': 'Private', 'description': 'Alice-only'})).json()['id']
    rid = (await client.post(P + '/reflections', json={'content_text': 'Alice-only reflection'})).json()['id']
    async with database() as db:
        hypothesis = Hypothesis(user_id=uuid.UUID(account['id']), statement_text='A tentative idea', status='pending')
        db.add(hypothesis)
        await db.commit()
        hid = str(hypothesis.id)
    await client.post(P + '/auth/logout')
    await register(client, 'bob')
    for route in [f'/conversations/{cid}', f'/conversations/{cid}/messages', f'/captures/{capid}', f'/reflections/{rid}']:
        assert (await client.get(P + route)).status_code == 404
    for route in [f'/conversations/{cid}', f'/captures/{capid}', f'/passport/{pid}', f'/reflections/{rid}']:
        assert (await client.delete(P + route)).status_code == 404
    assert (await message(client, cid)).status_code == 404
    assert (await client.patch(P + f'/patterns/{hid}', json={'status': 'confirmed'})).status_code == 404
    assert (await client.post(P + '/reflections', json={'content_text': 'Bad link', 'hypothesis_id': hid})).status_code == 404
    assert (await client.get(P + '/history')).json()['total'] == 0
    assert (await client.get(P + '/passport')).json() == []

async def test_pattern_feedback_and_evidence_permission(client, account, database):
    cid = await conversation(client)
    denied = (await message(client, cid)).json()['id']
    await client.patch(P + '/users/me/preferences', json={'memory_allowed': True, 'save_context_allowed': True})
    permitted = (await message(client, cid, 'May be used as evidence')).json()['id']
    async with database() as db:
        h = Hypothesis(user_id=uuid.UUID(account['id']), statement_text='Could planning help?', status='pending')
        db.add(h)
        await db.flush()
        for mid in [denied, permitted]:
            db.add(HypothesisEvidence(hypothesis_id=h.id, message_id=uuid.UUID(mid), evidence_role='support'))
        await db.commit()
        hid = str(h.id)
    pattern = (await client.get(P + '/patterns')).json()[0]
    assert [e['id'] for e in pattern['evidence']] == [permitted]
    response = await client.patch(P + f'/patterns/{hid}', json={'status': 'rejected', 'correction': 'This does not fit.'})
    assert response.status_code == 200
    pattern = (await client.get(P + '/patterns')).json()[0]
    assert pattern['status'] == 'rejected' and pattern['user_correction'] == 'This does not fit.'

async def test_refresh_replay_revokes_sessions(client, account, database):
    old = client.cookies.get('refresh_token')
    claims = verify_token(old, 'refresh')
    await client.post(P + '/auth/refresh')
    current = client.cookies.get('refresh_token')
    response = await client.post(P + '/auth/refresh', headers={'cookie': f'refresh_token={old}'})
    assert response.status_code == 401 and 'set-cookie' not in response.headers
    async with database() as db:
        row = await db.get(RefreshToken, claims.jti)
        row.revoked_at = datetime.now(UTC) - timedelta(seconds=20)
        await db.commit()
    assert (await client.post(P + '/auth/refresh', headers={'cookie': f'refresh_token={old}'})).status_code == 401
    assert (await client.post(P + '/auth/refresh', headers={'cookie': f'refresh_token={current}'})).status_code == 401

async def test_origin_validation(client, account):
    assert (await client.post(P + '/captures', json={'content': 'blocked'}, headers={'origin': 'https://untrusted.example'})).status_code == 403
    assert (await client.post(P + '/captures', json={'content': 'allowed'}, headers={'origin': 'http://localhost:3000'})).status_code == 201

async def test_google_exchange_and_collision(client, monkeypatch):
    from app.api.v1.auth import routes
    monkeypatch.setattr(settings, 'google_client_id', 'test-client')
    monkeypatch.setattr(routes, 'verify_google_identity', lambda _token: {'sub': 'google-subject-123', 'email': 'google@example.com', 'name': 'Google User'})
    response = await client.post(P + '/auth/google', json={'id_token': 'stubbed-verifier-token'})
    assert response.status_code == 200, response.text
    uid = response.json()['id']
    assert (await client.get(P + '/users/me')).json()['id'] == uid
    await client.post(P + '/auth/logout')
    assert (await client.post(P + '/auth/google', json={'id_token': 'stubbed-verifier-token'})).json()['id'] == uid
    await register(client)
    monkeypatch.setattr(routes, 'verify_google_identity', lambda _token: {'sub': 'another-subject', 'email': 'alice@example.com'})
    assert (await client.post(P + '/auth/google', json={'id_token': 'stubbed-verifier-token'})).status_code == 409
    def invalid(_token):
        raise ValueError('invalid signature')
    monkeypatch.setattr(routes, 'verify_google_identity', invalid)
    assert (await client.post(P + '/auth/google', json={'id_token': 'invalid'})).status_code == 401
    monkeypatch.setattr(settings, 'google_client_id', '')
    assert (await client.post(P + '/auth/google', json={'id_token': 'not-configured'})).status_code == 503
