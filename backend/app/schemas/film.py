from datetime import date
from typing import Any

from pydantic import BaseModel


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


class FilmSummary(BaseModel):
    tmdb_id: int
    title: str
    release_date: date | None = None
    overview: str | None = None
    poster_path: str | None = None
    vote_average: float | None = None

    @classmethod
    def from_tmdb(cls, data: dict[str, Any]) -> "FilmSummary":
        return cls(
            tmdb_id=data["id"],
            title=data.get("title") or data.get("name") or "",
            release_date=_parse_date(data.get("release_date")),
            overview=data.get("overview"),
            poster_path=data.get("poster_path"),
            vote_average=data.get("vote_average"),
        )


class NamedRef(BaseModel):
    id: int
    name: str


class CreditOut(BaseModel):
    person_id: int
    name: str
    credit_type: str
    job: str | None = None
    character: str | None = None


class ProviderOut(BaseModel):
    provider_id: int
    provider_name: str
    logo_path: str | None = None
    offer_type: str


class FilmDetail(BaseModel):
    tmdb_id: int
    media_type: str
    title: str
    original_title: str | None = None
    overview: str | None = None
    release_date: date | None = None
    runtime: int | None = None
    poster_path: str | None = None
    backdrop_path: str | None = None
    vote_average: float | None = None
    vote_count: int | None = None
    region: str
    genres: list[NamedRef]
    keywords: list[NamedRef]
    cast: list[CreditOut]
    crew: list[CreditOut]
    watch_providers: list[ProviderOut]
