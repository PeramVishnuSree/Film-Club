from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db import get_session
from app.models import User
from app.schemas.auth import Token, UserCreate, UserLogin, UserOut, UserUpdate

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
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

    token = create_access_token(user.id)
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=Token)
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
