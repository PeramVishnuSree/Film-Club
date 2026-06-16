"""Import all models so Base.metadata is fully populated (used by Alembic)."""

from app.models.film import (
    Film,
    FilmCredit,
    FilmGenre,
    FilmKeyword,
    FilmWatchProvider,
    Genre,
    Keyword,
    Person,
)
from app.models.interaction import Interaction, InteractionType
from app.models.library import (
    DiaryEntry,
    List,
    ListItem,
    ListLike,
    Rating,
    Review,
    ReviewLike,
    WatchlistItem,
)
from app.models.user import Follow, User

__all__ = [
    "User",
    "Follow",
    "Film",
    "Genre",
    "FilmGenre",
    "Keyword",
    "FilmKeyword",
    "Person",
    "FilmCredit",
    "FilmWatchProvider",
    "Rating",
    "DiaryEntry",
    "WatchlistItem",
    "Review",
    "List",
    "ListItem",
    "ReviewLike",
    "ListLike",
    "Interaction",
    "InteractionType",
]
