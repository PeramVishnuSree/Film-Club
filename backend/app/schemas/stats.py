from pydantic import BaseModel


class RatingBucket(BaseModel):
    value: float  # 0.5 .. 5.0
    count: int


class GenreCount(BaseModel):
    name: str
    count: int


class MonthCount(BaseModel):
    month: int  # 1..12
    count: int


class TopFilm(BaseModel):
    tmdb_id: int
    title: str
    poster_path: str | None = None
    rating: float | None = None


class YearStats(BaseModel):
    year: int
    entries: int  # diary entries logged in the year (rewatches counted)
    distinct_films: int
    hours: float  # total runtime of logged films, in hours
    by_month: list[MonthCount]
    top_genres: list[GenreCount]
    top_films: list[TopFilm]


class LifetimeStats(BaseModel):
    films_logged: int  # distinct films ever logged
    entries: int  # total diary entries
    ratings: int
    reviews: int
    lists: int
    average_rating: float | None = None
    rating_distribution: list[RatingBucket]


class StatsOut(BaseModel):
    lifetime: LifetimeStats
    year: YearStats
    available_years: list[int]  # years the user has diary activity, descending
