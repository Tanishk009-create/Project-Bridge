"""Background delivery of generic reminders and opt-in Reflection Previews."""
import asyncio
from datetime import UTC, datetime, timedelta
import logging
from sqlalchemy import select, update
from starlette.concurrency import run_in_threadpool
from app.core import SessionLocal, settings
from app.models import Conversation, Message, Notification, PreviewSchedule, Reminder, User, UserPreferences
from app.schemas.ai import AnalysisRequest
from app.services.mail import send_mail
from app.services.model_gateway import get_gateway

log = logging.getLogger(__name__)


async def deliver_reminders():
    if settings.mail_mode == "disabled":
        return
    async with SessionLocal() as db:
        due = (await db.execute(select(Reminder.id, User.email).join(User, User.id == Reminder.user_id)
            .join(UserPreferences, UserPreferences.user_id == Reminder.user_id)
            .where(Reminder.scheduled_at <= datetime.now(UTC), Reminder.status == "scheduled",
                   Reminder.delivery_status == "pending", UserPreferences.notification_enabled.is_(True),
                   UserPreferences.notification_email_enabled.is_(True), User.email_verified_at.is_not(None))
            .order_by(Reminder.scheduled_at).limit(20))).all()
    for reminder_id, email in due:
        async with SessionLocal() as db:
            claimed = await db.execute(update(Reminder).where(Reminder.id == reminder_id,
                Reminder.status == "scheduled", Reminder.delivery_status == "pending")
                .values(delivery_status="sending"))
            await db.commit()
            if not claimed.rowcount:
                continue
            reminder = await db.get(Reminder, reminder_id)
            prefs = await db.get(UserPreferences, reminder.user_id)
            if not prefs or not (prefs.notification_enabled and prefs.notification_email_enabled) or reminder.status != "scheduled":
                reminder.delivery_status = "pending"
                await db.commit()
                continue
        try:
            result = await run_in_threadpool(send_mail, email, "A moment for your Bridge space",
                f"You have a reminder in Project Bridge. Open {settings.public_url.rstrip('/')}/profile?tab=reminders when you are ready.\n\nNo private writing is included in this email.")
            state = "sent" if result == "sent" else "local-file"
        except Exception:
            log.warning("Generic reminder delivery failed for reminder %s", reminder_id)
            state = "failed"
        async with SessionLocal() as db:
            await db.execute(update(Reminder).where(Reminder.id == reminder_id, Reminder.delivery_status == "sending")
                .values(delivery_status=state, delivered_at=datetime.now(UTC) if state != "failed" else None))
            await db.commit()


async def generate_previews():
    from app.api.v1.review import generate_reflection
    now = datetime.now(UTC)
    async with SessionLocal() as db:
        due = list(await db.scalars(select(PreviewSchedule).where(PreviewSchedule.enabled.is_(True),
            PreviewSchedule.next_run_at <= now).order_by(PreviewSchedule.next_run_at).limit(5)))
        due = [(item.user_id, item.cadence_days, item.last_run_at) for item in due]
    for user_id, cadence, last_run in due:
        async with SessionLocal() as db:
            claimed = await db.execute(update(PreviewSchedule).where(PreviewSchedule.user_id == user_id,
                PreviewSchedule.enabled.is_(True), PreviewSchedule.next_run_at <= now)
                .values(next_run_at=now+timedelta(days=cadence), last_run_at=now, last_status="processing"))
            await db.commit()
            if not claimed.rowcount:
                continue
            user = await db.get(User, user_id)
            prefs = await db.get(UserPreferences, user_id)
            if not user or not prefs or not (prefs.save_history and prefs.memory_allowed and prefs.save_context_allowed and prefs.reflection_allowed):
                await db.execute(update(PreviewSchedule).where(PreviewSchedule.user_id == user_id).values(last_status="paused"))
                await db.commit()
                continue
            latest = await db.scalar(select(Conversation.id).join(Message, Message.conversation_id == Conversation.id)
                .where(Conversation.user_id == user_id, Message.sender == "user", Message.memory_allowed.is_(True),
                    Message.created_at > (last_run or datetime(1970, 1, 1, tzinfo=UTC)))
                .order_by(Message.created_at.desc()).limit(1))
            if not latest:
                await db.execute(update(PreviewSchedule).where(PreviewSchedule.user_id == user_id).values(last_status="no-new-writing"))
                await db.commit()
                continue
            try:
                result = await generate_reflection(latest, AnalysisRequest(consent=True), user, db, get_gateway(), scheduled=True)
                await db.execute(update(PreviewSchedule).where(PreviewSchedule.user_id == user_id)
                    .values(last_status="ready", last_reflection_id=result["id"]))
                await db.commit()
            except Exception:
                await db.rollback()
                active = await db.get(PreviewSchedule, user_id, populate_existing=True)
                await db.execute(update(PreviewSchedule).where(PreviewSchedule.user_id == user_id)
                    .values(last_status="failed" if active and active.enabled else "paused"))
                await db.commit()
                log.warning("Scheduled reflection preview failed for account %s", user_id)
                continue
            await db.refresh(prefs)
            if prefs.notification_enabled and prefs.notification_email_enabled and user.email_verified_at and settings.mail_mode != "disabled":
                try:
                    delivery = await run_in_threadpool(send_mail, user.email, "A Bridge reflection is ready",
                        f"A reflection is ready for review in Project Bridge. Open {settings.public_url.rstrip('/')}/reflection?id={result['id']}.\n\nNo private writing is included in this email.")
                    db.add(Notification(user_id=user_id, reflection_id=result["id"], scheduled_at=now,
                        delivery_status="sent" if delivery == "sent" else "local-file"))
                    await db.commit()
                except Exception:
                    await db.rollback()
                    db.add(Notification(user_id=user_id, reflection_id=result["id"], scheduled_at=now, delivery_status="failed"))
                    await db.commit()
                    log.warning("Reflection preview email failed for account %s", user_id)


async def scheduler_loop():
    while True:
        try:
            await deliver_reminders()
            await generate_previews()
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("Background scheduler cycle failed")
        await asyncio.sleep(30)
