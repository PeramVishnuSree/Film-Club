"""Import a Letterboxd CSV export into a user's library.

Letterboxd's "Export your data" produces several CSVs. We support the three
that map cleanly onto our models:

- **watchlist.csv** — Date, Name, Year, Letterboxd URI
- **ratings.csv**   — Date, Name, Year, Letterboxd URI, Rating
- **diary.csv**     — Date, Name, Year, Letterboxd URI, Rating, Rewatch, Tags, Watched Date

The export has no TMDB id, only a Letterboxd slug, so each film is resolved by
searching TMDB on title (+ release year) and taking the best match. Unmatched
titles are reported back rather than silently dropped. Imports are idempotent:
re-running won't create duplicate watchlist items, ratings, or same-day diary
entries.
"""

from __future__ import annotations

import csv
import io
from datetime import date

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DiaryEntry, Rating, User, WatchlistItem
from app.schemas.importing import ImportResult
from app.services.film_cache import get_or_cache_film
from app.services.tmdb import TMDBClient

# Safety cap so a huge export can't tie up a request indefinitely.
MAX_ROWS = 1000


def _detect_kind(fieldnames: list[str]) -> str:
    names = {f.strip().lower() for f in fieldnames}
    if "watched date" in names:
        return "diary"
    if "rating" in names:
        return "ratings"
    return "watchlist"


def _parse_year(raw: str | None) -> int | None:
    if not raw:
        return None
    try:
        return int(raw.strip()[:4])
    except (ValueError, TypeError):
        return None


def _parse_rating(raw: str | None) -> float | None:
    if not raw or not raw.strip():
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    # Letterboxd uses the same 0.5–5.0 half-star scale we do.
    if 0.5 <= value <= 5.0 and (value * 2) % 1 == 0:
        return value
    return None


def _parse_date(raw: str | None) -> date | None:
    if not raw or not raw.strip():
        return None
    try:
        return date.fromisoformat(raw.strip()[:10])
    except ValueError:
        return None


async def _resolve_tmdb_id(
    tmdb: TMDBClient, title: str, year: int | None, cache: dict[tuple[str, int | None], int | None]
) -> int | None:
    key = (title.lower(), year)
    if key in cache:
        return cache[key]
    result: int | None = None
    try:
        data = await tmdb.search_movies(title, year=year)
        results = data.get("results") or []
        if not results and year is not None:
            # Retry without the year constraint — Letterboxd years can be off
            # by one versus TMDB's primary release year.
            data = await tmdb.search_movies(title)
            results = data.get("results") or []
        if results:
            result = results[0]["id"]
    except httpx.HTTPError:
        result = None
    cache[key] = result
    return result


async def import_letterboxd_csv(
    session: AsyncSession,
    tmdb: TMDBClient,
    user: User,
    raw_csv: str,
) -> ImportResult:
    reader = csv.DictReader(io.StringIO(raw_csv))
    if reader.fieldnames is None:
        return ImportResult(kind="unknown", rows=0, imported=0, skipped=0, unmatched=[])

    kind = _detect_kind(list(reader.fieldnames))
    rows = 0
    imported = 0
    skipped = 0
    unmatched: list[str] = []
    resolve_cache: dict[tuple[str, int | None], int | None] = {}

    for row in reader:
        if rows >= MAX_ROWS:
            break
        title = (row.get("Name") or "").strip()
        if not title:
            continue
        rows += 1
        year = _parse_year(row.get("Year"))

        tmdb_id = await _resolve_tmdb_id(tmdb, title, year, resolve_cache)
        if tmdb_id is None:
            unmatched.append(title if not year else f"{title} ({year})")
            continue

        try:
            film = await get_or_cache_film(session, tmdb, tmdb_id, user.region)
        except httpx.HTTPError:
            unmatched.append(title)
            continue

        if kind == "watchlist":
            exists = (
                await session.execute(
                    select(WatchlistItem.id).where(
                        WatchlistItem.user_id == user.id,
                        WatchlistItem.film_id == film.id,
                    )
                )
            ).first()
            if exists:
                skipped += 1
            else:
                session.add(WatchlistItem(user_id=user.id, film_id=film.id))
                imported += 1

        elif kind == "ratings":
            value = _parse_rating(row.get("Rating"))
            if value is None:
                skipped += 1
                continue
            existing = (
                await session.execute(
                    select(Rating).where(
                        Rating.user_id == user.id, Rating.film_id == film.id
                    )
                )
            ).scalar_one_or_none()
            if existing is None:
                session.add(
                    Rating(user_id=user.id, film_id=film.id, value=value)
                )
                imported += 1
            else:
                existing.value = value
                skipped += 1

        else:  # diary
            watched_on = _parse_date(row.get("Watched Date")) or _parse_date(
                row.get("Date")
            )
            if watched_on is None:
                skipped += 1
                continue
            dup = (
                await session.execute(
                    select(DiaryEntry.id).where(
                        DiaryEntry.user_id == user.id,
                        DiaryEntry.film_id == film.id,
                        DiaryEntry.watched_on == watched_on,
                    )
                )
            ).first()
            if dup:
                skipped += 1
                continue
            rewatch = (row.get("Rewatch") or "").strip().lower() in ("yes", "true", "1")
            session.add(
                DiaryEntry(
                    user_id=user.id,
                    film_id=film.id,
                    watched_on=watched_on,
                    rating_value=_parse_rating(row.get("Rating")),
                    rewatch=rewatch,
                    note=(row.get("Tags") or None),
                )
            )
            imported += 1

    await session.commit()
    return ImportResult(
        kind=kind,
        rows=rows,
        imported=imported,
        skipped=skipped,
        unmatched=unmatched[:50],  # cap the list returned to the client
    )
