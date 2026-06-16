from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_optional_user
from app.db import get_session
from app.models import (
    DiaryEntry,
    Film,
    Follow,
    Interaction,
    InteractionType,
    Review,
    User,
)
from app.schemas.social import FeedFilm, FeedItem, ProfileOut, ProfileStats, UserCard

router = APIRouter(tags=["social"])

# Interaction types worth surfacing in a feed (excludes view / watchlist_remove).
FEED_TYPES = [
    InteractionType.log,
    InteractionType.rate,
    InteractionType.review,
    InteractionType.watchlist_add,
    InteractionType.like,
    InteractionType.list_add,
]


async def _get_user_by_username(session: AsyncSession, username: str) -> User:
    user = (
        await session.execute(select(User).where(User.username == username))
    ).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def _is_following(session: AsyncSession, follower_id: int, followee_id: int) -> bool:
    return (
        await session.execute(
            select(Follow.id).where(
                Follow.follower_id == follower_id, Follow.followee_id == followee_id
            )
        )
    ).first() is not None


async def _build_feed(
    session: AsyncSession,
    where: ColumnElement[bool],
    limit: int,
    offset: int,
) -> list[FeedItem]:
    rows = (
        await session.execute(
            select(Interaction, User, Film)
            .join(User, User.id == Interaction.user_id)
            .join(Film, Film.id == Interaction.film_id)
            .where(Interaction.type.in_(FEED_TYPES))
            .where(where)
            .order_by(Interaction.id.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return [
        FeedItem(
            id=interaction.id,
            actor=UserCard.model_validate(actor),
            type=interaction.type.value,
            value=interaction.value,
            film=FeedFilm(
                tmdb_id=film.tmdb_id, title=film.title, poster_path=film.poster_path
            ),
            created_at=interaction.created_at,
        )
        for interaction, actor, film in rows
    ]


# ------------------------------------------------------------------ profile


@router.get("/users/{username}", response_model=ProfileOut)
async def get_profile(
    username: str,
    session: AsyncSession = Depends(get_session),
    viewer: User | None = Depends(get_optional_user),
) -> ProfileOut:
    user = await _get_user_by_username(session, username)

    films_logged = (
        await session.execute(
            select(func.count(func.distinct(DiaryEntry.film_id))).where(
                DiaryEntry.user_id == user.id
            )
        )
    ).scalar_one()
    reviews = (
        await session.execute(
            select(func.count(Review.id)).where(Review.user_id == user.id)
        )
    ).scalar_one()
    followers = (
        await session.execute(
            select(func.count(Follow.id)).where(Follow.followee_id == user.id)
        )
    ).scalar_one()
    following = (
        await session.execute(
            select(func.count(Follow.id)).where(Follow.follower_id == user.id)
        )
    ).scalar_one()

    is_self = viewer is not None and viewer.id == user.id
    is_following = (
        await _is_following(session, viewer.id, user.id)
        if viewer is not None and not is_self
        else False
    )

    return ProfileOut(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        bio=user.bio,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
        stats=ProfileStats(
            films_logged=films_logged,
            reviews=reviews,
            followers=followers,
            following=following,
        ),
        is_following=is_following,
        is_self=is_self,
    )


@router.get("/users/{username}/activity", response_model=list[FeedItem])
async def get_user_activity(
    username: str,
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=30, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[FeedItem]:
    user = await _get_user_by_username(session, username)
    return await _build_feed(session, Interaction.user_id == user.id, limit, offset)


@router.get("/users/{username}/followers", response_model=list[UserCard])
async def get_followers(
    username: str,
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[UserCard]:
    user = await _get_user_by_username(session, username)
    rows = (
        await session.execute(
            select(User)
            .join(Follow, Follow.follower_id == User.id)
            .where(Follow.followee_id == user.id)
            .order_by(Follow.id.desc())
            .limit(limit)
            .offset(offset)
        )
    ).scalars().all()
    return [UserCard.model_validate(u) for u in rows]


@router.get("/users/{username}/following", response_model=list[UserCard])
async def get_following(
    username: str,
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[UserCard]:
    user = await _get_user_by_username(session, username)
    rows = (
        await session.execute(
            select(User)
            .join(Follow, Follow.followee_id == User.id)
            .where(Follow.follower_id == user.id)
            .order_by(Follow.id.desc())
            .limit(limit)
            .offset(offset)
        )
    ).scalars().all()
    return [UserCard.model_validate(u) for u in rows]


# ------------------------------------------------------------------ follow


@router.post("/users/{username}/follow", status_code=status.HTTP_201_CREATED)
async def follow_user(
    username: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    target = await _get_user_by_username(session, username)
    if target.id == user.id:
        raise HTTPException(status_code=400, detail="You cannot follow yourself")
    if not await _is_following(session, user.id, target.id):
        session.add(Follow(follower_id=user.id, followee_id=target.id))
        await session.commit()
    return {"following": True}


@router.delete("/users/{username}/follow", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow_user(
    username: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    target = await _get_user_by_username(session, username)
    existing = (
        await session.execute(
            select(Follow).where(
                Follow.follower_id == user.id, Follow.followee_id == target.id
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        await session.delete(existing)
        await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ------------------------------------------------------------------ feed


@router.get("/me/feed", response_model=list[FeedItem])
async def my_feed(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=30, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[FeedItem]:
    """Recent activity from the people the current user follows."""
    followees = select(Follow.followee_id).where(Follow.follower_id == user.id)
    return await _build_feed(session, Interaction.user_id.in_(followees), limit, offset)
