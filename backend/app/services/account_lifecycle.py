"""Issue and consume one-time account links without storing bearer tokens."""
from datetime import UTC, datetime, timedelta
import secrets
from sqlalchemy import select, update
from app.core import settings
from app.core.jwt import hash_token
from app.models import AccountToken


async def issue_link(db, user, purpose: str) -> tuple[tuple[str, str, str] | None, bool]:
    recent = await db.scalar(select(AccountToken.id).where(AccountToken.user_id == user.id,
        AccountToken.purpose == purpose, AccountToken.created_at > datetime.now(UTC)-timedelta(minutes=2)).limit(1))
    if recent:
        return None, False
    raw = secrets.token_urlsafe(32)
    db.add(AccountToken(user_id=user.id, purpose=purpose, token_hash=hash_token(raw),
        expires_at=datetime.now(UTC)+timedelta(hours=24 if purpose == "verify" else 1)))
    await db.commit()
    page = "verify-email" if purpose == "verify" else "reset-password"
    url = f"{settings.public_url.rstrip('/')}/{page}?token={raw}"
    subject = "Verify your Project Bridge email" if purpose == "verify" else "Reset your Project Bridge password"
    body = ("Use this one-time link to verify your Bridge email:\n" if purpose == "verify" else
            "Use this one-time link to reset your Bridge password:\n") + url + "\n\nIf you did not request this, you can ignore this message."
    return (user.email, subject, body), True


async def consume_token(db, raw: str, purpose: str):
    if not 20 <= len(raw) <= 200:
        return None
    result = await db.execute(update(AccountToken).where(AccountToken.token_hash == hash_token(raw),
        AccountToken.purpose == purpose, AccountToken.used_at.is_(None), AccountToken.expires_at > datetime.now(UTC))
        .values(used_at=datetime.now(UTC)).returning(AccountToken.user_id))
    return result.scalar_one_or_none()
