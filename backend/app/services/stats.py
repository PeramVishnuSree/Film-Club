"""Profile statistics and year-in-review aggregations.

All computed with SQL aggregates scoped to a single user. Lifetime numbers
cover all activity; the year block drills into one calendar year (watched_on).
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import Integer, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    DiaryEntry,
    Film,
    FilmGenre,
    Genre,
    List,
    Rating,
    Review,
    User,
)
from app.schemas.stats import (
    GenreCount,
    LifetimeStats,
    MonthCount,
    RatingBucket,
    StatsOut,
    TopFilm,
    YearStats,
)


async def _lifetime(session: AsyncSession, user_id: int) -> LifetimeStats:
    films_logged = (
        await session.execute(
            select(func.count(func.distinct(DiaryEntry.film_id))).where(
                DiaryEntry.user_id == user_id
            )
        )
    ).scalar_one()
    entries = (
        await session.execute(
            select(func.count(DiaryEntry.id)).where(DiaryEntry.user_id == user_id)
        )
    ).scalar_one()
    ratings = (
        await session.execute(
            select(func.count(Rating.id)).where(Rating.user_id == user_id)
        )
    ).scalar_one()
    reviews = (
        await session.execute(
            select(func.count(Review.id)).where(Review.user_id == user_id)
        )
    ).scalar_one()
    lists = (
        await session.execute(
            select(func.count(List.id)).where(List.user_id == user_id)
        )
    ).scalar_one()
    avg_rating = (
        await session.execute(
            select(func.avg(Rating.value)).where(Rating.user_id == user_id)
        )
    ).scalar_one()

    dist_rows = (
        await session.execute(
            select(Rating.value, func.count(Rating.id))
            .where(Rating.user_id == user_id)
            .group_by(Rating.value)
        )
    ).all()
    by_value = {float(v): c for v, c in dist_rows}
    # Always emit all ten half-star buckets so the chart has a stable shape.
    distribution = [
        RatingBucket(value=v / 2, count=by_value.get(v / 2, 0))
        for v in range(1, 11)
    ]

    return LifetimeStats(
        films_logged=films_logged,
        entries=entries,
        ratings=ratings,
        reviews=reviews,
        lists=lists,
        average_rating=round(float(avg_rating), 2) if avg_rating is not None else None,
        rating_distribution=distribution,
    )


async def _year(session: AsyncSession, user_id: int, year: int) -> YearStats:
    start = date(year, 1, 1)
    end = date(year + 1, 1, 1)
    in_year = (DiaryEntry.watched_on >= start) & (DiaryEntry.watched_on < end)

    entries = (
        await session.execute(
            select(func.count(DiaryEntry.id)).where(
                DiaryEntry.user_id == user_id, in_year
            )
        )
    ).scalar_one()
    distinct_films = (
        await session.execute(
            select(func.count(func.distinct(DiaryEntry.film_id))).where(
                DiaryEntry.user_id == user_id, in_year
            )
        )
    ).scalar_one()
    runtime_minutes = (
        await session.execute(
            select(func.coalesce(func.sum(Film.runtime), 0))
            .select_from(DiaryEntry)
            .join(Film, Film.id == DiaryEntry.film_id)
            .where(DiaryEntry.user_id == user_id, in_year)
        )
    ).scalar_one()

    month_expr = cast(func.extract("month", DiaryEntry.watched_on), Integer)
    month_rows = (
        await session.execute(
            select(month_expr.label("m"), func.count(DiaryEntry.id))
            .where(DiaryEntry.user_id == user_id, in_year)
            .group_by("m")
        )
    ).all()
    by_month_map = {int(m): c for m, c in month_rows}
    by_month = [MonthCount(month=m, count=by_month_map.get(m, 0)) for m in range(1, 13)]

    genre_rows = (
        await session.execute(
            select(Genre.name, func.count(DiaryEntry.id).label("c"))
            .select_from(DiaryEntry)
            .join(FilmGenre, FilmGenre.film_id == DiaryEntry.film_id)
            .join(Genre, Genre.id == FilmGenre.genre_id)
            .where(DiaryEntry.user_id == user_id, in_year)
            .group_by(Genre.name)
            .order_by(func.count(DiaryEntry.id).desc())
            .limit(8)
        )
    ).all()
    top_genres = [GenreCount(name=n, count=c) for n, c in genre_rows]

    # Highest-rated films logged this year (prefer the diary rating).
    film_rows = (
        await session.execute(
            select(
                Film.tmdb_id,
                Film.title,
                Film.poster_path,
                func.max(DiaryEntry.rating_value).label("r"),
            )
            .select_from(DiaryEntry)
            .join(Film, Film.id == DiaryEntry.film_id)
            .where(
                DiaryEntry.user_id == user_id,
                in_year,
                DiaryEntry.rating_value.isnot(None),
            )
            .group_by(Film.tmdb_id, Film.title, Film.poster_path)
            .order_by(func.max(DiaryEntry.rating_value).desc())
            .limit(5)
        )
    ).all()
    top_films = [
        TopFilm(tmdb_id=t, title=title, poster_path=p, rating=float(r) if r else None)
        for t, title, p, r in film_rows
    ]

    return YearStats(
        year=year,
        entries=entries,
        distinct_films=distinct_films,
        hours=round(int(runtime_minutes) / 60, 1),
        by_month=by_month,
        top_genres=top_genres,
        top_films=top_films,
    )


async def _available_years(session: AsyncSession, user_id: int) -> list[int]:
    year_expr = cast(func.extract("year", DiaryEntry.watched_on), Integer)
    rows = (
        await session.execute(
            select(year_expr.label("y"))
            .where(DiaryEntry.user_id == user_id)
            .group_by("y")
            .order_by(year_expr.desc())
        )
    ).all()
    return [int(y) for (y,) in rows]


async def get_stats(
    session: AsyncSession, user: User, year: int | None
) -> StatsOut:
    available = await _available_years(session, user.id)
    target = year or (available[0] if available else date.today().year)
    return StatsOut(
        lifetime=await _lifetime(session, user.id),
        year=await _year(session, user.id, target),
        available_years=available,
    )
