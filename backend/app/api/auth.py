from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.ratelimit import rate_limit
from app.core.security import (
    create_access_token,
    create_email_verify_token,
    create_password_reset_token,
    hash_password,
    read_token_subject,
    verify_email_verify_token,
    verify_password,
    verify_password_reset_token,
)
from app.db import get_session
from app.models import User
from app.schemas.auth import (
    EmailVerifyConfirm,
    MessageOut,
    PasswordResetConfirm,
    PasswordResetRequest,
    Token,
    UserCreate,
    UserLogin,
    UserOut,
    UserUpdate,
)
from app.services.email import send_password_reset_email, send_verification_email

router = APIRouter(prefix="/auth", tags=["auth"])

# Per-IP brute-force / abuse limits on the sensitive flows. Generous enough not
# to trip up real users, tight enough to make online guessing impractical.
_login_limit = rate_limit(max_hits=10, window_seconds=60, scope="login")
_signup_limit = rate_limit(max_hits=5, window_seconds=3600, scope="signup")
_reset_limit = rate_limit(max_hits=5, window_seconds=3600, scope="pwreset")


@router.post(
    "/signup",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_signup_limit)],
)
async def signup(payload: UserCreate, session: AsyncSession = Depends(get_session)) -> Token:
    existing = (
        await session.execute(
            select(User).where(
                or_(User.username == payload.username, User.email == payload.email)
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already taken",
        )

    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        display_name=payload.display_name,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # Kick off email verification (logged to console when SMTP isn't configured).
    await send_verification_email(user.email, create_email_verify_token(user.id))

    token = create_access_token(user.id)
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=Token, dependencies=[Depends(_login_limit)])
async def login(payload: UserLogin, session: AsyncSession = Depends(get_session)) -> Token:
    user = (
        await session.execute(
            select(User).where(
                or_(User.username == payload.identifier, User.email == payload.identifier)
            )
        )
    ).scalar_one_or_none()

    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
        )

    token = create_access_token(user.id)
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)


@router.patch("/me", response_model=UserOut)
async def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UserOut:
    # exclude_unset: only overwrite fields the client actually sent, so a
    # partial update can't accidentally null out untouched fields.
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        if field == "region" and value is not None:
            value = value.upper()
        if field in ("display_name", "bio", "avatar_url") and value == "":
            value = None  # treat a cleared field as null
        setattr(current_user, field, value)
    await session.commit()
    await session.refresh(current_user)
    return UserOut.model_validate(current_user)


# ---------------------------------------------------------------- password reset


@router.post(
    "/password-reset/request",
    response_model=MessageOut,
    dependencies=[Depends(_reset_limit)],
)
async def request_password_reset(
    payload: PasswordResetRequest, session: AsyncSession = Depends(get_session)
) -> MessageOut:
    """Email a reset link if the address belongs to an account.

    Always returns the same response whether or not the email exists, so the
    endpoint can't be used to enumerate registered addresses.
    """
    user = (
        await session.execute(select(User).where(User.email == payload.email))
    ).scalar_one_or_none()
    if user is not None:
        token = create_password_reset_token(user.id, user.hashed_password)
        await send_password_reset_email(user.email, token)
    return MessageOut(detail="If that email is registered, a reset link is on its way.")


@router.post("/password-reset/confirm", response_model=MessageOut)
async def confirm_password_reset(
    payload: PasswordResetConfirm, session: AsyncSession = Depends(get_session)
) -> MessageOut:
    user_id = read_token_subject(payload.token)
    user = await session.get(User, user_id) if user_id is not None else None
    if user is None or not verify_password_reset_token(payload.token, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset link is invalid or has expired.",
        )
    # Changing the hash invalidates the token (it was signed against the old one).
    user.hashed_password = hash_password(payload.new_password)
    await session.commit()
    return MessageOut(detail="Your password has been reset. You can now log in.")


# ---------------------------------------------------------------- email verify


@router.post("/verify-email/request", response_model=MessageOut)
async def request_email_verification(
    current_user: User = Depends(get_current_user),
) -> MessageOut:
    if current_user.email_verified:
        return MessageOut(detail="Your email is already verified.")
    await send_verification_email(
        current_user.email, create_email_verify_token(current_user.id)
    )
    return MessageOut(detail="Verification email sent.")


@router.post("/verify-email/confirm", response_model=MessageOut)
async def confirm_email_verification(
    payload: EmailVerifyConfirm, session: AsyncSession = Depends(get_session)
) -> MessageOut:
    user_id = read_token_subject(payload.token)
    if user_id is None or not verify_email_verify_token(payload.token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This verification link is invalid or has expired.",
        )
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This verification link is invalid or has expired.",
        )
    if not user.email_verified:
        user.email_verified = True
        await session.commit()
    return MessageOut(detail="Your email has been verified. Thanks!")
