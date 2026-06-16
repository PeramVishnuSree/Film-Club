"""Recommendations v1.

A lightweight, explainable recommender driven by the social graph and the
positive signals already in the database. Two sources, in priority order:

1. **Social** — films that people you follow rated highly or liked, that you
   haven't engaged with yet. Scored by how many of your followees endorsed it.
2. **Popular fallback** — well-rated films from the cache, used to top up the
   list when your graph is sparse (e.g. you follow nobody yet).

Everything runs off small per-user result sets, so we aggregate in Python
rather than reaching for window functions. Good enough at this scale and far
easier to reason about.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DiaryEntry, Film, Follow, Rating, User, WatchlistItem
from app.schemas.recommend import RecommendedFilm

# A rating at or above this counts as a positive endorsement.
POSITIVE_RATING = 3.5


@dataclass
class _Candidate:
    film_id: int
    endorsers: set[int] = field(default_factory=set)
    rating_sum: float = 0.0
    rating_n: int = 0

    @property
    def avg_rating(self) -> float | None:
        return self.rating_sum / self.rating_n if self.rating_n else None

    def sort_key(self) -> tuple:
        # More distinct endorsers first, then higher average rating.
        return (len(self.endorsers), self.avg_rating or 0.0)


async def _seen_film_ids(session: AsyncSession, user_id: int) -> set[int]:
    """Films the user has already rated, logged, or watchlisted — to exclude."""
    seen: set[int] = set()
    for stmt in (
        select(Rating.film_id).where(Rating.user_id == user_id),
        select(DiaryEntry.film_id).where(DiaryEntry.user_id == user_id),
        select(WatchlistItem.film_id).where(WatchlistItem.user_id == user_id),
    ):
        seen.update((await session.execute(stmt)).scalars().all())
    return seen


def _reason(
    candidate: _Candidate, names: dict[int, str]
) -> str:
    endorsers = [names.get(uid, "someone") for uid in candidate.endorsers]
    n = len(endorsers)
    avg = candidate.avg_rating
    rated = f" ({avg:.1f}★ avg)" if avg is not None else ""
    if n == 1:
        return f"{endorsers[0]} rated this highly{rated}"
    if n == 2:
        return f"{endorsers[0]} and {endorsers[1]} liked this{rated}"
    return f"{endorsers[0]} and {n - 1} others you follow liked this{rated}"


def _to_summary(film: Film, reason: str) -> RecommendedFilm:
    return RecommendedFilm(
        tmdb_id=film.tmdb_id,
        title=film.title,
        release_date=film.release_date,
        overview=film.overview,
        poster_path=film.poster_path,
        vote_average=film.vote_average,
        reason=reason,
    )


async def get_recommendations(
    session: AsyncSession, user: User, limit: int = 20
) -> list[RecommendedFilm]:
    seen = await _seen_film_ids(session, user.id)

    followee_ids = (
        await session.execute(
            select(Follow.followee_id).where(Follow.follower_id == user.id)
        )
    ).scalars().all()

    candidates: dict[int, _Candidate] = {}

    if followee_ids:
        # High ratings from followees.
        rating_rows = (
            await session.execute(
                select(Rating.film_id, Rating.user_id, Rating.value).where(
                    Rating.user_id.in_(followee_ids),
                    Rating.value >= POSITIVE_RATING,
                )
            )
        ).all()
        for film_id, uid, value in rating_rows:
            if film_id in seen:
                continue
            cand = candidates.setdefault(film_id, _Candidate(film_id=film_id))
            cand.endorsers.add(uid)
            cand.rating_sum += value
            cand.rating_n += 1

        # Diary logs from followees that were liked or highly rated.
        diary_rows = (
            await session.execute(
                select(
                    DiaryEntry.film_id, DiaryEntry.user_id, DiaryEntry.rating_value
                ).where(
                    DiaryEntry.user_id.in_(followee_ids),
                    (DiaryEntry.liked.is_(True))
                    | (DiaryEntry.rating_value >= POSITIVE_RATING),
                )
            )
        ).all()
        for film_id, uid, rating_value in diary_rows:
            if film_id in seen:
                continue
            cand = candidates.setdefault(film_id, _Candidate(film_id=film_id))
            cand.endorsers.add(uid)
            if rating_value is not None:
                cand.rating_sum += rating_value
                cand.rating_n += 1

    ranked = sorted(
        candidates.values(), key=lambda c: c.sort_key(), reverse=True
    )[:limit]

    results: list[RecommendedFilm] = []
    picked_ids: set[int] = set(seen)

    if ranked:
        # Resolve endorser display names for the reason strings.
        endorser_ids = {uid for c in ranked for uid in c.endorsers}
        name_rows = (
            await session.execute(
                select(User.id, User.display_name, User.username).where(
                    User.id.in_(endorser_ids)
                )
            )
        ).all()
        names = {uid: (dn or un) for uid, dn, un in name_rows}

        film_ids = [c.film_id for c in ranked]
        films = {
            f.id: f
            for f in (
                await session.execute(select(Film).where(Film.id.in_(film_ids)))
            ).scalars().all()
        }
        for cand in ranked:
            film = films.get(cand.film_id)
            if film is None:
                continue
            results.append(_to_summary(film, _reason(cand, names)))
            picked_ids.add(film.id)

    # Top up with popular, well-rated films the user hasn't seen.
    if len(results) < limit:
        need = limit - len(results)
        stmt = (
            select(Film)
            .where(
                Film.vote_average.isnot(None),
                Film.vote_count.isnot(None),
                Film.vote_count >= 100,
            )
            .order_by(Film.vote_average.desc(), Film.vote_count.desc())
            .limit(need)
        )
        if picked_ids:
            stmt = stmt.where(Film.id.notin_(picked_ids))
        popular = (await session.execute(stmt)).scalars().all()
        for film in popular:
            results.append(_to_summary(film, "Popular and well-rated"))

    return results
