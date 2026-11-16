from datetime import UTC, datetime, timedelta
import uuid
import pytest
from sqlalchemy import select,func
from app.main import app
from app.models import Reflection,ReflectionSource,Reminder
from app.schemas.ai import SafetyDecision,GroundedReflection
from app.services.model_gateway import get_gateway
from app.services.ai_workflow import _active,_requests
from conftest import register
from test_integration import conversation,message,P
from test_ai import permissions

class ReflectionGateway:
    bad_quote=False
    async def generate(self,instruction,data,schema,max_tokens=None):
        if schema is SafetyDecision:return SafetyDecision(risk='ordinary')
        source=data['sources'][0]
        return GroundedReflection(observation='You described a difficult deadline.',reflection='There may be a connection between approaching deadlines and feeling tense.',question='What feels familiar about this?',evidence=[{'message_id':source['id'],'quote':'invented quote' if self.bad_quote else source['text'],'explanation':'Your words describe tension in the context of a deadline.'}])

@pytest.fixture
def reflection_gateway():
    _active.clear();_requests.clear()
    fake=ReflectionGateway();app.dependency_overrides[get_gateway]=lambda:fake
    yield fake
    app.dependency_overrides.pop(get_gateway,None)

async def test_grounded_reflection_permissions_quotes_and_deletion(client,account,reflection_gateway,database):
    cid=await conversation(client)
    assert (await client.post(P+f'/conversations/{cid}/reflection',json={'consent':True})).status_code==409
    await permissions(client)
    mid=(await message(client,cid,'I feel tense as the deadline approaches.')).json()['id']
    assert (await client.post(P+f'/conversations/{cid}/reflection',json={'consent':False})).status_code==422
    reflection_gateway.bad_quote=True
    bad=await client.post(P+f'/conversations/{cid}/reflection',json={'consent':True})
    assert bad.status_code==502,bad.text
    assert (await client.get(P+'/reflection-review')).json()==[]
    reflection_gateway.bad_quote=False
    response=await client.post(P+f'/conversations/{cid}/reflection',json={'consent':True})
    assert response.status_code==201,response.text
    record=response.json();rid=record['id']
    assert record['evidence'][0]['message_id']==mid
    assert record['evidence'][0]['quote']=='I feel tense as the deadline approaches.'
    assert (await client.patch(P+f'/reflections/{rid}',json={'content_text':'Replacement text'})).status_code==409
    await client.patch(P+'/users/me/preferences',json={'notification_enabled':True})
    reminder=await client.post(P+'/reminders',json={'scheduled_at':(datetime.now(UTC)+timedelta(days=1)).isoformat(),'reflection_id':rid})
    assert reminder.status_code==201,reminder.text
    assert (await client.delete(P+f'/conversations/{cid}')).status_code==204
    assert (await client.get(P+f'/reflection-review/{rid}')).status_code==404
    async with database() as db:
        assert await db.scalar(select(func.count()).select_from(ReflectionSource))==0
        assert await db.scalar(select(func.count()).select_from(Reminder))==0

async def test_review_and_reminder_owner_scope(client,account,reflection_gateway):
    await permissions(client);cid=await conversation(client);await message(client,cid,'The deadline feels difficult.')
    r=await client.post(P+f'/conversations/{cid}/reflection',json={'consent':True});assert r.status_code==201,r.text
    rid=r.json()['id']
    await client.patch(P+'/users/me/preferences',json={'notification_enabled':True})
    payload={'scheduled_at':(datetime.now(UTC)+timedelta(days=1)).isoformat(),'reflection_id':rid}
    reminder=(await client.post(P+'/reminders',json=payload)).json()['id']
    await register(client,'second')
    assert (await client.get(P+'/reflection-review')).json()==[]
    assert (await client.get(P+f'/reflection-review/{rid}')).status_code==404
    assert (await client.post(P+f'/conversations/{cid}/reflection',json={'consent':True})).status_code==404
    assert (await client.get(P+'/reminders')).json()==[]
    assert (await client.patch(P+f'/reminders/{reminder}',json={'status':'completed'})).status_code==404
    assert (await client.delete(P+f'/reminders/{reminder}')).status_code==404
    await client.patch(P+'/users/me/preferences',json={'notification_enabled':True})
    assert (await client.post(P+'/reminders',json=payload)).status_code==404

async def test_reminders_validation_and_persistence(client,account):
    future=(datetime.now(UTC)+timedelta(hours=1)).isoformat()
    assert (await client.post(P+'/reminders',json={'scheduled_at':future})).status_code==409
    await client.patch(P+'/users/me/preferences',json={'notification_enabled':True})
    for bad in ['2020-01-01T00:00:00Z','2099-01-01T00:00:00']:
        assert (await client.post(P+'/reminders',json={'scheduled_at':bad})).status_code==422
    result=await client.post(P+'/reminders',json={'scheduled_at':future,'destination':'notebook'})
    assert result.status_code==201,result.text
    rid=result.json()['id']
    assert (await client.get(P+'/reminders')).json()[0]['destination']=='notebook'
    assert (await client.patch(P+f'/reminders/{rid}',json={'status':'completed'})).json()['status']=='completed'
    assert (await client.delete(P+f'/reminders/{rid}')).status_code==204
    assert (await client.get(P+'/reminders')).json()==[]

async def test_password_change_and_revoke_sessions(client,account):
    payload={'current_password':'wrong','new_password':'New-Bridge-42!'}
    assert (await client.post(P+'/users/me/password',json=payload)).status_code==400
    payload.update(current_password='Bridge-Test-42!',new_password='short')
    assert (await client.post(P+'/users/me/password',json=payload)).status_code==422
    payload['new_password']='New-Bridge-42!'
    old_refresh=client.cookies.get('refresh_token')
    response=await client.post(P+'/users/me/password',json=payload)
    assert response.status_code==204,response.text
    assert (await client.get(P+'/users/me')).status_code==401
    assert (await client.post(P+'/auth/login',json={'email':'alice@example.com','password':'Bridge-Test-42!'})).status_code==401
    assert (await client.post(P+'/auth/login',json={'email':'alice@example.com','password':'New-Bridge-42!'})).status_code==200
    assert (await client.post(P+'/users/me/sign-out-all')).status_code==204
    assert (await client.get(P+'/users/me')).status_code==401
    client.cookies.clear();client.cookies.set('refresh_token',old_refresh)
    assert (await client.post(P+'/auth/refresh')).status_code==401

async def test_diary_length_tags_and_history_filter(client,account):
    content='My diary title\n'+'A day worth remembering. '*600
    result=await client.post(P+'/captures',json={'content':content,'category':'Moment','analysis_allowed':False})
    assert result.status_code==201,result.text
    capture=result.json()
    assert not capture['analysis_allowed'] and capture['content']==content.strip()
    await conversation(client)
    history=(await client.get(P+'/history?kind=quick-capture')).json()
    assert history['total']==1 and all(item['type']=='quick-capture' for item in history['items'])
    assert history['items'][0]['href']==f"/notebook?id={capture['id']}"
    assert (await client.get(P+'/history?kind=invalid')).status_code==422
    assert (await client.post(P+'/captures',json={'content':'a'*20001,'category':'Note'})).status_code==422
