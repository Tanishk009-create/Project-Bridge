from datetime import UTC, datetime, timedelta
import secrets
import smtplib
import uuid
from typing import Annotated

import jwt
from fastapi import APIRouter, Cookie, HTTPException, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.core.config import settings
from app.core.google import verify_google_identity
from google.auth.exceptions import GoogleAuthError

from app.api.deps import RefreshTokenRepoDep, UserRepoDep, SessionDep
from app.services.account_lifecycle import issue_link, consume_token
from app.services.mail import send_mail
from app.core.jwt import (
    REFRESH_TOKEN_COOKIE,
    clear_auth_cookies,
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    set_auth_cookies,
    verify_password,
    verify_token,
)
from app.models import RefreshToken, User
from app.schemas import LoginRequest, LoginResponse, SignupRequest, SignupResponse

router = APIRouter(prefix="/auth", tags=["auth"])

# Verified against when the user doesn't exist, so a failed login takes as long
# whether or not the account exists (prevents user enumeration by timing).
_DUMMY_PASSWORD_HASH = hash_password("dummy-password-for-timing")

# A rotated token presented again within this window is treated as two tabs
# refreshing at once rather than theft.
REFRESH_REUSE_GRACE_PERIOD = timedelta(seconds=10)

class GoogleLoginRequest(BaseModel):
    id_token: str = Field(min_length=1, max_length=10000)

class EmailRequest(BaseModel):
    email: EmailStr

class TokenRequest(BaseModel):
    token: str = Field(min_length=20, max_length=200)

class ResetPasswordRequest(TokenRequest):
    new_password: str

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        return SignupRequest.strong_password(value)

async def send_account_link(db, user, purpose: str) -> str:
    message, issued = await issue_link(db, user, purpose)
    if not issued or not message:
        return "rate-limited"
    try:
        return await run_in_threadpool(send_mail, *message)
    except (OSError, RuntimeError, TimeoutError, smtplib.SMTPException):
        return "unavailable"

@router.post("/google", response_model=LoginResponse)
async def google_login(payload: GoogleLoginRequest, response: Response, users: UserRepoDep, refresh_tokens: RefreshTokenRepoDep):
    if not settings.google_client_id:
        raise HTTPException(503, "Google sign-in is not configured")
    try:
        claims = await run_in_threadpool(verify_google_identity, payload.id_token)
    except (ValueError, GoogleAuthError):
        raise HTTPException(401, "Google identity could not be verified") from None
    user = await users.get_by_google_subject(claims["sub"])
    if user is None:
        email = claims["email"].lower()
        if await users.get_by_email(email):
            raise HTTPException(409, "This email already has an account. Sign in with your password; automatic account linking is disabled.")
        user = User(email=email, username="google_" + uuid.uuid4().hex[:24], google_subject=claims["sub"], email_verified_at=datetime.now(UTC),
                    display_name=claims.get("name", "")[:100] or None,
                    hashed_password=await run_in_threadpool(hash_password, secrets.token_urlsafe(64)))
        try:
            user = await users.add(user)
        except IntegrityError:
            raise HTTPException(409, "Account creation conflicted. Please sign in again.") from None
    refresh = create_refresh_token(user.id)
    await refresh_tokens.add(RefreshToken(id=refresh.jti, user_id=user.id, token_hash=hash_token(refresh.token), expires_at=refresh.expires_at))
    set_auth_cookies(response, create_access_token(user.id), refresh.token)
    return user


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest, users: UserRepoDep, db: SessionDep) -> dict:
    existing = await users.get_by_email_or_username(payload.email, payload.username)
    if existing is not None:
        field = "email" if existing.email == payload.email else "username"
        raise HTTPException(status.HTTP_409_CONFLICT, f"A user with this {field} already exists")

    user = User(
        email=payload.email,
        username=payload.username,
        display_name=payload.display_name,
        hashed_password=await run_in_threadpool(hash_password, payload.password),
        email_verified_at=datetime.now(UTC) if settings.mail_mode == "disabled" else None,
    )
    try:
        user = await users.add(user)
    except IntegrityError:
        # A concurrent signup took the email/username between the check and the insert.
        raise HTTPException(
            status.HTTP_409_CONFLICT, "A user with this email or username already exists"
        ) from None
    delivery = await send_account_link(db, user, "verify") if settings.mail_mode != "disabled" else "disabled"
    return {"id": user.id, "email": user.email, "username": user.username,
            "verification_required": settings.mail_mode != "disabled", "delivery": delivery}


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    users: UserRepoDep,
    refresh_tokens: RefreshTokenRepoDep,
) -> User:
    if payload.email is not None:
        user = await users.get_by_email(payload.email)
    else:
        user = await users.get_by_username(payload.username)

    hashed_password = user.hashed_password if user is not None else _DUMMY_PASSWORD_HASH
    password_ok = await run_in_threadpool(verify_password, payload.password, hashed_password)
    if user is None or not password_ok:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if user.email_verified_at is None and settings.mail_mode != "disabled":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Verify your email before logging in. You can request a new verification link.")

    access_token = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    await refresh_tokens.add(
        RefreshToken(
            id=refresh.jti,
            user_id=user.id,
            token_hash=hash_token(refresh.token),
            expires_at=refresh.expires_at,
        )
    )
    set_auth_cookies(response, access_token, refresh.token)
    return user


@router.post("/resend-verification")
async def resend_verification(payload: EmailRequest, users: UserRepoDep, db: SessionDep):
    user = await users.get_by_email(payload.email.lower())
    if user and user.email_verified_at is None and settings.mail_mode != "disabled":
        await send_account_link(db, user, "verify")
    return {"message": "If this account needs verification, a link has been sent or saved to the local outbox."}


@router.post("/verify-email")
async def verify_email(payload: TokenRequest, db: SessionDep):
    user_id = await consume_token(db, payload.token, "verify")
    if not user_id:
        raise HTTPException(400, "This verification link is invalid or expired.")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(400, "This verification link is invalid or expired.")
    user.email_verified_at = datetime.now(UTC)
    await db.flush()
    return {"message": "Email verified. You can now log in."}


@router.post("/request-password-reset")
async def request_password_reset(payload: EmailRequest, users: UserRepoDep, db: SessionDep):
    user = await users.get_by_email(payload.email.lower())
    if user and not user.google_subject and settings.mail_mode != "disabled":
        await send_account_link(db, user, "reset")
    return {"message": "If this account can reset its password, a link has been sent or saved to the local outbox."}


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, db: SessionDep, refresh_tokens: RefreshTokenRepoDep):
    user_id = await consume_token(db, payload.token, "reset")
    if not user_id:
        raise HTTPException(400, "This reset link is invalid or expired.")
    user = await db.get(User, user_id)
    if not user or user.google_subject:
        raise HTTPException(400, "This reset link is invalid or expired.")
    user.hashed_password = await run_in_threadpool(hash_password, payload.new_password)
    await refresh_tokens.revoke_all_for_user(user.id)
    await db.flush()
    return {"message": "Password updated. Log in with your new password."}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    refresh_tokens: RefreshTokenRepoDep,
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_TOKEN_COOKIE)] = None,
) -> None:
    """Revoke this session's refresh token and clear both cookies.

    Always succeeds: a missing, invalid, expired or already-revoked token just
    means there is nothing to revoke. The access token isn't stored, so it stays
    valid until it expires; only its cookie is removed.
    """
    clear_auth_cookies(response)
    if refresh_token is None:
        return
    try:
        claims = verify_token(refresh_token, "refresh")
    except jwt.InvalidTokenError:
        return

    row = await refresh_tokens.get(claims.jti)
    if row is None or row.token_hash != hash_token(refresh_token) or row.user_id != claims.user_id:
        return
    if row.revoked_at is None:
        await refresh_tokens.revoke(row.id)
    elif row.replaced_by_id is not None:
        # Already rotated, so presenting it again means it was copied: end every session.
        await refresh_tokens.revoke_all_for_user(row.user_id)


def _invalid_refresh_token(*, clear_cookies: bool = True) -> JSONResponse:
    # Returned rather than raised so get_db still commits (revoke_all_for_user
    # must persist) and so the cookie changes are actually sent.
    response = JSONResponse(
        {"detail": "Invalid refresh token"}, status_code=status.HTTP_401_UNAUTHORIZED
    )
    if clear_cookies:
        clear_auth_cookies(response)
    return response


@router.post(
    "/refresh",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "Invalid refresh token"}},
)
async def refresh(
    refresh_tokens: RefreshTokenRepoDep,
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_TOKEN_COOKIE)] = None,
) -> Response:
    """Rotate the refresh token: issue new access + refresh cookies, revoke the old token.

    Presenting an already-rotated token revokes all of the user's sessions,
    unless it was rotated within REFRESH_REUSE_GRACE_PERIOD (two tabs refreshing
    at once). In that case the cookies are left alone, since the browser may
    already hold the winning tab's new ones.
    """
    if refresh_token is None:
        return _invalid_refresh_token()
    try:
        claims = verify_token(refresh_token, "refresh")
    except jwt.InvalidTokenError:
        return _invalid_refresh_token()

    row = await refresh_tokens.get(claims.jti)
    if row is None or row.token_hash != hash_token(refresh_token) or row.user_id != claims.user_id:
        return _invalid_refresh_token()

    if row.revoked_at is not None:
        if row.replaced_by_id is None:  # logged out
            return _invalid_refresh_token()
        if datetime.now(UTC) - row.revoked_at.replace(tzinfo=UTC) < REFRESH_REUSE_GRACE_PERIOD:
            return _invalid_refresh_token(clear_cookies=False)
        await refresh_tokens.revoke_all_for_user(row.user_id)
        return _invalid_refresh_token()

    new_refresh = create_refresh_token(row.user_id)
    await refresh_tokens.add(
        RefreshToken(
            id=new_refresh.jti,
            user_id=row.user_id,
            token_hash=hash_token(new_refresh.token),
            expires_at=new_refresh.expires_at,
        )
    )
    if not await refresh_tokens.revoke(row.id, replaced_by_id=new_refresh.jti):
        # A concurrent request rotated this token first. Raising rolls back the
        # row added above; the cookies are left for the winning request's.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")

    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    set_auth_cookies(response, create_access_token(row.user_id), new_refresh.token)
    return response
