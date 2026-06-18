import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_tmdb
from app.db import get_session
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
from app.schemas.film import (
    CreditOut,
    FilmDetail,
    FilmSummary,
    NamedRef,
    ProviderOut,
)
from app.services.film_cache import get_or_cache_film, get_or_cache_providers
from app.services.tmdb import TMDBClient

router = APIRouter(prefix="/films", tags=["films"])


@router.get("/search", response_model=list[FilmSummary])
async def search_films(
    q: str = Query(..., min_length=1),
    tmdb: TMDBClient = Depends(get_tmdb),
) -> list[FilmSummary]:
    data = await tmdb.search_movies(q)
    return [FilmSummary.from_tmdb(r) for r in data.get("results", [])]


@router.get("/{tmdb_id}", response_model=FilmDetail)
async def get_film(
    tmdb_id: int,
    region: str = "US",
    session: AsyncSession = Depends(get_session),
    tmdb: TMDBClient = Depends(get_tmdb),
) -> FilmDetail:
    try:
        film = await get_or_cache_film(session, tmdb, tmdb_id, region)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Film not found on TMDB") from exc
        raise HTTPException(status_code=502, detail="TMDB request failed") from exc

    return await _build_film_detail(session, film, region)


@router.get("/{tmdb_id}/providers", response_model=list[ProviderOut])
async def get_film_providers(
    tmdb_id: int,
    region: str = "US",
    session: AsyncSession = Depends(get_session),
    tmdb: TMDBClient = Depends(get_tmdb),
) -> list[ProviderOut]:
    """Lightweight watch-provider lookup used for poster hover previews."""
    try:
        providers = await get_or_cache_providers(session, tmdb, tmdb_id, region)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Film not found on TMDB") from exc
        raise HTTPException(status_code=502, detail="TMDB request failed") from exc

    return [
        ProviderOut(
            provider_id=p.provider_id,
            provider_name=p.provider_name,
            logo_path=p.logo_path,
            offer_type=p.offer_type,
        )
        for p in providers
    ]


async def _build_film_detail(session: AsyncSession, film: Film, region: str) -> FilmDetail:
    genres = (
        await session.execute(
            select(Genre)
            .join(FilmGenre, FilmGenre.genre_id == Genre.id)
            .where(FilmGenre.film_id == film.id)
        )
    ).scalars().all()

    keywords = (
        await session.execute(
            select(Keyword)
            .join(FilmKeyword, FilmKeyword.keyword_id == Keyword.id)
            .where(FilmKeyword.film_id == film.id)
        )
    ).scalars().all()

    credit_rows = (
        await session.execute(
            select(FilmCredit, Person.name)
            .join(Person, Person.id == FilmCredit.person_id)
            .where(FilmCredit.film_id == film.id)
        )
    ).all()

    cast = [
        CreditOut(
            person_id=c.person_id,
            name=name,
            credit_type=c.credit_type,
            job=c.job,
            character=c.character,
        )
        for c, name in sorted(
            (row for row in credit_rows if row[0].credit_type == "cast"),
            key=lambda row: row[0].billing_order if row[0].billing_order is not None else 999,
        )
    ]
    crew = [
        CreditOut(
            person_id=c.person_id,
            name=name,
            credit_type=c.credit_type,
            job=c.job,
            character=c.character,
        )
        for c, name in credit_rows
        if c.credit_type == "crew"
    ]

    providers = (
        await session.execute(
            select(FilmWatchProvider)
            .where(FilmWatchProvider.film_id == film.id)
            .where(FilmWatchProvider.region == region)
        )
    ).scalars().all()

    return FilmDetail(
        tmdb_id=film.tmdb_id,
        media_type=film.media_type,
        title=film.title,
        original_title=film.original_title,
        overview=film.overview,
        release_date=film.release_date,
        runtime=film.runtime,
        poster_path=film.poster_path,
        backdrop_path=film.backdrop_path,
        vote_average=film.vote_average,
        vote_count=film.vote_count,
        region=region,
        genres=[NamedRef(id=g.id, name=g.name) for g in genres],
        keywords=[NamedRef(id=k.id, name=k.name) for k in keywords],
        cast=cast,
        crew=crew,
        watch_providers=[
            ProviderOut(
                provider_id=p.provider_id,
                provider_name=p.provider_name,
                logo_path=p.logo_path,
                offer_type=p.offer_type,
            )
            for p in providers
        ],
    )
