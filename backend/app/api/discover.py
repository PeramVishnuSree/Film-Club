from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_tmdb
from app.db import get_session
from app.models import Film, ListItem, User
from app.schemas.discover import RankedFilm
from app.schemas.film import FilmSummary
from app.schemas.recommend import RecommendedFilm
from app.services.recommend import get_recommendations
from app.services.tmdb import TMDBClient
from app.services.top500 import get_top_500_list, refresh_top_500

router = APIRouter(prefix="/discover", tags=["discover"])


@router.get("/trending", response_model=list[FilmSummary])
async def trending(
    window: str = Query(default="week", pattern="^(day|week)$"),
    tmdb: TMDBClient = Depends(get_tmdb),
) -> list[FilmSummary]:
    data = await tmdb.trending_movies(window)
    return [FilmSummary.from_tmdb(r) for r in data.get("results", [])]


@router.get("/top500", response_model=list[RankedFilm])
async def top500(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[RankedFilm]:
    film_list = await get_top_500_list(session)
    if film_list is None:
        return []
    rows = (
        await session.execute(
            select(ListItem.rank, Film)
            .join(Film, Film.id == ListItem.film_id)
            .where(ListItem.list_id == film_list.id)
            .order_by(ListItem.rank)
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return [
        RankedFilm(
            rank=rank,
            tmdb_id=film.tmdb_id,
            title=film.title,
            release_date=film.release_date,
            overview=film.overview,
            poster_path=film.poster_path,
            vote_average=film.vote_average,
        )
        for rank, film in rows
    ]


@router.get("/recommendations", response_model=list[RecommendedFilm])
async def recommendations(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=20, ge=1, le=50),
) -> list[RecommendedFilm]:
    """Personalized picks from the people you follow, topped up with popular films."""
    return await get_recommendations(session, user, limit)


@router.post("/top500/refresh")
async def refresh_top500(
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    tmdb: TMDBClient = Depends(get_tmdb),
) -> dict[str, int]:
    count = await refresh_top_500(session, tmdb)
    return {"count": count}
