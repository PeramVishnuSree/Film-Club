import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_optional_user, get_tmdb
from app.db import get_session
from app.models import (
    DiaryEntry,
    Film,
    InteractionType,
    Rating,
    Review,
    ReviewLike,
    User,
    WatchlistItem,
)
from app.schemas.film import FilmSummary
from app.schemas.library import (
    DiaryIn,
    DiaryOut,
    FilmMeState,
    RatingIn,
    RatingOut,
    ReviewAuthor,
    ReviewIn,
    ReviewOut,
)
from app.services.film_cache import get_or_cache_film
from app.services.interactions import record_interaction
from app.services.tmdb import TMDBClient

router = APIRouter(tags=["library"])


async def _resolve_film(
    session: AsyncSession, tmdb: TMDBClient, tmdb_id: int, region: str
) -> Film:
    try:
        return await get_or_cache_film(session, tmdb, tmdb_id, region)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Film not found on TMDB") from exc
        raise HTTPException(status_code=502, detail="TMDB request failed") from exc


# ---------------------------------------------------------------- ratings


@router.put("/films/{tmdb_id}/rating", response_model=RatingOut)
async def set_rating(
    tmdb_id: int,
    payload: RatingIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    tmdb: TMDBClient = Depends(get_tmdb),
) -> RatingOut:
    film = await _resolve_film(session, tmdb, tmdb_id, user.region)
    rating = (
        await session.execute(
            select(Rating).where(Rating.user_id == user.id, Rating.film_id == film.id)
        )
    ).scalar_one_or_none()

    if rating is None:
        rating = Rating(user_id=user.id, film_id=film.id, value=payload.value)
        session.add(rating)
    else:
        rating.value = payload.value

    record_interaction(session, user.id, film.id, InteractionType.rate, value=payload.value)
    await session.commit()
    return RatingOut(film_tmdb_id=tmdb_id, value=payload.value)


@router.delete("/films/{tmdb_id}/rating", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rating(
    tmdb_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    film = (
        await session.execute(select(Film).where(Film.tmdb_id == tmdb_id))
    ).scalar_one_or_none()
    if film is not None:
        await session.execute(
            delete(Rating).where(Rating.user_id == user.id, Rating.film_id == film.id)
        )
        await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------- watchlist


@router.post("/films/{tmdb_id}/watchlist", status_code=status.HTTP_201_CREATED)
async def add_to_watchlist(
    tmdb_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    tmdb: TMDBClient = Depends(get_tmdb),
) -> dict[str, bool]:
    film = await _resolve_film(session, tmdb, tmdb_id, user.region)
    existing = (
        await session.execute(
            select(WatchlistItem).where(
                WatchlistItem.user_id == user.id, WatchlistItem.film_id == film.id
            )
        )
    ).scalar_one_or_none()
    if existing is None:
        session.add(WatchlistItem(user_id=user.id, film_id=film.id))
        record_interaction(session, user.id, film.id, InteractionType.watchlist_add)
        await session.commit()
    return {"watchlisted": True}


@router.delete("/films/{tmdb_id}/watchlist", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_watchlist(
    tmdb_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    film = (
        await session.execute(select(Film).where(Film.tmdb_id == tmdb_id))
    ).scalar_one_or_none()
    if film is not None:
        existing = (
            await session.execute(
                select(WatchlistItem).where(
                    WatchlistItem.user_id == user.id, WatchlistItem.film_id == film.id
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            await session.delete(existing)
            record_interaction(
                session, user.id, film.id, InteractionType.watchlist_remove
            )
            await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me/watchlist", response_model=list[FilmSummary])
async def my_watchlist(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=100, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[FilmSummary]:
    rows = (
        await session.execute(
            select(Film)
            .join(WatchlistItem, WatchlistItem.film_id == Film.id)
            .where(WatchlistItem.user_id == user.id)
            .order_by(WatchlistItem.id.desc())  # most recently added first
            .limit(limit)
            .offset(offset)
        )
    ).scalars().all()
    return [
        FilmSummary(
            tmdb_id=film.tmdb_id,
            title=film.title,
            release_date=film.release_date,
            overview=film.overview,
            poster_path=film.poster_path,
            vote_average=film.vote_average,
        )
        for film in rows
    ]


# ---------------------------------------------------------------- diary


@router.post(
    "/films/{tmdb_id}/diary", response_model=DiaryOut, status_code=status.HTTP_201_CREATED
)
async def add_diary_entry(
    tmdb_id: int,
    payload: DiaryIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    tmdb: TMDBClient = Depends(get_tmdb),
) -> DiaryOut:
    film = await _resolve_film(session, tmdb, tmdb_id, user.region)
    entry = DiaryEntry(
        user_id=user.id,
        film_id=film.id,
        watched_on=payload.watched_on,
        rating_value=payload.rating_value,
        liked=payload.liked,
        rewatch=payload.rewatch,
        note=payload.note,
    )
    session.add(entry)
    record_interaction(
        session, user.id, film.id, InteractionType.log, value=payload.rating_value
    )
    await session.commit()
    await session.refresh(entry)
    return DiaryOut(
        id=entry.id,
        film_tmdb_id=film.tmdb_id,
        film_title=film.title,
        poster_path=film.poster_path,
        watched_on=entry.watched_on,
        rating_value=entry.rating_value,
        liked=entry.liked,
        rewatch=entry.rewatch,
        note=entry.note,
        created_at=entry.created_at,
    )


@router.get("/me/diary", response_model=list[DiaryOut])
async def my_diary(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[DiaryOut]:
    rows = (
        await session.execute(
            select(DiaryEntry, Film)
            .join(Film, Film.id == DiaryEntry.film_id)
            .where(DiaryEntry.user_id == user.id)
            .order_by(DiaryEntry.watched_on.desc(), DiaryEntry.id.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return [
        DiaryOut(
            id=entry.id,
            film_tmdb_id=film.tmdb_id,
            film_title=film.title,
            poster_path=film.poster_path,
            watched_on=entry.watched_on,
            rating_value=entry.rating_value,
            liked=entry.liked,
            rewatch=entry.rewatch,
            note=entry.note,
            created_at=entry.created_at,
        )
        for entry, film in rows
    ]


@router.delete("/diary/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_diary_entry(
    entry_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    entry = await session.get(DiaryEntry, entry_id)
    if entry is not None and entry.user_id == user.id:
        await session.delete(entry)
        await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------- reviews


@router.post(
    "/films/{tmdb_id}/reviews", response_model=ReviewOut, status_code=status.HTTP_201_CREATED
)
async def add_review(
    tmdb_id: int,
    payload: ReviewIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    tmdb: TMDBClient = Depends(get_tmdb),
) -> ReviewOut:
    film = await _resolve_film(session, tmdb, tmdb_id, user.region)
    review = Review(
        user_id=user.id,
        film_id=film.id,
        diary_entry_id=payload.diary_entry_id,
        body=payload.body,
        contains_spoilers=payload.contains_spoilers,
    )
    session.add(review)
    record_interaction(session, user.id, film.id, InteractionType.review)
    await session.commit()
    await session.refresh(review)
    return ReviewOut(
        id=review.id,
        film_tmdb_id=film.tmdb_id,
        author=ReviewAuthor(
            id=user.id, username=user.username, display_name=user.display_name
        ),
        body=review.body,
        contains_spoilers=review.contains_spoilers,
        created_at=review.created_at,
    )


@router.get("/films/{tmdb_id}/reviews", response_model=list[ReviewOut])
async def list_reviews(
    tmdb_id: int,
    session: AsyncSession = Depends(get_session),
    viewer: User | None = Depends(get_optional_user),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[ReviewOut]:
    film = (
        await session.execute(select(Film).where(Film.tmdb_id == tmdb_id))
    ).scalar_one_or_none()
    if film is None:
        return []
    rows = (
        await session.execute(
            select(Review, User)
            .join(User, User.id == Review.user_id)
            .where(Review.film_id == film.id)
            .order_by(Review.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()
    review_ids = [review.id for review, _ in rows]

    # Like counts for the reviews on this page, in one grouped query.
    like_counts: dict[int, int] = {}
    if review_ids:
        count_rows = (
            await session.execute(
                select(ReviewLike.review_id, func.count())
                .where(ReviewLike.review_id.in_(review_ids))
                .group_by(ReviewLike.review_id)
            )
        ).all()
        like_counts = {rid: count for rid, count in count_rows}

    # Which of these the viewer has liked (empty set when logged out).
    liked_ids: set[int] = set()
    if viewer is not None and review_ids:
        liked_ids = set(
            (
                await session.execute(
                    select(ReviewLike.review_id).where(
                        ReviewLike.user_id == viewer.id,
                        ReviewLike.review_id.in_(review_ids),
                    )
                )
            )
            .scalars()
            .all()
        )

    return [
        ReviewOut(
            id=review.id,
            film_tmdb_id=tmdb_id,
            author=ReviewAuthor(
                id=author.id, username=author.username, display_name=author.display_name
            ),
            body=review.body,
            contains_spoilers=review.contains_spoilers,
            created_at=review.created_at,
            like_count=like_counts.get(review.id, 0),
            liked=review.id in liked_ids,
        )
        for review, author in rows
    ]


@router.post("/reviews/{review_id}/like", status_code=status.HTTP_201_CREATED)
async def like_review(
    review_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool | int]:
    review = await session.get(Review, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    existing = (
        await session.execute(
            select(ReviewLike).where(
                ReviewLike.user_id == user.id, ReviewLike.review_id == review_id
            )
        )
    ).scalar_one_or_none()
    if existing is None:
        session.add(ReviewLike(user_id=user.id, review_id=review_id))
        await session.commit()
    count = (
        await session.execute(
            select(func.count()).select_from(ReviewLike).where(
                ReviewLike.review_id == review_id
            )
        )
    ).scalar_one()
    return {"liked": True, "like_count": count}


@router.delete("/reviews/{review_id}/like", status_code=status.HTTP_200_OK)
async def unlike_review(
    review_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool | int]:
    await session.execute(
        delete(ReviewLike).where(
            ReviewLike.user_id == user.id, ReviewLike.review_id == review_id
        )
    )
    await session.commit()
    count = (
        await session.execute(
            select(func.count()).select_from(ReviewLike).where(
                ReviewLike.review_id == review_id
            )
        )
    ).scalar_one()
    return {"liked": False, "like_count": count}


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    review = await session.get(Review, review_id)
    if review is not None and review.user_id == user.id:
        await session.delete(review)
        await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------- film state


@router.get("/films/{tmdb_id}/me", response_model=FilmMeState)
async def my_film_state(
    tmdb_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> FilmMeState:
    film = (
        await session.execute(select(Film).where(Film.tmdb_id == tmdb_id))
    ).scalar_one_or_none()
    if film is None:
        return FilmMeState()

    rating = (
        await session.execute(
            select(Rating.value).where(
                Rating.user_id == user.id, Rating.film_id == film.id
            )
        )
    ).scalar_one_or_none()
    watchlisted = (
        await session.execute(
            select(WatchlistItem.id).where(
                WatchlistItem.user_id == user.id, WatchlistItem.film_id == film.id
            )
        )
    ).first() is not None
    watched = (
        await session.execute(
            select(DiaryEntry.id).where(
                DiaryEntry.user_id == user.id, DiaryEntry.film_id == film.id
            ).limit(1)
        )
    ).first() is not None

    return FilmMeState(rating=rating, watchlisted=watchlisted, watched=watched)
