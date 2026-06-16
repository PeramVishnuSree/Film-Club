from datetime import datetime

from pydantic import BaseModel


class UserCard(BaseModel):
    """Compact public identity, used in lists and as a feed actor."""

    id: int
    username: str
    display_name: str | None = None
    avatar_url: str | None = None
    bio: str | None = None

    model_config = {"from_attributes": True}


class ProfileStats(BaseModel):
    films_logged: int
    reviews: int
    followers: int
    following: int


class ProfileOut(BaseModel):
    id: int
    username: str
    display_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    created_at: datetime
    stats: ProfileStats
    is_following: bool  # does the requester follow this profile?
    is_self: bool


class FeedFilm(BaseModel):
    tmdb_id: int
    title: str
    poster_path: str | None = None


class FeedItem(BaseModel):
    id: int  # interaction id (also a pagination cursor)
    actor: UserCard
    type: str  # log | rate | review | watchlist_add | like | list_add
    value: float | None = None
    film: FeedFilm
    created_at: datetime
