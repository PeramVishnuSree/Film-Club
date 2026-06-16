from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, TimestampMixin


class Rating(Base, TimestampMixin):
    """A user's current rating of a film (0.5–5.0). One per user/film."""

    __tablename__ = "ratings"
    __table_args__ = (UniqueConstraint("user_id", "film_id", name="uq_rating_user_film"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    film_id: Mapped[int] = mapped_column(
        ForeignKey("films.id", ondelete="CASCADE"), index=True, nullable=False
    )
    value: Mapped[float] = mapped_column(Float, nullable=False)


class DiaryEntry(Base, TimestampMixin):
    """A logged watch on a date (the journal). Multiple rows per film = rewatches."""

    __tablename__ = "diary_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    film_id: Mapped[int] = mapped_column(
        ForeignKey("films.id", ondelete="CASCADE"), index=True, nullable=False
    )
    watched_on: Mapped[date] = mapped_column(Date, nullable=False)
    rating_value: Mapped[float | None] = mapped_column(Float)
    liked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rewatch: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    note: Mapped[str | None] = mapped_column(Text)


class WatchlistItem(Base, TimestampMixin):
    __tablename__ = "watchlist_items"
    __table_args__ = (UniqueConstraint("user_id", "film_id", name="uq_watchlist_user_film"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    film_id: Mapped[int] = mapped_column(
        ForeignKey("films.id", ondelete="CASCADE"), index=True, nullable=False
    )


class Review(Base, TimestampMixin):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    film_id: Mapped[int] = mapped_column(
        ForeignKey("films.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # Optional link to the watch this review is about.
    diary_entry_id: Mapped[int | None] = mapped_column(
        ForeignKey("diary_entries.id", ondelete="SET NULL")
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    contains_spoilers: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class List(Base, TimestampMixin):
    """User-curated list. The 'Top 500' is a system list (is_system=True)."""

    __tablename__ = "lists"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Nullable owner so system lists (Top 500) can be ownerless.
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_ranked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ListItem(Base, TimestampMixin):
    __tablename__ = "list_items"
    __table_args__ = (UniqueConstraint("list_id", "film_id", name="uq_list_film"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    list_id: Mapped[int] = mapped_column(
        ForeignKey("lists.id", ondelete="CASCADE"), index=True, nullable=False
    )
    film_id: Mapped[int] = mapped_column(
        ForeignKey("films.id", ondelete="CASCADE"), index=True, nullable=False
    )
    rank: Mapped[int | None] = mapped_column(Integer)
    note: Mapped[str | None] = mapped_column(Text)


class ReviewLike(Base, TimestampMixin):
    """A user's like on a review. FK cascade drops likes when either side goes."""

    __tablename__ = "review_likes"
    __table_args__ = (UniqueConstraint("user_id", "review_id", name="uq_review_like"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    review_id: Mapped[int] = mapped_column(
        ForeignKey("reviews.id", ondelete="CASCADE"), index=True, nullable=False
    )


class ListLike(Base, TimestampMixin):
    """A user's like on a list."""

    __tablename__ = "list_likes"
    __table_args__ = (UniqueConstraint("user_id", "list_id", name="uq_list_like"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    list_id: Mapped[int] = mapped_column(
        ForeignKey("lists.id", ondelete="CASCADE"), index=True, nullable=False
    )
