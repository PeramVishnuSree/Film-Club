from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import List, ListItem
from app.services.film_cache import upsert_film_summary
from app.services.tmdb import TMDBClient

TOP_500_TITLE = "Top 500"
TOP_500_DESCRIPTION = "The 500 highest-rated films, generated from TMDB ratings."
PAGES = 25  # 20 films per page = 500.


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

    rank = 0
    seen: set[int] = set()
    for page in range(1, PAGES + 1):
        data = await client.top_rated_movies(page)
        for movie in data.get("results", []):
            if movie["id"] in seen:
                continue
            seen.add(movie["id"])
            rank += 1
            film_id = await upsert_film_summary(session, movie)
            session.add(ListItem(list_id=film_list.id, film_id=film_id, rank=rank))

    await session.commit()
    return rank
