from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.social import UserCard


class ListCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    is_ranked: bool = False
    is_public: bool = True


class ListUpdate(BaseModel):
    """All optional; only provided fields change."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    is_ranked: bool | None = None
    is_public: bool | None = None


class ListItemIn(BaseModel):
    tmdb_id: int
    note: str | None = Field(default=None, max_length=2000)


class ListItemNote(BaseModel):
    note: str | None = Field(default=None, max_length=2000)


class ListReorder(BaseModel):
    """Full new ordering of the list, given as tmdb_ids top to bottom."""

    tmdb_ids: list[int]


class ListFilm(BaseModel):
    tmdb_id: int
    title: str
    release_date: str | None = None
    poster_path: str | None = None
    vote_average: float | None = None


class ListItemOut(BaseModel):
    film: ListFilm
    rank: int | None = None
    note: str | None = None


class ListSummary(BaseModel):
    id: int
    title: str
    description: str | None = None
    is_ranked: bool
    is_public: bool
    is_system: bool
    item_count: int
    owner: UserCard | None = None  # null for system lists
    created_at: datetime
    # First few posters, for a preview thumbnail strip.
    preview_posters: list[str] = []
    like_count: int = 0
    liked: bool = False  # whether the requesting user liked it


class ListDetail(ListSummary):
    items: list[ListItemOut] = []
    is_owner: bool = False
