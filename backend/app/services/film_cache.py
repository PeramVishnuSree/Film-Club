from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Film,
    FilmCredit,
    FilmGenre,
    FilmKeyword,
    FilmWatchProvider,
    Genre,
    Keyword,
    Person,
)
from app.services.tmdb import TMDBClient

# Crew jobs worth keeping as recommender features / display.
CREW_JOBS = {
    "Director",
    "Writer",
    "Screenplay",
    "Producer",
    "Director of Photography",
    "Original Music Composer",
    "Editor",
}
MAX_CAST = 20
CACHE_TTL = timedelta(hours=24)


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _is_fresh(film: Film) -> bool:
    if film.tmdb_synced_at is None:
        return False
    synced = film.tmdb_synced_at
    if synced.tzinfo is None:
        synced = synced.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - synced < CACHE_TTL


def _film_summary_fields(data: dict[str, Any]) -> dict[str, Any]:
    return dict(
        tmdb_id=data["id"],
        media_type="movie",
        title=data.get("title") or data.get("name") or "",
        original_title=data.get("original_title"),
        overview=data.get("overview"),
        release_date=_parse_date(data.get("release_date")),
        original_language=data.get("original_language"),
        poster_path=data.get("poster_path"),
        backdrop_path=data.get("backdrop_path"),
        popularity=data.get("popularity"),
        vote_average=data.get("vote_average"),
        vote_count=data.get("vote_count"),
    )


async def upsert_film_summary(session: AsyncSession, data: dict[str, Any]) -> int:
    """Insert/refresh a lightweight film row (no credits/keywords/providers).

    Used to seed lists in bulk without a full detail fetch per film. Leaves
    tmdb_synced_at untouched so a later detail view still enriches the row.
    Returns the local film id.
    """
    fields = _film_summary_fields(data)
    stmt = pg_insert(Film).values(**fields)
    update_cols = {key: stmt.excluded[key] for key in fields if key != "tmdb_id"}
    stmt = stmt.on_conflict_do_update(
        index_elements=[Film.tmdb_id], set_=update_cols
    ).returning(Film.id)
    return (await session.execute(stmt)).scalar_one()


async def get_or_cache_film(
    session: AsyncSession, client: TMDBClient, tmdb_id: int, region: str = "US"
) -> Film:
    film = (
        await session.execute(select(Film).where(Film.tmdb_id == tmdb_id))
    ).scalar_one_or_none()

    if film is not None and _is_fresh(film):
        # Watch providers are region-specific; make sure this region is cached.
        has_region = (
            await session.execute(
                select(FilmWatchProvider.id)
                .where(FilmWatchProvider.film_id == film.id)
                .where(FilmWatchProvider.region == region)
                .limit(1)
            )
        ).first()
        if has_region:
            return film

    data = await client.get_movie(tmdb_id)
    film = await _upsert_film(session, film, data)
    await _sync_genres(session, film, data)
    await _sync_keywords(session, film, data)
    await _sync_credits(session, film, data)
    await _sync_watch_providers(session, film, data, region)
    await session.commit()
    await session.refresh(film)
    return film


async def _upsert_film(session: AsyncSession, film: Film | None, data: dict[str, Any]) -> Film:
    fields = dict(
        tmdb_id=data["id"],
        media_type="movie",
        title=data.get("title") or data.get("name") or "",
        original_title=data.get("original_title"),
        overview=data.get("overview"),
        release_date=_parse_date(data.get("release_date")),
        runtime=data.get("runtime"),
        original_language=data.get("original_language"),
        poster_path=data.get("poster_path"),
        backdrop_path=data.get("backdrop_path"),
        popularity=data.get("popularity"),
        vote_average=data.get("vote_average"),
        vote_count=data.get("vote_count"),
        tmdb_synced_at=datetime.now(timezone.utc),
    )
    if film is None:
        film = Film(**fields)
        session.add(film)
    else:
        for key, value in fields.items():
            setattr(film, key, value)
    await session.flush()
    return film


async def _sync_genres(session: AsyncSession, film: Film, data: dict[str, Any]) -> None:
    genres = data.get("genres", [])
    for genre in genres:
        await session.execute(
            pg_insert(Genre)
            .values(id=genre["id"], name=genre["name"])
            .on_conflict_do_nothing(index_elements=[Genre.id])
        )
    await session.execute(delete(FilmGenre).where(FilmGenre.film_id == film.id))
    for genre in genres:
        await session.execute(
            pg_insert(FilmGenre)
            .values(film_id=film.id, genre_id=genre["id"])
            .on_conflict_do_nothing()
        )


async def _sync_keywords(session: AsyncSession, film: Film, data: dict[str, Any]) -> None:
    keywords = (data.get("keywords") or {}).get("keywords", [])
    for kw in keywords:
        await session.execute(
            pg_insert(Keyword)
            .values(id=kw["id"], name=kw["name"])
            .on_conflict_do_nothing(index_elements=[Keyword.id])
        )
    await session.execute(delete(FilmKeyword).where(FilmKeyword.film_id == film.id))
    for kw in keywords:
        await session.execute(
            pg_insert(FilmKeyword)
            .values(film_id=film.id, keyword_id=kw["id"])
            .on_conflict_do_nothing()
        )


async def _sync_credits(session: AsyncSession, film: Film, data: dict[str, Any]) -> None:
    credits = data.get("credits") or {}
    cast = [c for c in credits.get("cast", []) if c.get("order", 999) < MAX_CAST]
    crew = [c for c in credits.get("crew", []) if c.get("job") in CREW_JOBS]

    people = {c["id"]: c for c in cast + crew}
    for person in people.values():
        await session.execute(
            pg_insert(Person)
            .values(
                id=person["id"],
                name=person.get("name", ""),
                profile_path=person.get("profile_path"),
            )
            .on_conflict_do_nothing(index_elements=[Person.id])
        )

    await session.execute(delete(FilmCredit).where(FilmCredit.film_id == film.id))
    for c in cast:
        await session.execute(
            pg_insert(FilmCredit)
            .values(
                film_id=film.id,
                person_id=c["id"],
                credit_type="cast",
                job=None,
                character=c.get("character"),
                billing_order=c.get("order"),
            )
            .on_conflict_do_nothing()
        )
    for c in crew:
        await session.execute(
            pg_insert(FilmCredit)
            .values(
                film_id=film.id,
                person_id=c["id"],
                credit_type="crew",
                job=c.get("job"),
                character=None,
                billing_order=None,
            )
            .on_conflict_do_nothing()
        )


async def _sync_watch_providers(
    session: AsyncSession, film: Film, data: dict[str, Any], region: str
) -> None:
    results = (data.get("watch/providers") or {}).get("results", {})
    region_data = results.get(region, {})

    await session.execute(
        delete(FilmWatchProvider)
        .where(FilmWatchProvider.film_id == film.id)
        .where(FilmWatchProvider.region == region)
    )
    now = datetime.now(timezone.utc)
    for offer_type in ("flatrate", "rent", "buy"):
        for provider in region_data.get(offer_type, []):
            await session.execute(
                pg_insert(FilmWatchProvider)
                .values(
                    film_id=film.id,
                    region=region,
                    provider_id=provider["provider_id"],
                    provider_name=provider.get("provider_name", ""),
                    logo_path=provider.get("logo_path"),
                    offer_type=offer_type,
                    synced_at=now,
                )
                .on_conflict_do_nothing()
            )
