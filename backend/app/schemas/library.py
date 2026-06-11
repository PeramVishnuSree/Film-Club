from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator


class RatingIn(BaseModel):
    value: float = Field(ge=0.5, le=5.0)

    @field_validator("value")
    @classmethod
    def half_steps(cls, v: float) -> float:
        if (v * 2) % 1 != 0:
            raise ValueError("rating must be in 0.5 increments")
        return v


class RatingOut(BaseModel):
    film_tmdb_id: int
    value: float


class FilmMeState(BaseModel):
    """Current user's relationship to a film, for rendering the film page."""

    rating: float | None = None
    watchlisted: bool = False
    watched: bool = False


class DiaryIn(BaseModel):
    watched_on: date
    rating_value: float | None = Field(default=None, ge=0.5, le=5.0)
    liked: bool = False
    rewatch: bool = False
    note: str | None = None


class DiaryOut(BaseModel):
    id: int
    film_tmdb_id: int
    film_title: str
    poster_path: str | None = None
    watched_on: date
    rating_value: float | None = None
    liked: bool
    rewatch: bool
    note: str | None = None
    created_at: datetime


class ReviewIn(BaseModel):
    body: str = Field(min_length=1)
    contains_spoilers: bool = False
    diary_entry_id: int | None = None


class ReviewAuthor(BaseModel):
    id: int
    username: str
    display_name: str | None = None


class ReviewOut(BaseModel):
    id: int
    film_tmdb_id: int
    author: ReviewAuthor
    body: str
    contains_spoilers: bool
    created_at: datetime
