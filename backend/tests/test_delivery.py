"""Account links and background delivery use fake mail and isolated databases."""
import re
from datetime import UTC, datetime, timedelta
import uuid
from sqlalchemy import select
from app.core import settings
from app.api.v1.auth import routes as auth_routes
from app.models import PreviewSchedule, Reminder, Reflection
from app.services import scheduler
from app.services import mail
from pydantic import SecretStr
from test_integration import P, conversation, message
from test_ai import permissions
from test_review import ReflectionGateway

def test_smtp_transport_uses_tls_and_configured_sender(monkeypatch):
    calls=[]
    class FakeSMTP:
        def __init__(self,host,port,timeout):calls.append((host,port,timeout))
        def __enter__(self):return self
        def __exit__(self,*args):return False
        def starttls(self):calls.append("tls")
        def login(self,user,password):calls.append((user,password))
        def send_message(self,message):calls.append((message["From"],message["To"],message["Subject"],message.get_content()))
    monkeypatch.setattr(settings,"mail_mode","smtp")
    monkeypatch.setattr(settings,"smtp_host","smtp.example.test")
    monkeypatch.setattr(settings,"smtp_port",587)
    monkeypatch.setattr(settings,"smtp_username","bridge")
    monkeypatch.setattr(settings,"smtp_password",SecretStr("test-only"))
    monkeypatch.setattr(settings,"smtp_from","Bridge <hello@example.test>")
    monkeypatch.setattr(mail.smtplib,"SMTP",FakeSMTP)
    assert mail.send_mail("reader@example.test","Bridge reminder","A neutral reminder") == "sent"
    assert "tls" in calls and ("bridge","test-only") in calls
    assert calls[-1][1:3] == ("reader@example.test","Bridge reminder")


async def test_verification_and_password_reset_links(client, monkeypatch):
    sent=[]
    monkeypatch.setattr(settings,"mail_mode","smtp")
    monkeypatch.setattr(auth_routes,"send_mail",lambda to,subject,body:sent.append((to,subject,body)) or "sent")
    account={"username":"newperson","email":"newperson@example.com","password":"Bridge-Test-42!"}
    created=await client.post(P+"/auth/signup",json=account)
    assert created.status_code==201 and created.json()["verification_required"]
    assert (await client.post(P+"/auth/login",json={"email":account["email"],"password":account["password"]})).status_code==403
    verify=re.search(r"token=([^\s]+)",sent[-1][2]).group(1)
    assert (await client.post(P+"/auth/verify-email",json={"token":verify})).status_code==200
    assert (await client.post(P+"/auth/verify-email",json={"token":verify})).status_code==400
    assert (await client.post(P+"/auth/login",json={"email":account["email"],"password":account["password"]})).status_code==200
    assert (await client.post(P+"/auth/request-password-reset",json={"email":account["email"]})).status_code==200
    reset=re.search(r"token=([^\s]+)",sent[-1][2]).group(1)
    assert (await client.post(P+"/auth/reset-password",json={"token":reset,"new_password":"New-Bridge-42!"})).status_code==200
    assert (await client.post(P+"/auth/reset-password",json={"token":reset,"new_password":"New-Bridge-42!"})).status_code==400
    assert (await client.post(P+"/auth/login",json={"email":account["email"],"password":"Bridge-Test-42!"})).status_code==401
    assert (await client.post(P+"/auth/login",json={"email":account["email"],"password":"New-Bridge-42!"})).status_code==200
    previous=len(sent)
    assert (await client.post(P+"/auth/request-password-reset",json={"email":"unknown@example.com"})).status_code==200
    assert len(sent)==previous


async def test_preview_opt_in_and_generic_reminder_delivery(client,account,database,monkeypatch):
    monkeypatch.setattr(settings,"mail_mode","smtp")
    monkeypatch.setattr(scheduler,"SessionLocal",database)
    sent=[]
    monkeypatch.setattr(scheduler,"send_mail",lambda to,subject,body:sent.append((to,subject,body)) or "sent")
    assert (await client.put(P+"/reflection-preview/schedule",json={"enabled":True,"cadence_days":7})).status_code==409
    await permissions(client)
    assert (await client.put(P+"/reflection-preview/schedule",json={"enabled":True,"cadence_days":7})).status_code==200
    await client.patch(P+"/users/me/preferences",json={"notification_enabled":True,"notification_email_enabled":True})
    due=datetime.now(UTC)+timedelta(hours=1)
    result=await client.post(P+"/reminders",json={"scheduled_at":due.isoformat(),"destination":"notebook"})
    assert result.status_code==201,result.text
    async with database() as db:
        reminder=await db.get(Reminder,uuid.UUID(result.json()["id"]))
        reminder.scheduled_at=datetime.now(UTC)-timedelta(minutes=1)
        await db.commit()
    await scheduler.deliver_reminders()
    assert len(sent)==1 and "No private writing is included" in sent[0][2] and "notebook" not in sent[0][2]
    assert (await client.get(P+"/reminders")).json()[0]["delivery_status"]=="sent"
    await scheduler.deliver_reminders()
    assert len(sent)==1
    second=await client.post(P+"/reminders",json={"scheduled_at":(datetime.now(UTC)+timedelta(hours=2)).isoformat(),"destination":"conversation"})
    async with database() as db:
        record=await db.get(Reminder,uuid.UUID(second.json()["id"]))
        record.scheduled_at=datetime.now(UTC)-timedelta(minutes=1)
        await db.commit()
    await client.patch(P+"/users/me/preferences",json={"notification_email_enabled":False})
    await scheduler.deliver_reminders()
    assert len(sent)==1


async def test_due_preview_creates_cited_reflection(client,account,database,monkeypatch):
    monkeypatch.setattr(scheduler,"SessionLocal",database)
    monkeypatch.setattr(scheduler,"get_gateway",lambda:ReflectionGateway())
    await permissions(client)
    cid=await conversation(client)
    await message(client,cid,"I feel tense as the deadline approaches.")
    assert (await client.put(P+"/reflection-preview/schedule",json={"enabled":True,"cadence_days":7})).status_code==200
    async with database() as db:
        schedule=await db.get(PreviewSchedule,uuid.UUID(account["id"]))
        schedule.next_run_at=datetime.now(UTC)-timedelta(minutes=1)
        await db.commit()
    await scheduler.generate_previews()
    schedule=(await client.get(P+"/reflection-preview/schedule")).json()
    assert schedule["last_status"]=="ready" and schedule["last_reflection_id"]
    result=(await client.get(P+"/reflection-review/"+schedule["last_reflection_id"])).json()
    assert result["status"]=="preview"
    assert result["evidence"][0]["quote"]=="I feel tense as the deadline approaches."
    kept=await client.post(P+"/reflection-preview/"+result["id"]+"/keep")
    assert kept.status_code==200 and kept.json()["status"]=="generated"
    assert (await client.delete(P+"/reflection-preview/"+result["id"])).status_code==409
    await message(client,cid,"I noticed another tense deadline today.")
    async with database() as db:
        schedule_row=await db.get(PreviewSchedule,uuid.UUID(account["id"]))
        schedule_row.next_run_at=datetime.now(UTC)-timedelta(minutes=1)
        await db.commit()
    await scheduler.generate_previews()
    second=(await client.get(P+"/reflection-preview/schedule")).json()["last_reflection_id"]
    assert second and second!=result["id"]
    assert (await client.delete(P+"/reflection-preview/"+second)).status_code==204
    assert (await client.get(P+"/reflection-review/"+second)).status_code==404
