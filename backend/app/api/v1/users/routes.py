from fastapi import APIRouter, HTTPException, status, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.exc import IntegrityError
from starlette.concurrency import run_in_threadpool

from app.api.deps import CurrentUserDep, UserRepoDep, RefreshTokenRepoDep, SessionDep
from app.core import settings
from app.services.account_lifecycle import issue_link
from app.services.mail import send_mail
from datetime import UTC, datetime
from app.core.jwt import verify_password, hash_password, clear_auth_cookies
from app.schemas.auth import SignupRequest
from app.models import DEFAULT_PREFERENCES, Address, User, UserPreferences
from app.schemas import (
    UserPreferencesResponse,
    UserPreferencesUpdateRequest,
    UserProfileResponse,
    UserProfileUpdateRequest,
)

router = APIRouter(prefix="/users", tags=["users"])

class PasswordChange(BaseModel):
    model_config=ConfigDict(extra="forbid")
    current_password: str = Field(min_length=1,max_length=256)
    new_password: str = Field(min_length=8,max_length=128)
    @field_validator("new_password")
    @classmethod
    def strong(cls,value):
        return SignupRequest.strong_password(value)

@router.post("/me/password",status_code=204)
async def change_password(payload:PasswordChange,user:CurrentUserDep,users:UserRepoDep,tokens:RefreshTokenRepoDep,response:Response):
    if not await run_in_threadpool(verify_password,payload.current_password,user.hashed_password):
        raise HTTPException(400,"The current password is incorrect.")
    if payload.current_password==payload.new_password:
        raise HTTPException(422,"Choose a different new password.")
    user.hashed_password=await run_in_threadpool(hash_password,payload.new_password)
    await users.update(user)
    await tokens.revoke_all_for_user(user.id)
    clear_auth_cookies(response)

@router.post("/me/sign-out-all",status_code=204)
async def sign_out_all(user:CurrentUserDep,tokens:RefreshTokenRepoDep,response:Response):
    await tokens.revoke_all_for_user(user.id)
    clear_auth_cookies(response)

_EMAIL_TAKEN = "A user with this email already exists"


@router.get("/me", response_model=UserProfileResponse)
async def me(user: CurrentUserDep, users: UserRepoDep) -> User:
    return await users.get_with_address(user.id)


@router.patch("/me", response_model=UserProfileResponse)
async def update_me(
    payload: UserProfileUpdateRequest, current_user: CurrentUserDep, users: UserRepoDep, db: SessionDep
) -> User:
    """Update the profile fields sent; null clears a field, `address: null` removes the address."""
    user = await users.get_with_address(current_user.id)
    sent = payload.model_fields_set
    email_changed = False

    if "email" in sent:
        password_ok = await run_in_threadpool(
            verify_password, payload.current_password, user.hashed_password
        )
        if not password_ok:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect password")
        if payload.email != user.email:
            if await users.get_by_email(payload.email) is not None:
                raise HTTPException(status.HTTP_409_CONFLICT, _EMAIL_TAKEN)
            user.email = payload.email
            user.email_verified_at = datetime.now(UTC) if settings.mail_mode == "disabled" else None
            email_changed = True

    for field in ("display_name", "phone_no", "gender", "date_of_birth"):
        if field in sent:
            setattr(user, field, getattr(payload, field))
    if "profile_picture" in sent:
        user.profile_picture = str(payload.profile_picture) if payload.profile_picture else None

    if "address" in sent:
        if payload.address is None:
            if user.address is not None:
                old_address, user.address = user.address, None
                await users.delete_address(old_address)
        elif user.address is None:
            user.address = Address(**payload.address.model_dump())
        else:
            for field, value in payload.address.model_dump().items():
                setattr(user.address, field, value)

    try:
        updated = await users.update(user)
    except IntegrityError:
        # A concurrent request took the email between the check and the update.
        raise HTTPException(status.HTTP_409_CONFLICT, _EMAIL_TAKEN) from None
    if email_changed and settings.mail_mode != "disabled":
        message, issued = await issue_link(db, updated, "verify")
        if issued and message:
            try:
                await run_in_threadpool(send_mail, *message)
            except Exception:
                pass  # The user can request a fresh link after mail is configured.
    return updated


@router.get("/me/preferences", response_model=UserPreferencesResponse)
async def get_preferences(user: CurrentUserDep, users: UserRepoDep) -> UserPreferences:
    """The saved preferences, or the defaults if the user hasn't saved any yet."""
    preferences = await users.get_preferences(user.id)
    return preferences or UserPreferences(user_id=user.id, **DEFAULT_PREFERENCES)


@router.patch("/me/preferences", response_model=UserPreferencesResponse)
async def update_preferences(
    payload: UserPreferencesUpdateRequest, user: CurrentUserDep, users: UserRepoDep
) -> UserPreferences:
    """Update the fields sent; the first update creates the row, with defaults for the rest."""
    preferences = await users.get_preferences(user.id)
    if preferences is None:
        preferences = UserPreferences(user_id=user.id, **DEFAULT_PREFERENCES)
    for field in payload.model_fields_set:
        setattr(preferences, field, getattr(payload, field))
    return await users.save_preferences(preferences)
