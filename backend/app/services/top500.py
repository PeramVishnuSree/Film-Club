from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import List, ListItem
from app.services.film_cache import upsert_film_summary
from app.services.tmdb import TMDBClient

TOP_500_TITLE = "Top 500"
TOP_500_DESCRIPTION = "The 500 highest-rated films, generated from TMDB ratings."
# Pull a larger candidate pool, then re-rank with a Bayesian weighted score so
# low-vote anomalies don't outrank well-established films.
CANDIDATE_PAGES = 50  # 20 films/page -> ~1000 candidates
TOP_N = 500
MIN_VOTES = 3000  # Bayesian prior strength (m): votes needed to "trust" a rating


def _weighted_rating(vote_average: float, vote_count: int, mean: float) -> float:
    """IMDb-style Bayesian average: pull sparse-vote ratings toward the pool mean."""
    v = vote_count
    return (v / (v + MIN_VOTES)) * vote_average + (MIN_VOTES / (v + MIN_VOTES)) * mean


async def get_top_500_list(session: AsyncSession) -> List | None:
    return (
        await session.execute(
            select(List).where(List.is_system.is_(True), List.title == TOP_500_TITLE)
        )
    ).scalar_one_or_none()


async def refresh_top_500(session: AsyncSession, client: TMDBClient) -> int:
    """(Re)build the Top 500 system list from TMDB top-rated films."""
    film_list = await get_top_500_list(session)
    if film_list is None:
        film_list = List(
            user_id=None,
            title=TOP_500_TITLE,
            description=TOP_500_DESCRIPTION,
            is_ranked=True,
            is_public=True,
            is_system=True,
        )
        session.add(film_list)
        await session.flush()

    await session.execute(delete(ListItem).where(ListItem.list_id == film_list.id))

    # Gather a deduped candidate pool with the data needed to re-rank.
    candidates: dict[int, dict] = {}
    for page in range(1, CANDIDATE_PAGES + 1):
        data = await client.top_rated_movies(page)
        for movie in data.get("results", []):
            if movie["id"] in candidates:
                continue
            if movie.get("vote_count") and movie.get("vote_average") is not None:
                candidates[movie["id"]] = movie

    if not candidates:
        await session.commit()
        return 0

    pool = list(candidates.values())
    mean = sum(m["vote_average"] for m in pool) / len(pool)
    pool.sort(
        key=lambda m: _weighted_rating(m["vote_average"], m["vote_count"], mean),
        reverse=True,
    )

    rank = 0
    for movie in pool[:TOP_N]:
        rank += 1
        film_id = await upsert_film_summary(session, movie)
        session.add(ListItem(list_id=film_list.id, film_id=film_id, rank=rank))

    await session.commit()
    return rank
